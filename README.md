# ReconAI — AI-powered Reconciliation Platform

Monorepo with one Flask backend and two frontends (plain HTML and React) sharing the same API.

```
Reconv2/
├── backend/           Flask 3 + SQLite + DuckDB reconciliation engine
├── frontend_html/     Zero-dependency single-file HTML/JS app
└── frontend_react/    React + Vite SPA
```

---

## Architecture

| Layer | Tech |
|---|---|
| App storage | SQLite (via SQLAlchemy — no setup required) |
| Source / Target inputs | Oracle (`oracledb`) · PostgreSQL (`psycopg2`) · CSV/XLSX uploads |
| Reconciliation engine | pandas full-outer merge + column-wise diff |
| AI narrative | Anthropic Claude (if API key set) → Ollama fallback |
| RAG chatbot | Ollama running locally · context from SQLite mismatch data |
| Credential storage | Fernet (AES-128-CBC) encrypted passwords |
| Column mapping | Fuzzy string matching (stdlib `difflib`) |
| Exports | Mismatch export + Detailed row-level export (xlsx/csv) |

---

## Quick Start

### 1. Backend

```powershell
cd backend

# Copy env template and fill in your values
copy .env.example .env

# Install deps
pip install -r requirements.txt

# Run dev server (SQLite DB created automatically on first run)
python run.py
```

**Required `.env` values:**
```
FERNET_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

**Optional `.env` values:**
```
ANTHROPIC_API_KEY=sk-ant-...    # enables Claude for narrative; Ollama used if blank
OLLAMA_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
MAX_ROWS_PER_TABLE=100000
```

---

### 2. Chatbot (Ollama)

The RAG chatbot requires [Ollama](https://ollama.ai) running locally:

```powershell
# 1. Install Ollama from https://ollama.ai
# 2. Pull a model
ollama pull llama3.1:8b       # recommended
# or
ollama pull mistral:7b
```

The `/api/chat/health` endpoint shows which models are installed and whether Ollama is reachable.

---

### 3. HTML Frontend

Open `frontend_html/index.html` directly in a browser. No build step.

---

### 4. React Frontend

```powershell
cd frontend_react
npm install
npm run dev       # dev server at http://localhost:5174
# or
npm run build     # production build
```

---

## How Each Feature Works

This app uses **real data only**. There is no in-memory/mock dataset in runtime flows.

### Connections
- Stored in SQLite with Fernet-encrypted passwords
- Test button verifies actual DB connectivity
- Tables/columns are fetched live from the source DB

### Reconciliation (New Run)
1. Choose source and target as either:
   - database table (Oracle/PostgreSQL), or
   - uploaded file (`.csv`, `.xlsx`, `.xls`)
2. Backend loads real columns from the selected inputs and runs fuzzy name matching to suggest mappings
3. User reviews mappings and checks match-key columns
4. `POST /api/runs/` — loads both tables into memory, performs full-outer merge, classifies each difference per row/column:
   - `value_diff` — genuine numeric/string difference
   - `format_diff` — same value after normalisation (whitespace, case, rounding)
   - `null_diff` — one side is NULL
   - `missing_in_target` / `missing_in_source` — row key only on one side
5. Results are persisted in SQLite:
   - mismatch details (`/api/runs/{id}/results`)
   - detailed row-wise report (`/api/runs/{id}/detailed-report`)

### Results Views
- **Mismatch View**: per-difference rows (`row_key`, `column`, `source`, `target`, `category`)
- **Detailed View**: one row per match key with per-column triplets:
  - `src_<column>`
  - `tgt_<column>`
  - `status_<column>`

API:
- `GET /api/runs/{id}/results?page=...&category=...`
- `GET /api/runs/{id}/detailed-report?page=...&status=all|match|mismatch`

### AI Narrative
- `GET /api/runs/{id}/narrative/stream` — Server-Sent Events
- Uses **Claude** (`claude-3-5-sonnet`) if `ANTHROPIC_API_KEY` is set, otherwise **Ollama** (`OLLAMA_CHAT_MODEL`)
- Narrative is persisted to SQLite after streaming

### RAG Chatbot
- Select one or more completed runs in the sidebar
- Backend fetches mismatch details + run summary from SQLite for the selected runs
- Builds a structured context block and sends it to Ollama with the user's question
- No external vector store required — the reconciliation data itself is the retrieval layer
- Model is configured via `OLLAMA_CHAT_MODEL` in `.env` and can be changed in the UI

### Export
- `GET /api/runs/{id}/export?format=xlsx` or `?format=csv`
- `GET /api/runs/{id}/export?format=summary`
- `GET /api/runs/{id}/detailed-report/export?format=xlsx|csv&status=all|match|mismatch`

### UI Theme & Typography
- Light/Dark mode toggle in top bar (stored in browser local storage as `recon_theme`)
- UI typography uses **DM Sans** with production weights
- Color palette uses tokens:
  - `--green: #2C7A4B`
  - `--amber: #A86410`
  - `--red: #C0372A`
  - `--blue: #1A5FA8`
  - `--coral: #BF4528`

### Reliability, Audit, and Ops
- `rules` can be passed during run creation for per-column normalization/tolerance and are persisted in run metadata for auditability
- Run lifecycle now includes `stage` and `progress_pct` so UI can poll and display live progress
- `GET /api/runs/{id}/counts` returns both mismatch category counts and row-level match/mismatch totals
- Upload guardrails include max file size, extension and MIME validation, and unsafe filename rejection
- Request-level audit events are captured for connection create/test/delete, run creation, exports, file upload/delete, and chat prompts
- `GET /api/health/readiness` verifies DB writability, uploads directory writability, and Ollama reachability
