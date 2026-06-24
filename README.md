# ASM Asset Management System

## Overview
A backend asset management system designed for cybersecurity Attack Surface Monitoring (ASM). It serves as the central repository for discovered internet-facing assets (domains, subdomains, IPs, services, certificates, and technologies).

## Features
- **Asset Inventory**: Full CRUD operations for various asset types.
- **Bulk Import & Deduplication**: High-performance bulk ingestion of JSON data. Intelligently deduplicates based on `(type, value)`, merging metadata and tags seamlessly.
- **Relationship Graph**: Store, validate, and traverse relationships between assets (e.g., `subdomain -> domain`). 
- **Advanced Querying**: Filter by type, status, source, tags, or dates, complete with pagination and sorting.
- **Authentication**: JWT-based security protecting write operations while allowing public read access.

## Architecture
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + Asyncpg
- **ORM**: SQLAlchemy 2.0 (Async) + Alembic Migrations
- **Validation**: Pydantic V2
- **Deployment**: Docker + Docker Compose

## Quickstart

1. **Environment Setup**
   ```bash
   cp .env.example .env
   ```

2. **Run the Application**
   ```bash
   docker compose up --build
   ```
   This will spin up the PostgreSQL database and the FastAPI application. Alembic migrations are applied automatically on startup.

3. **Access API Documentation**
   Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to explore the interactive Swagger UI.

## Testing
The application uses `pytest` with `pytest-asyncio` and an in-memory SQLite database (`aiosqlite`) for fast, isolated tests.

To run the test suite:
```bash
docker compose exec api pytest app/tests/ -v
```

## Seed Data
You can test the bulk import functionality using the provided seed data file:
```bash
# First, register and login via the Swagger UI to get a Bearer token.
# Then, import the seed data:
curl -X POST http://localhost:8000/import \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d @app/seed/sample_assets.json
```
