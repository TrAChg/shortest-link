# Project: Production Short-Link Service (URL Shortener) 🔗⚡
*A high-throughput, low-latency URL Shortener built with FastAPI, PostgreSQL, SQLAlchemy Async, Redis, and Docker.*

---

## 📖 Table of Contents
1. [Project Overview & System Design Context](#project-overview--system-design-context)
2. [Functional & Non-Functional Requirements](#functional--non-functional-requirements)
3. [System Architecture Diagram](#system-architecture-diagram)
4. [Mathematical & Algorithmic Foundation: Base62](#mathematical--algorithmic-foundation-base62)
   - [Why Base62?](#why-base62)
   - [Mathematical Formulation of Base Conversion](#mathematical-formulation-of-base-conversion)
   - [Step-by-Step Numerical Example](#step-by-step-numerical-example)
   - [Base62 vs. Hashing (MD5/SHA256) Collision Analysis](#base62-vs-hashing-md5sha256-collision-analysis)
5. [Database Architecture & Data Modeling](#database-architecture--data-modeling)
   - [Entity Relationship Diagram](#entity-relationship-diagram)
   - [Indexing Strategy for High-Speed Lookups](#indexing-strategy-for-high-speed-lookups)
6. [HTTP Redirect Semantics: `301` vs. `307`](#http-redirect-semantics-301-vs-307)
7. [Caching Layer: Redis Cache-Aside Pattern](#caching-layer-redis-cache-aside-pattern)
8. [API Specification (Contract)](#api-specification-contract)
9. [Step-by-Step Implementation Roadmap](#step-by-step-implementation-roadmap)
   - [Phase 1: Pure Algorithm & Unit Tests](#phase-1-pure-algorithm--unit-tests)
   - [Phase 2: Configuration & Database Layer](#phase-2-configuration--database-layer)
   - [Phase 3: Pydantic Validation & Service Layer](#phase-3-pydantic-validation--service-layer)
   - [Phase 4: FastAPI Router & HTTP Endpoints](#phase-4-fastapi-router--http-endpoints)
   - [Phase 5: Redis Caching Integration](#phase-5-redis-caching-integration)
   - [Phase 6: Containerization & Integration Testing](#phase-6-containerization--integration-testing)
10. [Defense & Technical Interview Questions](#defense--technical-interview-questions)

---

## Project Overview & System Design Context

A **URL Shortener** (such as Bitly or TinyURL) is one of the most classic and revealing system design problems in modern software engineering. It appears simple on the surface, but requires mastery of:
- **Read-heavy scaling**: Typical read-to-write ratios exceed $100 : 1$.
- **Sub-millisecond latency**: URL redirection must not degrade user browsing experience.
- **Bijective encoding algorithms**: Converting database identity sequences into compact strings without collision.
- **Asynchronous I/O**: Ensuring database and network calls do not block the Python event loop.

This project is structured according to **Clean Architecture** principles, separating domain logic, database persistence, caching, and API routing.

---

## Functional & Non-Functional Requirements

### 1. Functional Requirements
1. **URL Shortening**: Given any valid HTTP/HTTPS URL, the system returns a unique short alias (e.g., `http://localhost:8000/a8F3x9`).
2. **Custom Aliases**: Users can optionally specify a custom alias (e.g., `http://localhost:8000/my-custom-link`).
3. **URL Redirection**: Visiting `http://localhost:8000/{short_code}` redirects the user to the original long URL with `HTTP 307 Temporary Redirect`.
4. **URL Expiration**: Links can have an optional expiration date (`expires_at`). Expired links must return `HTTP 410 Gone` or `HTTP 404 Not Found`.
5. **Click Analytics**: The system records click timestamps, user IP address, referrer header, and user-agent string asynchronously.
6. **Analytics Dashboard API**: Retrieve aggregate statistics (total clicks, click history) for a given short code.

### 2. Non-Functional Requirements
- **High Availability**: Redirection must succeed even under high concurrency.
- **Ultra-low Latency**: Read redirection latency $< 5\text{ ms}$ via Redis caching.
- **Uniqueness Guarantee**: No two distinct long URLs can produce colliding short codes.
- **Input Validation**: Rejection of malformed URLs and self-referencing redirect loops.

---

## System Architecture Diagram

```
                                  ┌──────────────────────────────────────────────┐
                                  │                 Redis Cache                  │
                                  │   Key: "short:{code}" -> Target URL (TTL)    │
                                  └──────────────────────▲───────────────────────┘
                                                         │
                                        1. Check cache   │  2. Cache Hit (< 1ms)
                                           for {code}    │     Return target URL
                                                         │
┌──────────────────────┐          ┌──────────────────────┴───────────────────────┐
│                      │          │                 FastAPI App                  │
│                      │ ───────► │                                              │
│   Web Browser /      │  Request │  • Endpoint: GET /{code}                     │
│   Client Application │          │  • Endpoint: POST /api/v1/shorten            │
│                      │ ◄─────── │  • Endpoint: GET /api/v1/analytics/{code}    │
│                      │ Redirect │                                              │
└──────────────────────┘ (307)    └──────────────────────┬───────────────────────┘
                                                         │
                                        3. Cache Miss    │  4. Async Log Click
                                           Query DB      │     to Analytics
                                                         │
                                  ┌──────────────────────▼───────────────────────┐
                                  │             PostgreSQL Database              │
                                  │                                              │
                                  │  • Table: urls (id, code, original_url...)   │
                                  │  • Table: click_analytics (id, url_id...)    │
                                  └──────────────────────────────────────────────┘
```

---

## Mathematical & Algorithmic Foundation: Base62

### Why Base62?
URLs are transmitted over HTTP and must adhere to RFC 3986 (URI Generic Syntax). Characters in URLs should be URL-safe to avoid percent-encoding (like `%20` or `%2B`).

The Base62 alphabet consists of:
$$\Sigma_{\text{Base62}} = [0\text{--}9, a\text{--}z, A\text{--}Z]$$

- Digits: $0\dots9$ (10 characters)
- Lowercase letters: $a\dots z$ (26 characters)
- Uppercase letters: $A\dots Z$ (26 characters)
- **Total alphabet size**: $|\Sigma| = 10 + 26 + 26 = 62$

With a 6-character short code, the total number of unique addressable links is:
$$N = 62^6 = 56,800,235,584 \quad (\approx 56.8 \text{ billion URLs})$$

With a 7-character short code:
$$N = 62^7 = 3,521,614,606,208 \quad (\approx 3.52 \text{ trillion URLs})$$

### Mathematical Formulation of Base Conversion

Converting an auto-incrementing integer ID $n \in \mathbb{N}_{> 0}$ to a Base62 string is a positional numeral system conversion:

$$n = \sum_{i=0}^{k-1} d_i \cdot 62^i = d_0 \cdot 62^0 + d_1 \cdot 62^1 + \dots + d_{k-1} \cdot 62^{k-1}$$

where each digit $d_i \in \{0, 1, \dots, 61\}$ maps to a character in $\Sigma_{\text{Base62}}$:
$$\text{char} = \Sigma_{\text{Base62}}[d_i]$$

#### The Algorithm (Integer to Base62 String):
1. While $n > 0$:
   - Compute remainder: $r = n \pmod{62}$
   - Compute quotient: $n = \lfloor n / 62 \rfloor$
   - Append $\Sigma_{\text{Base62}}[r]$ to the result.
2. Reverse the accumulated characters (since least significant digits were produced first).
3. If $n = 0$, return `"0"`.

#### The Inverse Algorithm (Base62 String to Integer):
Given a string $S = s_0 s_1 \dots s_{m-1}$:
$$n = \sum_{j=0}^{m-1} \text{index}(s_j) \cdot 62^{m - 1 - j}$$

Complexity:
- Time Complexity: $\mathcal{O}(\log_{62} n)$
- Space Complexity: $\mathcal{O}(\log_{62} n)$

### Step-by-Step Numerical Example

Suppose the database assigns primary key $n = 125,380$:

1. **Step 1**:
   - $125,380 \div 62 = 2022$, remainder $r_0 = 125,380 - (2022 \times 62) = 16$.
   - $\Sigma[16] \rightarrow$ `'g'` (since $0..9 \rightarrow 0..9$, $a \rightarrow 10, b \rightarrow 11, \dots, g \rightarrow 16$).
2. **Step 2**:
   - $2022 \div 62 = 32$, remainder $r_1 = 2022 - (32 \times 62) = 38$.
   - $\Sigma[38] \rightarrow$ `'C'` (since $a..z \rightarrow 10..35$, $A \rightarrow 36, B \rightarrow 37, C \rightarrow 38$).
3. **Step 3**:
   - $32 \div 62 = 0$, remainder $r_2 = 32$.
   - $\Sigma[32] \rightarrow$ `'w'`.
4. **Step 4**:
   - Quotients reached 0. Characters produced: `['g', 'C', 'w']`.
   - Reversed: `'w'` + `'C'` + `'g'` = **`"wCg"`**.

Verify by decoding:
$$\text{value} = \text{index}('w') \cdot 62^2 + \text{index}('C') \cdot 62^1 + \text{index}('g') \cdot 62^0$$
$$\text{value} = 32 \cdot 3844 + 38 \cdot 62 + 16 \cdot 1 = 123,008 + 2356 + 16 = 125,380 \quad \checkmark$$

### Base62 vs. Hashing (MD5/SHA256) Collision Analysis

| Approach | Mechanism | Collision Risk | Handling Collisions |
| :--- | :--- | :--- | :--- |
| **Integer ID + Base62** | Bijective 1-to-1 conversion of sequence | **Mathematically Impossible (0%)** | None needed; every integer has a unique Base62 representation. |
| **Hash Truncation** (MD5/Murmur) | Truncate hash of URL to 7 chars | **Birthday Paradox applies** ($p \approx 1 - e^{-k^2 / (2N)}$) | Requires database lookups on write and salt appending on collisions. |

> [!TIP]
> In production architectures, combining a 64-bit integer generator (e.g. PostgreSQL `BIGSERIAL` or distributed Snowflake IDs) with Base62 encoding gives **zero collisions** and **predictable length**.

---

## Database Architecture & Data Modeling

### Entity Relationship Diagram

```
┌────────────────────────────────────────┐
│                 urls                   │
├────────────────────────────────────────┤
│ id           : BIGSERIAL PRIMARY KEY   │
│ original_url : TEXT NOT NULL           │
│ short_code   : VARCHAR(16) UNIQUE      │
│ custom_alias : BOOLEAN DEFAULT FALSE   │
│ is_active    : BOOLEAN DEFAULT TRUE    │
│ created_at   : TIMESTAMPTZ DEFAULT NOW │
│ expires_at   : TIMESTAMPTZ NULLABLE    │
└──────────────────┬─────────────────────┘
                   │ 1
                   │
                   │ N
┌──────────────────▼─────────────────────┐
│           click_analytics              │
├────────────────────────────────────────┤
│ id           : BIGSERIAL PRIMARY KEY   │
│ url_id       : BIGINT REFERENCES urls  │
│ clicked_at   : TIMESTAMPTZ DEFAULT NOW │
│ ip_address   : VARCHAR(45) NULLABLE    │
│ user_agent   : TEXT NULLABLE           │
│ referrer     : TEXT NULLABLE           │
└────────────────────────────────────────┘
```

### Indexing Strategy for High-Speed Lookups
1. **`urls.short_code`**: Unique B-tree Index (`CREATE UNIQUE INDEX idx_urls_short_code ON urls(short_code)`).
   - This ensures $O(\log N)$ point lookups when redirecting on cache misses.
2. **`click_analytics.url_id`**: Foreign key B-tree Index (`CREATE INDEX idx_analytics_url_id ON click_analytics(url_id)`).
   - Enables fast aggregation for analytics queries (`COUNT(*)` grouped by date).

---

## HTTP Redirect Semantics: `301` vs. `307`

When a client queries `GET /{short_code}`, your server responds with an HTTP redirection:

- **`HTTP 301 Moved Permanently`**:
  - The client's browser caches the target URL in local browser storage indefinitely.
  - Subsequent requests to `/{short_code}` are redirected by the browser *without contacting your server*.
  - **Trade-off**: Saves server bandwidth, but **destroys click analytics** because you cannot track subsequent clicks.
- **`HTTP 302 Found` (Legacy Temporary)**:
  - Some older clients erroneously convert `POST` to `GET` during redirection.
- **`HTTP 307 Temporary Redirect` (Recommended Standard)**:
  - Guarantees the HTTP method is preserved.
  - The browser requests the server on **every single click**, enabling 100% accurate click analytics and real-time link deactivation.

---

## Caching Layer: Redis Cache-Aside Pattern

```
                       Request GET /{code}
                               │
                               ▼
                    [ Does Key exist in Redis? ]
                               │
                 ┌─────────────┴─────────────┐
                 │ YES                       │ NO
                 ▼                           ▼
          [ Cache Hit ]              [ Cache Miss ]
      Return Target URL (<1ms)       Query PostgreSQL
                                             │
                                     [ Found in DB? ]
                                             │
                                  ┌──────────┴──────────┐
                                  │ YES                 │ NO
                                  ▼                     ▼
                           Set Redis Key           Return 404
                          (TTL = 24 Hours)
                                  │
                                  ▼
                          Return Target URL
```

Key naming convention:
- `shortlink:code:{short_code}` $\rightarrow$ String value containing `original_url` (with TTL, e.g. 86400 seconds).

---

## API Specification (Contract)

### 1. `POST /api/v1/shorten`
**Request Payload**:
```json
{
  "url": "https://deepmind.google/technologies/gemini/",
  "custom_alias": "gemini-overview",
  "expires_in_days": 30
}
```
**Response (201 Created)**:
```json
{
  "short_code": "gemini-overview",
  "short_url": "http://localhost:8000/gemini-overview",
  "original_url": "https://deepmind.google/technologies/gemini/",
  "created_at": "2026-09-23T15:45:00Z",
  "expires_at": "2026-10-23T15:45:00Z"
}
```

### 2. `GET /{short_code}`
- **Response**: `HTTP 307 Temporary Redirect` with Header `Location: <original_url>`.
- If expired or not found: `HTTP 404 Not Found`.

### 3. `GET /api/v1/analytics/{short_code}`
**Response (200 OK)**:
```json
{
  "short_code": "gemini-overview",
  "original_url": "https://deepmind.google/technologies/gemini/",
  "total_clicks": 142,
  "created_at": "2026-09-23T15:45:00Z",
  "recent_clicks": [
    {
      "clicked_at": "2026-09-23T15:48:12Z",
      "referrer": "https://linkedin.com",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

---

## Step-by-Step Implementation Roadmap

You will build this project module-by-module. Each module has pre-defined test criteria:

### Phase 1: Pure Algorithm & Unit Tests
- **Target File**: [`src/core/base62.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/core/base62.py)
- **Goal**: Implement `encode_base62(num: int) -> str` and `decode_base62(code: str) -> int`.
- **Validation**: Run `pytest tests/test_base62.py` until all tests pass.

### Phase 2: Configuration & Database Layer
- **Target Files**:
  - [`src/config.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/config.py): Load settings with `pydantic-settings`.
  - [`src/db/session.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/db/session.py): Setup async SQLAlchemy engine (`create_async_engine`) and session dependency (`get_db`).
  - [`src/db/models.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/db/models.py): Define `URL` and `ClickAnalytics` ORM models.

### Phase 3: Pydantic Validation & Service Layer
- **Target Files**:
  - [`src/schemas/url.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/schemas/url.py): Pydantic input/output schemas with URL regex validation.
  - [`src/services/shortener.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/services/shortener.py): Business logic to create short links, handle custom aliases, and retrieve destinations.

### Phase 4: FastAPI Router & HTTP Endpoints
- **Target Files**:
  - [`src/api/routes.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/api/routes.py): Implement `/api/v1/shorten`, `/{short_code}`, and `/api/v1/analytics/{short_code}`.
  - [`src/main.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/main.py): Wire the router into the FastAPI application.

### Phase 5: Redis Caching Integration
- **Target Files**:
  - [`src/services/cache.py`](file:///c:/Users/TC/AI_Engineer/Projet/shortest-link/src/services/cache.py): Implement `get_url_cache` and `set_url_cache` using `redis.asyncio`.

### Phase 6: Containerization & Integration Testing
- Start PostgreSQL and Redis via Docker Compose: `docker compose up -d`.
- Run complete test suite: `uv run pytest`.

---

## Defense & Technical Interview Questions

When presenting this project in a technical interview, expect these questions:
1. **"What happens if two users request the same custom alias simultaneously?"**
   *(Answer: Handled by PostgreSQL UNIQUE constraint on `short_code`, throwing an `IntegrityError` which maps to HTTP 409 Conflict).*
2. **"How do you handle the ID generation if you run across multiple database instances?"**
   *(Answer: A single sequence doesn't scale across multi-master DBs; use a distributed ID generator like Twitter Snowflake or UUIDv7).*
3. **"Why use Redis rather than in-memory Python dictionary?"**
   *(Answer: FastAPI runs with multiple worker processes (Uvicorn workers). In-memory dict is process-local and lost on reload; Redis is shared and persistent).*
4. **"How do you prevent malicious users from shortening phishing or redirect-loop URLs?"**
   *(Answer: Validate domain against Google Safe Browsing API, block self-referential hostnames).*
