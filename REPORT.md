# Assignment 2 — LLM Debate with Judge Pipeline

> Replace every `TODO` item in this file with your own writing and your real experimental outputs before submitting.

## 1. Methodology

### 1.1 Task domain and dataset
**TODO:** State which domain you chose (for example StrategyQA / ARC-Challenge / SciFact), why you chose it, and how many questions you evaluated.

- Domain:
- Dataset source:
- Final number of questions:
- Any filtering / preprocessing decisions:

### 1.2 System architecture
**TODO:** Describe the four phases of your pipeline in your own words.

Suggested coverage:
- initialization phase
- multi-round debate phase
- adaptive stopping rule
- judge phase
- evaluation phase

### 1.3 Models and hyperparameters
**TODO:** Fill in the exact model names, temperatures, token limits, and round limits used in your final run.

| Setting | Value used in final run |
|---|---|
| Debater model | TODO |
| Judge model | TODO |
| Debater temperature | TODO |
| Judge temperature | TODO |
| Baseline temperature | TODO |
| Min debate rounds | TODO |
| Max debate rounds | TODO |
| Convergence threshold | TODO |
| Judge panel size (if used) | TODO |
| Max output tokens | TODO |

### 1.4 Implementation details
**TODO:** Explain the implementation choices that matter most for reproducibility.

Suggested coverage:
- separate debater and judge modules
- prompt templating with placeholders
- structured JSON outputs
- logging format
- baseline budget matching
- optional jury mode

### 1.5 AI-tool disclosure
**TODO:** Disclose any AI tools you used for coding help, debugging help, or UI prototyping, exactly as required by the assignment.

---

## 2. Experiments

### 2.1 Experimental setup
**TODO:** Describe how you ran the experiments.

Suggested coverage:
- dataset split or sample construction
- single-model baselines
- debate configuration
- hardware / API setup if relevant
- how you ensured reproducibility

### 2.2 Main quantitative results
After running:
```bash
python scripts/generate_report_artifacts.py runs/<run_id>.jsonl --out-dir artifacts/<run_id>
```
copy the generated table here.

**TODO:** Paste `artifacts/<run_id>/metrics_table.md` below.

### 2.3 Statistical testing
**TODO:** Paste the contents of `artifacts/<run_id>/stats_summary.md` and explain what the p-values and confidence intervals mean.

### 2.4 Figure
**TODO:** Embed `artifacts/<run_id>/accuracy_comparison.png` here.

Example Markdown:
```md
![Accuracy comparison](artifacts/<run_id>/accuracy_comparison.png)
```

### 2.5 Interpretation of the quantitative results
**TODO:** Explain whether debate helped, hurt, or had mixed effects compared with Direct QA and Self-Consistency.

Suggested coverage:
- absolute accuracy differences
- significance vs. practical effect size
- whether the extra test-time compute appears useful
- whether jury mode helped if you enabled it

---

## 3. Analysis

### 3.1 Transcript case study 1
**TODO:** Insert one real transcript example from your run logs and explain what happened.

### 3.2 Transcript case study 2
**TODO:** Insert a second real transcript example and explain what happened.

### 3.3 Transcript case study 3
**TODO:** Insert a third real transcript example and explain what happened.

### 3.4 Failure cases
**TODO:** Describe at least one failure mode where debate did not help.

### 3.5 Connection to the course papers
**TODO:** Connect your observations to the lecture papers, especially debate-style oversight and test-time compute scaling.

---

## 4. Prompt Engineering

### 4.1 Prompt design goals
**TODO:** Explain your role framing for Debater A, Debater B, and the Judge.

### 4.2 Iteration history
**TODO:** Describe what changed between prompt versions and why.

Suggested coverage:
- what failed initially
- what modifications improved behavior
- tradeoffs between longer reasoning and stable structured output

### 4.3 Why the final prompts look the way they do
**TODO:** Explain why your final prompt format was the one you kept.

---

## Appendix — Full Prompt Templates

The repo already stores the final prompts in `prompts/`. Keep them verbatim and include them here for the final submission.

<details>
<summary>Debater A prompt</summary>

```text
{{copy prompts/debater_a.txt here verbatim before submission}}
```

</details>

<details>
<summary>Debater B prompt</summary>

```text
{{copy prompts/debater_b.txt here verbatim before submission}}
```

</details>

<details>
<summary>Judge prompt</summary>

```text
{{copy prompts/judge.txt here verbatim before submission}}
```

</details>

<details>
<summary>Optional jury deliberation prompt</summary>

```text
{{copy prompts/jury_deliberation.txt here verbatim if you used jury mode}}
```

</details>
