"""Billing & Subscription router: Tier plans, Razorpay sandbox checkout, HMAC verification, and webhooks."""
import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, status, Depends, Header

from config.settings import SUBSCRIPTION_PLANS, DB_PATH, RAZORPAY_KEY_SECRET
from modules.subscription_service import (
    get_user_subscription,
    get_user_usage,
    execute_test_sandbox_checkout,
    verify_razorpay_payment_signature,
    generate_razorpay_payment_signature,
    process_payment_webhook,
    update_user_subscription
)
from modules.storage import get_user_by_id
from backend.auth import get_current_user_optional

router = APIRouter(tags=["Billing & Plans"])


class OrderRequest(BaseModel):
    plan_id: str  # 'free', 'plus', or 'pro'
    billing_cycle: str = "monthly"


class VerifyPaymentRequest(BaseModel):
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    signature: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    plan_id: Optional[str] = "plus"
    billing_cycle: str = "monthly"


class SwitchPlanRequest(BaseModel):
    plan_id: Optional[str] = None
    target_plan: Optional[str] = None
    billing_cycle: str = "monthly"


def get_full_user_profile(user_id: str) -> Dict[str, Any]:
    """Compile single source of truth user profile directly from database."""
    user = get_user_by_id(user_id, db_path=DB_PATH)
    sub = get_user_subscription(user_id, db_path=DB_PATH)
    usage = get_user_usage(user_id, db_path=DB_PATH)
    return {
        "id": user_id,
        "email": user.get("email") if user else f"{user_id}@chromastudio.ai",
        "full_name": user.get("full_name") if user else "Architect User",
        "role": user.get("role", "designer") if user else "designer",
        "plan_id": sub["plan_id"],
        "plan_name": sub["plan_details"]["name"],
        "subscription": sub,
        "usage": usage
    }


@router.get("/plans")
def get_plans():
    """Retrieve available subscription tiers with feature quotas and INR pricing."""
    return SUBSCRIPTION_PLANS


@router.get("/billing/subscription")
def get_user_current_subscription(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Retrieve active user subscription plan and current monthly usage counters directly from DB."""
    user_id = current_user["id"] if current_user else "guest_user"
    sub = get_user_subscription(user_id=user_id, db_path=DB_PATH)
    usage = get_user_usage(user_id=user_id, db_path=DB_PATH)
    return {
        "status": "success",
        "subscription": sub,
        "usage": usage,
        "user": get_full_user_profile(user_id) if current_user else None
    }


@router.post("/billing/order")
def create_billing_order(
    req: OrderRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Initiate a Razorpay order or sandbox checkout for tier upgrade."""
    user_id = current_user["id"] if current_user else "guest_user"
    if req.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan '{req.plan_id}'. Choose from: {list(SUBSCRIPTION_PLANS.keys())}"
        )

    current_sub = get_user_subscription(user_id=user_id, db_path=DB_PATH)
    if current_sub.get("plan_id") == req.plan_id and current_sub.get("status") == "active":
        return {
            "status": "info",
            "already_active": True,
            "message": f"You already have the {SUBSCRIPTION_PLANS[req.plan_id]['name']} plan active.",
            "order_id": None,
            "checkout": None,
            "user": get_full_user_profile(user_id)
        }

    plan_info = SUBSCRIPTION_PLANS[req.plan_id]
    price_inr = plan_info["annual_price_inr"] if req.billing_cycle == "annual" else plan_info["monthly_price_inr"]
    order_id = f"order_{uuid.uuid4().hex[:14]}"
    payment_id = f"pay_{uuid.uuid4().hex[:14]}"
    signature = generate_razorpay_payment_signature(order_id, payment_id, secret=RAZORPAY_KEY_SECRET)

    checkout_data = {
        "order_id": order_id,
        "payment_id": payment_id,
        "signature": signature,
        "simulated_payment_id": payment_id,
        "simulated_signature": signature,
        "amount": price_inr * 100,
        "currency": "INR",
        "plan_id": req.plan_id,
        "billing_cycle": req.billing_cycle
    }

    return {
        "status": "success",
        "already_active": False,
        "message": f"Order created for {plan_info['name']}.",
        "order_id": order_id,
        "checkout": checkout_data,
        "user": get_full_user_profile(user_id)
    }


