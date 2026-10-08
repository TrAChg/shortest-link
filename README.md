# ShortestLink

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: Mypy](https://img.shields.io/badge/Type%20Checked-Mypy-blue.svg)](https://mypy-lang.org/)

**ShortestLink** is a production-grade, high-throughput, low-latency URL Shortener service built with **FastAPI**, **SQLAlchemy Async**, **PostgreSQL**, **Redis**, and **Docker**.

It provides sub-millisecond redirection via an in-memory Redis cache-aside pattern, zero-collision Base62 integer-to-alphanumeric encoding, and non-blocking background click analytics.

---

## Key Features

- **Sub-Millisecond Redirection**: Uses **Redis (Cache-Aside pattern)** to serve popular links straight from RAM in $< 1\text{ ms}$.
- **Zero-Collision Base62 Encoding**: Pure bijective mathematical conversion converting database IDs into compact 6-character strings with **0% collision rate**.
- **Custom Aliases**: Allows users to reserve vanity URLs (e.g., `http://localhost:8000/my-brand`) with duplicate collision prevention (`409 Conflict`).
- **URL Expiration**: Supports link lifespan via `expires_in_days` with automatic expiration enforcement.
- **Asynchronous Click Analytics**: Tracks click timestamps, client IP addresses, User-Agents, and HTTP Referrers via non-blocking **FastAPI `BackgroundTasks`** without delaying redirection.
- **Production Quality Gates**: 100% type-annotated with `mypy`, formatted and linted with `ruff`, pre-commit hooks, and a complete `pytest` automated integration test suite.
- **One-Command Containerization**: Ready to run with multi-stage `Dockerfile` and `docker compose`.

---

## System Architecture

```mermaid
flowchart TD
    User([Client / Browser]) -->|GET /{short_code}| Router[FastAPI Redirection Engine]
    Router -->|1. Check RAM| Cache[(Redis Cache)]

    Cache -->|Cache Hit < 1ms| Redirect[HTTP 307 Redirect]
    Cache -->|Cache Miss| DB[(PostgreSQL / SQLite)]

    DB -->|Found Target URL| WarmCache[Populate Redis with TTL]
    WarmCache --> Redirect
    DB -->|Not Found / Expired| NotFound[HTTP 404 Not Found]

    Redirect --> BG[BackgroundTasks]
    BG -.->|Async Fire-and-Forget| Analytics[(Click Analytics Table)]
    Redirect -->|Instant Location Header| User
```

---

## Quickstart & How to Run

### Option 1: Run with Docker Compose (Recommended)

This spins up **PostgreSQL 16**, **Redis 7**, and the **FastAPI web service** in isolated containers.

```powershell
# 1. Start all services in the background
docker compose up -d

# 2. View live service logs
docker compose logs -f

# 3. Stop all services when finished
docker compose down
```

Once running, visit the interactive Swagger UI at **[http://localhost:8000/docs](http://localhost:8000/docs)**!

---

### Option 2: Run Locally with `uv`

If you want to run the service locally without Docker (using local SQLite and optional local Redis):

```powershell
# 1. Install dependencies
uv sync

# 2. Run the development server with live reload
uv run uvicorn src.main:app --reload
```

---

## API Reference & Endpoints

Interactive documentation and testing are available out of the box at **`/docs`** (Swagger UI) and **`/redoc`**.

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/shorten` | Creates a new shortened link or custom alias | `201 Created` |
| `GET` | `/{short_code}` | Redirects visitor to the original destination | `307 Temporary Redirect` |
| `GET` | `/api/v1/analytics/{short_code}` | Retrieves click counts and recent click records | `200 OK` |

### 1. Create a Short Link
**Request:**
```http
POST /api/v1/shorten HTTP/1.1
Content-Type: application/json

{
  "url": "https://fastapi.tiangolo.com/tutorial/",
  "custom_alias": "fastapi-guide",
  "expires_in_days": 30
}
```

**Response (`201 Created`):**
```json
{
  "short_code": "fastapi-guide",
  "short_url": "http://localhost:8000/fastapi-guide",
  "original_url": "https://fastapi.tiangolo.com/tutorial/",
  "created_at": "2026-10-08T14:30:00Z",
  "expires_at": "2026-11-07T14:30:00Z"
}
```

### 2. URL Redirection
**Request:**
```http
GET /fastapi-guide HTTP/1.1
```
**Response (`307 Temporary Redirect`):**
```http
Location: https://fastapi.tiangolo.com/tutorial/
```

### 3. Click Analytics
**Request:**
```http
GET /api/v1/analytics/fastapi-guide HTTP/1.1
```
**Response (`200 OK`):**
```json
{
  "short_code": "fastapi-guide",
  "original_url": "https://fastapi.tiangolo.com/tutorial/",
  "total_clicks": 42,
  "created_at": "2026-10-08T14:30:00Z",
  "expires_at": "2026-11-07T14:30:00Z",
  "recent_clicks": [
    {
      "clicked_at": "2026-10-08T14:35:10Z",
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "referrer": null
    }
  ]
}
```

---

## Project Structure

```text
shortest-link/
├── src/
│   ├── api/
│   │   └── routes.py         # HTTP endpoints (Shorten, Redirect, Analytics)
│   ├── core/
│   │   └── base62.py         # Bijective Base62 encoding/decoding
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM models (URL, ClickAnalytics)
│   │   └── session.py        # Async engine & session connection pool
│   ├── schemas/
│   │   └── url.py            # Pydantic schemas with validation rules
│   ├── services/
│   │   ├── cache.py          # Redis caching service (aioredis)
│   │   └── shortener.py      # Core business logic with Dependency Injection
│   ├── config.py             # Settings management with pydantic-settings
│   └── main.py               # FastAPI application entrypoint & lifespan
├── tests/
│   ├── conftest.py           # Pytest fixtures & isolated DB runner
│   ├── test_api.py           # Integration tests for all HTTP routes
│   └── test_base62.py        # Unit tests for Base62 encoding/decoding
├── docker-compose.yml        # Multi-container orchestration (App + Postgres + Redis)
├── Dockerfile                # Multi-stage optimized Docker build with uv
├── pyproject.toml            # Project dependencies & tool configurations
└── README.md                 # Project documentation
```
