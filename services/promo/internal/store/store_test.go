package store

import (
	"testing"
	"time"

	"github.com/hook-press/promo/internal/models"
)

func TestDuplicateEventDetection(t *testing.T) {
	s := New()
	c := s.Create(models.CreateCampaignRequest{Name: "Dup", BudgetCents: 1000})
	active := models.CampaignStatusActive
	if _, err := s.Update(c.ID, models.UpdateCampaignRequest{Status: &active}); err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 7, 15, 12, 0, 0, 0, time.UTC)
	req := models.RecordEventRequest{
		EventType: models.EventTypeListen,
		UserID:    "user-1",
		TrackID:   "track-1",
	}
	if _, err := s.RecordEvent(c.ID, req, now); err != nil {
		t.Fatalf("first event: %v", err)
	}
	if _, err := s.RecordEvent(c.ID, req, now.Add(time.Second)); err != ErrDuplicateEvent {
		t.Fatalf("expected duplicate, got %v", err)
	}
}

func TestRecordListenAndRating(t *testing.T) {
	s := New()
	c := s.Create(models.CreateCampaignRequest{Name: "Listen", BudgetCents: 1000})
	active := models.CampaignStatusActive
	if _, err := s.Update(c.ID, models.UpdateCampaignRequest{Status: &active}); err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 7, 15, 12, 0, 0, 0, time.UTC)
	if _, err := s.RecordListen(c.ID, models.ListenRequest{UserID: "u1", TrackID: "t1"}, now); err != nil {
		t.Fatalf("listen: %v", err)
	}
	if _, err := s.RecordRating(c.ID, models.RateRequest{UserID: "u1", TrackID: "t1", Score: 5}, now.Add(time.Minute)); err != nil {
		t.Fatalf("rate: %v", err)
	}
	stats, err := s.Stats(c.ID)
	if err != nil {
		t.Fatal(err)
	}
	if stats.Listens != 1 {
		t.Fatalf("expected 1 listen, got %d", stats.Listens)
	}
	if stats.RatingCount != 1 || stats.AvgRating != 5 {
		t.Fatalf("unexpected rating stats: %+v", stats)
	}
}

func TestCampaignBudgetAndSchedule(t *testing.T) {
	s := New()
	start := time.Date(2026, 7, 1, 0, 0, 0, 0, time.UTC)
	end := time.Date(2026, 7, 31, 0, 0, 0, 0, time.UTC)
	c := s.Create(models.CreateCampaignRequest{
		Name:        "Summer",
		BudgetCents: 15,
		Schedule:    models.Schedule{StartAt: start, EndAt: end},
	})
	active := models.CampaignStatusActive
	if _, err := s.Update(c.ID, models.UpdateCampaignRequest{Status: &active}); err != nil {
		t.Fatal(err)
	}

	mid := time.Date(2026, 7, 15, 12, 0, 0, 0, time.UTC)
	if _, err := s.RecordEvent(c.ID, models.RecordEventRequest{
		EventType: models.EventTypeComplete,
		UserID:    "u-budget",
		TrackID:   "t-budget",
	}, mid); err != nil {
		t.Fatalf("record event: %v", err)
	}
	if _, err := s.RecordEvent(c.ID, models.RecordEventRequest{
		EventType: models.EventTypeComplete,
		UserID:    "u-budget-2",
		TrackID:   "t-budget-2",
	}, mid.Add(time.Minute)); err == nil {
		t.Fatal("expected budget exceeded")
	}

	before := time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC)
	if _, err := s.RecordEvent(c.ID, models.RecordEventRequest{
		EventType: models.EventTypeListen,
		UserID:    "u-sched",
		TrackID:   "t-sched",
	}, before); err != ErrNotScheduled {
		t.Fatalf("expected outside schedule, got %v", err)
	}
}

func TestCampaignCRUD(t *testing.T) {
	s := New()
	c := s.Create(models.CreateCampaignRequest{Name: "Test", BudgetCents: 100})
	got, err := s.Get(c.ID)
	if err != nil || got.Name != "Test" {
		t.Fatalf("get: %+v err=%v", got, err)
	}
	name := "Updated"
	if _, err := s.Update(c.ID, models.UpdateCampaignRequest{Name: &name}); err != nil {
		t.Fatal(err)
	}
	if err := s.Delete(c.ID); err != nil {
		t.Fatal(err)
	}
	if _, err := s.Get(c.ID); err != ErrNotFound {
		t.Fatalf("expected not found after delete")
	}
}
