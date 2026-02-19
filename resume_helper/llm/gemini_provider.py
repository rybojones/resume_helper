"""Google Gemini LLM provider implementation."""
from google import genai
from google.genai import types

from resume_helper.config import GEMINI_API_KEY

MODEL = "gemini-3-flash-preview"


class GeminiProvider:
    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = genai.Client(api_key=GEMINI_API_KEY)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=4096,
            ),
        )
        return response.text

    def get_model_name(self) -> str:
        return MODEL
