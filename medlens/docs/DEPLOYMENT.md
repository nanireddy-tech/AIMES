# Deployment

Build the backend into a Cloud Run container with `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`. Configure `DATABASE_URL` for Cloud SQL, `GCS_BUCKET` for Cloud Storage, Vertex AI and Document AI identifiers, and Firebase project settings through Secret Manager and Cloud Run environment bindings. Use least-privilege service accounts and private database networking.
