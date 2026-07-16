package middleware

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"sync"
	"time"
)

type idempotencyRecord struct {
	status  int
	body    []byte
	expires time.Time
}

// IdempotencyStore caches prior responses keyed by idempotency header.
type IdempotencyStore struct {
	mu      sync.Mutex
	records map[string]idempotencyRecord
	ttl     time.Duration
}

// NewIdempotencyStore creates an in-memory idempotency cache.
func NewIdempotencyStore(ttl time.Duration) *IdempotencyStore {
	return &IdempotencyStore{
		records: make(map[string]idempotencyRecord),
		ttl:     ttl,
	}
}

type captureWriter struct {
	http.ResponseWriter
	status int
	body   bytes.Buffer
}

func (w *captureWriter) WriteHeader(status int) {
	w.status = status
	w.ResponseWriter.WriteHeader(status)
}

func (w *captureWriter) Write(b []byte) (int, error) {
	w.body.Write(b)
	return w.ResponseWriter.Write(b)
}

// Middleware replays prior responses when Idempotency-Key matches.
func (s *IdempotencyStore) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			next.ServeHTTP(w, r)
			return
		}
		key := r.Header.Get("Idempotency-Key")
		if key == "" {
			next.ServeHTTP(w, r)
			return
		}

		cacheKey := r.Method + ":" + r.URL.Path + ":" + key
		s.mu.Lock()
		if rec, ok := s.records[cacheKey]; ok && time.Now().Before(rec.expires) {
			s.mu.Unlock()
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Idempotency-Replay", "true")
			w.WriteHeader(rec.status)
			_, _ = w.Write(rec.body)
			return
		}
		s.mu.Unlock()

		capture := &captureWriter{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(capture, r)

		if capture.status >= 200 && capture.status < 300 {
			s.mu.Lock()
			s.records[cacheKey] = idempotencyRecord{
				status:  capture.status,
				body:    append([]byte(nil), capture.body.Bytes()...),
				expires: time.Now().Add(s.ttl),
			}
			s.mu.Unlock()
		}
	})
}

// DecodeJSON reads and restores the request body for downstream handlers.
func DecodeJSON(r *http.Request, v any) error {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}
	r.Body = io.NopCloser(bytes.NewReader(body))
	return json.Unmarshal(body, v)
}
