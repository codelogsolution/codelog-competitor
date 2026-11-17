# KOMP Competitor Intelligence Agent

KOMP is an upload-first competitor intelligence workspace for marketing teams. Users upload SEMrush, G2, Capterra, and competitor website exports (CSV/XLSX); KOMP validates and normalizes records, scores competitors, researches only high-priority competitors, drafts evidence-backed battlecards, and requires human review before export.

## Product boundaries

- Phase 1 is file-upload only; no live SEMrush, G2, Capterra, or website integrations are claimed.
- No login/register or application authentication is included, by explicit scope. Run behind a private network/VPN or company access gateway; do not expose directly to the public internet.
- No automatic publishing, campaign sending, CRM writes, or external business actions.
- Only approved battlecards can be exported.
- `skills/competitor-intelligence/SKILL.md` is the single source of business rules. Python implements scoring; do not duplicate scoring formulas in prompts or frontend code.
- Each upload is registered in `source_imports`, linked to its analysis attempt, and shown on the workspace home with validation, stage, draft, and review status. The raw file is kept in `UPLOAD_DIR`; evidence, battlecards, run traces, and review decisions are persisted in the database.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS.
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic.
- Workflow: LangGraph.
- LLM: configurable Anthropic-compatible, OpenAI, or Vertex AI provider.
- Public research: Tavily, selectively for high-priority competitors.
- Database: PostgreSQL 16 for local and production runtime. SQLite is limited to isolated automated tests and one-time legacy data migration.
- Runtime: Python 3.12, Node 22, pnpm 11.24.0.

## Project structure

```text
komp-agent/
├── backend/
│   ├── app/
│   │   ├── ai/             # provider, prompts and evidence/research tools
│   │   ├── agents/         # LangGraph agent and typed state
│   │   ├── api/v1/         # FastAPI endpoints and router
│   │   ├── core/           # settings, logging, security helpers
│   │   ├── database/       # SQLAlchemy base and session
│   │   ├── models/         # evidence, battlecard, audit and run models
│   │   ├── repositories/   # database access
│   │   ├── schemas/        # API contracts
│   │   ├── services/       # validation, scoring, research, approvals
│   │   └── workflows/      # LangGraph nodes and graph
│   ├── alembic/            # database migrations
│   ├── tests/              # unit and integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/api/            # API clients
│   ├── src/components/     # shared UI
│   ├── src/pages/          # marketing-user workspace pages
│   ├── Dockerfile
│   └── nginx.conf
├── skills/competitor-intelligence/SKILL.md
├── docker-compose.yml
└── README.md
```

## Environment configuration

Use a **single root `.env`** file. Do not create separate backend/frontend `.env` files. Keep secrets local and out of Git.

Important settings:

```dotenv
APP_ENV=development
DEBUG=false
FRONTEND_ORIGIN=http://localhost:5173
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
POSTGRES_PASSWORD=local-development-only-change-me
DATABASE_URL=postgresql+psycopg://komp:local-development-only-change-me@127.0.0.1:5432/komp

LLM_PROVIDER=anthropic
LLM_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=3500
ANTHROPIC_API_KEY=
ANTHROPIC_BASE_URL=http://127.0.0.1:31415
OPENAI_API_KEY=
OPENAI_BASE_URL=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=us-central1
TAVILY_API_KEY=

MAX_UPLOAD_SIZE_MB=10
MAX_UPLOAD_ROWS=10000
MAX_XLSX_UNCOMPRESSED_MB=100
```

For local development, start the PostgreSQL service with `docker compose up -d db` and configure `DATABASE_URL` for that local database. Change the example password before using the stack beyond local development. KOMP now refuses to start when `DATABASE_URL` is blank or points to SQLite. The repository's `.gitignore` intentionally ignores `.env` and `.env.example` according to the maintainer's preference.

## Run locally on macOS

