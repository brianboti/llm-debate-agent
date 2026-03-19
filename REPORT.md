# Assignment 2 Report: LLM Debate + Judge Pipeline

## Overview

This project implements a complete multi-agent debate pipeline for commonsense question answering. The system contains two debaters and one judge. Debater A argues for one answer, Debater B argues for the competing answer, and the judge reads the full transcript and selects the final verdict. I evaluated the system on a 120-question StrategyQA subset and compared it against two required baselines: Direct QA and Self-Consistency.

My main research question was whether structured adversarial debate can improve answer quality over a single direct response. In the final single-judge run I report here, the answer was still **no** overall: the debate system generated useful transcripts and did recover a few errors, but it did not beat the simpler baselines on this benchmark.

---

## 1. Methodology

### 1.1 Task domain and dataset

I selected the **Commonsense QA** setting and used **StrategyQA**, which is a good fit for a debate-style architecture because many questions require multi-hop world knowledge and disambiguation rather than simple retrieval. To make the evaluation reproducible, I created a fixed 120-question subset using a deterministic random seed and stored both the dataset file and metadata in the repository:

- `data/strategyqa_120.jsonl`
- `data/strategyqa_120_metadata.json`
- `data/strategyqa_120_preview.md`

Each example follows this schema:

```json
{"id":"strategyqa-0001","question":"...","context":"","ground_truth":"yes"}
```

I kept the `context` field empty in this experiment so that the system would be evaluated as a pure reasoning pipeline rather than a retrieval-augmented system.

### 1.2 System architecture

The pipeline follows the required four-phase structure:

1. **Initialization**
   - The same question is shown independently to Debater A and Debater B.
   - Each debater produces an initial answer and rationale.
   - If both debaters initially agree, the system records consensus and skips directly to judgment.

2. **Multi-round debate**
   - If the initial answers disagree, the system runs a multi-round exchange.
   - Debater A argues first, then Debater B responds.
   - Both agents receive the transcript from previous rounds.
   - The system enforces the assignment requirement that debate runs have at least three rounds available, while also allowing early stopping when both agents converge for two consecutive rounds.

3. **Judgment**
   - The judge receives the original question plus the full transcript.
   - The judge returns:
     - a final verdict,
     - a 1–5 confidence score,
     - strongest and weakest points for both sides,
     - a concise step-by-step comparative analysis explaining why one side was more persuasive.

4. **Evaluation**
   - The final verdict is compared against ground truth.
   - The full run log stores initial positions, round-by-round debate, judge output, baseline outputs, and correctness fields.

### 1.3 Implementation details

The repository is organized into separate modules for the main components:

- `backend/src/debater_agent.py`
- `backend/src/judge_agent.py`
- `backend/src/debate.py`
- `backend/src/baselines.py`
- `backend/src/eval.py`
- `backend/src/app.py`

This separation made it easier to test each stage independently and aligns with the assignment requirement for modular code.

The backend is implemented with FastAPI and the frontend is a lightweight Vite/React interface that lets a user enter a question, inspect debate rounds, and view the final verdict and baselines.

### 1.4 Configuration and reproducibility

A major design goal was to keep all important hyperparameters in configuration rather than hardcoding them in the pipeline. The repository exposes model names, temperatures, token budgets, round limits, and judge panel size through configuration and environment variables.

In this setup, the OpenAI Responses API exposes model aliases rather than a separate public date-pinned snapshot string, so I report the exact model aliases used at run time and save the full experiment configuration with the run summary.

For the final run reported here, the runtime configuration was:

- debater model: `gpt-4o-mini`
- judge model: `gpt-4o-mini`
- debater temperature: `0.7`
- judge temperature: `0.2`
- baseline temperature: `0.2`
- max output tokens: `600`

For the final single-judge experiment, the key protocol settings were:

- debate domain: StrategyQA yes/no commonsense QA
- dataset size: 120 questions
- debate round window: minimum 3, maximum 6
- adaptive stopping: enabled
- judge panel size: 1
- baseline set: Direct QA and Self-Consistency
- logging: full JSONL transcripts for every item

