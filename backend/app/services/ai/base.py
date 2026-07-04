from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIService(ABC):
    """Abstract base class for LLM text generation and agent reasoning services."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate text from a single prompt."""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate chat completion response from a conversation transcript."""
        pass


class BaseEmbeddingService(ABC):
    """Abstract base class for text embedding vector generation."""

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate a single high-dimensional vector for a string of text."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate multiple high-dimensional vectors for a list of text strings."""
        pass
