# Mock Integrations

All mock implementations are **explicitly labeled** in API metadata (`provider: "mock"`) where applicable.

| Integration | Interface | Mock implementation | Env switch | Default |
|-------------|-----------|----------------------|------------|---------|
| LLM | `LLMProvider` | `MockLLMProvider` | `LLM_PROVIDER=openai\|claude\|yandex` + keys | mock |
| Audio | `AudioProvider` | `MockAudioProvider` | `AUDIO_PROVIDER=external` + key | mock |
| OAuth | `OAuthProvider` | `MockOAuthProvider` / dev-login | `OAUTH_*_CLIENT_ID` | dev-login |
| Payments | `PaymentProvider` | `MockPaymentProvider` | `PAYMENT_PROVIDER=...` | mock |
| Distribution | `DistributionProvider` | `MockDistributionProvider` | `DISTRIBUTION_PROVIDER=...` | mock |
| Charts | `ChartSource` | `MockChartSource` (demo-top-40) | `CHART_SOURCE_*` | mock |
| Scoring | `ScoringProvider` | `LibrosaHeuristicProvider` (target) / mock interim | `SCORING_PROVIDER=ml` | librosa |
| AV scan | `AntivirusScanner` | `MockAntivirusScanner` | `AV_SCANNER=clamav` | mock pass |
| Email | `NotificationChannel` | `MailhogChannel` / log sink | `SMTP_*` | mailhog profile |
| RSS ingest | `FeedIngestProvider` | Local RSS fetch + moderation queue | — | mock-labeled |

See `services/api/app/infrastructure/providers/` and `workers/celery/app/providers.py`.
