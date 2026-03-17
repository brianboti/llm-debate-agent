from __future__ import annotations

import json
from dataclasses import dataclass

from .config import settings
from .openai_client import OpenAIClient
from .prompts import PromptStore
from .types import Item, ModelAnswer


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "enum": ["yes", "no"],
            "description": "Final answer label. Must be exactly 'yes' or 'no'.",
        },
        "rationale": {"type": "string", "description": "Concise argument."},
        "citations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional quotes/ids from the given context.",
        },
    },
    "required": ["answer", "rationale", "citations"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class TranscriptTurn:
    speaker: str
    round_index: int
    payload: dict


class DebaterAgent:
    def __init__(self, *, client: OpenAIClient, prompts: PromptStore, side: str) -> None:
        if side not in {"A", "B"}:
            raise ValueError("side must be 'A' or 'B'")
        self._client = client
        self._prompts = prompts
        self._side = side

    @property
    def role_name(self) -> str:
        return f"Debater {self._side}"

    @property
    def opponent_name(self) -> str:
        return "Debater B" if self._side == "A" else "Debater A"

    def initial(self, *, item: Item) -> ModelAnswer:
        prompt = self._render_prompt(
            item=item,
            transcript=[],
            round_index=0,
            turn_kind="initial_position",
        )
        data = self._client.create_json(
            model=settings.openai_model_debater,
            instructions="Return only JSON matching the requested schema. The answer field must be exactly 'yes' or 'no'.",
            input_text=prompt,
            temperature=settings.temp_debater,
            max_output_tokens=settings.max_output_tokens,
            json_schema=ANSWER_SCHEMA,
            schema_name=f"debater_{self._side.lower()}",
            strict=True,
        )
        return ModelAnswer(**data)

    def debate_turn(self, *, item: Item, round_index: int, transcript: list[TranscriptTurn]) -> ModelAnswer:
        prompt = self._render_prompt(
            item=item,
            transcript=transcript,
            round_index=round_index,
            turn_kind="debate_round",
        )
        data = self._client.create_json(
            model=settings.openai_model_debater,
            instructions="Return only JSON matching the requested schema. The answer field must be exactly 'yes' or 'no'.",
            input_text=prompt,
            temperature=settings.temp_debater,
            max_output_tokens=settings.max_output_tokens,
            json_schema=ANSWER_SCHEMA,
            schema_name=f"debater_{self._side.lower()}",
            strict=True,
        )
        return ModelAnswer(**data)

    def _render_prompt(
        self,
        *,
        item: Item,
        transcript: list[TranscriptTurn],
        round_index: int,
        turn_kind: str,
    ) -> str:
        template = self._prompts.debater_a() if self._side == "A" else self._prompts.debater_b()
        return template.render(
            ROLE_NAME=self.role_name,
            OPPONENT_NAME=self.opponent_name,
            QUESTION=item.question.strip(),
            CONTEXT=item.context.strip() or "[NO CONTEXT PROVIDED]",
            TRANSCRIPT=self._format_transcript(transcript),
            ROUND_INDEX=str(round_index),
            TURN_KIND=turn_kind,
            JSON_SCHEMA=json.dumps(ANSWER_SCHEMA, indent=2),
        )

    @staticmethod
    def _format_transcript(transcript: list[TranscriptTurn]) -> str:
        if not transcript:
            return "[NO PRIOR TRANSCRIPT]"
        blocks: list[str] = []
        for turn in transcript:
            payload = json.dumps(turn.payload, ensure_ascii=False)
            blocks.append(f"{turn.speaker} | round={turn.round_index} | {payload}")
        return "\n".join(blocks)
