from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

import httpx

from .config import settings

if TYPE_CHECKING:  # pragma: no cover
    from openai.types.responses import Response


class OpenAIClient:
    """Thin wrapper around the OpenAI Responses API."""

    def __init__(self) -> None:
        if not settings.has_real_api_key():
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Add it to backend/.env or your shell environment before running debate requests."
            )
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
            raise RuntimeError("The openai package is not installed. Run `pip install -e .[dev]` in backend/.") from exc

        self._client = OpenAI(api_key=settings.openai_api_key)

    @staticmethod
    def _output_text(resp: "Response") -> str:
        text = getattr(resp, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        chunks: list[str] = []
        for item in getattr(resp, "output", []) or []:
            content = getattr(item, "content", None)
            if not content:
                continue
            for part in content:
                if getattr(part, "type", None) == "output_text":
                    chunks.append(getattr(part, "text", "") or "")
        return "".join(chunks).strip()

    def create_text(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        temperature: float,
        max_output_tokens: int,
        text_format: dict[str, Any] | None = None,
    ) -> str:
        last_err: Exception | None = None

        for attempt in range(1, 6):
            try:
                payload: dict[str, Any] = {
                    "model": model,
                    "instructions": instructions,
                    "input": input_text,
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
                if text_format is not None:
                    payload["text"] = {"format": text_format}

                resp = self._client.responses.create(**payload)
                return self._output_text(resp)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_err = exc
            except Exception as exc:  # pragma: no cover - network/SDK behavior
                last_err = exc

            time.sleep(min(2**attempt, 16))

        raise RuntimeError(f"OpenAI request failed after retries: {last_err}")

    def create_json(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        temperature: float,
        max_output_tokens: int,
        json_schema: dict[str, Any],
        schema_name: str,
        strict: bool = True,
    ) -> dict[str, Any]:
        text_format = {
            "type": "json_schema",
            "name": schema_name,
            "schema": json_schema,
            "strict": strict,
        }

        text = self.create_text(
            model=model,
            instructions=instructions,
            input_text=input_text,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            text_format=text_format,
        )

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - depends on model output
            raise ValueError(f"Model returned non-JSON text (first 500 chars): {text[:500]}") from exc
