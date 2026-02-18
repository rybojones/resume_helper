"""Anthropic Claude LLM provider implementation."""


class ClaudeProvider:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError("claude_provider not yet implemented")

    def get_model_name(self) -> str:
        raise NotImplementedError("claude_provider not yet implemented")
