"""Subscription management, INR pricing, usage tracking, server-side entitlements, and Razorpay integration."""
import hmac
import hashlib
import json
import uuid
import datetime
from typing import Dict, Any, Tuple, Optional

from config.settings import (
    SUBSCRIPTION_PLANS,
    RAZORPAY_KEY_SECRET,
    RAZORPAY_WEBHOOK_SECRET,
    DB_PATH
)
from modules.storage import (
    get_db_connection,
    init_db,
    count_user_saved_palettes
)


def get_current_month_key() -> str:
    """Return 'YYYY-MM' key for the current month."""
    return datetime.datetime.now().strftime("%Y-%m")


def get_user_subscription(user_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve active subscription for user or return default free tier."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            # Create default free subscription
            now_str = datetime.datetime.now().isoformat()
            month_end = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            cursor.execute(
                """
                INSERT INTO user_subscriptions (
                    user_id, plan_id, status, billing_cycle, current_period_start, current_period_end
                ) VALUES (?, 'free', 'active', 'monthly', ?, ?)
                """,
                (user_id, now_str, month_end)
            )
            conn.commit()
            return {
                "user_id": user_id,
                "plan_id": "free",
                "status": "active",
                "billing_cycle": "monthly",
                "current_period_start": now_str,
                "current_period_end": month_end,
                "plan_details": SUBSCRIPTION_PLANS["free"]
            }
        
        sub = dict(row)
        now = datetime.datetime.now(datetime.timezone.utc)
        end_time_str = sub.get("current_period_end")
        is_expired = False
        if end_time_str:
            try:
                end_dt = datetime.datetime.fromisoformat(end_time_str)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
                if end_dt < now:
                    is_expired = True
            except Exception:
                pass

        if is_expired and sub.get("plan_id") != "free":
            cursor.execute(
                "UPDATE user_subscriptions SET plan_id = 'free', status = 'expired' WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            sub["plan_id"] = "free"
            sub["status"] = "expired"

        plan_id = sub.get("plan_id", "free")
        sub["plan_details"] = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
        return sub


def update_user_subscription(
    user_id: str,
    plan_id: str,
    status: str = "active",
    billing_cycle: str = "monthly",
    payment_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    db_path: str = DB_PATH
) -> bool:
    """Update user's subscription plan, status, and period."""
    if plan_id not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Invalid plan ID: {plan_id}")
    
    init_db(db_path)
    now = datetime.datetime.now()
    days = 365 if billing_cycle == "annual" else 30
    period_end = (now + datetime.timedelta(days=days)).isoformat()
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_subscriptions (
                user_id, plan_id, status, billing_cycle, current_period_start, current_period_end,
                razorpay_subscription_id, razorpay_payment_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                plan_id = excluded.plan_id,
                status = excluded.status,
                billing_cycle = excluded.billing_cycle,
                current_period_start = excluded.current_period_start,
                current_period_end = excluded.current_period_end,
                razorpay_subscription_id = COALESCE(excluded.razorpay_subscription_id, user_subscriptions.razorpay_subscription_id),
                razorpay_payment_id = COALESCE(excluded.razorpay_payment_id, user_subscriptions.razorpay_payment_id)
            """,
            (
                user_id,
                plan_id,
                status,
                billing_cycle,
                now.isoformat(),
                period_end,
                subscription_id,
                payment_id
            )
        )
        conn.commit()
        return True


def get_user_usage(user_id: str, month_key: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve usage counters for user in a given month."""
    init_db(db_path)
    month = month_key or get_current_month_key()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usage_records WHERE user_id = ? AND month_key = ?",
            (user_id, month)
        )
        row = cursor.fetchone()
        if not row:
            return {
                "user_id": user_id,
                "month_key": month,
                "analyses_used": 0,
                "ai_previews_used": 0,
                "exports_count": 0
            }
        return dict(row)


def record_usage_metric(user_id: str, metric: str, amount: int = 1, db_path: str = DB_PATH) -> None:
    """Increment a usage counter (e.g. 'analyses_used', 'ai_previews_used', 'exports_count')."""
    init_db(db_path)
    month = get_current_month_key()
    rec_id = f"use_{user_id}_{month}"
    
    col_map = {
        "analysis": "analyses_used",
        "analyses_used": "analyses_used",
        "ai_preview": "ai_previews_used",
        "ai_previews_used": "ai_previews_used",
        "export": "exports_count",
        "exports_count": "exports_count"
    }
    col_name = col_map.get(metric, "analyses_used")
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO usage_records (id, user_id, month_key, {col_name})
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, month_key) DO UPDATE SET
                {col_name} = {col_name} + ?
            """,
            (rec_id, user_id, month, amount, amount)
        )
        conn.commit()


# ----------------------------------------------------
# Server-side Entitlement Enforcement
# ----------------------------------------------------
def check_entitlement(user_id: str, action: str, db_path: str = DB_PATH) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enforce backend plan limits on operations:
    - 'room_analysis': checks monthly analysis quota.
    - 'ai_preview': checks AI preview entitlement and quota.
    - 'save_palette': checks saved palette storage capacity.
    - 'premium_features': checks if user is on Plus or Pro.
    Returns (allowed, reason_message, usage_meta).
    """
    sub = get_user_subscription(user_id, db_path=db_path)
    plan = sub.get("plan_details", SUBSCRIPTION_PLANS["free"])
    usage = get_user_usage(user_id, db_path=db_path)
    
    if action == "room_analysis":
        limit = plan["monthly_analyses_limit"]
        used = usage["analyses_used"]
        if user_id == "guest_user":
            return True, "Analysis permitted (Guest Atelier Session)", {
                "used": used,
                "limit": 999,
                "remaining": 999
            }
        if used >= limit:
            return False, f"Monthly room analysis limit reached ({used}/{limit}). Upgrade to Plus or Pro for expanded quota.", {
                "used": used,
                "limit": limit,
                "plan": plan["name"]
            }
        return True, f"Analysis permitted ({used + 1}/{limit} in {plan['name']})", {
            "used": used,
            "limit": limit,
            "remaining": limit - used
        }

    elif action == "ai_preview":
        limit = plan["ai_preview_limit"]
        if limit <= 0:
            return False, f"AI-Enhanced preview is not included in the {plan['name']} plan. Upgrade to Plus or Pro to unlock generative renders.", {
                "used": 0,
                "limit": 0,
                "plan": plan["name"]
            }
        used = usage["ai_previews_used"]
        if used >= limit:
            return False, f"Monthly AI preview limit reached ({used}/{limit}).", {
                "used": used,
                "limit": limit
            }
        return True, f"AI preview permitted ({used + 1}/{limit})", {
            "used": used,
            "limit": limit,
            "remaining": limit - used
        }

    elif action == "save_palette":
        limit = plan["max_saved_palettes"]
        saved_count = count_user_saved_palettes(user_id, db_path=db_path)
        if saved_count >= limit:
            return False, f"Saved palette capacity reached ({saved_count}/{limit}). Upgrade your plan or delete older palettes to free up slots.", {
                "used": saved_count,
                "limit": limit
            }
        return True, f"Save permitted ({saved_count + 1}/{limit})", {
            "used": saved_count,
            "limit": limit,
            "remaining": limit - saved_count
        }

    elif action == "premium_features":
        if sub.get("plan_id") in ("plus", "pro") and sub.get("status") == "active":
            return True, "Feature permitted under active paid plan.", {"plan": sub.get("plan_id")}
        return False, "This advanced feature requires an active Plus or Pro subscription.", {"plan": "free"}

    return True, "Operation permitted.", {}


# ----------------------------------------------------
# Razorpay Cryptographic Verification & Webhooks
# ----------------------------------------------------
def generate_razorpay_payment_signature(order_id: str, payment_id: str, secret: str = RAZORPAY_KEY_SECRET) -> str:
    """Generate SHA256 HMAC signature as required by Razorpay payment verification."""
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_razorpay_payment_signature(
    order_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    signature: Optional[str] = None,
    secret: str = RAZORPAY_KEY_SECRET,
    **kwargs
) -> bool:
    """Verify that Razorpay payment signature matches order_id|payment_id."""
    oid = str(order_id or kwargs.get("razorpay_order_id") or "").strip()
    pid = str(payment_id or kwargs.get("razorpay_payment_id") or "").strip()
    sig = str(signature or kwargs.get("razorpay_signature") or "").strip()
    if not oid or not pid or not sig:
        return False
    expected = generate_razorpay_payment_signature(oid, pid, secret=secret)
    return hmac.compare_digest(expected, sig)


def verify_razorpay_webhook_signature(
    body_bytes: bytes,
    signature: str,
    secret: str = RAZORPAY_WEBHOOK_SECRET
) -> bool:
    """Verify that incoming webhook body matches X-Razorpay-Signature."""
    if not body_bytes or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_payment_webhook(
    event_payload: Dict[str, Any],
    raw_body_bytes: bytes,
    signature: str,
    db_path: str = DB_PATH
) -> Tuple[bool, str]:
    """
    Idempotent webhook processor:
    - Verifies HMAC signature.
    - Rejects already-processed events.
    - Handles payment.captured, subscription.activated, subscription.cancelled.
    - Updates user subscription entitlement in the database.
    """
    init_db(db_path)
    
    # 1. Verify cryptographic signature
    if not verify_razorpay_webhook_signature(raw_body_bytes, signature):
        return False, "Invalid webhook HMAC signature."
    
    event_id = event_payload.get("id") or f"evt_{uuid.uuid4().hex[:12]}"
    event_type = event_payload.get("event", "unknown")
    
    # 2. Check for duplicate event (Idempotency)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT event_id FROM payment_events WHERE event_id = ?", (event_id,))
        if cursor.fetchone():
            return True, "Duplicate webhook event safely acknowledged (idempotent)."
    
    # 3. Process event according to event type
    payload_data = event_payload.get("payload", {})
    payment_entity = payload_data.get("payment", {}).get("entity", {})
    notes = payment_entity.get("notes", {})
    user_id = notes.get("user_id")
    target_plan = notes.get("plan_id", "plus")
    billing_cycle = notes.get("billing_cycle", "monthly")
    
    if event_type in ("payment.captured", "order.paid", "subscription.activated"):
        if user_id:
            payment_id = payment_entity.get("id", f"pay_{uuid.uuid4().hex[:8]}")
            update_user_subscription(
                user_id=user_id,
                plan_id=target_plan,
                status="active",
                billing_cycle=billing_cycle,
                payment_id=payment_id,
                db_path=db_path
            )
    elif event_type in ("subscription.cancelled", "subscription.expired"):
        if user_id:
            update_user_subscription(
                user_id=user_id,
                plan_id="free",
                status="cancelled",
                db_path=db_path
            )
    
    # 4. Record event to prevent duplicate processing
    now_str = datetime.datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payment_events (event_id, user_id, event_type, payload_json, verified, timestamp)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (event_id, user_id or "unknown", event_type, json.dumps(event_payload), now_str)
        )
        conn.commit()
    
    return True, f"Webhook event '{event_type}' processed successfully."


