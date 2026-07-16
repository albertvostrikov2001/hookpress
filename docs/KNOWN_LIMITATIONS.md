# Known Limitations — MVP

## Documented TODOs

| ID | Priority | Description | Close when |
|----|----------|-------------|------------|
| TODO-001 | P2 | Fixed-decisions source doc not provided | Original doc received OR effective doc superseded with signed-off ADR update |
| TODO-002 | P1 | Production OAuth requires client secrets | Real OAuth apps configured in staging |
| TODO-003 | P1 | Real payment provider / payouts | PSP contract + KYC/AML flow live |
| TODO-004 | P2 | Apple Sign-In | Apple developer account + adapter impl |
| TODO-005 | P2 | Licensed chart sources | Partner API agreements |
| TODO-006 | P2 | DDEX distribution | Distributor API integration |
| TODO-007 | P3 | ML-based hit scoring | Validated model + ethics review |
| TODO-008 | P2 | Antivirus scanning | ClamAV or cloud AV integrated |
| TODO-009 | P3 | Full WCAG audit | External accessibility audit pass |

## MVP Scope Exclusions

1. **Real money movement** — Mock `PaymentProvider` simulates authorize/capture/refund. Ledger logic is production-grade; external settlement is not.
2. **KYC/AML** — Not implemented.
3. **Official UPC/ISRC** — Test codes only, prefixed `TEST-`.
4. **External DSP promotion** — No stream inflation; internal campaigns only.
5. **CAPTCHA** — Not needed for mock auth; add with public registration if enabled.
6. **Production LLM/audio** — Mock providers default; quality of generated content is placeholder.
7. **Mobile admin/CMS** — Web-only for admin and complex release builder.
8. **Multi-region deployment** — Single-region compose/K8s skeleton only.

## Mock Integrations (explicit)

| Integration | Mock | Env to enable production |
|-------------|------|--------------------------|
| LLM | `MockLLMProvider` | `LLM_PROVIDER=openai` + key |
| Audio | `MockAudioProvider` | `AUDIO_PROVIDER=external` + key |
| OAuth | `dev-login` | `OAUTH_GOOGLE_CLIENT_ID`, etc. |
| Payments | `MockPaymentProvider` | `PAYMENT_PROVIDER=...` |
| Distribution | `MockDistributor` | `DISTRIBUTION_PROVIDER=...` |
| Charts | `MockChartSource` | `CHART_SOURCE_...` |

Mock responses are labeled in API metadata where applicable (`"provider": "mock"`).

## Performance

Load targets (10k MAU, 100 RPS sustained) validated in Stage 11; not guaranteed before acceptance testing.

## Legal

Platform does not guarantee chart performance, hit prediction, or distribution acceptance. Scoring output is advisory heuristics only.
