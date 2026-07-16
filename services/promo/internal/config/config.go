package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds promo service configuration.
type Config struct {
	Port               string
	ClickHouseURL      string
	ClickHouseDB       string
	RateLimitRequests  int
	RateLimitWindow    time.Duration
}

// Load reads configuration from environment variables.
func Load() Config {
	port := os.Getenv("PROMO_PORT")
	if port == "" {
		port = "8081"
	}
	chURL := os.Getenv("CLICKHOUSE_URL")
	if chURL == "" {
		chURL = "http://clickhouse:8123"
	}
	chDB := os.Getenv("CLICKHOUSE_DB")
	if chDB == "" {
		chDB = "hookpress_promo"
	}
	rateLimit := 120
	if v := os.Getenv("PROMO_RATE_LIMIT_REQUESTS"); v != "" {
		if parsed, err := strconv.Atoi(v); err == nil && parsed > 0 {
			rateLimit = parsed
		}
	}
	windowSeconds := 60
	if v := os.Getenv("PROMO_RATE_LIMIT_WINDOW_SECONDS"); v != "" {
		if parsed, err := strconv.Atoi(v); err == nil && parsed > 0 {
			windowSeconds = parsed
		}
	}
	return Config{
		Port:              port,
		ClickHouseURL:     chURL,
		ClickHouseDB:      chDB,
		RateLimitRequests: rateLimit,
		RateLimitWindow:   time.Duration(windowSeconds) * time.Second,
	}
}
