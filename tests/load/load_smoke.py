"""Lightweight load smoke when k6 is unavailable."""

import asyncio
import statistics
import time

import httpx

API_URL = "http://127.0.0.1:8000"
TARGET_RPS = 50
DURATION_SEC = 30


async def worker(client: httpx.AsyncClient, results: list[float]) -> None:
    end = time.time() + DURATION_SEC
    while time.time() < end:
        start = time.perf_counter()
        try:
            r = await client.get("/health")
            results.append(time.perf_counter() - start)
            if r.status_code != 200:
                results.append(-1.0)
        except Exception:
            results.append(-1.0)
        await asyncio.sleep(max(0, 1 / TARGET_RPS / 2))


async def main() -> None:
    latencies: list[float] = []
    async with httpx.AsyncClient(base_url=API_URL, trust_env=False, timeout=10.0) as client:
        tasks = [asyncio.create_task(worker(client, latencies)) for _ in range(TARGET_RPS)]
        await asyncio.gather(*tasks)
    ok = [x for x in latencies if x >= 0]
    failed = len(latencies) - len(ok)
    print(f"requests={len(latencies)} failed={failed}")
    if ok:
        print(f"p50_ms={statistics.median(ok)*1000:.1f} p95_ms={sorted(ok)[int(len(ok)*0.95)-1]*1000:.1f}")


if __name__ == "__main__":
    asyncio.run(main())
