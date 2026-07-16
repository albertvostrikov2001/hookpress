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

func TestListenAndRateEndpoints(t *testing.T) {
	st := store.New()
	h := &CampaignHandler{
		Store: st,
		Clock: func() time.Time {
			return time.Date(2026, 7, 15, 0, 0, 0, 0, time.UTC)
		},
	}

	body, _ := json.Marshal(models.CreateCampaignRequest{Name: "Promo", BudgetCents: 500})
	req := httptest.NewRequest(http.MethodPost, "/api/v1/campaigns", bytes.NewReader(body))
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	var created models.Campaign
	if err := json.Unmarshal(rec.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}

	active := models.CampaignStatusActive
	patch, _ := json.Marshal(models.UpdateCampaignRequest{Status: &active})
	req = httptest.NewRequest(http.MethodPatch, "/api/v1/campaigns/"+created.ID, bytes.NewReader(patch))
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)

	listenBody, _ := json.Marshal(models.ListenRequest{UserID: "u1", TrackID: "track-1"})
	req = httptest.NewRequest(http.MethodPost, "/api/v1/campaigns/"+created.ID+"/listen", bytes.NewReader(listenBody))
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("listen status=%d body=%s", rec.Code, rec.Body.String())
	}

	rateBody, _ := json.Marshal(models.RateRequest{UserID: "u1", TrackID: "track-1", Score: 4})
	req = httptest.NewRequest(http.MethodPost, "/api/v1/campaigns/"+created.ID+"/rate", bytes.NewReader(rateBody))
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("rate status=%d body=%s", rec.Code, rec.Body.String())
	}

	req = httptest.NewRequest(http.MethodGet, "/api/v1/campaigns/"+created.ID+"/stats", nil)
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	var stats models.CampaignStats
	if err := json.Unmarshal(rec.Body.Bytes(), &stats); err != nil {
		t.Fatal(err)
	}
	if stats.Listens != 1 || stats.RatingCount != 1 {
		t.Fatalf("unexpected stats: %+v", stats)
	}
}
