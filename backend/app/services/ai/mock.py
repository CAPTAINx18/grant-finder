import hashlib
import random
from typing import Any, Dict, List, Optional

from app.services.ai.base import BaseAIService, BaseEmbeddingService


class MockAIService(BaseAIService):
    """Mock implementation of the AI service for tests and development without API keys."""

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        sys_part = f" [System: {system_instruction}]" if system_instruction else ""
        return f"Mock AI Response to: '{prompt}'{sys_part} with temp={temperature}"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        return f"Mock AI Chat response to: '{last_msg}'"


class MockEmbeddingService(BaseEmbeddingService):
    """Mock embedding generator producing stable 1536-dimensional vectors for tests."""

    def _generate_vector(self, text: str) -> List[float]:
        # Generate a deterministic vector based on MD5 of the input text
        hasher = hashlib.md5(text.encode("utf-8"))
        seed = int(hasher.hexdigest(), 16) % 10000
        random.seed(seed)
        # Create a unit-normalized mock vector of size 1536
        vec = [random.uniform(-0.1, 0.1) for _ in range(1536)]
        norm = sum(x*x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def get_embedding(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(text) for text in texts]