### 1.5 Baselines

I compared the debate system against two baselines required by the assignment:

- **Direct QA**: a single model answers the question directly.
- **Self-Consistency**: multiple independent samples are generated and the majority vote is used as the answer.

I also fixed a correctness issue during development: self-consistency voting now normalizes answers before majority voting, so formatting variants such as `Yes`, `yes`, or `yes.` do not split votes incorrectly.

### 1.6 Development process and tools used

I used **Codex** as a coding assistant during implementation. I mainly used it for debugging, refactoring, UI iteration, test scaffolding, and some late-stage documentation cleanup. I did not use it to choose the dataset or to decide what conclusions to report. I checked the code and results myself by running the backend tests, building the frontend, and reproducing the saved experiments from the committed scripts and logs.

---

## 2. Experiments

### 2.1 Experimental setup

The main single-judge experiment was run on the reproducible 120-question StrategyQA subset stored in `data/strategyqa_120.jsonl`. The evaluation script executed the debate pipeline on every question, saved a JSONL transcript file for the run, and then generated aggregate metrics and report artifacts.

Final run ID:

`run_20260318T045614Z_0cf78544`

Final run timestamp:

`2026-03-18 04:56:14 UTC`

Main run artifacts:

- `runs/run_20260318T045614Z_0cf78544.jsonl`
- `runs/run_20260318T045614Z_0cf78544.summary.json`
- `artifacts/run_20260318T045614Z_0cf78544/metrics_table.md`
- `artifacts/run_20260318T045614Z_0cf78544/stats_summary.md`
- `artifacts/run_20260318T045614Z_0cf78544/failure_patterns.md`
- `artifacts/run_20260318T045614Z_0cf78544/case_studies/index.md`
- `artifacts/run_20260318T045614Z_0cf78544/accuracy_comparison.png`

### 2.2 Quantitative results

The final accuracy table is reproduced below.

| Method | Accuracy | Correct / Total |
|---|---:|---:|
| Debate + Judge | 0.742 | 89 / 120 |
| Direct QA | 0.775 | 93 / 120 |
| Self-Consistency | 0.775 | 93 / 120 |

The main result is that **Direct QA and Self-Consistency tied for best**, and **Debate + Judge** finished slightly behind them.

### 2.3 Statistical significance

I used McNemar’s test and bootstrap confidence intervals to compare debate against the baselines.

- Number of questions: **120**
- McNemar p-value (Debate vs Direct QA): **0.3877**
- McNemar p-value (Debate vs Self-Consistency): **0.3877**
- Bootstrap accuracy difference, Debate − Direct QA: **-0.034** (95% CI: **[-0.092, 0.017]**)
- Bootstrap accuracy difference, Debate − Self-Consistency: **-0.034** (95% CI: **[-0.092, 0.025]**)

On this run, debate was worse in raw accuracy, but the gap was **not statistically significant** against either baseline. I still would not claim that debate helped here, because it did not win on the headline metric, but the March 18 run is a closer negative result than the earlier pilot-style runs suggested.

### 2.4 Figure

![Accuracy comparison](artifacts/run_20260318T045614Z_0cf78544/accuracy_comparison.png)

### 2.5 Interpretation of the quantitative results

This experiment still did not support the hypothesis that adversarial debate improves answer accuracy for this benchmark under my current setup, but the result is a little more nuanced than a simple “debate fails” story:

1. **The simpler baselines were still better overall.**  
   Direct QA and Self-Consistency both finished at 93/120, while Debate + Judge finished at 89/120.

2. **The gap was smaller than I expected.**  
   Debate did not beat the baselines, but it also was not statistically separated from them in this run. That matters because it suggests the pipeline is not obviously hopeless; it is just not clearly better in its current form.

3. **Debate sometimes helped, just not often enough.**  
   In this run, debate beat both baselines on two items, which means the architecture occasionally recovered something useful that the simpler methods missed. The problem is that those wins were outweighed by other cases where the extra interaction added noise or let the judge favor a polished but wrong line of reasoning.

