from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_PLACEHOLDER_RE = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    raw_text: str

    def placeholders(self) -> set[str]:
        return set(_PLACEHOLDER_RE.findall(self.raw_text))

    def render(self, **values: str) -> str:
        missing = sorted(key for key in self.placeholders() if key not in values)
        if missing:
            raise KeyError(f"Missing prompt variables for {self.name}: {', '.join(missing)}")

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(values[key])

        return _PLACEHOLDER_RE.sub(repl, self.raw_text).strip()


class PromptStore:
    """Load editable prompt templates from the repo-level prompts directory."""

    def __init__(self, prompts_dir: Path) -> None:
        self._dir = prompts_dir

    def _template(self, filename: str) -> PromptTemplate:
        path = self._dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing prompt file: {path}")
        return PromptTemplate(name=filename, raw_text=path.read_text(encoding="utf-8"))

    def debater_a(self) -> PromptTemplate:
        return self._template("debater_a.txt")

    def debater_b(self) -> PromptTemplate:
        return self._template("debater_b.txt")

    def judge(self) -> PromptTemplate:
        return self._template("judge.txt")

    def jury_deliberation(self) -> PromptTemplate:
        return self._template("jury_deliberation.txt")

    def direct_qa(self) -> PromptTemplate:
        return self._template("direct_qa.txt")

    def self_consistency(self) -> PromptTemplate:
        return self._template("self_consistency.txt")
