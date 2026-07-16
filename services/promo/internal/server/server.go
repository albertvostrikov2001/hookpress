package server

import (
	"context"
	"log"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/hook-press/promo/internal/config"
	"github.com/hook-press/promo/internal/handlers"
	"github.com/hook-press/promo/internal/middleware"
	"github.com/hook-press/promo/internal/sink"
	"github.com/hook-press/promo/internal/store"
)

// Server wraps the promo HTTP server and dependencies.
type Server struct {
	cfg    config.Config
	mux    *http.ServeMux
	store  *store.Store
	sink   *sink.ClickHouseSink
	reqCnt atomic.Int64
	evCnt  atomic.Int64
}

// New builds a configured promo server.
func New(cfg config.Config) *Server {
	s := &Server{cfg: cfg, store: store.New()}
	s.sink = sink.NewClickHouseSink(cfg.ClickHouseURL, cfg.ClickHouseDB)
	s.buildRoutes()
	return s
}

func (s *Server) buildRoutes() {
	mux := http.NewServeMux()
	eventCh := make(chan struct{}, 64)

	campaigns := &handlers.CampaignHandler{
		Store:  s.store,
		Sink:   s.sink,
		Events: eventCh,
	}
	go func() {
		for range eventCh {
			s.evCnt.Add(1)
		}
	}()

	rateLimiter := middleware.NewRateLimiter(s.cfg.RateLimitRequests, s.cfg.RateLimitWindow)
	idempotency := middleware.NewIdempotencyStore(24 * time.Hour)

	mux.Handle("/health", &handlers.HealthHandler{})
	mux.Handle("/metrics", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := &handlers.MetricsHandler{
			RequestCount: s.reqCnt.Load(),
			EventCount:   s.evCnt.Load(),
		}
		h.ServeHTTP(w, r)
	}))
	campaignHandler := rateLimiter.Middleware(idempotency.Middleware(campaigns))
	mux.Handle("/api/v1/campaigns", s.instrument(campaignHandler))
	mux.Handle("/api/v1/campaigns/", s.instrument(campaignHandler))

	s.mux = mux
}

func (s *Server) instrument(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.reqCnt.Add(1)
		next.ServeHTTP(w, r)
	})
}

// InitClickHouse ensures analytics table exists (best-effort on startup).
func (s *Server) InitClickHouse(ctx context.Context) {
	if err := s.sink.EnsureTable(ctx); err != nil {
		log.Printf("clickhouse init (non-fatal): %v", err)
	}
}

// Handler returns the root HTTP handler.
func (s *Server) Handler() http.Handler {
	return s.mux
}

// ListenAndServe starts the HTTP server.
func (s *Server) ListenAndServe() error {
	addr := ":" + s.cfg.Port
	srv := &http.Server{
		Addr:              addr,
		Handler:           s.mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("promo service listening on %s (legal promotion only)", addr)
	return srv.ListenAndServe()
}

// Store exposes the campaign store (for tests).
func (s *Server) Store() *store.Store {
	return s.store
}
