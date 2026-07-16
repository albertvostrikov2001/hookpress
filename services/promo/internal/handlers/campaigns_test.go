package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/hook-press/promo/internal/models"
	"github.com/hook-press/promo/internal/store"
)

func TestCampaignCRUDAPI(t *testing.T) {
	st := store.New()
	h := &CampaignHandler{Store: st, Clock: func() time.Time {
		return time.Date(2026, 7, 15, 0, 0, 0, 0, time.UTC)
	}}

	body, _ := json.Marshal(models.CreateCampaignRequest{
		Name:        "Launch",
		BudgetCents: 500,
	})
	req := httptest.NewRequest(http.MethodPost, "/api/v1/campaigns", bytes.NewReader(body))
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("create status=%d body=%s", rec.Code, rec.Body.String())
	}
	var created models.Campaign
	if err := json.Unmarshal(rec.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}

	req = httptest.NewRequest(http.MethodGet, "/api/v1/campaigns/"+created.ID, nil)
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("get status=%d", rec.Code)
	}

	active := models.CampaignStatusActive
	patch, _ := json.Marshal(models.UpdateCampaignRequest{Status: &active})
	req = httptest.NewRequest(http.MethodPatch, "/api/v1/campaigns/"+created.ID, bytes.NewReader(patch))
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("patch status=%d", rec.Code)
	}

	evBody, _ := json.Marshal(models.RecordEventRequest{
		EventType: models.EventTypeListen,
		UserID:    "u1",
		TrackID:   "t1",
	})
	req = httptest.NewRequest(http.MethodPost, "/api/v1/campaigns/"+created.ID+"/events", bytes.NewReader(evBody))
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("event status=%d body=%s", rec.Code, rec.Body.String())
	}

	req = httptest.NewRequest(http.MethodGet, "/api/v1/campaigns/"+created.ID+"/stats", nil)
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("stats status=%d", rec.Code)
	}
	var stats models.CampaignStats
	if err := json.Unmarshal(rec.Body.Bytes(), &stats); err != nil {
		t.Fatal(err)
	}
	if stats.Listens != 1 {
		t.Fatalf("expected 1 listen, got %d", stats.Listens)
	}
}

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rec := httptest.NewRecorder()
	(&HealthHandler{}).ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}
}
