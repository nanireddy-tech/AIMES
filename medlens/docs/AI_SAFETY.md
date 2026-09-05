# AI safety

MedLens never treats model output as trusted by default. Structured fields carry source, page, source text, confidence, and provenance. Missing ranges remain `null` and classify as `NOT_ASSESSED`; the system does not apply generic medical ranges.

The local provider is deterministic demo data. A production Vertex AI provider should use strict JSON schema output, retry malformed responses, reject unsupported claims, and pass summaries through a safety policy check before display. Summaries must not diagnose, prescribe, recommend medication or dosage changes, or turn uncertainty into fact.

Visible notice: MedLens organizes and summarizes medical information. It does not diagnose conditions or replace professional medical advice.
