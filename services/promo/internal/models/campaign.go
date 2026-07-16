package models

import "time"

// CampaignStatus represents campaign lifecycle state.
type CampaignStatus string

const (
	CampaignStatusDraft    CampaignStatus = "draft"
	CampaignStatusActive   CampaignStatus = "active"
	CampaignStatusPaused   CampaignStatus = "paused"
	CampaignStatusCompleted CampaignStatus = "completed"
)

// Campaign is a legal internal promotion campaign.
type Campaign struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	Description string         `json:"description,omitempty"`
	BudgetCents int64          `json:"budget_cents"`
	SpentCents  int64          `json:"spent_cents"`
	Status      CampaignStatus `json:"status"`
	Schedule    Schedule       `json:"schedule"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
}

// Schedule defines when a campaign may run (internal listening only).
type Schedule struct {
	StartAt time.Time `json:"start_at"`
	EndAt   time.Time `json:"end_at"`
}

// IsWithinSchedule returns true if now falls within the campaign window.
func (c Campaign) IsWithinSchedule(now time.Time) bool {
	if c.Schedule.StartAt.IsZero() && c.Schedule.EndAt.IsZero() {
		return true
	}
	if !c.Schedule.StartAt.IsZero() && now.Before(c.Schedule.StartAt) {
		return false
	}
	if !c.Schedule.EndAt.IsZero() && now.After(c.Schedule.EndAt) {
		return false
	}
	return true
}

// HasBudget returns true if spent amount is below budget limit.
func (c Campaign) HasBudget(additionalCents int64) bool {
	return c.SpentCents+additionalCents <= c.BudgetCents
}

// CreateCampaignRequest is the payload for POST /campaigns.
type CreateCampaignRequest struct {
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	BudgetCents int64    `json:"budget_cents"`
	Schedule    Schedule `json:"schedule"`
}

// UpdateCampaignRequest is the payload for PATCH /campaigns/{id}.
type UpdateCampaignRequest struct {
	Name        *string         `json:"name,omitempty"`
	Description *string         `json:"description,omitempty"`
	BudgetCents *int64          `json:"budget_cents,omitempty"`
	Status      *CampaignStatus `json:"status,omitempty"`
	Schedule    *Schedule       `json:"schedule,omitempty"`
}

// CampaignStats aggregates internal listening metrics.
type CampaignStats struct {
	CampaignID      string  `json:"campaign_id"`
	Impressions     int64   `json:"impressions"`
	Listens         int64   `json:"listens"`
	Completes       int64   `json:"completes"`
	SpentCents      int64   `json:"spent_cents"`
	BudgetRemaining int64   `json:"budget_remaining"`
	AvgRating       float64 `json:"avg_rating,omitempty"`
	RatingCount     int64   `json:"rating_count,omitempty"`
}

// RatingRecord stores voluntary user feedback.
type RatingRecord struct {
	ID         string    `json:"id"`
	CampaignID string    `json:"campaign_id"`
	UserID     string    `json:"user_id"`
	TrackID    string    `json:"track_id"`
	Score      int       `json:"score"`
	EventID    string    `json:"event_id"`
	CreatedAt  time.Time `json:"created_at"`
}
