# Production Integrations (deferred — require credentials/contracts)

| Integration | Required configuration | Close condition | MVP status |
|-------------|------------------------|-----------------|------------|
| Google OAuth | `OAUTH_GOOGLE_CLIENT_ID`, secret | Staging OAuth app | adapter stub |
| Yandex OAuth | `OAUTH_YANDEX_*` | Partner app | adapter stub |
| VK OAuth | `OAUTH_VK_*` | Partner app | adapter stub |
| Apple Sign-In | Apple dev certs | Apple developer account | architecture ready |
| OpenAI / Claude / YandexGPT | API keys | Billing + keys in vault | env-switch adapters |
| External audio | API key | Provider contract | env-switch adapter |
| Payment PSP | PSP credentials + webhooks | KYC/AML + contract | mock only |
| DDEX distributor | Distributor API | Partner agreement | interface stub |
| Licensed charts | Partner API keys | License agreement | mock labeled |
| ML scoring | Model artifact + review | Ethics review | interface stub |
| ClamAV / cloud AV | Scanner endpoint | Infra provisioned | mock scanner |
| Sentry | `SENTRY_DSN` | Project created | hook stub |
| OTel collector | `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector deployed | SDK wiring |
| Production SMTP | `SMTP_*` | Domain + SPF/DKIM | Mailhog in dev |

Real money movement, KYC/AML, and official UPC/ISRC issuance remain **out of MVP scope** per ADR-005 and `KNOWN_LIMITATIONS.md`.
