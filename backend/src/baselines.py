from __future__ import annotations

import json
from collections import Counter

from .config import settings
from .openai_client import OpenAIClient
from .prompts import PromptStore
from .types import Baselines, Item, ModelAnswer, normalize_answer


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "enum": ["yes", "no"],
            "description": "Final answer label. Must be exactly 'yes' or 'no'.",
        },
        "rationale": {"type": "string", "description": "Concise justification."},
        "citations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional quotes/ids from the given context.",
        },
    },
    "required": ["answer", "rationale", "citations"],
    "additionalProperties": False,
}


def _render_shared_fields(item: Item) -> dict[str, str]:
    return {
        "QUESTION": item.question.strip(),
        "CONTEXT": item.context.strip() or "[NO CONTEXT PROVIDED]",
        "JSON_SCHEMA": json.dumps(ANSWER_SCHEMA, indent=2),
    }


def direct_qa(*, client: OpenAIClient, prompts: PromptStore, item: Item) -> ModelAnswer:
    data = client.create_json(
        model=settings.openai_model_debater,
        instructions="Return only JSON matching the requested schema. The answer field must be exactly 'yes' or 'no'.",
        input_text=prompts.direct_qa().render(**_render_shared_fields(item)),
        temperature=settings.temp_baseline,
        max_output_tokens=settings.max_output_tokens,
        json_schema=ANSWER_SCHEMA,
        schema_name="direct_qa",
        strict=True,
    )
    return ModelAnswer(**data)


def self_consistency(
    *,
    client: OpenAIClient,
    prompts: PromptStore,
    item: Item,
    n_samples: int,
) -> tuple[list[ModelAnswer], str]:
    samples: list[ModelAnswer] = []
    for sample_index in range(1, n_samples + 1):
        data = client.create_json(
            model=settings.openai_model_debater,
            instructions="Return only JSON matching the requested schema. The answer field must be exactly 'yes' or 'no'.",
            input_text=prompts.self_consistency().render(SAMPLE_INDEX=str(sample_index), **_render_shared_fields(item)),
            temperature=max(settings.temp_debater, 0.7),
            max_output_tokens=settings.max_output_tokens,
            json_schema=ANSWER_SCHEMA,
            schema_name="self_consistency",
            strict=True,
        )
        samples.append(ModelAnswer(**data))

    normalized_to_raw: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for sample in samples:
        normalized = normalize_answer(sample.answer)
        counts[normalized] += 1
        normalized_to_raw.setdefault(normalized, sample.answer.strip())

    vote_normalized = counts.most_common(1)[0][0]
    vote = normalized_to_raw[vote_normalized]
    return samples, vote


def run_baselines(
    *,
    client: OpenAIClient,
    prompts: PromptStore,
    item: Item,
    self_consistency_samples: int | None = None,
) -> Baselines:
    direct = direct_qa(client=client, prompts=prompts, item=item)
    sample_budget = self_consistency_samples or settings.self_consistency_samples
    samples, vote = self_consistency(
        client=client,
        prompts=prompts,
        item=item,
        n_samples=sample_budget,
    )
    return Baselines(direct=direct, self_consistency_samples=samples, self_consistency_vote=vote)