For me, that is still a useful result. The point of the assignment was to test whether debate helps, not to assume that it should.

---

## 3. Analysis

In this section I analyze representative transcript patterns from the final single-judge run.

### 3.1 Case study A: all methods fail because all three systems fall into the same framing mistake

**Example:** `strategyqa-0014`  
**Question:** *Is electricity necessary to balance an account in Microsoft Excel?*  
**Ground truth:** `yes`  
**Debate:** `no`  
**Direct QA:** `no`  
**Self-Consistency:** `no`  
**Debate rounds:** `0`  
**Stop reason:** `initial_consensus`

This is a good example of a failure that debate never had a chance to fix. All three methods gave the same wrong answer immediately. The likely issue is not reasoning depth but framing: the models seem to interpret “balance an account” as an accounting task that can be done in the abstract or on paper, while the benchmark label takes the wording literally and treats **using Microsoft Excel** as requiring electricity.

That distinction matters because the debate architecture only helps if one side notices the framing issue and pushes back. Here that never happened. The system took early agreement as a sign that the item was easy, when in fact it was a shared misread.

**Takeaway:** if both debaters start from the same bad interpretation, the debate stage cannot rescue the answer.

### 3.2 Case study B: long debate does not guarantee error correction

**Example:** `strategyqa-0003`  
**Question:** *Is capturing giant squid in natural habitat impossible with no gear?*  
**Ground truth:** `yes`  
**Debate:** `no`  
**Direct QA:** `yes`  
**Self-Consistency:** `yes`  
**Debate rounds:** `6`  
**Stop reason:** `max_rounds_reached`

This case illustrates the opposite failure mode. Unlike the previous example, the system did not collapse into early consensus. Instead, it used the full debate budget and still ended with the wrong answer. Both baselines were correct, but debate was not.

That pattern suggests that extra interaction did not improve reasoning here. Instead, the debate appears to have amplified disagreement without producing a corrective signal strong enough for the judge to select the correct side. Reaching the maximum number of rounds is especially important: the system spent its full test-time compute budget and still lost to cheaper baselines.

This is one of the clearest examples in the run of “more reasoning steps” not leading to “better reasoning.” It connects directly to a broader lesson from inference-time compute work: compute only helps when the additional computation is actually productive. If the extra rounds mostly recycle unsupported assumptions, then more rounds simply make the transcript longer, not better.

**Takeaway:** debate can fail even when given maximum interaction budget, especially when repeated turns do not introduce new evidence or better disambiguation.

### 3.3 Case study C: multiple independent starts can help even without a full debate

**Example:** `strategyqa-0050`  
**Question:** *Could Eddie Hall hypothetically deadlift the world's largest cheeseburger?*  
**Ground truth:** `no`  
**Debate:** `no`  
**Direct QA:** `yes`  
**Self-Consistency:** `no`  
**Debate rounds:** `0`  
**Stop reason:** `initial_consensus`

This was one of the cleaner “success” cases in the run. The debate system and self-consistency were correct, while direct QA was wrong. What I find interesting here is that the debate pipeline never needed a back-and-forth exchange. Both debaters independently started with the correct answer, so the system stopped early.

My reading is that the gain here came from diversity, not from rebuttal. The direct answer seems to have overfocused on Eddie Hall’s strength and underweighted the scale implied by “the world’s largest cheeseburger.” Once the system got two independent initial passes, the answer corrected itself before debate rounds even started.

The fact that self-consistency also got this one right points in the same direction. In other words, some of the value in a debate pipeline may come from getting multiple initial attempts, not necessarily from the multi-round adversarial exchange.

**Takeaway:** some of the benefit of debate may actually come from diversified initial reasoning before the debate even begins.

### 3.4 Aggregate failure patterns

The final run produced several recurring patterns:

- `debate_beats_both`: **2**
- `debate_loses_to_both`: **8**
- `debate_and_sc_beat_direct`: **2**
- `all_fail`: **23**
- `max_rounds_reached`: **18**

