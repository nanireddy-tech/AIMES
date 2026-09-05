from __future__ import annotations

import json
import mimetypes
import os
import re
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MedLens API", version="0.1.0", description="Traceable clinical information intelligence")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def provenance(kind: str, source: str, page: int | None = None, text: str | None = None, confidence: float = 1.0) -> dict[str, Any]:
    return {"kind": kind, "source": source, "page": page, "text": text, "confidence": confidence}


def classify(value: float | None, lower: float | None, upper: float | None) -> str:
    if value is None or lower is None or upper is None:
        return "NOT_ASSESSED"
    if lower == float("-inf") and value > upper:
        return "HIGH"
    if upper == float("inf") and value < lower:
        return "LOW"
    if value < lower:
        return "LOW"
    if value > upper:
        return "HIGH"
    return "NORMAL"


def extract_local_text(document: dict[str, Any]) -> str:
    """Extract text locally; image-only and unsupported content stays reviewable."""
    matches = list(UPLOAD_DIR.glob(f"{document['id']}-*"))
    if not matches:
        return ""
    path = matches[0]
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="replace").strip()
    if path.suffix.lower() == ".pdf":
        try:
            import fitz

            with fitz.open(path) as pdf:
                return "\n".join(page.get_text("text") for page in pdf).strip()
        except Exception:
            return ""
    return ""


def extract_observations_from_text(document: dict[str, Any], text: str) -> list[dict[str, Any]]:
    """Parse conservative lab rows; absent ranges remain NOT_ASSESSED."""
    found = []
    pattern = re.compile(r"^\s*([A-Za-z][A-Za-z /_-]{1,40})\s+(-?\d+(?:\.\d+)?)\s*([A-Za-z%/^0-9µ.-]+)?(?:\s+(?:reference\s*)?([<>]?\s*-?\d+(?:\.\d+)?\s*(?:-|to|–)\s*-?\d+(?:\.\d+)?|[<>]\s*-?\d+(?:\.\d+)?))?\s*$", re.IGNORECASE)
    for raw_line in text.splitlines():
        match = pattern.match(raw_line)
        if not match:
            continue
        name, raw_value, unit, raw_range = match.groups()
        value = float(raw_value)
        lower = upper = None
        if raw_range:
            bounds = re.findall(r"-?\d+(?:\.\d+)?", raw_range)
            if len(bounds) == 2:
                lower, upper = float(bounds[0]), float(bounds[1])
            elif raw_range.strip().startswith(">"):
                lower, upper = float(bounds[0]), float("inf")
            elif raw_range.strip().startswith("<"):
                lower, upper = float("-inf"), float(bounds[0])
        observation = demo_observation(document["patient_id"], document["id"], name.strip(), re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"), value, unit or "", lower, upper, document["uploaded_at"], 1, raw_line.strip())
        observation["reference_range"] = raw_range.strip() if raw_range else None
        found.append(observation)
    return found


def demo_observation(patient_id: str, document_id: str, name: str, canonical: str, value: float | None, unit: str, low: float | None, high: float | None, observed: str, page: int, source_text: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()), "patient_id": patient_id, "document_id": document_id,
        "test_name": name, "canonical_test_name": canonical, "value": value,
        "numeric_value": value, "unit": unit, "reference_range": f"{low:g}-{high:g}" if low is not None and high is not None else None,
        "lower_bound": low, "upper_bound": high, "status": classify(value, low, high),
        "observation_date": observed, "observation": None, "source_page": page, "source_text": source_text,
        "confidence": 0.96, "provenance": provenance("REPORT_EXTRACTED", "CBC_Report.pdf", page, source_text, 0.96),
        "verification_status": "PENDING", "verified_by": None, "verified_at": None, "created_at": now(), "updated_at": now()
    }

