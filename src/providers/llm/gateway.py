from src.providers.llm.openai_compat import OpenAICompatibleLLM


class LLMGateway(OpenAICompatibleLLM):
    """One OpenAI-compatible surface for Ollama, vLLM, TGI, and hosted APIs."""
