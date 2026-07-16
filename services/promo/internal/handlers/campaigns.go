package handlers

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/hook-press/promo/internal/models"
	"github.com/hook-press/promo/internal/sink"
	"github.com/hook-press/promo/internal/store"
)

// CampaignHandler serves campaign CRUD and stats endpoints.
type CampaignHandler struct {
	Store  *store.Store
	Sink   *sink.ClickHouseSink
	Clock  func() time.Time
	Events chan struct{}
}

func (h *CampaignHandler) now() time.Time {
	if h.Clock != nil {
		return h.Clock()
	}
	return time.Now().UTC()
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]any{
		"error": map[string]string{"code": code, "message": message},
	})
}

// ServeHTTP routes campaign API requests.
func (h *CampaignHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/api/v1/campaigns")
	path = strings.Trim(path, "/")

	switch {
	case path == "" && r.Method == http.MethodGet:
		h.list(w, r)
	case path == "" && r.Method == http.MethodPost:
		h.create(w, r)
	case path != "" && !strings.Contains(path, "/") && r.Method == http.MethodGet:
		h.get(w, r, path)
	case path != "" && !strings.Contains(path, "/") && r.Method == http.MethodPatch:
		h.update(w, r, path)
	case path != "" && !strings.Contains(path, "/") && r.Method == http.MethodDelete:
		h.delete(w, r, path)
	case strings.HasSuffix(path, "/stats") && r.Method == http.MethodGet:
		id := strings.TrimSuffix(path, "/stats")
		h.stats(w, r, id)
	case strings.HasSuffix(path, "/events") && r.Method == http.MethodPost:
		id := strings.TrimSuffix(path, "/events")
		h.recordEvent(w, r, id)
	case strings.HasSuffix(path, "/listen") && r.Method == http.MethodPost:
		id := strings.TrimSuffix(path, "/listen")
		h.listen(w, r, id)
	case strings.HasSuffix(path, "/rate") && r.Method == http.MethodPost:
		id := strings.TrimSuffix(path, "/rate")
		h.rate(w, r, id)
	default:
		writeError(w, http.StatusNotFound, "not_found", "route not found")
	}
}

func (h *CampaignHandler) list(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"items": h.Store.List()})
}

func (h *CampaignHandler) create(w http.ResponseWriter, r *http.Request) {
	var req models.CreateCampaignRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", "invalid JSON body")
		return
	}
	if req.Name == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "name is required")
		return
	}
	if req.BudgetCents <= 0 {
		writeError(w, http.StatusBadRequest, "validation_error", "budget_cents must be positive")
		return
	}
	c := h.Store.Create(req)
	writeJSON(w, http.StatusCreated, c)
}

func (h *CampaignHandler) get(w http.ResponseWriter, _ *http.Request, id string) {
	c, err := h.Store.Get(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "campaign not found")
		return
	}
	writeJSON(w, http.StatusOK, c)
}

func (h *CampaignHandler) update(w http.ResponseWriter, r *http.Request, id string) {
	var req models.UpdateCampaignRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", "invalid JSON body")
		return
	}
	c, err := h.Store.Update(id, req)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "campaign not found")
		return
	}
	writeJSON(w, http.StatusOK, c)
}

func (h *CampaignHandler) delete(w http.ResponseWriter, _ *http.Request, id string) {
	if err := h.Store.Delete(id); err != nil {
		writeError(w, http.StatusNotFound, "not_found", "campaign not found")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (h *CampaignHandler) stats(w http.ResponseWriter, _ *http.Request, id string) {
	st, err := h.Store.Stats(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", "campaign not found")
		return
	}
	writeJSON(w, http.StatusOK, st)
}

func (h *CampaignHandler) recordEvent(w http.ResponseWriter, r *http.Request, id string) {
	var req models.RecordEventRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", "invalid JSON body")
		return
	}
	ev, err := h.Store.RecordEvent(id, req, h.now())
	if err != nil {
		h.writeEventError(w, err)
		return
	}
	if h.Sink != nil {
		if err := h.Sink.InsertEvent(r.Context(), ev); err != nil {
			writeError(w, http.StatusBadGateway, "sink_error", "failed to persist event")
			return
		}
	}
	h.notifyEvent()
	writeJSON(w, http.StatusCreated, ev)
}

func (h *CampaignHandler) listen(w http.ResponseWriter, r *http.Request, id string) {
	var req models.ListenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", "invalid JSON body")
		return
	}
	if req.UserID == "" || req.TrackID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "user_id and track_id are required")
		return
	}
	ev, err := h.Store.RecordListen(id, req, h.now())
	if err != nil {
		h.writeEventError(w, err)
		return
	}
	if h.Sink != nil {
		if err := h.Sink.InsertEvent(r.Context(), ev); err != nil {
			writeError(w, http.StatusBadGateway, "sink_error", "failed to persist event")
			return
		}
	}
	h.notifyEvent()
	writeJSON(w, http.StatusCreated, ev)
}

func (h *CampaignHandler) rate(w http.ResponseWriter, r *http.Request, id string) {
	var req models.RateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_body", "invalid JSON body")
		return
	}
	if req.UserID == "" || req.TrackID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "user_id and track_id are required")
		return
	}
	record, err := h.Store.RecordRating(id, req, h.now())
	if err != nil {
		h.writeEventError(w, err)
		return
	}
	h.notifyEvent()
	writeJSON(w, http.StatusCreated, record)
}

func (h *CampaignHandler) writeEventError(w http.ResponseWriter, err error) {
	switch err {
	case store.ErrNotFound:
		writeError(w, http.StatusNotFound, "not_found", "campaign not found")
	case store.ErrBudgetExceeded:
		writeError(w, http.StatusPaymentRequired, "budget_exceeded", "campaign budget exceeded")
	case store.ErrNotScheduled:
		writeError(w, http.StatusConflict, "outside_schedule", "campaign outside schedule window")
	case store.ErrInvalidStatus:
		writeError(w, http.StatusConflict, "invalid_status", "campaign must be active")
	case store.ErrDuplicateEvent:
		writeError(w, http.StatusConflict, "duplicate_event", "duplicate event within antifraud window")
	default:
		writeError(w, http.StatusBadRequest, "invalid_event", err.Error())
	}
}

func (h *CampaignHandler) notifyEvent() {
	if h.Events != nil {
		select {
		case h.Events <- struct{}{}:
		default:
		}
	}
}
