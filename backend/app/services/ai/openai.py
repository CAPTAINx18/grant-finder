from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.ai.base import BaseAIService, BaseEmbeddingService


class OpenAIService(BaseAIService):
    """Concrete OpenAI API wrapper service utilizing HTTPX client calls."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")

        payload = {
            "model": kwargs.get("model", "gpt-4o-mini"),
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])


class OpenAIEmbeddingService(BaseEmbeddingService):
    """Concrete OpenAI text embedding generator (text-embedding-3-small default)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )

    async def get_embedding(self, text: str) -> List[float]:
        res = await self.get_embeddings([text])
        return res[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")

        payload = {
            "model": "text-embedding-3-small",
            "input": texts
        }
        response = await self.client.post("/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
