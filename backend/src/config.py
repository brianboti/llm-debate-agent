from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent
_PLACEHOLDER_API_KEY = "YOUR_OPENAI_API_KEY_HERE"


def _env_file_path() -> Path:
    """Return an explicit path to backend/.env for deterministic loading."""
    return _BACKEND_DIR / ".env"


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (_BACKEND_DIR / path).resolve()


class Settings(BaseSettings):
    """Application settings loaded from environment variables and backend/.env."""

    model_config = SettingsConfigDict(
        env_file=_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required at runtime, but defaulting here keeps imports/tests working without a committed secret.
    openai_api_key: str = Field(_PLACEHOLDER_API_KEY, alias="OPENAI_API_KEY")

    # Models
    openai_model_debater: str = Field("gpt-4o-mini", alias="OPENAI_MODEL_DEBATER")
    openai_model_judge: str = Field("gpt-4o-mini", alias="OPENAI_MODEL_JUDGE")

    # Debate protocol
    debate_min_rounds: int = Field(3, alias="DEBATE_MIN_ROUNDS", ge=3)
    debate_max_rounds: int = Field(6, alias="DEBATE_MAX_ROUNDS", ge=3)
    debate_convergence_rounds: int = Field(2, alias="DEBATE_CONVERGENCE_ROUNDS", ge=1)
    judge_panel_size: int = Field(1, alias="JUDGE_PANEL_SIZE", ge=1)

    # Temperatures
    temp_debater: float = Field(0.7, alias="TEMP_DEBATER", ge=0.0, le=2.0)
    temp_judge: float = Field(0.2, alias="TEMP_JUDGE", ge=0.0, le=2.0)
    temp_baseline: float = Field(0.2, alias="TEMP_BASELINE", ge=0.0, le=2.0)

    # Baselines
    self_consistency_samples: int = Field(9, alias="SELF_CONSISTENCY_SAMPLES", ge=1)

    # Limits
    max_output_tokens: int = Field(600, alias="MAX_OUTPUT_TOKENS", ge=1)

    # Server
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(False, alias="CORS_ALLOW_CREDENTIALS")

    # Paths relative to backend/
    runs_dir: str = Field("../runs", alias="RUNS_DIR")
    prompts_dir: str = Field("../prompts", alias="PROMPTS_DIR")
    report_artifacts_dir: str = Field("../artifacts", alias="REPORT_ARTIFACTS_DIR")

    @model_validator(mode="after")
    def validate_round_bounds(self) -> "Settings":
        if self.debate_max_rounds < self.debate_min_rounds:
            raise ValueError("DEBATE_MAX_ROUNDS must be >= DEBATE_MIN_ROUNDS.")
        return self

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def runs_path(self) -> Path:
        return _resolve_repo_path(self.runs_dir)

    def prompts_path(self) -> Path:
        return _resolve_repo_path(self.prompts_dir)

    def report_artifacts_path(self) -> Path:
        return _resolve_repo_path(self.report_artifacts_dir)

    def has_real_api_key(self) -> bool:
        key = (self.openai_api_key or "").strip()
        return bool(key and key != _PLACEHOLDER_API_KEY)


settings = Settings()
