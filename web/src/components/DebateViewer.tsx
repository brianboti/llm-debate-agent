type ModelAnswer = { answer: string; rationale: string; citations: string[] };
type DebateRound = { round_index: number; debater_a: ModelAnswer; debater_b: ModelAnswer };

type ItemResult = {
  consensus: boolean;
  debate_rounds: DebateRound[];
};

function AnswerCard({ title, a }: { title: string; a: ModelAnswer }) {
  return (
    <div className="subcard">
      <div className="row">
        <strong>{title}</strong>
        <span className="pill">Answer: {a.answer}</span>
      </div>

      {a.rationale && <p className="muted">{a.rationale}</p>}

      {a.citations?.length > 0 && (
        <details>
          <summary>Citations ({a.citations.length})</summary>
          <ul>
            {a.citations.map((c, i) => (
              <li key={i} className="muted">
                {c}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default function DebateViewer({ result }: { result: ItemResult }) {
  if (result.consensus) {
    return (
      <div className="muted">
        Debaters agreed immediately. Debate rounds were skipped.
      </div>
    );
  }

  if (!result.debate_rounds || result.debate_rounds.length === 0) {
    return <div className="muted">No debate rounds recorded.</div>;
  }

  return (
    <div className="stack">
      {result.debate_rounds.map((r) => (
        <div key={r.round_index} className="round">
          <h3>Round {r.round_index}</h3>
          <div className="grid2">
            <AnswerCard title="Debater A" a={r.debater_a} />
            <AnswerCard title="Debater B" a={r.debater_b} />
          </div>
        </div>
      ))}
    </div>
  );
}
