package models

import "time"

// EventType is an internal promo listening event (legal, in-app only).
type EventType string

const (
	EventTypeImpression EventType = "impression"
	EventTypeListen     EventType = "listen"
	EventTypeComplete   EventType = "complete"
	EventTypeRating     EventType = "rating"
)

// PromoEvent records voluntary in-app listening activity.
type PromoEvent struct {
	ID         string    `json:"id"`
	CampaignID string    `json:"campaign_id"`
	EventType  EventType `json:"event_type"`
	UserID     string    `json:"user_id,omitempty"`
	TrackID    string    `json:"track_id,omitempty"`
	CostCents  int64     `json:"cost_cents"`
	OccurredAt time.Time `json:"occurred_at"`
}

// RecordEventRequest is the payload for POST /campaigns/{id}/events.
type RecordEventRequest struct {
	EventType EventType `json:"event_type"`
	UserID    string    `json:"user_id,omitempty"`
	TrackID   string    `json:"track_id,omitempty"`
}

// ListenRequest is the payload for voluntary listening POST /campaigns/{id}/listen.
type ListenRequest struct {
	UserID  string `json:"user_id"`
	TrackID string `json:"track_id"`
}

// RateRequest is the payload for voluntary feedback POST /campaigns/{id}/rate.
type RateRequest struct {
	UserID  string `json:"user_id"`
	TrackID string `json:"track_id"`
	Score   int    `json:"score"`
}

// EventCost returns the internal cost in cents for an event type.
func EventCost(eventType EventType) int64 {
	switch eventType {
	case EventTypeImpression:
		return 1
	case EventTypeListen:
		return 5
	case EventTypeComplete:
		return 10
	case EventTypeRating:
		return 2
	default:
		return 0
	}
}
