import os
import time
import pandas as pd
import streamlit as st

# Stripe nur initialisieren, wenn Secrets vorhanden sind
HAS_STRIPE = all(k in st.secrets for k in ["STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "APP_BASE_URL"])
if HAS_STRIPE:
    import stripe
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

st.set_page_config(page_title="Investio – KI-Invest-Bot", layout="wide")
st.title("📊 Investio – KI-Investitions-Bot")

# --------- Subscription-Check ----------
def check_subscription_from_session():
    # Admin-Bypass
    if st.session_state.get("is_admin", False):
        return True

    if not HAS_STRIPE:
        return True  # Dev-Modus immer durchlassen

    try:
        q = st.query_params  # neue API
        sid = q.get("session_id", None)
        if not sid:
            return False
        sess = stripe.checkout.Session.retrieve(sid, expand=["subscription"])
        sub = sess.get("subscription")
        return bool(sub and sub.get("status") in ("active", "trialing"))
    except Exception:
        return False

def create_checkout(email: str):
    assert HAS_STRIPE, "Stripe nicht konfiguriert."
    price_id = st.secrets["STRIPE_PRICE_ID"]
    base = st.secrets["APP_BASE_URL"].rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{base}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=base,
            customer_email=email if email else None,
            allow_promotion_codes=True,
        )
        return session.url
    except Exception as e:
        st.error(f"Checkout-Fehler: {e}")
        return None

# --------- Sidebar ----------
with st.sidebar:
    st.header("Zugang")

    # Admin-Login
    admin_pw = st.text_input("Admin Login", type="password")
    if admin_pw and "ADMIN_PASS" in st.secrets and admin_pw == st.secrets["ADMIN_PASS"]:
        st.session_state["is_admin"] = True
