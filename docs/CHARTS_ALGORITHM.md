# Charts Algorithm

Hook.press chart rankings combine weighted signals from configured sources into a weekly position list.

## Pipeline overview

1. **Source configuration** — Each chart source (`chart_sources`) stores normalized `source_weights` (JSON object). Weights are admin-tuned via `PATCH /api/v1/admin/charts/sources/{slug}/weights` and must sum to 1.0 after normalization.
2. **Signal ingestion** — Mock sources populate demo entries through the Celery task `charts.refresh_pipeline`, scheduled daily by Celery Beat.
3. **Weekly bucket** — Entries are keyed by `week_date` (ISO week start, Monday). Positions 1–N are unique per `(source_id, week_date)`.
4. **Ranking** — For production sources, each track receives a composite score:

   ```
   score(track) = Σ weight[signal] × normalized_signal_value(track)
   ```

   Default mock weights:

   | Signal    | Weight |
   |-----------|--------|
   | streams   | 0.45   |
   | downloads | 0.25   |
   | social    | 0.15   |
   | editorial | 0.15   |

5. **Output** — Tracks are sorted by score descending and assigned positions. Demo/mock entries are labeled with `is_demo=true`.

## Refresh schedule

Celery Beat runs `charts.refresh_pipeline` every 24 hours. The task skips sources that already have entries for the target week.

## API

- `GET /api/v1/charts/sources` — list sources and weights
- `GET /api/v1/charts/{source_slug}?week=YYYY-MM-DD` — chart for a week
- `PATCH /api/v1/admin/charts/sources/{slug}/weights` — update weights (admin)

## Notes

- Mock pipeline data is clearly labeled; it must not be presented as external chart authority.
- Weight changes apply to the next pipeline run for non-mock integrations.