These counts are generated directly from the saved run log and exported to `artifacts/run_20260318T045614Z_0cf78544/failure_patterns.md`.

These counts help explain the final leaderboard.

First, debate did beat both baselines on two items, so I do not think the architecture was useless. There were cases where the extra structure genuinely helped.

Second, the fact that debate still lost to both baselines on eight items shows that those wins were not frequent enough to change the overall ranking.

Third, the 23 “all fail” cases show that some StrategyQA items remain difficult or label-sensitive no matter which inference strategy I used.

Fourth, the 18 max-round cases show that long debates were fairly common. In practice, those longer transcripts often reflected persistent disagreement rather than real error correction.

### 3.5 Connection to theory

Theoretical work on AI debate assumes that adversarial interaction can expose hidden flaws in reasoning and make truth easier for a judge to recover. My implementation only partially achieved that goal. In some cases, the system did create useful disagreement, and in a couple of examples it even beat both baselines. But the final run still points to three practical limitations:

1. if both agents begin from the same bad framing, there is no debate benefit;
2. if the debate repeats weak claims instead of generating new evidence, longer transcripts do not help;
3. if the judge prefers rhetorical coherence over factual reliability, the final verdict may favor the more persuasive wrong answer.

So while the project validates the *mechanics* of a debate pipeline, it also shows that debate quality depends heavily on prompt design, transcript diversity, and judge robustness.

---

## 4. Prompt Engineering

### 4.1 Initial prompt goals

My prompt design had four goals:

1. make the debaters adopt distinct roles,
2. force structured yes/no outputs for easy evaluation,
3. give the judge a standardized schema for verdicts,
4. reduce formatting noise so the pipeline is reliable under batch execution.

The earliest working version allowed free-form answers, which made evaluation fragile. For example, a model might answer with `Yes, because...`, `Probably yes`, or even a debater-side label such as `Debater A`. Those outputs were semantically understandable to a human reader but noisy for automated evaluation.

### 4.2 Most important prompt iteration

The most important improvement was tightening the output schema so that all answer fields had to be exactly `yes` or `no`.

That change fixed two issues at once:

- it made comparison against ground truth robust,
- it prevented the judge from returning a side label instead of a verdict label.

I also added stronger instructions that the explanation must go into `rationale` or `analysis`, not into the `answer` field itself, and that the reasoning should be presented as concise step-by-step argumentation rather than a free-form paragraph.

### 4.3 Real-world commonsense framing

Another important iteration was explicitly telling both debaters and the judge to use **ordinary real-world commonsense unless the question explicitly asks about fictional or hypothetical rules**.

This change was motivated by failures where the system drifted into imaginative reasoning, narrative elaboration, or speculative worldbuilding. For commonsense QA, that behavior is often harmful because it encourages the model to invent a plausible-sounding world instead of resolving the benchmark’s intended interpretation.

### 4.4 What worked

The final prompts did several things well:

- they made the pipeline stable under batch evaluation,
- they produced parseable outputs,
- they pushed both the debaters and judge toward concise step-by-step reasoning instead of one-line assertions,
- they gave the judge richer structure than a bare answer,
- they supported useful logging for post hoc transcript analysis.

### 4.5 What still did not work well

The final results also show that the prompt design still left room for improvement.

The main remaining weaknesses are:

- debaters often repeat the same claim in multiple rounds instead of introducing new evidence,
- the judge can still be swayed by coherence rather than truth,
- early consensus can lock in a shared bad framing,
- longer debates do not necessarily increase epistemic quality.

If I continued this project, I would test three prompt changes first:

1. require each new round to introduce either a new factual premise or an explicit rebuttal to the opponent’s strongest prior point;
2. make the judge score factual grounding and contradiction handling separately from persuasiveness;
3. require each debater to explicitly consider one alternative interpretation of the question before committing to an answer.

### 4.6 Bonus extension: judge panel workflow

