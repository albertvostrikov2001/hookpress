package handlers

import (
	"encoding/json"
	"net/http"
)

type healthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
	Mode    string `json:"mode"`
}

// HealthHandler serves liveness checks.
type HealthHandler struct{}

func (h *HealthHandler) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(healthResponse{
		Status:  "ok",
		Service: "promo",
		Mode:    "legal-promotion-only",
	})
}

// MetricsHandler exposes Prometheus text metrics.
type MetricsHandler struct {
	RequestCount int64
	EventCount   int64
}

func (h *MetricsHandler) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	body := "# HELP hookpress_promo_requests_total Total HTTP requests\n" +
		"# TYPE hookpress_promo_requests_total counter\n" +
		"hookpress_promo_requests_total " + itoa(h.RequestCount) + "\n" +
		"# HELP hookpress_promo_events_total Total recorded promo events\n" +
		"# TYPE hookpress_promo_events_total counter\n" +
		"hookpress_promo_events_total " + itoa(h.EventCount) + "\n"
	_, _ = w.Write([]byte(body))
}

func itoa(n int64) string {
	if n == 0 {
		return "0"
	}
	var buf [20]byte
	i := len(buf)
	neg := n < 0
	if neg {
		n = -n
	}
	for n > 0 {
		i--
		buf[i] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}
