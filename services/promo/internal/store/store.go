package store

import (
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/hook-press/promo/internal/models"
)

var (
	ErrNotFound       = errors.New("campaign not found")
	ErrBudgetExceeded = errors.New("campaign budget exceeded")
	ErrNotScheduled   = errors.New("campaign outside schedule window")
	ErrInvalidStatus  = errors.New("campaign not active")
	ErrDuplicateEvent = errors.New("duplicate event detected")
)

const antifraudWindow = 60 * time.Second

type eventFingerprint struct {
	seenAt time.Time
}

// Store is an in-memory campaign and event store.
type Store struct {
	mu          sync.RWMutex
	campaigns   map[string]*models.Campaign
	stats       map[string]*models.CampaignStats
	recent      map[string]eventFingerprint
	ratings     map[string][]models.RatingRecord
}

// New creates an empty store.
func New() *Store {
	return &Store{
		campaigns: make(map[string]*models.Campaign),
		stats:     make(map[string]*models.CampaignStats),
		recent:    make(map[string]eventFingerprint),
		ratings:   make(map[string][]models.RatingRecord),
	}
}

// List returns all campaigns.
func (s *Store) List() []models.Campaign {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]models.Campaign, 0, len(s.campaigns))
	for _, c := range s.campaigns {
		out = append(out, *c)
	}
	return out
}

// Get returns a campaign by ID.
func (s *Store) Get(id string) (models.Campaign, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	c, ok := s.campaigns[id]
	if !ok {
		return models.Campaign{}, ErrNotFound
	}
	return *c, nil
}

// Create inserts a new campaign.
func (s *Store) Create(req models.CreateCampaignRequest) models.Campaign {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC()
	c := &models.Campaign{
		ID:          uuid.NewString(),
		Name:        req.Name,
		Description: req.Description,
		BudgetCents: req.BudgetCents,
		Status:      models.CampaignStatusDraft,
		Schedule:    req.Schedule,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	s.campaigns[c.ID] = c
	s.stats[c.ID] = &models.CampaignStats{CampaignID: c.ID}
	return *c
}

// Update modifies an existing campaign.
func (s *Store) Update(id string, req models.UpdateCampaignRequest) (models.Campaign, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, ok := s.campaigns[id]
	if !ok {
		return models.Campaign{}, ErrNotFound
	}
	if req.Name != nil {
		c.Name = *req.Name
	}
	if req.Description != nil {
		c.Description = *req.Description
	}
	if req.BudgetCents != nil {
		c.BudgetCents = *req.BudgetCents
	}
	if req.Status != nil {
		c.Status = *req.Status
	}
	if req.Schedule != nil {
		c.Schedule = *req.Schedule
	}
	c.UpdatedAt = time.Now().UTC()
	return *c, nil
}

// Delete removes a campaign.
func (s *Store) Delete(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.campaigns[id]; !ok {
		return ErrNotFound
	}
	delete(s.campaigns, id)
	delete(s.stats, id)
	delete(s.ratings, id)
	return nil
}

func (s *Store) fingerprint(campaignID string, req models.RecordEventRequest) string {
	return fmt.Sprintf("%s:%s:%s:%s", campaignID, req.EventType, req.UserID, req.TrackID)
}

func (s *Store) checkDuplicate(key string, now time.Time) error {
	if prev, ok := s.recent[key]; ok && now.Sub(prev.seenAt) < antifraudWindow {
		return ErrDuplicateEvent
	}
	s.recent[key] = eventFingerprint{seenAt: now}
	return nil
}

// RecordEvent appends an internal listening event and updates spend.
func (s *Store) RecordEvent(campaignID string, req models.RecordEventRequest, now time.Time) (models.PromoEvent, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, ok := s.campaigns[campaignID]
	if !ok {
		return models.PromoEvent{}, ErrNotFound
	}
	if c.Status != models.CampaignStatusActive {
		return models.PromoEvent{}, ErrInvalidStatus
	}
	if !c.IsWithinSchedule(now) {
		return models.PromoEvent{}, ErrNotScheduled
	}
	if err := s.checkDuplicate(s.fingerprint(campaignID, req), now); err != nil {
		return models.PromoEvent{}, err
	}
	cost := models.EventCost(req.EventType)
	if cost == 0 {
		return models.PromoEvent{}, errors.New("unknown event type")
	}
	if !c.HasBudget(cost) {
		return models.PromoEvent{}, ErrBudgetExceeded
	}
	c.SpentCents += cost
	c.UpdatedAt = now
	st := s.stats[campaignID]
	switch req.EventType {
	case models.EventTypeImpression:
		st.Impressions++
	case models.EventTypeListen:
		st.Listens++
	case models.EventTypeComplete:
		st.Completes++
	}
	st.SpentCents = c.SpentCents
	st.BudgetRemaining = c.BudgetCents - c.SpentCents
	ev := models.PromoEvent{
		ID:         uuid.NewString(),
		CampaignID: campaignID,
		EventType:  req.EventType,
		UserID:     req.UserID,
		TrackID:    req.TrackID,
		CostCents:  cost,
		OccurredAt: now,
	}
	return ev, nil
}

// RecordListen records voluntary listening for an active campaign.
func (s *Store) RecordListen(campaignID string, req models.ListenRequest, now time.Time) (models.PromoEvent, error) {
	return s.RecordEvent(campaignID, models.RecordEventRequest{
		EventType: models.EventTypeListen,
		UserID:    req.UserID,
		TrackID:   req.TrackID,
	}, now)
}

// RecordRating records voluntary feedback and stores the rating score.
func (s *Store) RecordRating(campaignID string, req models.RateRequest, now time.Time) (models.RatingRecord, error) {
	if req.Score < 1 || req.Score > 5 {
		return models.RatingRecord{}, errors.New("score must be between 1 and 5")
	}
	ev, err := s.RecordEvent(campaignID, models.RecordEventRequest{
		EventType: models.EventTypeRating,
		UserID:    req.UserID,
		TrackID:   req.TrackID,
	}, now)
	if err != nil {
		return models.RatingRecord{}, err
	}
	record := models.RatingRecord{
		ID:         uuid.NewString(),
		CampaignID: campaignID,
		UserID:     req.UserID,
		TrackID:    req.TrackID,
		Score:      req.Score,
		EventID:    ev.ID,
		CreatedAt:  now,
	}
	s.mu.Lock()
	s.ratings[campaignID] = append(s.ratings[campaignID], record)
	s.mu.Unlock()
	return record, nil
}

// Stats returns aggregated stats for a campaign.
func (s *Store) Stats(id string) (models.CampaignStats, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	c, ok := s.campaigns[id]
	if !ok {
		return models.CampaignStats{}, ErrNotFound
	}
	st := s.stats[id]
	stats := models.CampaignStats{
		CampaignID:      id,
		Impressions:     st.Impressions,
		Listens:         st.Listens,
		Completes:       st.Completes,
		SpentCents:      st.SpentCents,
		BudgetRemaining: c.BudgetCents - c.SpentCents,
	}
	if ratings, ok := s.ratings[id]; ok && len(ratings) > 0 {
		var total int64
		for _, r := range ratings {
			total += int64(r.Score)
		}
		stats.AvgRating = float64(total) / float64(len(ratings))
		stats.RatingCount = int64(len(ratings))
	}
	return stats, nil
}