p1 = "pat-001"
p2 = "pat-002"
d1 = "doc-cbc-001"
d2 = "doc-metabolic-001"
d3 = "doc-lipid-001"
patients: list[dict[str, Any]] = [
    {"id": p1, "name": "Avery Morgan", "identifier": "ML-1042", "age": 42, "sex": "Female", "symptoms": "Fatigue noted in intake", "conditions": ["No conditions recorded"], "allergies": "No known allergies", "medications": ["Vitamin D"], "notes": "Synthetic demonstration patient", "created_at": "2026-01-10", "updated_at": "2026-09-05"},
    {"id": p2, "name": "Jordan Lee", "identifier": "ML-1043", "age": 35, "sex": "Male", "symptoms": "None recorded", "conditions": ["No conditions recorded"], "allergies": "Not documented", "medications": [], "notes": "Synthetic demonstration patient", "created_at": "2026-02-12", "updated_at": "2026-09-05"},
]
documents: list[dict[str, Any]] = [
    {"id": d1, "patient_id": p1, "filename": "CBC_Report.pdf", "type": "PDF", "size": 245760, "status": "VERIFIED", "uploaded_at": "2026-01-10", "pages": 2, "text": "Haemoglobin 13.8 g/dL 12-16\nWBC 10.2 x10^9/L 4-10", "source": "demo"},
    {"id": d2, "patient_id": p1, "filename": "Metabolic_Panel.pdf", "type": "PDF", "size": 182430, "status": "REVIEW_REQUIRED", "uploaded_at": "2026-03-18", "pages": 1, "text": "Glucose 108 mg/dL 70-99\nCreatinine 0.9 mg/dL", "source": "demo"},
    {"id": d3, "patient_id": p1, "filename": "Lipid_Panel.pdf", "type": "PDF", "size": 153220, "status": "EXTRACTED", "uploaded_at": "2026-05-20", "pages": 1, "text": "HDL 58 mg/dL >40\nLDL 142 mg/dL", "source": "demo"},
]
observations = [
    demo_observation(p1, d1, "Hemoglobin", "hemoglobin", 13.8, "g/dL", 12, 16, "2026-01-10", 2, "Haemoglobin 13.8 g/dL 12-16"),
    demo_observation(p1, d1, "WBC", "wbc", 10.2, "x10^9/L", 4, 10, "2026-01-10", 2, "WBC 10.2 x10^9/L 4-10"),
    demo_observation(p1, d2, "Glucose", "glucose", 108, "mg/dL", 70, 99, "2026-03-18", 1, "Glucose 108 mg/dL 70-99"),
    demo_observation(p1, d2, "Creatinine", "creatinine", 0.9, "mg/dL", None, None, "2026-03-18", 1, "Creatinine 0.9 mg/dL"),
    demo_observation(p1, d3, "HDL", "hdl", 58, "mg/dL", 40, 100, "2026-05-20", 1, "HDL 58 mg/dL >40"),
    demo_observation(p1, d3, "LDL", "ldl", 142, "mg/dL", None, None, "2026-05-20", 1, "LDL 142 mg/dL"),
]
conflicts = [{"id": "conf-001", "patient_id": p1, "type": "ALLERGY", "severity": "REVIEW", "message": "These records contain conflicting information. Human verification is required.", "left": "USER PROVIDED: No known allergies", "right": "REPORT EXTRACTED: Penicillin allergy", "status": "OPEN"}]
audit: list[dict[str, Any]] = [{"id": "audit-001", "timestamp": "2026-09-05T09:00:00Z", "action": "DEMO_DATA_LOADED", "entity": "patient", "entity_id": p1, "metadata": {"synthetic": True}}]


class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    identifier: str = Field(min_length=2, max_length=40)
    age: int | None = Field(default=None, ge=0, le=130)
    sex: str | None = None
    symptoms: str = ""
    conditions: list[str] = []
    allergies: str = ""
    medications: list[str] = []
    notes: str = ""


class ObservationEdit(BaseModel):
    test_name: str | None = None
    value: float | None = None
    unit: str | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    observation_date: str | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-demo", "ai_provider": os.getenv("AI_PROVIDER", "mock")}


@app.get("/api/patients")
def list_patients() -> list[dict[str, Any]]:
    return patients