I ran an additional bonus experiment on `2026-03-18` to compare a single judge against a 3-judge panel. To keep the comparison clean, I used the completed single-judge run as the base condition and re-evaluated the exact same 120 saved debate transcripts with a 3-judge panel plus deliberation. This isolates the effect of judge mode instead of mixing it with fresh debater randomness.

Bonus run IDs:

- single-judge source run: `run_20260318T045614Z_0cf78544`
- 3-judge panel re-evaluation: `run_20260318T193321Z_722078f5`

The panel re-evaluation and comparison workflow are reproducible with:

```bash
python scripts/rejudge_run_with_panel.py \
  runs/<single_run_id>.jsonl \
  --judge-panel-size 3

python scripts/compare_judge_modes.py \
  runs/<single_run_id>.jsonl \
  runs/<panel_run_id>.jsonl \
  --out-dir artifacts/<panel_run_id>_vs_<single_run_id>
```

The comparison artifacts are saved under:

- `artifacts/run_20260318T193321Z_722078f5_vs_run_20260318T045614Z_0cf78544/`

The key results were:

| Judge Mode | Accuracy | Correct / Total |
|---|---:|---:|
| Single Judge | 0.742 | 89 / 120 |
| Panel Majority | 0.750 | 90 / 120 |
| Deliberated Jury | 0.742 | 89 / 120 |

Panel behavior was also highly concentrated:

- unanimous panel items: **119 / 120**
- split panel items: **1 / 120**
- deliberation changed the majority answer on **1** item
- deliberation changed the outcome from correct to wrong on **1** item
- McNemar p-value (Deliberated Jury vs Single Judge): **1.0000**
- Bootstrap accuracy difference, Deliberated Jury − Single Judge: **0.000** with 95% CI **[0.000, 0.000]**

The most important takeaway is that **majority voting helped slightly, but deliberation erased the gain**. The panel majority was correct on one additional item, but the deliberation step overrode that correct majority on `strategyqa-0003` and returned the final jury accuracy to exact parity with the single judge.

This bonus result is still informative. It suggests that the current judge prompt already produces very low variance across judges, which limits the upside of a panel. Disagreement appeared on only one question, and even there the deliberation step moved the answer in the wrong direction. In other words, the bottleneck in this setup is probably not the number of judges alone. The more promising next improvement would be to redesign deliberation so it respects a correct majority more reliably, or to induce more genuinely independent judge reasoning before aggregation.

---

## 5. Conclusion

This project successfully implemented a complete LLM Debate + Judge pipeline, including a working backend, a functional web UI, reproducible logging, evaluation scripts, and a 120-question benchmark run.

The final quantitative result was still negative for the central hypothesis: under my current prompt design and configuration, **debate did not outperform the simpler baselines**. In the main single-judge run, Debate + Judge reached `89/120`, while Direct QA and Self-Consistency both reached `93/120`. That said, the gap was not statistically significant on this run, and debate did beat both baselines on a small number of items.

I do not see that as a failed project. The system worked, the experiments were reproducible, and the transcript analysis made the tradeoffs visible. My main takeaway is that adversarial structure by itself is not enough. For debate to beat simpler inference-time methods, the prompts and the judging procedure have to reward actual error correction, not just fluent argumentation.

---

## Appendix A: Reproduction commands

### Backend tests

```bash
cd backend
./.venv/bin/pytest -q
```

### Run a pilot experiment

```bash
cd ..
python scripts/run_experiment.py data/strategyqa_120.jsonl --limit 10
```

### Run the final single-judge experiment

```bash
python scripts/run_experiment.py data/strategyqa_120.jsonl --judge-panel-size 1
```

### Generate single-run artifacts

```bash
python scripts/generate_report_artifacts.py runs/<single_run_id>.jsonl --out-dir artifacts/<single_run_id>
```

### Re-evaluate saved transcripts with a 3-judge panel

```bash
python scripts/rejudge_run_with_panel.py runs/<single_run_id>.jsonl --judge-panel-size 3
```

### Generate panel-run artifacts

```bash
python scripts/generate_report_artifacts.py runs/<panel_run_id>.jsonl --out-dir artifacts/<panel_run_id>
```

