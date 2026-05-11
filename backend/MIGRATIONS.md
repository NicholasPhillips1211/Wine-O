# Database Migration Guide for Wine-O

## Overview
Wine-O uses SQLAlchemy ORM with Alembic for database schema management. This enables version-controlled database migrations across environments.

## Database Setup

### Development (SQLite)
By default, Wine-O uses SQLite for development. The database file (`wine_o.db`) is created automatically in the `backend/` directory on first run.

### Production (PostgreSQL)
Update `backend/app/db/session.py`:
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/wine_o"
```

And update `backend/alembic.ini`:
```ini
sqlalchemy.url = postgresql://user:password@localhost:5432/wine_o
```

## Schema Versions

### Current Migration: 001_initial_schema.py
Creates all core tables:
- `users` — User accounts with authentication
- `wines` — Wine catalog with metadata
- `wine_collections` — User wine collections (one-to-many)
- `wine_collection_association` — Wine to collection mapping (many-to-many)
- `ocr_sessions` — OCR processing history
- `reconstructions` — 3D reconstruction models
- `analyses` — Wine analysis results

## Running Migrations

### Apply all pending migrations
```bash
cd backend
alembic upgrade head
```

### Create new migration (auto-detect model changes)
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Rollback last migration
```bash
cd backend
alembic downgrade -1
```

### View migration history
```bash
cd backend
alembic history
```

### View current database version
```bash
cd backend
alembic current
```

## Database Models

### User
- Stores user account information
- Email and username are unique
- Password is hashed using bcrypt
- Relationships: collections, analyses

### Wine
- Stores wine catalog metadata
- Indexed by: wine_name, region, vintage, country
- Relationships: collections (many-to-many), analyses

### WineCollection
- User-owned collections of wines
- Supports public/private visibility
- Relationships: owner (User), wines (many-to-many)

### OCRSession
- Tracks OCR processing history
- Stores raw text and extracted structured data
- Can reference wine if successfully identified

### Reconstruction
- Stores 3D mesh data in JSON format
- Tracks confidence scores and processing time
- Supports multiple quality levels and export formats
- Relationships: analyses

### Analysis
- Complete wine analysis result
- Links user, wine, and reconstruction
- Stores recommendations, compliance checks, tasting profile
- Relationships: user, wine, reconstruction

## Adding a New Column

1. Add column to model in `backend/app/db/models.py`
2. Create migration:
   ```bash
   alembic revision --autogenerate -m "Add column description"
   ```
3. Review generated migration file
4. Apply migration:
   ```bash
   alembic upgrade head
   ```

## Testing with Database

Tests use SQLite in-memory database (`:memory:`). Each test gets a clean database instance.

No migration needed for tests - `Base.metadata.create_all(bind=engine)` in `main.py` handles schema creation on startup.
