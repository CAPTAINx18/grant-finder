import pytest

from app.services.ai.mock import MockAIService, MockEmbeddingService


@pytest.mark.asyncio
async def test_mock_ai_service_generation() -> None:
    """Test MockAIService prompt generation and chat completions."""
    service = MockAIService()
    
    # Test simple generation
    prompt = "Suggest three grant directories"
    response = await service.generate_text(prompt, system_instruction="Be concise")
    assert "Mock AI Response to" in response
    assert prompt in response
    assert "Be concise" in response
    
    # Test chat completion
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "Can you help me?"}
    ]
    chat_response = await service.chat_completion(messages)
    assert "Mock AI Chat response to" in chat_response
    assert "Can you help me?" in chat_response


@pytest.mark.asyncio
async def test_mock_embedding_service_vectors() -> None:
    """Test MockEmbeddingService vector lengths and determinism."""
    service = MockEmbeddingService()
    
    text1 = "NSF Small Business Innovation Research (SBIR) program"
    text2 = "NIH Research Project Grant Program (R01)"
    
    # 1. Test vector length matches target dimension (1536)
    vec1 = await service.get_embedding(text1)
    assert isinstance(vec1, list)
    assert len(vec1) == 1536
    
    vec2 = await service.get_embedding(text2)
    assert len(vec2) == 1536
    
    # 2. Test unit-normalization (sum of squares is approximately 1.0)
    norm1 = sum(x*x for x in vec1)
    assert pytest.approx(norm1, abs=1e-5) == 1.0
    
    # 3. Test determinism (identical texts return identical embeddings)
    vec1_retry = await service.get_embedding(text1)
    assert vec1 == vec1_retry
    
    # 4. Test distinct texts return distinct embeddings
    assert vec1 != vec2
    
    # 5. Test batch retrieval
    batch = await service.get_embeddings([text1, text2])
    assert len(batch) == 2
    assert batch[0] == vec1
    assert batch[1] == vec2
