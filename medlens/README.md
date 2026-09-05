# MedLens

MedLens is a local-first clinical information intelligence workspace. It organizes medical records, preserves source traceability, classifies values only against ranges printed in the source document, and keeps human verification in the loop. It is not a diagnostic system.

## Run locally

```bash
cd medlens
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs.

Run tests with `uv run --python .venv/bin/python pytest tests -q` from the `medlens` directory.

The demo uses synthetic patients and a mock AI provider. Vertex AI, Document AI, Cloud Storage, PostgreSQL, Firebase, and Cloud Run environment hooks are documented in `.env.example` and can be connected without changing the product workflow.

## Free deployment

The easiest free deployment is Render. Push this repository to GitHub, create a Render account, choose **New > Blueprint**, select the repository, and accept `render.yaml`. If GitHub contains the full `AIMES` folder, Render uses the root Docker blueprint. If GitHub contains only this `medlens` folder, Render uses this folder's Python blueprint. Both deploy the FastAPI dashboard and provide a public HTTPS URL. The free service may sleep after inactivity, so the first request can take a few seconds.

The hosted demo uses synthetic data and `AI_PROVIDER=mock`. Do not upload real patient information to this public demo. For production use, add authentication, private storage, a managed database, and cloud AI credentials before handling any medical data.
