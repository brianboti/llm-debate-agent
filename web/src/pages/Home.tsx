import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Copy, Play, RotateCcw } from "lucide-react";
import { apiPost } from "@/api";
import { Card, CardBody, CardHeader, CardSubtitle, CardTitle } from "@/components/Card";
import Pill from "@/components/Pill";
import Shell from "@/components/Shell";

type Item = {
  id: string;
  question: string;
  context?: string;
  ground_truth: string;
};

type ModelAnswer = { answer: string; rationale: string; citations: string[] };
type DebateRound = { round_index: number; debater_a: ModelAnswer; debater_b: ModelAnswer };
type JudgeVerdict = {
  verdict_answer: string;
  confidence_1_to_5: number;
  analysis: string;
  debater_a_strongest: string;
  debater_a_weakest: string;
  debater_b_strongest: string;
  debater_b_weakest: string;
  reasoning: string;
};
type Baselines = {
  direct: ModelAnswer;
  self_consistency_samples: ModelAnswer[];
  self_consistency_vote: string;
};

type ItemResult = {
  item: Item;
  consensus: boolean;
  initial_a: ModelAnswer;
  initial_b: ModelAnswer;
  debate_rounds: DebateRound[];
  judge: JudgeVerdict;
  judge_panel?: JudgeVerdict[];
  baselines: Baselines;
  correct_debate: boolean;
  correct_direct: boolean;
  correct_sc: boolean;
  meta: Record<string, unknown>;
};

type RunResponse = { run_id: string; result: ItemResult };

const starter: Item = {
  id: "demo-1",
  question: "Is the moon farther from Earth than the Sun?",
  context: "",
  ground_truth: "no",
};

