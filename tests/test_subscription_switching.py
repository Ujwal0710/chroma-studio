"""Comprehensive tests for subscription plan switching, verification, entitlements, and edge cases.

Covers:
- Upgrade (Free -> Plus -> Pro)
- Downgrade (Pro -> Free)
- Repeat purchase / switching to already active plan
- Failed payment signature rejection
- Expired plan fallback to Free at request time
- Plan change followed immediately by a quota-limited action
"""
import uuid
import datetime
from fastapi.testclient import TestClient
from backend.main import app
from modules.subscription_service import (
    get_user_subscription,
    update_user_subscription,
    record_usage_metric,
    check_entitlement
)
import sqlite3
from config.settings import DB_PATH

client = TestClient(app)


def register_and_login_user():
    uid = uuid.uuid4().hex[:8]
    email = f"plan_switch_{uid}@example.com"
    pwd = "SwitchPassword123!"
    
    reg = client.post("/auth/register", json={
        "email": email,
        "full_name": f"User {uid}",
        "password": pwd
    })
    assert reg.status_code == 201
    
    login = client.post("/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login.status_code == 200
    token = login.cookies.get("access_token")
    user_data = login.json()["user"]
    return email, token, user_data


def test_upgrade_and_downgrade_flow():
    email, token, user = register_and_login_user()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Initial plan is Free
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["plan_id"] == "free"
    
    # 2. Create order for Plus
    order_resp = client.post("/billing/order", json={"plan_id": "plus", "billing_cycle": "monthly"}, headers=headers)
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    assert order_data.get("already_active") is False
    assert "checkout" in order_data
    checkout = order_data["checkout"]
    
    # Confirm DB is still Free prior to verification
    sub_before = get_user_subscription(user["id"])
    assert sub_before["plan_id"] == "free"
    
    # Verify payment
    verify_resp = client.post("/billing/verify", json={
        "order_id": checkout["order_id"],
        "payment_id": checkout["payment_id"],
        "signature": checkout["signature"],
        "plan_id": "plus",
        "billing_cycle": "monthly"
    }, headers=headers)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "success"
    assert verify_data["user"]["plan_id"] == "plus"
    assert verify_data["user"]["subscription"]["plan_id"] == "plus"
    
    # Check /auth/me immediately reflects Plus without re-login
    me_resp2 = client.get("/auth/me", headers=headers)
    assert me_resp2.status_code == 200
    assert me_resp2.json()["user"]["plan_id"] == "plus"
    
    # 3. Upgrade Plus -> Pro via switch-plan
    switch_resp = client.post("/billing/switch-plan", json={"plan_id": "pro", "billing_cycle": "monthly"}, headers=headers)
    assert switch_resp.status_code == 200
    switch_data = switch_resp.json()
    assert switch_data["user"]["plan_id"] == "pro"
    
    # 4. Downgrade Pro -> Free
    down_resp = client.post("/billing/switch-plan", json={"plan_id": "free"}, headers=headers)
    assert down_resp.status_code == 200
    down_data = down_resp.json()
    assert down_data["status"] == "success"
    assert down_data["user"]["plan_id"] == "free"
    
    # Check /auth/me reflects Free
    me_resp3 = client.get("/auth/me", headers=headers)
    assert me_resp3.json()["user"]["plan_id"] == "free"


def test_repeat_purchase_already_active():
    email, token, user = register_and_login_user()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upgrade to Plus
    client.post("/billing/switch-plan", json={"plan_id": "plus"}, headers=headers)
    
    # Attempting to order Plus again returns already_active: True
    order_resp = client.post("/billing/order", json={"plan_id": "plus"}, headers=headers)
    assert order_resp.status_code == 200
    data = order_resp.json()
    assert data["already_active"] is True
    assert "active" in data["message"].lower()
    
    # Calling switch-plan with currently active plan also returns already_active: True
    switch_resp = client.post("/billing/switch-plan", json={"plan_id": "plus"}, headers=headers)
    assert switch_resp.status_code == 200
    s_data = switch_resp.json()
    assert s_data["already_active"] is True
    assert "active" in s_data["message"].lower()


def test_failed_payment_signature():
    email, token, user = register_and_login_user()
    headers = {"Authorization": f"Bearer {token}"}
    
    order_resp = client.post("/billing/order", json={"plan_id": "pro"}, headers=headers)
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    checkout = order_data["checkout"]
    
    # Tampered signature
    bad_verify = client.post("/billing/verify", json={
        "order_id": checkout["order_id"],
        "payment_id": checkout["payment_id"],
        "signature": "bad_tampered_signature_hex",
        "plan_id": "pro"
    }, headers=headers)
    
    assert bad_verify.status_code == 400
    assert "Signature mismatch" in bad_verify.json()["detail"]
    
    # Plan remains Free
    me = client.get("/auth/me", headers=headers)
    assert me.json()["user"]["plan_id"] == "free"


def test_expired_plan_fallback_to_free():
    email, token, user = register_and_login_user()
    user_id = user["id"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Set to Plus
    update_user_subscription(user_id, "plus")
    sub = get_user_subscription(user_id)
    assert sub["plan_id"] == "plus"
    assert sub["status"] == "active"
    
    # Manually expire the subscription in DB by backdating current_period_end
    past_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE user_subscriptions SET current_period_end = ? WHERE user_id = ?", (past_date, user_id))
    conn.commit()
    conn.close()
    
    # Requesting subscription or /auth/me should auto-detect expiry and downgrade to Free
    expired_sub = get_user_subscription(user_id)
    assert expired_sub["plan_id"] == "free"
    assert expired_sub["status"] == "expired"
    
    # Check /auth/me
    me = client.get("/auth/me", headers=headers)
    assert me.json()["user"]["plan_id"] == "free"
    
    # Entitlement limits should now be Free limits (3), not Plus (30)
    allowed, msg, meta = check_entitlement(user_id, "room_analysis")
    assert allowed is True
    assert meta["limit"] == 3


def test_plan_change_followed_immediately_by_quota_limited_action():
    email, token, user = register_and_login_user()
    user_id = user["id"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Exhaust Free quota (3 analyses)
    record_usage_metric(user_id, "analysis", amount=3)
    
    # Check entitlement - should be blocked
    allowed, msg, meta = check_entitlement(user_id, "room_analysis")
    assert not allowed
    assert "limit reached" in msg.lower()
    
    # 2. Upgrade to Plus without logging out
    switch_res = client.post("/billing/switch-plan", json={"plan_id": "plus"}, headers=headers)
    assert switch_res.status_code == 200
    assert switch_res.json()["user"]["plan_id"] == "plus"
    
    # 3. Immediately re-check entitlement - should be allowed now (limit is 30)
    allowed2, msg2, meta2 = check_entitlement(user_id, "room_analysis")
    assert allowed2 is True
    assert meta2["limit"] == 30
    assert meta2["used"] == 3
