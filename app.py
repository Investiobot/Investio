import os
import time
import pandas as pd
import streamlit as st

# Optional: Stripe nur initialisieren, wenn Secrets vorhanden sind
HAS_STRIPE = all(k in st.secrets for k in ["STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "APP_BASE_URL"])
if HAS_STRIPE:
    import stripe
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

st.set_page_config(page_title="Investio – KI-Invest-Bot", layout="wide")
st.title("📊 Investio – KI-Investitions-Bot")

# --- Paywall / Abo-Check ---
def check_subscription_from_session():
    # Admin-Bypass: Gratiszugang
    if st.session_state.get("is_admin", False):
        return True

    if not HAS_STRIPE:
        st.info("Dev-Modus: Keine Paywall aktiv (Stripe-Secrets fehlen).")
        return True

    try:
        # FIX: neue API statt experimental_get_query_params
        q = st.query_params  # liefert ein Mapping[str, str]
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
