from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from .config import settings
from .debater_agent import TranscriptTurn
from .openai_client import OpenAIClient
from .prompts import PromptStore
from .types import Item, JudgeVerdict, normalize_answer


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict_answer": {
            "type": "string",
            "enum": ["yes", "no"],
            "description": "Final chosen answer label. Must be exactly 'yes' or 'no'.",
        },
        "confidence_1_to_5": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "1=low confidence, 5=very confident.",
        },
        "analysis": {
            "type": "string",
            "description": "Concise judge comparison of both debaters.",
        },
        "debater_a_strongest": {"type": "string", "description": "Strongest argument made by Debater A."},
        "debater_a_weakest": {"type": "string", "description": "Weakest point in Debater A's case."},
        "debater_b_strongest": {"type": "string", "description": "Strongest argument made by Debater B."},
        "debater_b_weakest": {"type": "string", "description": "Weakest point in Debater B's case."},
        "reasoning": {"type": "string", "description": "Short decision-oriented summary for the verdict."},
    },
    "required": [
        "verdict_answer",
        "confidence_1_to_5",
        "analysis",
        "debater_a_strongest",
        "debater_a_weakest",
        "debater_b_strongest",
        "debater_b_weakest",
        "reasoning",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class JudgeExecution:
    final_verdict: JudgeVerdict
    panel: list[JudgeVerdict]
    llm_call_count: int


class JudgeAgent:
    def __init__(self, *, client: OpenAIClient, prompts: PromptStore) -> None:
        self._client = client
        self._prompts = prompts

    def evaluate(self, *, item: Item, transcript: list[TranscriptTurn]) -> JudgeExecution:
        panel_size = settings.judge_panel_size
        panel = [self._single_judge(item=item, transcript=transcript, judge_index=i + 1) for i in range(panel_size)]
        if panel_size == 1:
            return JudgeExecution(final_verdict=panel[0], panel=panel, llm_call_count=1)
        final_verdict = self._deliberate(item=item, transcript=transcript, panel=panel)
        return JudgeExecution(final_verdict=final_verdict, panel=panel, llm_call_count=panel_size + 1)

    def _single_judge(self, *, item: Item, transcript: list[TranscriptTurn], judge_index: int) -> JudgeVerdict:
        prompt = self._prompts.judge().render(
            QUESTION=item.question.strip(),
            CONTEXT=item.context.strip() or "[NO CONTEXT PROVIDED]",
            TRANSCRIPT=self._format_transcript(transcript),
            JUDGE_INDEX=str(judge_index),
            JSON_SCHEMA=json.dumps(JUDGE_SCHEMA, indent=2),
        )
        data = self._client.create_json(
            model=settings.openai_model_judge,
            instructions="Return only JSON matching the requested schema. verdict_answer must be exactly 'yes' or 'no', never a debater name.",
            input_text=prompt,
            temperature=settings.temp_judge,
            max_output_tokens=settings.max_output_tokens,
            json_schema=JUDGE_SCHEMA,
            schema_name=f"judge_verdict_{judge_index}",
            strict=True,
        )
        return JudgeVerdict(**data)

    def _deliberate(self, *, item: Item, transcript: list[TranscriptTurn], panel: list[JudgeVerdict]) -> JudgeVerdict:
        prompt = self._prompts.jury_deliberation().render(
            QUESTION=item.question.strip(),
            CONTEXT=item.context.strip() or "[NO CONTEXT PROVIDED]",
            TRANSCRIPT=self._format_transcript(transcript),
            PANEL_VERDICTS=self._format_panel(panel),
            MAJORITY_ANSWER=self._majority_answer(panel),
            JSON_SCHEMA=json.dumps(JUDGE_SCHEMA, indent=2),
        )
        data = self._client.create_json(
            model=settings.openai_model_judge,
            instructions="Return only JSON matching the requested schema. verdict_answer must be exactly 'yes' or 'no', never a debater name.",
            input_text=prompt,
            temperature=settings.temp_judge,
            max_output_tokens=settings.max_output_tokens,
            json_schema=JUDGE_SCHEMA,
            schema_name="jury_deliberation",
            strict=True,
        )
        return JudgeVerdict(**data)

    @staticmethod
    def _format_transcript(transcript: list[TranscriptTurn]) -> str:
        if not transcript:
            return "[NO TRANSCRIPT]"
        blocks: list[str] = []
        for turn in transcript:
            payload = json.dumps(turn.payload, ensure_ascii=False)
            blocks.append(f"{turn.speaker} | round={turn.round_index} | {payload}")
        return "\n".join(blocks)

    @staticmethod
    def _format_panel(panel: list[JudgeVerdict]) -> str:
        rows: list[str] = []
        for index, verdict in enumerate(panel, start=1):
            rows.append(f"Judge {index}: {verdict.model_dump_json(indent=2)}")
        return "\n\n".join(rows)

    @staticmethod
    def _majority_answer(panel: list[JudgeVerdict]) -> str:
        ranked = Counter(normalize_answer(verdict.verdict_answer) for verdict in panel).most_common()
        if not ranked:
            return ""
        return ranked[0][0]
