"""LLMProvider Protocol — structural typing, no inheritance required."""
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...
    def get_model_name(self) -> str: ...
