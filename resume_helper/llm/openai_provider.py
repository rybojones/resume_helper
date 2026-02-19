"""OpenAI LLM provider implementation."""
import openai

from resume_helper.config import OPENAI_API_KEY

MODEL = "gpt-5.2"


class OpenAIProvider:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def get_model_name(self) -> str:
        return MODEL
