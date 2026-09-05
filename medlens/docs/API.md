# MedLens API

The local API is served by FastAPI at `http://127.0.0.1:8000` with interactive OpenAPI docs at `/docs`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Local provider and service health |
| GET/POST | `/api/patients` | List or create patients |
| GET | `/api/patients/{id}` | Patient information |
| GET/POST | `/api/patients/{id}/documents` | List or upload documents |
| POST | `/api/documents/{id}/process` | Extract local text and structured rows |
| GET | `/api/patients/{id}/observations` | Traceable laboratory observations |
| PUT | `/api/observations/{id}` | Human edit with audit event |
| POST | `/api/observations/{id}/verify` | Mark an observation verified |
| GET | `/api/patients/{id}/conflicts` | Open conflicts |
| GET | `/api/patients/{id}/comparison` | Comparable historical values |
| GET | `/api/patients/{id}/timeline` | Chronological record events |
| POST | `/api/patients/{id}/summary` | Safe database-only summary |
| GET | `/api/patients/{id}/audit` | Redacted audit events |
| GET | `/api/patients/{id}/export` | Structured JSON export |
| GET | `/api/search?q=...` | Global record search |

The local mode is intentionally deterministic and uses synthetic data. Production authentication and patient authorization should be added at the API boundary before exposing records outside a local environment.
