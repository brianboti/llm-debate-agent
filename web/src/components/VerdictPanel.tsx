type ItemResult = {
  correct_debate: boolean;
  item: { ground_truth: string };
  judge: { verdict_answer: string; confidence_1_to_5: number; reasoning: string };
};

export default function VerdictPanel({ result }: { result: ItemResult }) {
  const { judge } = result;
  return (
    <div className="stack">
      <div className="row">
        <span className="pill">Verdict: {judge.verdict_answer}</span>
        <span className="pill">Confidence: {judge.confidence_1_to_5}/5</span>
        <span className="pill">GT: {result.item.ground_truth}</span>
        <span className="pill">{result.correct_debate ? "✅ correct" : "❌ wrong"}</span>
      </div>
      <p className="muted">{judge.reasoning}</p>
    </div>
  );
}
