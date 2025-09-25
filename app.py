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
        st.success("Admin-Modus: Gratiszugang ✔")

    # Nur wenn kein Admin
    if not st.session_state.get("is_admin", False):
        if HAS_STRIPE:
            email = st.text_input("E-Mail für Abo", "")
            if st.button("🔒 Abo abschließen"):
                url = create_checkout(email)
                if url:
                    st.markdown(f"[➡️ Zum Stripe-Checkout]({url})")
            st.caption("Nach erfolgreichem Checkout kommst du zurück – Zugang frei.")
        else:
            st.info("Dev-Modus: Keine Paywall aktiv.")


# --------- Inhalt ----------
subscribed = check_subscription_from_session()

# Eingabefeld immer anzeigen, wenn Admin oder subscribed
if subscribed or st.session_state.get("is_admin", False):
    st.subheader("Analyse")
    ticker = st.text_input("Ticker (z. B. AAPL, TSLA, RHM, PLTR)")
    if st.button("Analysieren"):
        if not ticker:
            st.warning("Bitte Ticker eingeben.")
        else:
            with st.spinner(f"Analysiere {ticker} …"):
                import yfinance as yf
                try:
                    data = yf.download(ticker, period="1mo", interval="1d", progress=False)
                    if data.empty:
                        st.warning("Kein Daten-Feed gefunden. Prüfe Ticker.")
                    else:
                        st.line_chart(data["Close"])
                        st.dataframe(data.tail().reset_index(), use_container_width=True)
                except Exception as e:
                    st.error(f"Fehler bei der Analyse: {e}")
else:
    st.info("Kein Zugang: Bitte Abo abschließen oder im Admin-Modus einloggen.")
