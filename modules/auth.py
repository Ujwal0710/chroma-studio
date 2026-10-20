"""Authentication, password security, session handling, and access control."""
import os
import hmac
import hashlib
import secrets
import datetime
from typing import Optional, Tuple, Dict, Any

from config.settings import AUTH_SECRET_KEY, MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, DB_PATH
from modules.storage import (
    get_user_by_email,
    get_user_by_id,
    create_user_record,
    update_user_password,
    record_login_attempt,
    get_recent_failed_login_count,
    clear_login_attempts,
    store_password_reset_token,
    verify_and_consume_reset_token
)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a secure salt.
    Returns (hex_hash, salt_hex).
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    salt_bytes = salt.encode('utf-8')
    pwd_bytes = password.encode('utf-8')
    
    derived = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=pwd_bytes,
        salt=salt_bytes,
        iterations=100000
    )
    return derived.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verify password against salt and expected hash using constant-time comparison."""
    calculated_hash, _ = hash_password(password, salt=salt)
    return hmac.compare_digest(calculated_hash, expected_hash)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate that password meets security requirements:
    - At least 8 characters
    - Contains at least one digit
    - Contains at least one letter
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one numeric digit."
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter."
    return True, "Password meets security strength requirements."


def register_user(
    email: str,
    password: str,
    full_name: str,
    terms_accepted: bool,
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Register a new user account."""
    target_db = db_path or DB_PATH
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean or "." not in email_clean:
        return False, "Please enter a valid email address.", None
    
    if not terms_accepted:
        return False, "You must agree to the Terms of Service and Privacy Policy to create an account.", None
    
    is_valid_pwd, msg = validate_password_strength(password)
    if not is_valid_pwd:
        return False, msg, None
    
    # Check if user already exists
    existing = get_user_by_email(email_clean, db_path=target_db)
    if existing:
        return False, "An account with this email address already exists.", None
    
    pwd_hash, salt = hash_password(password)
    user_record = create_user_record(
        email=email_clean,
        password_hash=pwd_hash,
        salt=salt,
        full_name=full_name.strip() or "Architectural Designer",
        db_path=target_db
    )
    return True, "Account created successfully.", user_record


def authenticate_user(
    email: str,
    password: str,
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate a user by email and password with rate-limiting against brute force.
    """
    target_db = db_path or DB_PATH
    email_clean = email.strip().lower()
    
    # Check rate limiting / lockouts
    failed_attempts = get_recent_failed_login_count(email_clean, minutes=LOCKOUT_MINUTES, db_path=target_db)
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        return False, f"Too many failed login attempts. Please wait {LOCKOUT_MINUTES} minutes before trying again.", None
    
    user = get_user_by_email(email_clean, db_path=target_db)
    if not user:
        record_login_attempt(email_clean, success=False, db_path=target_db)
        return False, "Invalid email or password.", None
    
    if not verify_password(password, user["salt"], user["password_hash"]):
        record_login_attempt(email_clean, success=False, db_path=target_db)
        return False, "Invalid email or password.", None
    
    # Successful login
    clear_login_attempts(email_clean, db_path=target_db)
    return True, "Authentication successful.", user


def initiate_password_reset(email: str, db_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a secure password reset token for an email.
    Returns (success, message, token_if_development).
    """
    target_db = db_path or DB_PATH
    email_clean = email.strip().lower()
    user = get_user_by_email(email_clean, db_path=target_db)
    if not user:
        return True, "If this email is registered, password recovery instructions have been initiated.", None
    
    raw_token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat()
    
    store_password_reset_token(email_clean, token_hash, expires_at, db_path=target_db)
    return True, "If this email is registered, password recovery instructions have been initiated.", raw_token


def complete_password_reset(token: str, new_password: str, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Complete a password reset using a valid token."""
    target_db = db_path or DB_PATH
    is_valid_pwd, msg = validate_password_strength(new_password)
    if not is_valid_pwd:
        return False, msg
    
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    email = verify_and_consume_reset_token(token_hash, db_path=target_db)
    if not email:
        return False, "Invalid or expired password reset token."
    
    pwd_hash, salt = hash_password(new_password)
    update_user_password(email, pwd_hash, salt, db_path=target_db)
    return True, "Your password has been reset successfully. Please log in with your new password."


def change_user_password(user_id: str, old_password: str, new_password: str, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Change password for an authenticated user."""
    target_db = db_path or DB_PATH
    user = get_user_by_id(user_id, db_path=target_db)
    if not user:
        return False, "User not found."
    
    if not verify_password(old_password, user["salt"], user["password_hash"]):
        return False, "Current password does not match our records."
    
    is_valid_pwd, msg = validate_password_strength(new_password)
    if not is_valid_pwd:
        return False, msg
    
    pwd_hash, salt = hash_password(new_password)
    update_user_password(user["email"], pwd_hash, salt, db_path=target_db)
    return True, "Password updated successfully."