@app.post("/api/patients")
def create_patient(payload: PatientCreate) -> dict[str, Any]:
    patient = {"id": f"pat-{uuid.uuid4().hex[:8]}", **payload.model_dump(), "created_at": now(), "updated_at": now()}
    patients.append(patient)
    audit.append({"id": str(uuid.uuid4()), "timestamp": now(), "action": "PATIENT_CREATED", "entity": "patient", "entity_id": patient["id"], "metadata": {}})
    return patient


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: str) -> dict[str, Any]:
    patient = next((item for item in patients if item["id"] == patient_id), None)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@app.get("/api/patients/{patient_id}/documents")
def get_documents(patient_id: str) -> list[dict[str, Any]]:
    return [item for item in documents if item["patient_id"] == patient_id]


@app.post("/api/patients/{patient_id}/documents")
def upload_document(patient_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    if not any(item["id"] == patient_id for item in patients):
        raise HTTPException(404, "Patient not found")
    allowed = {"application/pdf", "text/plain", "image/png", "image/jpeg"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".png", ".jpg", ".jpeg"} or (file.content_type and file.content_type not in allowed):
        raise HTTPException(400, "Unsupported file type. Use PDF, TXT, PNG, JPG, or JPEG.")
    content = file.file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(413, "File exceeds the 15 MB limit")
    document_id = f"doc-{uuid.uuid4().hex[:8]}"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.filename or "document")
    (UPLOAD_DIR / f"{document_id}-{safe_name}").write_bytes(content)
    doc = {"id": document_id, "patient_id": patient_id, "filename": safe_name, "type": suffix[1:].upper(), "size": len(content), "status": "UPLOADED", "uploaded_at": date.today().isoformat(), "pages": None, "text": "", "source": "local"}
    documents.append(doc)
    audit.append({"id": str(uuid.uuid4()), "timestamp": now(), "action": "DOCUMENT_UPLOADED", "entity": "document", "entity_id": document_id, "metadata": {"filename": safe_name, "size": len(content)}})
    return doc


@app.post("/api/documents/{document_id}/process")
def process_document(document_id: str) -> dict[str, Any]:
    doc = next((item for item in documents if item["id"] == document_id), None)
    if not doc:
        raise HTTPException(404, "Document not found")
    doc["status"] = "PROCESSING"
    extracted_text = extract_local_text(doc)
    doc["text"] = extracted_text
    doc["pages"] = max(1, extracted_text.count("\f") + 1) if extracted_text else None
    doc["status"] = "EXTRACTED" if extracted_text else "REVIEW_REQUIRED"
    if extracted_text:
        observations.extend(extract_observations_from_text(doc, extracted_text))
    audit.append({"id": str(uuid.uuid4()), "timestamp": now(), "action": "AI_EXTRACTION", "entity": "document", "entity_id": document_id, "metadata": {"provider": "mock-local", "safe_fallback": True}})
    return doc


@app.get("/api/patients/{patient_id}/observations")
def get_observations(patient_id: str) -> list[dict[str, Any]]:
    return [item for item in observations if item["patient_id"] == patient_id]


@app.put("/api/observations/{observation_id}")
def edit_observation(observation_id: str, payload: ObservationEdit) -> dict[str, Any]:
    item = next((row for row in observations if row["id"] == observation_id), None)
    if not item:
        raise HTTPException(404, "Observation not found")
    previous = {key: item.get(key) for key in payload.model_fields_set}
    for key, value in payload.model_dump(exclude_unset=True).items():
        item[key] = value
    item["status"] = classify(item.get("numeric_value"), item.get("lower_bound"), item.get("upper_bound"))
    item["provenance"] = provenance("HUMAN_VERIFIED", item["provenance"]["source"], item["source_page"], item["source_text"], item["confidence"])
    item["verification_status"] = "VERIFIED"
    item["verified_by"] = "local-user"
    item["verified_at"] = now()
    item["updated_at"] = now()
    audit.append({"id": str(uuid.uuid4()), "timestamp": now(), "action": "HUMAN_EDIT", "entity": "observation", "entity_id": observation_id, "metadata": {"previous": previous, "new": payload.model_dump(exclude_unset=True)}})
    return item


@app.post("/api/observations/{observation_id}/verify")
def verify_observation(observation_id: str) -> dict[str, Any]:
    return edit_observation(observation_id, ObservationEdit())


