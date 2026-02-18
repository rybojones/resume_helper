"""Anthropic Claude LLM provider implementation."""
import anthropic

from resume_helper.config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-4-6"


class ClaudeProvider:
    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        message = self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def get_model_name(self) -> str:
        return MODEL
