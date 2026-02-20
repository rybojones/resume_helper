"""OpenAI LLM provider implementation."""
import instructor
import openai

from resume_helper.config import OPENAI_API_KEY, MAX_TOKENS

MODEL = "gpt-5.2"


class OpenAIProvider:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self._instructor = instructor.from_openai(self._client)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

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
