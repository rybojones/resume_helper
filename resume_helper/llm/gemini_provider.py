"""Google Gemini LLM provider implementation."""
import instructor
from google import genai
from google.genai import types

from resume_helper.config import GEMINI_API_KEY, MAX_TOKENS

MODEL = "gemini-3-flash-preview"


class GeminiProvider:
    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._instructor = instructor.from_genai(self._client)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=MAX_TOKENS,
            ),
        )
        return response.text

    def complete_structured(self, system_prompt: str, user_prompt: str, response_model) -> list:
        return self._instructor.create(
            model=MODEL,
            response_model=list[response_model],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            generation_config={"max_tokens": MAX_TOKENS},
        )

    def complete_structured_one(self, system_prompt: str, user_prompt: str, response_model):
        return self._instructor.create(
            model=MODEL,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            generation_config={"max_tokens": MAX_TOKENS},
        )

    def get_model_name(self) -> str:
        return MODEL