@app.get("/api/patients/{patient_id}/conflicts")
def get_conflicts(patient_id: str) -> list[dict[str, Any]]:
    return [item for item in conflicts if item["patient_id"] == patient_id]


@app.get("/api/patients/{patient_id}/timeline")
def timeline(patient_id: str) -> list[dict[str, Any]]:
    events = [{"date": item["uploaded_at"], "type": "DOCUMENT", "title": f"{item['filename']} uploaded", "detail": item["status"]} for item in documents if item["patient_id"] == patient_id]
    events += [{"date": item["timestamp"][:10], "type": "AUDIT", "title": item["action"].replace("_", " ").title(), "detail": item["entity"]} for item in audit if item["entity_id"] == patient_id]
    return sorted(events, key=lambda item: item["date"], reverse=True)


@app.get("/api/patients/{patient_id}/audit")
def get_audit(patient_id: str) -> list[dict[str, Any]]:
    ids = {patient_id} | {item["id"] for item in documents if item["patient_id"] == patient_id} | {item["id"] for item in observations if item["patient_id"] == patient_id}
    return [item for item in audit if item["entity_id"] in ids]


@app.get("/api/patients/{patient_id}/comparison")
def comparison(patient_id: str) -> list[dict[str, Any]]:
    rows = [item for item in observations if item["patient_id"] == patient_id]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["canonical_test_name"], []).append(row)
    results = []
    for test_name, values in grouped.items():
        ordered = sorted(values, key=lambda item: item["observation_date"])
        if len(ordered) < 2 or ordered[-1]["numeric_value"] is None or ordered[-2]["numeric_value"] is None:
            continue
        previous = ordered[-2]
        current = ordered[-1]
        if previous["unit"] != current["unit"]:
            continue
        change = current["numeric_value"] - previous["numeric_value"]
        percent = (change / previous["numeric_value"] * 100) if previous["numeric_value"] else None
        results.append({"test": test_name, "previous": previous, "current": current, "change": change, "percentage_change": percent, "statement": "The recorded value increased." if change > 0 else "The recorded value decreased." if change < 0 else "The recorded value is unchanged."})
    return results


@app.post("/api/patients/{patient_id}/summary")
def summary(patient_id: str) -> dict[str, Any]:
    patient = get_patient(patient_id)
    rows = get_observations(patient_id)
    missing = [row["test_name"] for row in rows if row["status"] == "NOT_ASSESSED"]
    high = sum(row["status"] == "HIGH" for row in rows)
    return {"patient": patient["name"], "overview": f"The record contains {len(rows)} laboratory observations.", "recent_observations": rows[-5:], "changes": comparison(patient_id), "verification_needed": len([row for row in rows if row["verification_status"] != "VERIFIED"]), "missing_information": missing, "statement": f"The latest records contain {high} observation(s) marked HIGH according to ranges printed in the source reports.", "safety_notice": "MedLens organizes and summarizes medical information. It does not diagnose conditions or replace professional medical advice."}


@app.get("/api/patients/{patient_id}/export")
def export_record(patient_id: str) -> dict[str, Any]:
    return {"format": "json", "exported_at": now(), "patient": get_patient(patient_id), "documents": get_documents(patient_id), "observations": get_observations(patient_id), "timeline": timeline(patient_id), "conflicts": get_conflicts(patient_id), "summary": summary(patient_id), "audit": get_audit(patient_id)}


@app.get("/api/search")
def search(q: str) -> list[dict[str, Any]]:
    needle = q.lower()
    results = []
    for patient in patients:
        if needle in json.dumps(patient).lower(): results.append({"type": "Patient", "id": patient["id"], "title": patient["name"], "detail": patient["identifier"]})
    for item in observations:
        if needle in json.dumps(item).lower(): results.append({"type": "Observation", "id": item["id"], "title": item["test_name"], "detail": f"{item['value']} {item['unit']}"})
    return results[:25]


@app.get("/", response_class=HTMLResponse)
def frontend() -> str:
    index = FRONTEND / "index.html"
    return index.read_text() if index.exists() else "<h1>MedLens API</h1>"