@router.post("/billing/verify")
def verify_payment(
    req: VerifyPaymentRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Cryptographically verify Razorpay payment HMAC-SHA256 signature and activate user entitlement."""
    user_id = current_user["id"] if current_user else "guest_user"
    order_id = req.order_id or req.razorpay_order_id or ""
    payment_id = req.payment_id or req.razorpay_payment_id or ""
    signature = req.signature or req.razorpay_signature or ""
    plan_id = req.plan_id or "plus"

    if plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid plan '{plan_id}'.")

    # Check if already active
    current_sub = get_user_subscription(user_id=user_id, db_path=DB_PATH)
    if current_sub.get("plan_id") == plan_id and current_sub.get("status") == "active":
        return {
            "status": "info",
            "already_active": True,
            "message": f"You already have the {SUBSCRIPTION_PLANS[plan_id]['name']} plan active.",
            "user": get_full_user_profile(user_id),
            "subscription": current_sub,
            "usage": get_user_usage(user_id, db_path=DB_PATH)
        }

    is_valid = verify_razorpay_payment_signature(
        order_id=order_id,
        payment_id=payment_id,
        signature=signature,
        secret=RAZORPAY_KEY_SECRET
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Signature mismatch."
        )

    update_user_subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="active",
        billing_cycle=req.billing_cycle,
        payment_id=payment_id,
        subscription_id=order_id,
        db_path=DB_PATH
    )

    fresh_user = get_full_user_profile(user_id)
    return {
        "status": "success",
        "already_active": False,
        "message": f"Payment verified. Entitlements for {SUBSCRIPTION_PLANS[plan_id]['name']} unlocked.",
        "user": fresh_user,
        "subscription": fresh_user["subscription"],
        "usage": fresh_user["usage"]
    }


@router.post("/billing/switch-plan")
def switch_plan(
    req: SwitchPlanRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Switch user subscription tier (Upgrade, Downgrade to Free, or Sandbox Switch)."""
    user_id = current_user["id"] if current_user else "guest_user"
    target_plan = req.target_plan or req.plan_id

    if not target_plan or target_plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan '{target_plan}'. Choose from: {list(SUBSCRIPTION_PLANS.keys())}"
        )

    current_sub = get_user_subscription(user_id=user_id, db_path=DB_PATH)
    if current_sub.get("plan_id") == target_plan and current_sub.get("status") == "active":
        return {
            "status": "info",
            "already_active": True,
            "message": f"You already have the {SUBSCRIPTION_PLANS[target_plan]['name']} plan active.",
            "user": get_full_user_profile(user_id),
            "subscription": current_sub,
            "usage": get_user_usage(user_id, db_path=DB_PATH)
        }

    # If switching to free (Downgrade)
    if target_plan == "free":
        update_user_subscription(
            user_id=user_id,
            plan_id="free",
            status="active",
            billing_cycle="monthly",
            db_path=DB_PATH
        )
        fresh_user = get_full_user_profile(user_id)
        return {
            "status": "success",
            "already_active": False,
            "message": "Successfully downgraded to Free Starter tier.",
            "user": fresh_user,
            "subscription": fresh_user["subscription"],
            "usage": fresh_user["usage"]
        }

    # For paid tiers in sandbox/test mode:
    success, msg, data = execute_test_sandbox_checkout(
        user_id=user_id,
        plan_id=target_plan,
        billing_cycle=req.billing_cycle,
        db_path=DB_PATH
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    fresh_user = get_full_user_profile(user_id)
    return {
        "status": "success",
        "already_active": False,
        "message": f"Successfully switched to {SUBSCRIPTION_PLANS[target_plan]['name']}!",
        "user": fresh_user,
        "subscription": fresh_user["subscription"],
        "usage": fresh_user["usage"]
    }


@router.post("/webhooks/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """Handle incoming Razorpay payment events with HMAC signature validation and idempotency."""
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header."
        )

    raw_body = await request.body()
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON webhook payload.")

    ok, msg = process_payment_webhook(
        event_payload=payload,
        raw_body_bytes=raw_body,
        signature=x_razorpay_signature,
        db_path=DB_PATH
    )

    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {"status": "success", "message": msg}
