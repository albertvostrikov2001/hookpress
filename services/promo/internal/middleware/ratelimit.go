package middleware

import (
	"net/http"
	"sync"
	"time"
)

// RateLimiter provides a fixed-window per-client request limit.
type RateLimiter struct {
	mu       sync.Mutex
	limit    int
	window   time.Duration
	counters map[string]windowCount
}

type windowCount struct {
	count     int
	windowEnd time.Time
}

// NewRateLimiter creates a rate limiter with the given limit per window.
func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	return &RateLimiter{
		limit:    limit,
		window:   window,
		counters: make(map[string]windowCount),
	}
}

func clientKey(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}
	return r.RemoteAddr
}

// Middleware returns HTTP middleware enforcing the rate limit.
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := clientKey(r)
		now := time.Now()
		rl.mu.Lock()
		entry, ok := rl.counters[key]
		if !ok || now.After(entry.windowEnd) {
			entry = windowCount{count: 0, windowEnd: now.Add(rl.window)}
		}
		entry.count++
		rl.counters[key] = entry
		allowed := entry.count <= rl.limit
		rl.mu.Unlock()

		if !allowed {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("Retry-After", rl.window.String())
			w.WriteHeader(http.StatusTooManyRequests)
			_, _ = w.Write([]byte(`{"error":{"code":"rate_limit_exceeded","message":"Too many requests"}}`))
			return
		}
		next.ServeHTTP(w, r)
	})
}
