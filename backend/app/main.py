from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ingest import parse_dataset
from app.llm import LLMConfigurationError, assess_conditions
from app.memory import HindsightUnavailable, get_memory_provider, local_store
from app.models import AssessmentResponse, ChangeRequest, IngestResponse

app = FastAPI(title="ReleaseMind API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
memory_provider = get_memory_provider()
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "llm_configured": bool(settings.llm_api_key),
        "llm_model": settings.llm_model,
        "memory_provider": memory_provider.name,
        "memory_items": memory_provider.stats()["total_experiences"],
    }


@app.get("/api/memory/stats")
async def memory_stats():
    return memory_provider.stats()


@app.post("/api/memory/import", response_model=IngestResponse)
async def import_memory(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Choose a JSON or CSV incident dataset export.")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Dataset upload exceeds the 50 MB limit.")
    try:
        experiences, invalid_rows = parse_dataset(filename, raw)
        if not experiences:
            raise ValueError("No valid incident rows were found. Each row needs a title, narrative, and source URL.")
        try:
            imported, synthetic_skipped = await memory_provider.ingest(experiences)
            actual_provider = memory_provider.name
            fallback_note = ""
        except HindsightUnavailable:
            # HindsightMemoryProvider has already committed these records to local SQLite.
            imported = sum(1 for row in experiences if not row.is_synthetic)
            synthetic_skipped = sum(1 for row in experiences if row.is_synthetic)
            actual_provider = local_store.name
            fallback_note = " Hindsight was unavailable, so the records remain in local SQLite memory."
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Memory ingestion failed: {exc}") from exc
    skipped = invalid_rows + synthetic_skipped
    return IngestResponse(
        imported=imported,
        skipped=skipped,
        memory_provider=actual_provider,
        message=f"Imported source records into persistent memory. Verify dataset reuse rights before loading or sharing source text.{fallback_note}",
    )


@app.post("/api/assess", response_model=AssessmentResponse)
async def assess(request: ChangeRequest):
    try:
        query = request.change_description
        if request.context:
            query += f"\nChange context: {request.context}"
        try:
            experiences = await memory_provider.search(query, top_k=5)
            actual_provider = memory_provider.name
        except HindsightUnavailable:
            experiences = await local_store.search(query, top_k=5)
            actual_provider = f"{local_store.name} (Hindsight unavailable)"
        baseline, augmented = await assess_conditions(request.change_description, request.context, experiences)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AssessmentResponse(
        baseline_assessment=baseline,
        memory_assessment=augmented,
        retrieved_experiences=experiences,
        metadata={
            "memory_provider": actual_provider,
            "llm_model": settings.llm_model,
            "evidence_count": len(experiences),
            "assessment_scope": "historical context; not incident prediction",
        },
    )
