import pytest
from jose import jwt

from app.core.config import settings
from app.services.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing() -> None:
    """Test password hashing and verification logic using Argon2."""
    password = "SecurePassword123!"
    wrong_password = "WrongPassword123!"
    
    # Generate password hash
    hashed = get_password_hash(password)
    assert hashed != password
    assert hashed.startswith("$argon2")  # Verify it uses Argon2 scheme
    
    # Verify correct password succeeds
    assert verify_password(password, hashed) is True
    
    # Verify incorrect password fails
    assert verify_password(wrong_password, hashed) is False


def test_jwt_access_token_generation() -> None:
    """Test generating and decoding JWT access tokens."""
    subject = "a9d59247-f331-4127-b9c1-8409b30b427b"
    
    # Generate access token
    token = create_access_token(subject=subject)
    assert isinstance(token, str)
    
    # Decode token and verify claims
    claims = decode_token(token)
    assert claims is not None
    assert claims.get("sub") == subject
    assert claims.get("type") == "access"
    assert "exp" in claims


def test_jwt_refresh_token_generation() -> None:
    """Test generating and decoding JWT refresh tokens."""
    subject = "a9d59247-f331-4127-b9c1-8409b30b427b"
    
    # Generate refresh token
    token = create_refresh_token(subject=subject)
    assert isinstance(token, str)
    
    # Decode token and verify claims
    claims = decode_token(token)
    assert claims is not None
    assert claims.get("sub") == subject
    assert claims.get("type") == "refresh"
    assert "exp" in claims


def test_jwt_decoding_failure() -> None:
    """Test that invalid or tempered tokens return None on decoding."""
    invalid_token = "invalid.token.string"
    claims = decode_token(invalid_token)
    assert claims is None
    
    # Tempered token test
    subject = "a9d59247-f331-4127-b9c1-8409b30b427b"
    token = create_access_token(subject=subject)
    tempered_token = token + "tempered"
    assert decode_token(tempered_token) is None
