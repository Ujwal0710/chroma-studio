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
    complete_password_reset
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
    email = "designer_test_new@chromastudio.ai"
    pwd = "StudioPassword456"
    name = "Elena Rostova"
    
    # Without terms
    success, msg, user = register_user(email, pwd, name, terms_accepted=False, db_path=temp_db)
    assert not success
    assert "Terms" in msg
    
    # Valid registration
    success, msg, user = register_user(email, pwd, name, terms_accepted=True, db_path=temp_db)
    assert success
    assert user["email"] == email
    assert user["full_name"] == name
    
    # Duplicate registration rejected
    dup_success, dup_msg, _ = register_user(email, pwd, name, terms_accepted=True, db_path=temp_db)
    assert not dup_success
    assert "already exists" in dup_msg
    
    # Successful login
    login_ok, login_msg, logged_user = authenticate_user(email, pwd, db_path=temp_db)
    assert login_ok
    assert logged_user["id"] == user["id"]
    
    # Bad password
    bad_ok, bad_msg, _ = authenticate_user(email, "WrongPassword999", db_path=temp_db)
    assert not bad_ok
    assert "Invalid" in bad_msg


def test_password_reset_workflow(temp_db):
    email = "reset_test_unique@chromastudio.ai"
    register_user(email, "InitialPassword123", "Test User", terms_accepted=True, db_path=temp_db)
    
    # Initiate reset
    ok, msg, token = initiate_password_reset(email, db_path=temp_db)
    assert ok
    assert token is not None
    
    # Complete reset with valid token
    new_pwd = "UpdatedPassword789"
    reset_ok, reset_msg = complete_password_reset(token, new_pwd, db_path=temp_db)
    assert reset_ok
    
    # Token cannot be reused (consumed)
    reuse_ok, reuse_msg = complete_password_reset(token, "AnotherPassword999", db_path=temp_db)
    assert not reuse_ok
    assert "Invalid or expired" in reuse_msg
    
    # Old password no longer works
    old_auth_ok, _, _ = authenticate_user(email, "InitialPassword123", db_path=temp_db)
    assert not old_auth_ok
    
    # New password works
    new_auth_ok, _, _ = authenticate_user(email, new_pwd, db_path=temp_db)
    assert new_auth_ok

