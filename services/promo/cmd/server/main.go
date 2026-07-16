package main

import (
	"context"
	"log"
	"time"

	"github.com/hook-press/promo/internal/config"
	"github.com/hook-press/promo/internal/server"
)

func main() {
	cfg := config.Load()
	srv := server.New(cfg)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	srv.InitClickHouse(ctx)
	if err := srv.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
