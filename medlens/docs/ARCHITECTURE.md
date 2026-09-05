# Architecture

```mermaid
flowchart LR
  UI[Dashboard and record UI] --> API[FastAPI REST API]
  API --> STORE[(SQLite local / PostgreSQL production)]
  API --> FILES[Local files / Cloud Storage]
  API --> EXTRACT[PyMuPDF + OCR abstraction]
  EXTRACT --> AI[Mock provider / Vertex Gemini]
  AI --> VALIDATE[Pydantic schema validation]
  VALIDATE --> ENGINE[Reference range and conflict engines]
  ENGINE --> REVIEW[Human verification and audit log]
```

The application is deliberately local-first: patient browsing, uploads, source traceability, deterministic classification, editing, conflicts, timeline, search, and audit records remain available when cloud AI is unavailable.
