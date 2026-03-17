# Compliance Recheck Against the Assignment Brief

This file is a requirement-by-requirement audit of the repository against the uploaded assignment instructions.

## 1. Submission format
**Requirement:** public GitHub repository link containing code, blog post/report, and artifacts.

**Status:** **Partially satisfied by repository structure.**
- Code is present.
- `REPORT.md` is present as a student-fill submission scaffold.
- Final experiment artifacts still need to be generated from a real 100+ item run.

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

**Status:** **Satisfied in code; final large-scale experiment run still pending.**
- Direct QA baseline: `backend/src/baselines.py`
- Self-Consistency baseline with normalized majority voting: `backend/src/baselines.py`
- Budget matching to debate call count: `backend/src/app.py`

## 4. Written report/blog structure
**Requirement:** methodology, experiments, analysis, prompt engineering, appendix with full prompts.

**Status:** **Scaffold present; final student-authored prose still required.**
- Structured report scaffold: `REPORT.md`
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

**Status:** **Satisfied in tooling, pending final experiment execution.**
- McNemar significance tests: `backend/src/eval.py`
- Bootstrap confidence intervals: `backend/src/eval.py`
- Markdown export for report use: `scripts/generate_report_artifacts.py`

## 8. Bonus opportunity
**Requirement:** optional 3+ judge jury.

**Status:** **Implemented optionally.**
- Configure `JUDGE_PANEL_SIZE=3` (or higher) to enable a multi-judge panel with a deliberation pass.
- Raw panel outputs are logged for later disagreement analysis.

## 9. Clean-room verification
Rechecked from a fresh working tree:
- backend tests pass
- generated directories and dependency folders are no longer bundled in the submission zip

## 10. Remaining submission blockers
Before submitting, the student still needs to:
1. run the final 100+ question experiment set
2. commit resulting `runs/` logs and `artifacts/` outputs
3. write the final report/blog in their own words
4. add final figures/tables and transcript analysis to `REPORT.md`
5. verify the public repository contains no secrets