### 1. Backend setup

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
docker compose up -d db
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
```

To preserve existing local SQLite data, keep the SQLite file as a backup, create the PostgreSQL schema first, then run `python backend/scripts/migrate_sqlite_to_postgres.py`. The script copies the legacy run, battlecard, evidence, source, and audit rows into empty PostgreSQL tables without changing the SQLite file. Copy the configured upload directory separately if the legacy database contains registered source files.

### 2. Start backend

In terminal 1:

```bash
cd backend
PYTHONPATH=. ../backend/.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health/readiness: `http://127.0.0.1:8000/api/v1/health`

### 3. Start frontend

In terminal 2:

```bash
cd frontend
corepack enable
corepack prepare pnpm@11.24.0 --activate
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:5173`.

## Test and build

Backend:

```bash
cd backend
PYTHONPATH=. ../backend/.venv/bin/pytest -q
```

Live LLM tests are disabled by default to avoid surprise external calls/costs. Explicit opt-in:

```bash
RUN_LIVE_LLM_TESTS=true PYTHONPATH=. .venv/bin/pytest tests/integration/test_llm_connection.py -v
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm build
```

## Production release: GitHub + Vercel + Docker API

This release layout uses **Vercel for the React/Vite frontend**, a **Docker-capable cloud host for FastAPI**, managed **PostgreSQL** for application records, and persistent file storage for uploaded CSV/XLSX files. Vercel does not host the API just because the frontend repository is connected; the API and database must be provisioned separately.

```text
User's browser
  └── Vercel frontend (HTTPS)
        └── FastAPI Docker service (HTTPS, exact frontend origin allowed)
              ├── Managed PostgreSQL (private connection)
              ├── Persistent upload storage mounted at /app/data/uploads
              └── Hosted LLM provider + Tavily APIs
```

