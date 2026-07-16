package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/hook-press/promo/internal/config"
	"github.com/hook-press/promo/internal/server"
)

func TestHealthEndpoint(t *testing.T) {
	srv := server.New(config.Config{Port: "8081", ClickHouseURL: "http://127.0.0.1:1", ClickHouseDB: "test"})
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rec := httptest.NewRecorder()
	srv.Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}
	var body map[string]string
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if body["status"] != "ok" {
		t.Fatalf("unexpected body: %+v", body)
	}
}
