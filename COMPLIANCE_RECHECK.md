# Compliance Recheck Against the Assignment Brief

This file is a requirement-by-requirement audit of the repository against the uploaded assignment instructions.

## 1. Submission format
**Requirement:** public GitHub repository link containing code, blog post/report, and artifacts.

**Status:** **Satisfied in this checkout.**
- Code is present.
- `REPORT.md` is present as a filled report/blog-style write-up.
- Final experiment artifacts and run outputs are present for a real 120-item run.

## 2. Required system architecture
**Requirement:** initialization, multi-round debate with `N >= 3`, adaptive stopping after convergence, judge verdict, evaluation against ground truth, and full intermediate logging.

**Status:** **Satisfied in code.**
- Initialization: `backend/src/debate.py`
- Multi-round debate with enforced minimum of 3 rounds: `backend/src/debate.py`, `backend/src/config.py`, `backend/src/types.py`
- Adaptive stopping: `backend/src/debate.py`
- Judge verdict with structured fields: `backend/src/judge_agent.py`, `backend/src/types.py`
- Evaluation against ground truth: `backend/src/app.py`, `backend/src/eval.py`
- Logging for `/run` and `/batch`: `backend/src/app.py`, `backend/src/logs.py`

## 3. Required experiments
**Requirement:** compare debate pipeline against Direct QA and Self-Consistency, with Self-Consistency using the same total LLM-call budget as debate.

**Status:** **Satisfied in this checkout.**
- Direct QA baseline: `backend/src/baselines.py`
- Self-Consistency baseline with normalized majority voting: `backend/src/baselines.py`
- Budget matching to debate call count: `backend/src/app.py`

## 4. Written report/blog structure
**Requirement:** methodology, experiments, analysis, prompt engineering, appendix with full prompts.

**Status:** **Satisfied in this checkout.**
- Structured report/blog post: `REPORT.md`
- Full prompt templates stored in `prompts/`

## 5. Code repository requirements
### README with setup and reproducibility
**Status:** **Satisfied.** `README.md`

### Modular code
**Status:** **Satisfied.** Separate debater, judge, orchestration, and evaluation modules are now present in `backend/src/`.

### Configuration not hardcoded
**Status:** **Satisfied.** `backend/src/config.py`, `backend/.env.example`

### Prompt templates as editable files with clear placeholders
**Status:** **Satisfied.** `prompts/`, `backend/src/prompts.py`

### Full debate transcripts saved as JSON
**Status:** **Satisfied.** `backend/src/logs.py`, `runs/`

### Evaluation scripts producing tables/figures
**Status:** **Satisfied.** `scripts/generate_report_artifacts.py`

### Requirements file for reproducibility
**Status:** **Satisfied.** `backend/requirements.txt`, `backend/pyproject.toml`, `web/package.json`, `web/package-lock.json`

## 6. User interface
**Requirement:** question input, round-by-round debate display, and judge verdict panel.

**Status:** **Satisfied.** `web/src/pages/Home.tsx` and supporting components.

## 7. Statistical analysis requirement
**Requirement:** statistical significance tests where applicable.

**Status:** **Satisfied in this checkout.**
- McNemar significance tests: `backend/src/eval.py`
- Bootstrap confidence intervals: `backend/src/eval.py`
- Markdown/JSON export for report use: `scripts/generate_report_artifacts.py`

## 8. Bonus opportunity
**Requirement:** optional 3+ judge jury.

**Status:** **Satisfied, including an executed 3-judge comparison.**
- Configure `JUDGE_PANEL_SIZE=3` (or higher), use API `judge_panel_size`, or pass `--judge-panel-size 3` to `scripts/run_experiment.py`.
- `scripts/rejudge_run_with_panel.py` supports a matched transcript-fixed panel evaluation over a completed single-judge run.
- Raw panel outputs are logged for later disagreement analysis.
- `scripts/compare_judge_modes.py` compares a single-judge run against a jury run and exports disagreement/deliberation artifacts for the bonus write-up.
- The repo now includes a completed 120-question single-vs-3-judge comparison with saved artifacts under `artifacts/run_20260318T193321Z_722078f5_vs_run_20260318T045614Z_0cf78544/`.

## 9. Clean-room verification
Rechecked from a fresh working tree:
- backend tests pass
- generated directories and dependency folders are no longer bundled in the submission zip

## 10. Remaining submission checks
Before submitting, verify:
1. the intended final `runs/` logs are tracked in git
2. the matching `artifacts/` outputs are tracked in git
3. the public repository contains no secrets
