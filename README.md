# Wine-O

Wine-O is a monorepo for an AI-assisted wine recognition, collection, and reconstruction platform.
It combines mobile capture, backend orchestration, OCR-based wine label extraction, 3D reconstruction,
and AI-driven analysis into a single product vision.

## What the application does

Wine-O is designed to let a user scan a bottle or label, identify the wine, enrich the result with
structured data, and then continue into broader discovery and collection workflows.

At a high level, the product supports:

- Mobile image capture and upload for wine labels and bottle photos.
- Backend authentication, user management, and wine collection management.
- OCR extraction of label text, including a real Tesseract-backed path with a deterministic fallback.
- Wine label parsing that turns raw OCR output into structured fields such as vintage, region,
  varietals, and alcohol content.
- Background job processing for long-running OCR work through a Celery-based queue.
- 3D reconstruction workflows for bottle or object imagery.
- AI orchestration for higher-level wine analysis, recommendations, and future sommelier features.

## Current status

The backend is the most complete part of the system today. The current codebase includes working
FastAPI services, a test suite that passes, and a number of production-oriented service layers.

Completed or largely in place:

- Authentication, email flows, and OAuth integration.
- Wine CRUD, search, identification, and collection endpoints.
- OCR extraction and parsing for wine label text.
- Async OCR job submission, job tracking, and fallback execution when Redis is unavailable.
- 3D reconstruction and AI orchestration service surfaces.
- Shared schema and service abstractions.
- Automated tests across the major backend modules.

Validation currently shows the backend test suite passing.

### Implemented backend details

The backend now includes a more complete OCR and job-processing flow:

- `OCRService` detects a real Tesseract backend when available and falls back to deterministic
  synthetic text blocks when it is not.
- OCR image handling downloads remote images, applies EXIF-aware rotation, and converts images to
  RGB before extraction.
- Wine label parsing converts OCR text into structured fields such as winery name, region, vintage,
  varietals, alcohol content, and supporting text.
- Celery-based async OCR jobs allow the API to submit long-running work without blocking the
  request cycle.
- A lightweight job registry and status endpoint support polling even when Redis is unavailable in
  local development.
- The OCR API exposes both synchronous and asynchronous paths so the app can support development,
  testing, and production-style execution models.

## Roadmap

The original roadmap has evolved from basic scaffolding into a much more functional platform.
The next phases should focus on turning the strongest backend pieces into production-grade product
flows and extending the same patterns to the remaining domains.

### Phase 1: Core platform foundation

Status: mostly complete.

- Monorepo structure established.
- Backend service boundaries created.
- Shared schemas and service abstractions in place.
- Base documentation started in `docs/`.

### Phase 2: Identity, wine data, and OCR

Status: complete enough for development and validation, but still needs production hardening.

- Authentication and account flows exist.
- Wine data models, collection management, and identification endpoints exist.
- OCR is functional with a real Tesseract path and a safe fallback path.
- OCR job submission, status polling, and async processing are implemented.

### Phase 3: Background processing

Status: implemented for OCR, still needs extension to the rest of the platform.

- Celery-based job execution is in place for OCR.
- Job submission and polling endpoints are available.
- The same pattern should be applied to 3D reconstruction and AI orchestration.

### Phase 4: Product expansion

Status: planned.

- Mobile scanning flow and capture UX.
- Better wine matching and ranking logic.
- 3D reconstruction workflows exposed as async user-facing jobs.
- AI assistant and recommendation features.
- Marketplace and social features.

### Phase 5: Infrastructure and release hardening

Status: partially defined, needs more implementation.

- CI/CD pipelines.
- Containerization and deployment automation.
- Monitoring, logging, and alerting.
- Production Redis, PostgreSQL, and object storage configuration.

## Areas that need more focus

These are the highest-value areas to improve next:

- Production OCR deployment: install and standardize Tesseract in the runtime environment, then test
  against real label images.
- Async expansion: move 3D reconstruction and AI orchestration into the same background-job model
  used by OCR.
- Matching quality: improve wine name extraction, candidate ranking, and confidence handling so the
  app returns more useful identification results.
- Mobile experience: build the actual capture, upload, and progress UI so users can move from scan to
  result without friction.
- Observability and reliability: add stronger logging, metrics, and error handling around the job
  queue and external service calls.
- Infrastructure maturity: finalize deployment, environment variables, broker configuration, and
  cloud storage assumptions for production.

## Repository layout

- `backend/` - FastAPI backend, tests, and service logic.
- `mobile-app/` - Mobile client implementation.
- `ai-services/` - AI and computer-vision service layer.
- `3d-engine/` - Reconstruction and asset generation tooling.
- `infrastructure/` - Cloud and deployment infrastructure.
- `shared/` - Common schemas and utilities.
- `scripts/` - Setup and automation scripts.
- `docs/` - Architecture and planning documentation.
- `deployment/` - Release and deployment notes.

## Local development

Backend quick start:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run tests:

```powershell
cd backend
python -m pytest tests/ -q
```

## Related docs

- [Architecture overview](docs/ARCHITECTURE.md)
- [Roadmap notes](docs/ROADMAP.md)

