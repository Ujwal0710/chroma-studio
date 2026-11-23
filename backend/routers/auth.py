"""Authentication router: registration, login, logout, password recovery, and session profile."""
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Response, HTTPException, status, Depends
from modules.auth import (
    register_user,
    authenticate_user,
    initiate_password_reset,
    complete_password_reset
)
from backend.auth import create_access_token, get_current_user_optional, JWT_EXPIRE_HOURS

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    terms_accepted: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetInitRequest(BaseModel):
    email: EmailStr


class ResetConfirmRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, response: Response):
    success, msg, user_record = register_user(
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        terms_accepted=req.terms_accepted
    )
    if not success or not user_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Set httpOnly JWT session cookie
    token = create_access_token(user_id=user_record["id"], email=user_record["email"])
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=JWT_EXPIRE_HOURS * 3600,
        samesite="lax",
        secure=False  # Set True in production over HTTPS
    )

    return {
        "status": "success",
        "message": msg,
        "user": {
            "id": user_record["id"],
            "email": user_record["email"],
            "full_name": user_record["full_name"],
            "role": user_record.get("role", "designer")
        }
    }


@router.post("/login")
def login(req: LoginRequest, response: Response):
    success, msg, user_record = authenticate_user(
        email=req.email,
        password=req.password
    )
    if not success or not user_record:
        status_code = status.HTTP_403_FORBIDDEN if "locked" in msg.lower() else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=status_code, detail=msg)

    token = create_access_token(user_id=user_record["id"], email=user_record["email"])
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=JWT_EXPIRE_HOURS * 3600,
        samesite="lax",
        secure=False
    )

    return {
        "status": "success",
        "message": "Authentication successful.",
        "user": {
            "id": user_record["id"],
            "email": user_record["email"],
            "full_name": user_record["full_name"],
            "role": user_record.get("role", "designer")
        }
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Successfully signed out."}


@router.post("/reset-request")
def request_password_reset(req: ResetInitRequest):
    success, msg, token = initiate_password_reset(email=req.email)
    # Return friendly response (token returned in dev for testing)
    return {
        "status": "success",
        "message": msg if success else "If the email is registered, recovery instructions and token have been issued.",
        "dev_token": token
    }


@router.post("/reset-confirm")
def confirm_password_reset(req: ResetConfirmRequest):
    success, msg = complete_password_reset(token=req.token, new_password=req.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg}


from modules.subscription_service import get_user_subscription, get_user_usage
from config.settings import DB_PATH


@router.get("/me")
def get_authenticated_profile(current_user: Optional[dict] = Depends(get_current_user_optional)):
    if not current_user:
        return {"authenticated": False, "user": None}
    
    sub = get_user_subscription(current_user["id"], db_path=DB_PATH)
    usage = get_user_usage(current_user["id"], db_path=DB_PATH)

    return {
        "authenticated": True,
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "role": current_user.get("role", "designer"),
            "plan_id": sub["plan_id"],
            "plan_name": sub["plan_details"]["name"],
            "subscription": sub,
            "usage": usage
        }
    }
