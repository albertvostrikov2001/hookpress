package sink

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/hook-press/promo/internal/models"
)

// ClickHouseSink writes promo events via HTTP INSERT.
type ClickHouseSink struct {
	baseURL string
	db      string
	client  *http.Client
}

// NewClickHouseSink creates a sink targeting ClickHouse HTTP interface.
func NewClickHouseSink(baseURL, db string) *ClickHouseSink {
	return &ClickHouseSink{
		baseURL: baseURL,
		db:      db,
		client: &http.Client{
			Timeout: 5 * time.Second,
		},
	}
}

type chEventRow struct {
	ID         string `json:"id"`
	CampaignID string `json:"campaign_id"`
	EventType  string `json:"event_type"`
	UserID     string `json:"user_id"`
	TrackID    string `json:"track_id"`
	CostCents  int64  `json:"cost_cents"`
	OccurredAt string `json:"occurred_at"`
}

// EnsureTable creates the promo_events table if missing.
func (s *ClickHouseSink) EnsureTable(ctx context.Context) error {
	query := fmt.Sprintf(`
CREATE TABLE IF NOT EXISTS %s.promo_events (
	id String,
	campaign_id String,
	event_type String,
	user_id String,
	track_id String,
	cost_cents Int64,
	occurred_at DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (campaign_id, occurred_at)
`, s.db)
	return s.execQuery(ctx, query)
}

func (s *ClickHouseSink) execQuery(ctx context.Context, query string) error {
	reqURL := s.baseURL + "/?" + url.Values{"query": {query}}.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, reqURL, nil)
	if err != nil {
		return err
	}
	resp, err := s.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("clickhouse query failed (%d): %s", resp.StatusCode, string(body))
	}
	return nil
}

// InsertEvent sends a single event row using JSONEachRow format.
func (s *ClickHouseSink) InsertEvent(ctx context.Context, ev models.PromoEvent) error {
	row := chEventRow{
		ID:         ev.ID,
		CampaignID: ev.CampaignID,
		EventType:  string(ev.EventType),
		UserID:     ev.UserID,
		TrackID:    ev.TrackID,
		CostCents:  ev.CostCents,
		OccurredAt: ev.OccurredAt.UTC().Format("2006-01-02 15:04:05.000"),
	}
	data, err := json.Marshal(row)
	if err != nil {
		return err
	}
	query := fmt.Sprintf("INSERT INTO %s.promo_events FORMAT JSONEachRow", s.db)
	reqURL := s.baseURL + "/?" + url.Values{"query": {query}}.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, reqURL, bytes.NewReader(append(data, '\n')))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := s.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("clickhouse insert failed (%d): %s", resp.StatusCode, string(body))
	}
	return nil
}
