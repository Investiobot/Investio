import os
import pandas as pd
import streamlit as st

# ---------- Basis ----------
st.set_page_config(page_title="Investio – KI-Invest-Bot", layout="wide")
st.title("📊 Investio – KI-Investitions-Bot")

# Stripe nur initialisieren, wenn Secrets da sind
HAS_STRIPE = all(
    k in st.secrets
    for k in ["STRIPE_SECRET_KEY", "APP_BASE_URL", "STRIPE_PRICE_ID_MONTHLY", "STRIPE_PRICE_ID_YEARLY"]
)
if HAS_STRIPE:
    import stripe
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
else:
    stripe = None

ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "").lower()
APP_BASE_URL = st.secrets.get("APP_BASE_URL", "").rstrip("/")
BILLING_RETURN = st.secrets.get("BILLING_PORTAL_RETURN_URL", APP_BASE_URL)

PRICE_IDS = {
    "Monatlich": st.secrets.get("STRIPE_PRICE_ID_MONTHLY"),
    "Jährlich": st.secrets.get("STRIPE_PRICE_ID_YEARLY"),
}

# ---------- Helpers ----------
def _is_admin(email: str) -> bool:
    return bool(email) and email.lower() == ADMIN_EMAIL


def _set_user(email: str, customer_id: str | None, subscribed: bool):
    st.session_state["user_email"] = email
    st.session_state["customer_id"] = customer_id
    st.session_state["subscribed"] = bool(subscribed)
    st.sessi
