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
    # Wenn Admin → immer Zugang
    if st.session_state.get("is_admin", False):
        return True

    if not HAS_STRIPE:
        return True  # Dev-Modus: immer durchlassen

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
        sess = stripe.checkout.Session.ret
