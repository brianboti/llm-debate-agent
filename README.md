# LLM Debate + Judge Pipeline

FastAPI backend + React UI for a two-debater / one-judge (or optional jury) reasoning system.

## What is included
- `backend/`: debate orchestration, separate debater and judge agent modules, baselines, evaluation, logging, and FastAPI endpoints
- `web/`: React UI for single-question runs with round-by-round debate display and judge verdict panel
- `prompts/`: editable prompt templates with explicit variable placeholders
- `scripts/run_experiment.py`: CLI for reproducible dataset runs
- `scripts/rejudge_run_with_panel.py`: re-evaluates a saved run with a 3+ judge panel over the exact same transcripts
- `scripts/generate_report_artifacts.py`: generates Markdown tables, statistical summaries, failure-pattern summaries, case-study exports, and a PNG chart from saved run logs
- `scripts/compare_judge_modes.py`: compares a single-judge run against a 3+ judge jury run and exports bonus-analysis artifacts
- `REPORT.md`: a structured report/blog post covering methodology, experiments, analysis, and prompt design
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
- jury comparison workflow for single-vs-panel analysis and disagreement diagnostics
- report artifact generation from saved logs
- functional web UI for single-question runs
- paired statistical summaries for debate-vs-baseline comparisons

## Clean-room verification
From a fresh unzip and fresh Python environment:
- backend tests pass with `./.venv/bin/pytest -q` after backend setup
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
- `OPENAI_TIMEOUT_SECONDS`
- `RUNS_DIR`
- `PROMPTS_DIR`
- `REPORT_ARTIFACTS_DIR`

## API
- `GET /health`
- `POST /run`
- `POST /batch`
- `GET /logs/{run_id}`

Both `POST /run` and `POST /batch` also accept an optional `judge_panel_size` override.

### Single-item request example
```bash
curl -X POST http://localhost:8000/run   -H 'Content-Type: application/json'   -d '{
    "item": {
      "id": "demo-1",
      "question": "Is the moon farther from Earth than the Sun?",
      "context": "",
      "ground_truth": "no"
    },
    "rounds_max": 6,
    "judge_panel_size": 3
  }'
```

### Batch request example
```bash
curl -X POST http://localhost:8000/batch   -H 'Content-Type: application/json'   -d '{
    "dataset_jsonl_path": "../data/sample_questions.jsonl",
    "limit": 3,
    "judge_panel_size": 3
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
4. If you need to enrich an older run with saved config metadata before regenerating artifacts:
   ```bash
   python scripts/backfill_run_metadata.py runs/<run_id>.jsonl --in-place
   ```
5. Review `REPORT.md` and update any findings, figures, or transcript analysis if you rerun experiments.
6. Commit the code, prompts, report, `runs/<run_id>.jsonl`, `runs/<run_id>.summary.json`, and `artifacts/<run_id>/` to your public repository.

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
- metadata including executed rounds, stop reason, judge panel size, LLM call budget, and a full experiment config snapshot with prompt hashes

## Generate report artifacts
After running a batch experiment:
```bash
python scripts/generate_report_artifacts.py runs/<run_id>.jsonl --out-dir artifacts/<run_id>
```

This writes:
- `metrics_table.md`
- `stats_summary.md`
- `failure_patterns.md`
- `failure_patterns.json`
- `accuracy_comparison.png`
- `case_studies/index.md`
- `case_studies/manifest.json`
- selected `case_studies/*.json` transcript exports
- `summary.json` including dataset path and experiment config snapshot

## Bonus Jury Workflow
Run a baseline single-judge experiment:
```bash
python scripts/run_experiment.py data/strategyqa_120.jsonl --judge-panel-size 1
```

Run a jury experiment with 3 judges:
```bash
python scripts/run_experiment.py data/strategyqa_120.jsonl --judge-panel-size 3
```

Or, if you want to isolate judge-mode effects over the exact same debate transcripts, re-evaluate a completed single-judge run with a 3-judge panel:
```bash
python scripts/rejudge_run_with_panel.py runs/<single_run_id>.jsonl --judge-panel-size 3
```

Compare the two runs:
```bash
python scripts/compare_judge_modes.py \
  runs/<single_run_id>.jsonl \
  runs/<panel_run_id>.jsonl \
  --out-dir artifacts/<panel_run_id>_vs_<single_run_id>
```

This writes:
- `jury_vs_single_accuracy.md`
- `jury_vs_single_stats.md`
- `jury_panel_behavior.md`
- `jury_difficulty_correlation.md`
- `deliberation_changed_cases.json`
- `jury_compare_summary.json`
- `judge_mode_accuracy.png`

## Quality checks
From the repo root:
```bash
cd backend && ./.venv/bin/pytest -q
```

Recommended frontend check in a networked environment:
```bash
cd web && npm ci && npm run build
```
