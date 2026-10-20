"""Unit tests for subscription plans, INR pricing, usage limits, and Razorpay HMAC verification."""
import pytest
import os
import tempfile
import json
import hmac
import hashlib

from config.settings import SUBSCRIPTION_PLANS, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from modules.subscription_service import (
    get_user_subscription,
    update_user_subscription,
    get_user_usage,
    record_usage_metric,
    check_entitlement,
    generate_razorpay_payment_signature,
    verify_razorpay_payment_signature,
    verify_razorpay_webhook_signature,
    process_payment_webhook,
    execute_test_sandbox_checkout
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


def test_subscription_plan_inr_definitions():
    assert "free" in SUBSCRIPTION_PLANS
    assert "plus" in SUBSCRIPTION_PLANS
    assert "pro" in SUBSCRIPTION_PLANS
    
    assert SUBSCRIPTION_PLANS["free"]["monthly_price_inr"] == 0
    assert SUBSCRIPTION_PLANS["plus"]["monthly_price_inr"] == 299
    assert SUBSCRIPTION_PLANS["pro"]["monthly_price_inr"] == 699
    
    # Check annual discount proposal is cheaper than 12 * monthly
    assert SUBSCRIPTION_PLANS["plus"]["annual_price_inr"] < 12 * 299
    assert SUBSCRIPTION_PLANS["pro"]["annual_price_inr"] < 12 * 699


def test_entitlement_and_quota_enforcement(temp_db):
    user_id = "test_user_quota_1"
    sub = get_user_subscription(user_id, db_path=temp_db)
    assert sub["plan_id"] == "free"
    
    # Free tier has 3 monthly analyses
    limit = SUBSCRIPTION_PLANS["free"]["monthly_analyses_limit"]
    assert limit == 3
    
    # 0 used -> allowed
    allowed, msg, meta = check_entitlement(user_id, "room_analysis", db_path=temp_db)
    assert allowed
    
    # Use up quota
    record_usage_metric(user_id, "analysis", amount=3, db_path=temp_db)
    usage = get_user_usage(user_id, db_path=temp_db)
    assert usage["analyses_used"] == 3
    
    # Exceeded -> blocked
    allowed, msg, meta = check_entitlement(user_id, "room_analysis", db_path=temp_db)
    assert not allowed
    assert "limit reached" in msg
    
    # Upgrade to Plus
    update_user_subscription(user_id, "plus", db_path=temp_db)
    # Now allowed again because Plus limit is 30
    allowed, msg, meta = check_entitlement(user_id, "room_analysis", db_path=temp_db)
    assert allowed


def test_razorpay_signature_verification():
    order_id = "order_123456789"
    payment_id = "pay_987654321"
    
    # Valid signature
    sig = generate_razorpay_payment_signature(order_id, payment_id, secret=RAZORPAY_KEY_SECRET)
    assert verify_razorpay_payment_signature(order_id, payment_id, sig, secret=RAZORPAY_KEY_SECRET) is True
    
    # Tampered signature
    assert verify_razorpay_payment_signature(order_id, payment_id, "tampered_signature_hex", secret=RAZORPAY_KEY_SECRET) is False
    # Tampered order
    assert verify_razorpay_payment_signature("order_tampered", payment_id, sig, secret=RAZORPAY_KEY_SECRET) is False


def test_idempotent_payment_webhook_processing(temp_db):
    user_id = "user_webhook_test_1"
    event_id = "evt_payment_captured_101"
    payload = {
        "id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_captured_001",
                    "notes": {
                        "user_id": user_id,
                        "plan_id": "plus",
                        "billing_cycle": "monthly"
                    }
                }
            }
        }
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(RAZORPAY_WEBHOOK_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    
    # First delivery
    ok1, msg1 = process_payment_webhook(payload, body_bytes, sig, db_path=temp_db)
    assert ok1
    assert "processed successfully" in msg1
    
    sub = get_user_subscription(user_id, db_path=temp_db)
    assert sub["plan_id"] == "plus"
    assert sub["status"] == "active"
    
    # Duplicate webhook delivery (Idempotency test)
    ok2, msg2 = process_payment_webhook(payload, body_bytes, sig, db_path=temp_db)
    assert ok2
    assert "idempotent" in msg2


def test_sandbox_checkout_execution(temp_db):
    user_id = "user_sandbox_test"
    ok, msg, meta = execute_test_sandbox_checkout(user_id, "pro", billing_cycle="annual", db_path=temp_db)
    assert ok
    assert meta["verified"] is True
    
    sub = get_user_subscription(user_id, db_path=temp_db)
    assert sub["plan_id"] == "pro"
    assert sub["billing_cycle"] == "annual"
    assert sub["status"] == "active"