### Compare single judge vs jury

```bash
python scripts/compare_judge_modes.py \
  runs/<single_run_id>.jsonl \
  runs/<panel_run_id>.jsonl \
  --out-dir artifacts/<panel_run_id>_vs_<single_run_id>
```

### Backfill metadata into an older run log if needed

```bash
python scripts/backfill_run_metadata.py runs/<older_run_id>.jsonl --in-place
```

---

## Appendix B: Final Prompt Templates

### Debater A

```text
You are {{ROLE_NAME}} in a structured adversarial debate.

Task type: {{TURN_KIND}}
Round index: {{ROUND_INDEX}}
Opponent: {{OPPONENT_NAME}}

Question:
{{QUESTION}}

Context:
{{CONTEXT}}

Transcript so far:
{{TRANSCRIPT}}

Instructions:
- Defend the strongest answer you can justify.
- Use ordinary real-world commonsense unless the question explicitly asks about fictional or hypothetical rules.
- Use the context when it is available.
- When the transcript exposes a flaw in your earlier reasoning, correct it instead of repeating it.
- Keep the rationale concise but substantive.
- The `answer` field must be exactly `yes` or `no`.
- Put all explanation in `rationale`, not in `answer`.
- Use citations only for short evidence snippets or identifiers from the provided context.
- Return ONLY valid JSON matching this schema.

JSON schema:
{{JSON_SCHEMA}}
```

### Debater B

```text
You are {{ROLE_NAME}} in a structured adversarial debate.

Task type: {{TURN_KIND}}
Round index: {{ROUND_INDEX}}
Opponent: {{OPPONENT_NAME}}

Question:
{{QUESTION}}

Context:
{{CONTEXT}}

Transcript so far:
{{TRANSCRIPT}}

Instructions:
- Challenge weak assumptions, unsupported claims, and contradictions from {{OPPONENT_NAME}}.
- Present the strongest competing answer you can justify.
- Use ordinary real-world commonsense unless the question explicitly asks about fictional or hypothetical rules.
- Use the context when it is available.
- If the best answer changes after seeing the transcript, update your answer explicitly.
- Keep the rationale concise but substantive.
- The `answer` field must be exactly `yes` or `no`.
- Put all explanation in `rationale`, not in `answer`.
- Use citations only for short evidence snippets or identifiers from the provided context.
- Return ONLY valid JSON matching this schema.

JSON schema:
{{JSON_SCHEMA}}
```

### Judge

```text
You are Judge {{JUDGE_INDEX}} in a debate-evaluation pipeline.

Question:
{{QUESTION}}

Context:
{{CONTEXT}}

Full transcript:
{{TRANSCRIPT}}

Instructions:
- Compare the quality of the arguments, not just surface fluency.
- Use ordinary real-world commonsense unless the question explicitly asks about fictional or hypothetical rules.
- Reward claims that are supported by the provided context.
- In `analysis`, explain which side was more persuasive and why.
- In the strongest/weakest fields, identify the most important strength and weakness for each debater.
- `verdict_answer` must be exactly `yes` or `no`, never a debater name.
- Return ONLY valid JSON matching this schema.

JSON schema:
{{JSON_SCHEMA}}
```

### Optional jury deliberation prompt

```text
You are the deliberation chair for a multi-judge jury.

Question:
{{QUESTION}}

Context:
{{CONTEXT}}

Full transcript:
{{TRANSCRIPT}}

Panel verdicts:
{{PANEL_VERDICTS}}

Majority answer before deliberation:
{{MAJORITY_ANSWER}}

Instructions:
- Reconcile disagreements across the panel.
- Prefer the answer supported by the strongest evidence and reasoning in the debate.
- Use ordinary real-world commonsense unless the question explicitly asks about fictional or hypothetical rules.
- Use the panel verdicts as advisory inputs, not as hard constraints.
- `verdict_answer` must be exactly `yes` or `no`, never a debater name.
- Return ONLY valid JSON matching this schema.

JSON schema:
{{JSON_SCHEMA}}
```
