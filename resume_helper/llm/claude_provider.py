"""Anthropic Claude LLM provider implementation."""
import anthropic
import instructor

from resume_helper.config import ANTHROPIC_API_KEY, MAX_TOKENS

MODEL = "claude-sonnet-4-6"


class ClaudeProvider:
    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self._instructor = instructor.from_anthropic(self._client)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        message = self._client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def complete_structured(self, system_prompt: str, user_prompt: str, response_model) -> list:
        return self._instructor.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            response_model=list[response_model],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    def complete_structured_one(self, system_prompt: str, user_prompt: str, response_model):
        return self._instructor.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    def get_model_name(self) -> str:
        return MODEL
