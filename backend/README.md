# Backend

FastAPI service for the LLM Debate + Judge pipeline.

## Setup
```bash
cd backend
cp .env.example .env
# set OPENAI_API_KEY in .env
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Run
```bash
uvicorn src.app:app --reload --port 8000
```

## Endpoints
- `GET /health`
- `POST /run`
- `POST /batch`
- `GET /logs/{run_id}`

## Notes
- Prompt files are loaded from `../prompts/`.
- Every run is logged to `../runs/`.
- `scripts/generate_report_artifacts.py` can turn a run JSONL into Markdown tables and a PNG chart.
