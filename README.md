# ReleaseMind

ReleaseMind compares an LLM-only review of a proposed software change with a review augmented by retrieved, source-linked incident summaries. It shows the evidence used and recommends safeguards.

**Scope:** historical context for engineering review. ReleaseMind does not predict production incidents or claim that a historical report caused the outcome of a proposed change.

## Run locally

Requirements: Python 3.12+ and Node.js/npm. An OpenAI-compatible LLM API key is needed for assessments; Groq is supported.

### Configure and start the backend

```shell
cd backend
python -m venv .venv
```

Activate the environment, then install dependencies and create your local configuration:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

```bash
# macOS/Linux
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set the API key. For Groq, set:

```dotenv
OPENAI_API_KEY=your_groq_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b
```

Start the backend from the `backend` directory:

```shell
uvicorn app.main:app --reload --port 8001
```

### Start the frontend

In another terminal, from the project root:

```shell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The React development server proxies API calls to the FastAPI backend on port 8001. If memory is empty, use **Import authorized data** and select `data/postmortem-index-demo.json`. The local SQLite database persists at `data/releasemind.sqlite3` and is excluded from Git.

## Data and attribution

The included demo snapshot contains 195 short summaries from the [Postmortem Index](https://postmortems.app/about), whose publisher declares the index corpus GPL-3.0. Full linked postmortem text is not bundled; original source URLs are retained with records. Individual reports remain subject to their publishers' terms. Credit: “Postmortem Index, maintained by icco and contributors, GPL-3.0; individual incident reports remain the property of their original publishers.” See [data/README.md](data/README.md) and [data/SOURCE-MANIFEST.md](data/SOURCE-MANIFEST.md).

The TU Delft VOID sample is not included because reuse rights for the exact files and linked reports have not been verified. The included incident summaries do not establish general deployment-to-incident causal links.

## Memory and model configuration

The default provider is persistent local SQLite with BM25-style lexical retrieval. This is not Hindsight and is not embedding-based semantic retrieval. Hindsight is optional; configuration details are in [docs/architecture.md](docs/architecture.md) and `backend/.env.example`.

Keep API keys in `backend/.env`. Do not put keys in frontend code or commit local `.env` files. This prototype has no authentication or rate limiting; keep it on a trusted local machine and do not expose the API publicly without appropriate access and usage controls.

## Evaluation status

The side-by-side baseline and memory-augmented outputs are demonstration outputs, not experimental results. No retrieval-quality or answer-quality improvement is claimed.

## Project documentation

- [Architecture](docs/architecture.md)
- [Dataset access and import](data/README.md)