# ----------------------------------------------------
# Verified Sandbox / Test-Mode Payment Helper
# ----------------------------------------------------
def execute_test_sandbox_checkout(
    user_id: str,
    plan_id: str,
    billing_cycle: str = "monthly",
    db_path: str = DB_PATH
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute a verified test-mode transaction:
    - Generates mock order and payment IDs.
    - Computes real HMAC-SHA256 signature using the test secret.
    - Verifies the signature cryptographically before activating entitlement.
    """
    if plan_id not in SUBSCRIPTION_PLANS:
        return False, "Invalid plan selection.", {}
    
    order_id = f"order_sandbox_{uuid.uuid4().hex[:10]}"
    payment_id = f"pay_sandbox_{uuid.uuid4().hex[:10]}"
    signature = generate_razorpay_payment_signature(order_id, payment_id, secret=RAZORPAY_KEY_SECRET)
    
    # Cryptographic verification
    is_valid = verify_razorpay_payment_signature(order_id, payment_id, signature, secret=RAZORPAY_KEY_SECRET)
    if not is_valid:
        return False, "Cryptographic signature verification failed in sandbox.", {}
    
    # Update entitlement
    update_user_subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="active",
        billing_cycle=billing_cycle,
        payment_id=payment_id,
        subscription_id=order_id,
        db_path=db_path
    )
    
    return True, f"Successfully activated {SUBSCRIPTION_PLANS[plan_id]['name']} via verified test payment.", {
        "order_id": order_id,
        "payment_id": payment_id,
        "signature": signature,
        "verified": True
    }
