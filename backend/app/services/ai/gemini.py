from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.ai.base import BaseAIService, BaseEmbeddingService


class GeminiService(BaseAIService):
    """Concrete Google Gemini API wrapper service using direct REST calls."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta"
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key not configured.")

        model = kwargs.get("model", "gemini-1.5-flash")
        url = f"/models/{model}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        try:
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected response structure from Gemini API: {data}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key not configured.")

        model = kwargs.get("model", "gemini-1.5-flash")
        url = f"/models/{model}:generateContent?key={self.api_key}"

        # Map message roles from OpenAI format (user/system/assistant) to Gemini format (user/model)
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            elif role in ("user", "human"):
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role in ("assistant", "model"):
                contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        try:
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected response structure from Gemini API: {data}")


class GeminiEmbeddingService(BaseEmbeddingService):
    """Concrete Google Gemini text embedding generator using text-embedding-004."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta"
        )

    async def get_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            raise ValueError("Gemini API key not configured.")

        url = f"/models/text-embedding-004:embedContent?key={self.api_key}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Note: text-embedding-004 returns a 768-dimensional vector by default.
        # If we need exactly 1536-dimensional (like OpenAI's Ada/3-small), we pad or project,
        # but in pgvector we can declare vector length. In our schema we defined embedding as Vector(1536).
        # To make Gemini embeddings fit in Vector(1536), we pad the 768-dimensional array with zeros to match 1536.
        # This keeps the database model clean and compatible with both models!
        embedding = data["embedding"]["values"]
        if len(embedding) < 1536:
            embedding += [0.0] * (1536 - len(embedding))
        return embedding

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Map list of calls using single embedding resolution
        return [await self.get_embedding(text) for text in texts]