Render is used below as an example Docker host because it supports Docker services, managed PostgreSQL, and persistent disks. Use the equivalent settings if you choose another provider. Render persistent disks require a paid web-service plan and restrict the service to one instance; review current [Render pricing](https://render.com/pricing) before provisioning. See [Render Docker deploys](https://render.com/docs/docker), [Render Postgres](https://render.com/docs/postgresql), [Render persistent disks](https://render.com/docs/disks), and [Vercel's Vite guide](https://vercel.com/docs/frameworks/frontend/vite).

### Production gate: protect the API before exposing it

The current app has **no login or API authentication**. CORS only controls which browser origins can read responses; it does not stop direct API requests. Do not put sensitive company data into this deployment or expose its API publicly until an authentication/access-control layer protects **both** the frontend and API. Vercel Deployment Protection can restrict the Vercel site, but it does not automatically protect a separate Docker API host. Use a supported identity gateway in front of both, or add application authentication and authorization before public launch. Vercel documents [Deployment Protection](https://vercel.com/docs/deployment-protection).

The app currently stores uploaded source files on local disk. In production, mount durable storage at `/app/data/uploads`. A single attached disk is suitable for one API instance; it is not shared storage for multiple replicas. If you need horizontal scaling, move uploads to private object storage and update the file service before scaling out.

### 1. Prepare and push the repository safely

1. Keep the GitHub repository private while KOMP has no application login.
2. From the repository root, review what will be uploaded:

   ```bash
   git status --short
   git diff --check
   git diff --cached --check
   git check-ignore -v .env
   git ls-files --error-unmatch .env
   ```

3. `git ls-files --error-unmatch .env` should report that `.env` is not tracked. If it prints a path, stop and remove that file from Git history/index before pushing; adding it to `.gitignore` does not untrack it. Review the staged files before committing. Do not push `.env`, API keys, database passwords, local database files, uploaded customer/competitor exports, or generated secrets. Keep provider credentials in the cloud provider's secret settings. The repo intentionally ignores `.env` and `.env.example`; never force-add either file.
4. Push the reviewed application code and this README to GitHub. Before importing the repository into Vercel, decide which branch is allowed to become production: Vercel can automatically deploy the configured production branch. Use a non-production branch/Preview deployment for the first verification; do not connect or promote an unready branch to the public production domain.

### 2. Provision managed PostgreSQL

1. Create a production PostgreSQL database in the same region as the API service where possible.
2. Use the provider's **private/internal** connection string for the API. Do not expose PostgreSQL publicly unless the provider specifically requires it and you have set strict network rules.
3. Keep the production database separate from the local Docker database. Do not import demo or personal local data unless you explicitly intend to migrate it.
4. Configure automated backups/point-in-time recovery where available and document a restore procedure before storing business data.

### 3. Deploy the FastAPI Docker API

For a Render example, create a Docker **Web Service** from the private GitHub repository:

- Dockerfile path: `backend/Dockerfile`
- Docker build context: `backend`
- Health check path: `/api/v1/health`
- Region: same region as PostgreSQL (for users in India, Singapore is a nearby option if available)
- Instance count: one while uploads use a mounted local disk
- Persistent disk mount path: `/app/data/uploads`; set `UPLOAD_DIR=/app/data/uploads`

Render's public service runs under its `PORT` environment variable. Set the Docker start command to run migrations, then bind Uvicorn to that port:

```sh
sh -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}'
```

Set these API service environment variables in the host dashboard. Use its managed-database reference for `DATABASE_URL`; enter secrets through the dashboard, not GitHub:

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `DATABASE_URL` | Provider's private PostgreSQL connection string |
| `FRONTEND_ORIGIN` | Exact HTTPS Vercel production origin, e.g. `https://your-project.vercel.app` |
| `UPLOAD_DIR` | `/app/data/uploads` |
| `LLM_PROVIDER` | Provider configured for this deployment: `anthropic`, `openai`, or `vertex_ai` |
| `LLM_MODEL` | Model identifier supported by the selected provider |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Set only the selected provider's key |
| `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` | Set only when using a hosted compatible endpoint |
| `TAVILY_API_KEY` | Set if public research is enabled |
| `MAX_UPLOAD_SIZE_MB` | Choose the production upload limit (default `10`) |

Do not copy local `.env` values blindly. A local `127.0.0.1` or `localhost` LLM proxy is reachable only from your Mac, not from the cloud container. The deployed API needs a hosted provider endpoint and its own server-side credentials. OpenClaw is not currently part of KOMP's competitor-analysis request path; a locally running OpenClaw instance also cannot be reached from a cloud deployment without a separately secured, hosted integration.

After deploy, verify:

```bash
curl -fsS https://YOUR-API-HOST/api/v1/health
```

Confirm the response reports a healthy database. Check service logs for successful Alembic migrations and startup. Do not add API keys to the `curl` command or paste them into issue trackers.

### 4. Connect the GitHub repository to Vercel

1. In Vercel, create a project and import the private GitHub repository.
2. Set **Root Directory** to `frontend` (not the repository root).
3. Use the Vite framework preset and confirm these build settings:
   - Install command: `pnpm install --frozen-lockfile`
   - Build command: `pnpm build`
   - Output directory: `dist`
4. Add `VITE_API_BASE_URL` to Vercel's **Preview** and **Production** environments. For the production environment, set:

   ```text
   VITE_API_BASE_URL=https://YOUR-API-HOST/api/v1
   ```

   `VITE_*` values are included in browser assets. This variable may contain the API's public HTTPS base URL, but never an API key, database URL, or other secret.
5. Keep Preview and Production environment values separate. Point Preview at a staging API/database if you have one. Do not point experimental preview builds at the production database.
6. Make sure `FRONTEND_ORIGIN` on the API includes the exact Vercel origin being used. The backend currently uses an exact comma-separated CORS allowlist; avoid wildcards. A stable branch-preview domain can be added explicitly for QA.
7. Enable Vercel Deployment Protection for preview and production URLs as an additional access barrier. This does **not** replace authentication on the separately hosted API.

Vercel builds static assets when the connected branch or pull request deploys. Use a Preview deployment first; only select/promote the Production branch after the API URL, CORS origin, database, upload persistence, and access protection have all been verified.

### 5. Verify the production workflow before announcing the URL

Use synthetic, non-sensitive CSV/XLSX files first. Verify each behavior in the deployed environment:

1. Health endpoint succeeds and the API can reach PostgreSQL.
2. Upload and validate a source; refresh the page and confirm the uploaded filename and stage remain saved.
3. Run an analysis and follow the saved status through scoring, selective research, and draft generation.
4. Confirm source evidence and public evidence display correctly with working source links.
5. Approve one eligible battlecard and reject another; refresh and confirm both decisions persist.
6. Export and confirm that **only approved** battlecards appear.
7. Delete a test source and confirm its linked data is removed while its audit events remain.
8. Restart/redeploy the API and confirm uploaded files still exist on persistent storage.
9. Confirm unauthorized users cannot access either the workspace or API before any real data is uploaded.

If any request is redirected to HTML, check that `VITE_API_BASE_URL` points to the API (not the Vercel site), the API is HTTPS, and its `FRONTEND_ORIGIN` matches the browser's exact origin. After changing a Vercel environment variable, trigger a new deployment so the Vite build includes the updated value.

### 6. Operate and roll back

- Back up PostgreSQL and uploaded files independently; test restoration before relying on the backups.
- Monitor API health, logs, storage usage, database connections, and provider quotas/costs.
- Keep LLM and Tavily keys only in backend secrets. Rotate any credential that was ever committed or shared in a screenshot/chat.
- Keep the current deployment to one API instance while using a local persistent disk. Move to private object storage before enabling multiple API instances.
- For a bad frontend release, roll back to the previous Vercel deployment. For API/schema changes, take a database backup first and follow Alembic migration compatibility; do not delete production volumes to fix migration errors.

### Release checklist

- [ ] Repository is private and no secrets or user-uploaded files are committed.
- [ ] Application/API authentication or an equivalent identity gateway protects both frontend and API.
- [ ] Production PostgreSQL is provisioned with backups and private connectivity.
- [ ] API Docker service applies migrations and passes `/api/v1/health`.
- [ ] Upload storage persists across restart/deploy.
- [ ] Hosted LLM/Tavily credentials and provider endpoints are configured server-side.
- [ ] Vercel root directory is `frontend`; build succeeds; `VITE_API_BASE_URL` uses HTTPS.
- [ ] API CORS allowlist matches the final Vercel origin exactly.
- [ ] Preview workflow and approval/export/deletion scenarios pass before Production promotion.

**Current limitation:** the application-authentication checkbox is not implemented in this codebase yet. Until it is added or a verified access gateway protects both the UI and API, keep the production data empty and do not expose the API as a public business tool.

## Docker Compose deployment

1. Set `POSTGRES_PASSWORD` and provider credentials in root `.env`. Compose binds to `127.0.0.1` by default (`APP_BIND_ADDRESS`); for remote private access, use a VPN/private interface or a TLS reverse proxy.
2. Run from repository root:

   ```bash
   docker compose config
   docker compose build
   docker compose up -d
   docker compose ps
   docker compose logs -f backend
   ```

3. Open `http://localhost:8080` on the host (or the configured `APP_PORT`). The default loopback bind is intentional because the application has no login.
4. Verify `http://localhost:8080/api/v1/health`.
5. Test the complete workflow with a small non-sensitive CSV.
6. Back up the PostgreSQL and uploads volumes regularly.

Use `docker compose down` to stop services while preserving data. Never use `docker compose down -v` unless you intentionally want to delete persistent volumes.

## Workflow

1. Upload CSV/XLSX.
2. Review valid, warning, and invalid rows.
3. Run analysis; only valid evidence contributes to scoring.
4. Review competitor scores and supporting evidence.
5. Public research runs only for competitors scoring at least 70.
6. Battlecard drafts require score >=70 and usable evidence; drafts start `pending_review`.
7. Reviewer approves, rejects, requests changes, or resubmits.
8. Only approved battlecards can be exported.

## Business rules

- `skills/competitor-intelligence/SKILL.md` — business rules and scoring contract.

## Operational note

This is a private-workspace deployment baseline, not a public multi-tenant SaaS. The app has no authentication by design, and infrastructure-level access control is required.
