# New CRUD Demo — FastAPI Auth + React

An **end-to-end authentication & authorization** app: users can **sign up**, **sign in**,
or **sign in with Google**, and on success land on a protected **home page**.

- **Backend:** FastAPI (async) · SQLAlchemy 2.0 · PostgreSQL · Alembic
- **Frontend:** React (JavaScript) · Vite · React Router
- **Auth:** JWT access + refresh in **httpOnly cookies**, **refresh-token rotation with
  reuse detection**, **argon2** password hashing, **CSRF** double-submit protection, and
  **Google OAuth 2.0 / OIDC**

```
Browser (React SPA :5173) ──fetch, credentials:'include'──▶ FastAPI (:8000) ──▶ Postgres (:5432)
        │
        └─ "Sign in with Google" ─▶ /auth/google/login ─▶ Google ─▶ /auth/google/callback ─▶ set cookies ─▶ redirect to SPA /home
```

## Why these session choices (the "industry standard")

| Concern | Choice | Why |
|--------|--------|-----|
| Where tokens live | **httpOnly, Secure, SameSite cookies** | JS can't read them → safe from XSS token theft (unlike `localStorage`) |
| Token lifetimes | short **access** (~15 min) + longer **refresh** (~7 days) | limits blast radius of a leaked access token |
| Refresh handling | **rotation** + **reuse detection** | a stolen refresh token is single-use; replay revokes all sessions |
| Passwords | **argon2** (`pwdlib`) | current OWASP-recommended password hash |
| CSRF | **double-submit token** (`csrf_token` cookie ↔ `X-CSRF-Token` header) | cookies auto-send, so mutations need a token an attacker can't read |

## Project layout

```
New-crud-demo/
├── docker-compose.yml          # postgres + backend (runs migrations, then uvicorn)
├── backend/                    # FastAPI app
│   ├── app/                    # config, db, models, schemas, crud, security, api routes, services
│   ├── alembic/                # migrations (0001_initial creates users + refresh_tokens)
│   ├── tests/                  # pytest suite (SQLite, no Postgres needed)
│   └── requirements.txt
└── frontend/                   # Vite + React SPA
    └── src/                    # api client, AuthContext, ProtectedRoute, Login/Signup/Home
```

## Endpoints

| Method | Path                    | Purpose                                              |
|--------|-------------------------|------------------------------------------------------|
| POST   | `/auth/signup`          | create account (email + password), set cookies       |
| POST   | `/auth/login`           | verify credentials, set cookies                      |
| POST   | `/auth/refresh`         | rotate refresh token, issue new access cookie (CSRF) |
| POST   | `/auth/logout`          | revoke refresh token, clear cookies (CSRF)           |
| GET    | `/auth/me`              | current user (protected)                             |
| GET    | `/auth/google/login`    | redirect to Google consent                            |
| GET    | `/auth/google/callback` | exchange code, upsert user, set cookies → SPA `/home`|
| GET    | `/health`               | liveness probe                                        |
| GET    | `/docs`                 | Swagger UI (dev only)                                 |

## Quick start

### 1. Backend + database (Docker)

```bash
cd New-crud-demo
cp backend/.env.example backend/.env        # then edit SECRET_KEY (+ Google creds, see below)
docker compose up --build
```

This starts Postgres, waits for it to be healthy, runs `alembic upgrade head`, and serves
the API at **http://localhost:8000** (Swagger at **/docs**, health at **/health**).

> **Run the backend without Docker** (needs a local Postgres, or point `DATABASE_URL` at one):
> ```bash
> cd backend
> python -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> alembic upgrade head
> uvicorn app.main:app --reload
> ```

### 2. Frontend (React dev server)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /auth + /health to :8000)
```

Open **http://localhost:5173** → sign up → you land on the home page.

## Google sign-in setup

The password flow works out of the box; Google needs your own OAuth credentials:

1. Go to **Google Cloud Console → APIs & Services → Credentials**.
2. **Create OAuth client ID** → *Web application*.
3. Add **Authorized redirect URI**: `http://localhost:8000/auth/google/callback`
4. (Consent screen) add your Google account as a test user.
5. Put the values in `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   ```
6. Restart the backend. The **"Sign in with Google"** button now completes the flow and
   drops you on `/home`. Without credentials the button returns `503` (feature disabled).

## Running the tests

```bash
cd backend
source .venv/bin/activate            # if not already
pip install -r requirements.txt
pytest
```

The suite uses in-memory SQLite (no Postgres required) and covers: signup, duplicate-email
rejection, login success/failure, the `/auth/me` auth gate, CSRF enforcement, refresh
rotation + reuse detection, logout, and the Google user upsert/account-linking logic.

## Deploying frontend & backend on separate origins

In dev the Vite proxy makes the SPA and API same-origin, so cookies work with no CORS setup.
In production on different hosts:

- Set `FRONTEND_URL` to the SPA origin — it's the single allowed CORS origin
  (`allow_credentials=True` forbids `*`).
- Serve both over **HTTPS** and set `COOKIE_SECURE=true`.
- If the sites are cross-site (different registrable domains), set `COOKIE_SAMESITE=none`
  (requires Secure). Same-site subdomains can keep `lax` with a shared `COOKIE_DOMAIN`.

## Notes / next steps

- `is_verified` is modeled; **email verification & password reset** (sending mail) are the
  natural next step and are intentionally out of scope for this demo.
- Refresh-token rows accumulate; a periodic job (or a TTL/index) should prune
  expired/revoked rows in production.
