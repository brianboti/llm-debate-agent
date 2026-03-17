# LLM Debate + Judge Pipeline

FastAPI backend + React UI for a two-debater / one-judge (or optional jury) reasoning system.

## What is included
- `backend/`: debate orchestration, separate debater and judge agent modules, baselines, evaluation, logging, and FastAPI endpoints
- `web/`: React UI for single-question runs with round-by-round debate display and judge verdict panel
- `prompts/`: editable prompt templates with explicit variable placeholders
- `scripts/run_experiment.py`: CLI for reproducible dataset runs
- `scripts/generate_report_artifacts.py`: generates Markdown tables, statistical summaries, and a PNG chart from saved run logs
- `REPORT.md`: a submission scaffold you can fill with your own experimental findings and transcript analysis
- `COMPLIANCE_RECHECK.md`: a requirement-by-requirement audit against the assignment brief

## Assignment alignment
This repo is designed to satisfy the code-side deliverables from the assignment:
- 4-phase debate pipeline with adaptive stopping
- separate modules for debaters, judge, orchestration, and evaluation
- configurable hyperparameters loaded from configuration settings
- editable prompts stored as files with clear placeholders such as `{{QUESTION}}` and `{{TRANSCRIPT}}`
- JSON logging for every `/run` and `/batch` execution
- Direct QA and Self-Consistency baselines
- optional multi-judge jury mode via `JUDGE_PANEL_SIZE`
- report artifact generation from saved logs
- functional web UI for single-question runs
- paired statistical summaries for debate-vs-baseline comparisons

## Clean-room verification
From a fresh unzip and fresh Python environment:
- backend tests pass with `pytest -q`
- the repo no longer bundles `node_modules/`, `.pytest_cache/`, or build outputs

## Backend setup
```bash
cd backend
cp .env.example .env
# add your real OPENAI_API_KEY to backend/.env
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
uvicorn src.app:app --reload --port 8000
```

## Web UI setup
```bash
cd web
cp .env.example .env
npm ci
npm run dev
```

Open the UI at `http://localhost:5173`.

## Environment variables
`backend/.env.example` contains the main runtime knobs:
- `OPENAI_MODEL_DEBATER`
- `OPENAI_MODEL_JUDGE`
- `DEBATE_MIN_ROUNDS`
- `DEBATE_MAX_ROUNDS`
- `DEBATE_CONVERGENCE_ROUNDS`
- `JUDGE_PANEL_SIZE`
- `TEMP_DEBATER`
- `TEMP_JUDGE`
- `TEMP_BASELINE`
- `MAX_OUTPUT_TOKENS`
- `RUNS_DIR`
- `PROMPTS_DIR`
- `REPORT_ARTIFACTS_DIR`

## API
- `GET /health`
- `POST /run`
- `POST /batch`
- `GET /logs/{run_id}`

### Single-item request example
```bash
curl -X POST http://localhost:8000/run   -H 'Content-Type: application/json'   -d '{
    "item": {
      "id": "demo-1",
      "question": "Is the moon farther from Earth than the Sun?",
      "context": "",
      "ground_truth": "no"
    },
    "rounds_max": 6
  }'
```

### Batch request example
```bash
curl -X POST http://localhost:8000/batch   -H 'Content-Type: application/json'   -d '{
    "dataset_jsonl_path": "../data/sample_questions.jsonl",
    "limit": 3
  }'
```

## Reproducible experiment workflow
1. Choose a task domain and create a `data/<dataset_name>.jsonl` file with 100+ items.
2. Run the batch experiment:
   ```bash
   python scripts/run_experiment.py data/<dataset_name>.jsonl
   ```
3. Generate report artifacts:
   ```bash
   python scripts/generate_report_artifacts.py runs/<run_id>.jsonl --out-dir artifacts/<run_id>
   ```
4. Open `REPORT.md` and replace the TODO markers with your own findings, figures, and transcript analysis.
5. Commit the code, prompts, report, `runs/<run_id>.jsonl`, `runs/<run_id>.summary.json`, and `artifacts/<run_id>/` to your public repository.

## Dataset format
Each line in a dataset `.jsonl` file should look like this:
```json
{"id":"1","question":"...","context":"...","ground_truth":"A"}
```

A tiny example dataset is included at `data/sample_questions.jsonl` for smoke testing only.

## Logging and reproducibility
Every `/run` and `/batch` call writes:
- `runs/<run_id>.jsonl`
- `runs/<run_id>.summary.json`

Each JSONL row stores:
- the original item
- initial debater positions
- every debate round
- the final judge verdict and raw judge panel outputs
- baseline outputs
- correctness flags
- metadata including executed rounds, stop reason, judge panel size, and LLM call budget

## Generate report artifacts
After running a batch experiment:
```bash
python scripts/generate_report_artifacts.py runs/<run_id>.jsonl --out-dir artifacts/<run_id>
```

This writes:
- `metrics_table.md`
- `stats_summary.md`
- `accuracy_comparison.png`
- `summary.json`

## Quality checks
From the repo root:
```bash
cd backend && pytest -q
```

Recommended frontend check in a networked environment:
```bash
cd web && npm ci && npm run build
```

## Important submission note
The assignment requires a real 100+ question experiment and a student-authored blog post. This repository is now much closer to rubric-complete on the implementation side, but you still need to:
- run the final experiment set with your real API key
- commit the resulting run logs and artifact files
- write the final report/blog in your own words using the scaffold in `REPORT.md`
- disclose any AI coding tools you used in the methodology section

## Security
Do not commit real secrets. Keep API keys only in local `.env` files that are ignored by Git.
