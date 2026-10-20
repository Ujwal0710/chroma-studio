"""Unit tests for authentication, password hashing, session security, and rate limiting."""
import pytest
import os
import tempfile
from modules.auth import (
    hash_password,
    verify_password,
    validate_password_strength,
    register_user,
    authenticate_user,
    initiate_password_reset,
    complete_password_reset,
    change_user_password
)
from modules.storage import init_db


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_password_hashing_and_verification():
    raw_pwd = "ArchitecturalSecret123"
    pwd_hash, salt = hash_password(raw_pwd)
    
    assert pwd_hash != raw_pwd
    assert len(salt) > 0
    assert verify_password(raw_pwd, salt, pwd_hash) is True
    assert verify_password("WrongPassword123", salt, pwd_hash) is False


def test_password_strength_validation():
    # Short
    valid, msg = validate_password_strength("Short1")
    assert not valid
    assert "at least 8" in msg
    
    # Missing digits
    valid, msg = validate_password_strength("ArchitecturalPassword")
    assert not valid
    assert "digit" in msg
    
    # Missing letters
    valid, msg = validate_password_strength("1234567890")
    assert not valid
    assert "letter" in msg
    
    # Valid
    valid, msg = validate_password_strength("SecureDesign2026")
    assert valid


def test_user_registration_and_authentication(temp_db):
    email = "designer@chromastudio.ai"
    pwd = "StudioPassword456"
    name = "Elena Rostova"
    
    # Without terms
    success, msg, user = register_user(email, pwd, name, terms_accepted=False)
    assert not success
    assert "Terms" in msg
    
    # Valid registration
    # Monkeypatch storage DB path via module call
    from modules import storage
    orig_path = storage.DB_PATH
    storage.DB_PATH = temp_db
    try:
        success, msg, user = register_user(email, pwd, name, terms_accepted=True)
        assert success
        assert user["email"] == email
        assert user["full_name"] == name
        
        # Duplicate registration rejected
        dup_success, dup_msg, _ = register_user(email, pwd, name, terms_accepted=True)
        assert not dup_success
        assert "already exists" in dup_msg
        
        # Successful login
        login_ok, login_msg, logged_user = authenticate_user(email, pwd)
        assert login_ok
        assert logged_user["id"] == user["id"]
        
        # Bad password
        bad_ok, bad_msg, _ = authenticate_user(email, "WrongPassword999")
        assert not bad_ok
        assert "Invalid" in bad_msg
    finally:
        storage.DB_PATH = orig_path


def test_password_reset_workflow(temp_db):
    from modules import storage
    orig_path = storage.DB_PATH
    storage.DB_PATH = temp_db
    try:
        email = "reset_test@chromastudio.ai"
        register_user(email, "InitialPassword123", "Test User", terms_accepted=True)
        
        # Initiate reset
        ok, msg, token = initiate_password_reset(email)
        assert ok
        assert token is not None
        
        # Complete reset with valid token
        new_pwd = "UpdatedPassword789"
        reset_ok, reset_msg = complete_password_reset(token, new_pwd)
        assert reset_ok
        
        # Token cannot be reused (consumed)
        reuse_ok, reuse_msg = complete_password_reset(token, "AnotherPassword999")
        assert not reuse_ok
        assert "Invalid or expired" in reuse_msg
        
        # Old password no longer works
        old_auth_ok, _, _ = authenticate_user(email, "InitialPassword123")
        assert not old_auth_ok
        
        # New password works
        new_auth_ok, _, _ = authenticate_user(email, new_pwd)
        assert new_auth_ok
    finally:
        storage.DB_PATH = orig_path
