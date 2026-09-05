# Security

- Secrets are read from environment variables; none are stored in the frontend.
- Uploads are limited to PDF, TXT, PNG, JPG, and JPEG with a 15 MB limit.
- Filenames are sanitized and stored outside the frontend.
- Audit metadata avoids raw document content.
- Production deployment must enable Firebase token verification, patient-level authorization, PostgreSQL parameterization, private Cloud Storage, Secret Manager, HTTPS, rate limiting, and structured redacted logging.
- Demo data is synthetic and must not be replaced with real patient records during development.
