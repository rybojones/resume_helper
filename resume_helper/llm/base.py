"""LLMProvider Protocol — structural typing, no inheritance required."""
from typing import Protocol, Type, TypeVar

T = TypeVar("T")


class LLMProvider(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...
    def complete_structured(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> list[T]: ...
    def get_model_name(self) -> str: ...