function TextArea({
  label,
  value,
  onChange,
  rows = 4,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-xs text-muted">{label}</span>
      <textarea
        className="w-full rounded-xl ring-1 ring-[color:var(--border)] bg-white/60 px-3 py-2 text-sm text-primary outline-none focus:border-white/20"
        rows={rows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-xs text-muted">{label}</span>
      <input
        className="h-11 w-full rounded-xl ring-1 ring-[color:var(--border)] bg-white/60 px-3 text-sm text-primary outline-none focus:border-white/20"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function AnswerPanel({ title, answer, tone = "info" }: { title: string; answer: ModelAnswer; tone?: "neutral" | "info" }) {
  return (
    <div className="rounded-xl ring-1 ring-[color:var(--border)] bg-white/60 p-4">
      <div className="mb-2 flex items-center gap-2">
        <Pill tone={tone}>{title}</Pill>
        <Pill tone="info">{answer.answer}</Pill>
      </div>
      <p className="text-sm text-primary whitespace-pre-wrap">{answer.rationale}</p>
      {answer.citations.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-muted">Citations ({answer.citations.length})</summary>
          <ul className="mt-2 grid gap-1 pl-4 text-sm text-primary">
            {answer.citations.map((citation, index) => (
              <li key={`${answer.answer}-${index}`}>{citation}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default function Home() {
  const [item, setItem] = useState<Item>(starter);
  const [roundsMax, setRoundsMax] = useState("6");
  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [result, setResult] = useState<ItemResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const roundsMaxNumber = useMemo(() => {
    const value = Number(roundsMax);
    return Number.isFinite(value) && value >= 3 ? value : undefined;
  }, [roundsMax]);

  async function onRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    setRunId(null);

    try {
      const payload = { item: { ...item, context: item.context ?? "" }, rounds_max: roundsMaxNumber };
      const response = await apiPost<RunResponse>("/run", payload, { timeoutMs: 180_000 });
      setRunId(response.run_id);
      setResult(response.result);
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setItem(starter);
    setRoundsMax("6");
    setRunId(null);
    setResult(null);
    setError(null);
  }

  async function copyJson() {
    if (!result) return;
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
  }

  return (
    <Shell>
      <div className="grid gap-6 lg:grid-cols-12">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="lg:col-span-5"
        >
          <Card>
            <CardHeader>
              <CardTitle>Run a single item</CardTitle>
              <CardSubtitle>Input a question, optional context, and the ground-truth label.</CardSubtitle>
            </CardHeader>
            <CardBody>
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-3">
                  <Input label="Item ID" value={item.id} onChange={(value) => setItem({ ...item, id: value })} />
                  <Input
                    label="Ground truth"
                    value={item.ground_truth}
                    onChange={(value) => setItem({ ...item, ground_truth: value })}
                    placeholder="A / yes / no"
                  />
                </div>

                <TextArea label="Question" value={item.question} onChange={(value) => setItem({ ...item, question: value })} rows={3} />
                <TextArea
                  label="Context (optional)"
                  value={item.context ?? ""}
                  onChange={(value) => setItem({ ...item, context: value })}
                  rows={5}
                  placeholder="Paste evidence or supporting context here..."
                />

                <div className="grid grid-cols-2 gap-3">
                  <Input label="Max rounds" value={roundsMax} onChange={setRoundsMax} placeholder="e.g. 6 (min 3)" />
                  <div className="grid gap-2">
                    <span className="text-xs text-muted">Actions</span>
                    <div className="flex gap-2">
                      <button
                        onClick={onRun}
                        disabled={loading}
                        className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-500/90 px-4 py-2 text-sm font-medium text-white shadow-[0_14px_40px_rgba(79,70,229,0.25)] hover:brightness-110 disabled:opacity-60"
                      >
                        <Play className="h-4 w-4" />
                        {loading ? "Running..." : "Run"}
                      </button>
                      <button
                        onClick={reset}
                        className="inline-flex items-center justify-center rounded-xl ring-1 ring-[color:var(--border)] bg-white/80 px-3 py-2 text-sm text-primary hover:bg-white"
                        title="Reset"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {runId && (
                  <div className="flex flex-wrap items-center gap-2">
                    <Pill tone="info">Run ID: {runId}</Pill>
                    {result && (
                      <button
                        onClick={copyJson}
                        className="inline-flex items-center gap-2 rounded-full ring-1 ring-[color:var(--border)] bg-white/80 px-3 py-1 text-xs text-primary hover:bg-white"
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy JSON
                      </button>
                    )}
                  </div>
                )}

                {error && (
                  <div className="rounded-xl border border-[rgba(239,68,68,0.25)] bg-[rgba(239,68,68,0.08)] p-3 text-sm text-[color:var(--bad)]">
                    {error}
                  </div>
                )}
              </div>
            </CardBody>
          </Card>
        </motion.div>

        <div className="grid gap-6 lg:col-span-7">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.05 }}>
            <Card>
              <CardHeader>
                <CardTitle>Verdict</CardTitle>
                <CardSubtitle>Judge decision, confidence, and structured comparison.</CardSubtitle>
              </CardHeader>
              <CardBody>
                {!result ? (
                  <div className="text-sm text-muted">Run an item to see the verdict, transcript, and baselines.</div>
                ) : (
                  <div className="grid gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="info">Verdict: {result.judge.verdict_answer}</Pill>
                      <Pill tone="neutral">Confidence: {result.judge.confidence_1_to_5}/5</Pill>
                      <Pill tone="neutral">GT: {result.item.ground_truth}</Pill>
                      <Pill tone={result.correct_debate ? "good" : "bad"}>{result.correct_debate ? "✅ correct" : "❌ wrong"}</Pill>
                      {typeof result.meta.judge_panel_size === "number" && Number(result.meta.judge_panel_size) > 1 && (
                        <Pill tone="neutral">Judge panel: {String(result.meta.judge_panel_size)}</Pill>
                      )}
                    </div>
                    <p className="text-sm text-primary whitespace-pre-wrap">{result.judge.reasoning}</p>
                    <div className="grid gap-2 rounded-xl ring-1 ring-[color:var(--border)] bg-white/60 p-4">
                      <div className="text-xs text-muted">Judge analysis</div>
                      <div className="text-sm text-primary whitespace-pre-wrap">{result.judge.analysis}</div>
                      <div className="mt-2 grid gap-2 lg:grid-cols-2">
                        <div className="grid gap-1 text-sm text-primary">
                          <div className="text-xs text-muted">Debater A</div>
                          <div><span className="font-medium">Strongest:</span> {result.judge.debater_a_strongest}</div>
                          <div><span className="font-medium">Weakest:</span> {result.judge.debater_a_weakest}</div>
                        </div>
                        <div className="grid gap-1 text-sm text-primary">
                          <div className="text-xs text-muted">Debater B</div>
                          <div><span className="font-medium">Strongest:</span> {result.judge.debater_b_strongest}</div>
                          <div><span className="font-medium">Weakest:</span> {result.judge.debater_b_weakest}</div>
                        </div>
                      </div>
                    </div>
                    {typeof result.meta.llm_call_budget === "number" && (
                      <div className="flex flex-wrap gap-2">
                        <Pill tone="neutral">LLM call budget: {String(result.meta.llm_call_budget)}</Pill>
                        <Pill tone="neutral">Rounds executed: {String(result.meta.rounds_executed ?? result.debate_rounds.length)}</Pill>
                      </div>
                    )}
                  </div>
                )}
              </CardBody>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.08 }}>
            <Card>
              <CardHeader>
                <CardTitle>Debate</CardTitle>
                <CardSubtitle>Initial positions plus the round-by-round transcript.</CardSubtitle>
              </CardHeader>
              <CardBody>
                {!result ? (
                  <div className="text-sm text-muted">No transcript yet.</div>
                ) : (
                  <div className="grid gap-4">
                    <div className="grid gap-3 lg:grid-cols-2">
                      <AnswerPanel title="Debater A (initial)" answer={result.initial_a} tone="neutral" />
                      <AnswerPanel title="Debater B (initial)" answer={result.initial_b} tone="neutral" />
                    </div>

                    {result.consensus ? (
                      <div className="text-sm text-primary">Debaters agreed immediately, so debate rounds were skipped.</div>
                    ) : (
                      result.debate_rounds.map((round) => (
                        <div key={round.round_index} className="grid gap-3">
                          <div className="flex items-center gap-2">
                            <Pill tone="neutral">Round {round.round_index}</Pill>
                          </div>
                          <div className="grid gap-3 lg:grid-cols-2">
                            <AnswerPanel title="Debater A" answer={round.debater_a} />
                            <AnswerPanel title="Debater B" answer={round.debater_b} />
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </CardBody>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.1 }}>
            <Card>
              <CardHeader>
                <CardTitle>Baselines</CardTitle>
                <CardSubtitle>Direct QA and self-consistency for comparison.</CardSubtitle>
              </CardHeader>
              <CardBody>
                {!result ? (
                  <div className="text-sm text-muted">No baselines yet.</div>
                ) : (
                  <div className="grid gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="neutral">Direct: {result.baselines.direct.answer}</Pill>
                      <Pill tone={result.correct_direct ? "good" : "bad"}>{result.correct_direct ? "✅ correct" : "❌ wrong"}</Pill>
                    </div>
                    <p className="text-sm text-primary whitespace-pre-wrap">{result.baselines.direct.rationale}</p>

                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="neutral">SC vote: {result.baselines.self_consistency_vote}</Pill>
                      <Pill tone={result.correct_sc ? "good" : "bad"}>{result.correct_sc ? "✅ correct" : "❌ wrong"}</Pill>
                      <Pill tone="neutral">Samples: {result.baselines.self_consistency_samples.length}</Pill>
                    </div>

                    <details className="rounded-xl ring-1 ring-[color:var(--border)] bg-white/60 p-4">
                      <summary className="cursor-pointer text-sm text-primary">
                        Show self-consistency samples ({result.baselines.self_consistency_samples.length})
                      </summary>
                      <div className="mt-3 grid gap-3">
                        {result.baselines.self_consistency_samples.map((sample, index) => (
                          <div key={`${sample.answer}-${index}`} className="rounded-xl ring-1 ring-[color:var(--border)] bg-white/80 p-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-muted">Sample {index + 1}</span>
                              <Pill tone="info">{sample.answer}</Pill>
                            </div>
                            <p className="mt-2 text-sm text-primary whitespace-pre-wrap">{sample.rationale}</p>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </CardBody>
            </Card>
          </motion.div>
        </div>
      </div>
    </Shell>
  );
}
