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

# --- Paywall / Abo-Check (MVP) ---
def check_subscription_from_session():
    if not HAS_STRIPE:
        st.info("Dev-Modus: Keine Paywall aktiv (Stripe-Secrets fehlen).")
        return True
    try:
        # Session-ID aus URL ziehen (?session_id=cs_test_...)
        q = st.experimental_get_query_params()
        sid = q.get("session_id", [None])[0]
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

subscribed = check_subscription_from_session()

# --- UI: Gate ---
with st.sidebar:
    st.header("Zugang")
    if subscribed:
        st.success("Abo aktiv ✔")
    else:
        if HAS_STRIPE:
            email = st.text_input("E-Mail für Abo (für Checkout-Vorbefüllung)", "")
            if st.button("🔒 Abo abschließen"):
                url = create_checkout(email)
                if url:
                    st.markdown(f"[➡️ Zum Stripe-Checkout]({url})")
                else:
                    st.error("Checkout konnte nicht erstellt werden.")
            st.caption("Nach erfolgreichem Checkout kommst du zurück – dann ist der Zugang frei.")
        else:
            st.warning("Stripe-Secrets fehlen. App läuft im **Dev-Modus** ohne Paywall.")

# --- App-Inhalt (nur zeigen, wenn frei) ---
if subscribed or not HAS_STRIPE:
    st.subheader("Analyse")
    ticker = st.text_input("Ticker (z. B. AAPL, TSLA, RHM, PLTR)")
    run = st.button("Analysieren")

    if run and ticker:
        with st.spinner(f"Analysiere {ticker} …"):
            # Dummy-Analyse (später durch deinen Bot ersetzen)
            import yfinance as yf
            try:
                data = yf.download(ticker, period="1mo", interval="1d", progress=False)
                if data.empty:
                    st.warning("Kein Daten-Feed gefunden. Prüfe Ticker.")
                else:
                    st.line_chart(data["Close"])
                    st.write("Letzte Zeilen:")
                    st.dataframe(data.tail().reset_index())
            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")
    elif run and not ticker:
        st.warning("Bitte Ticker eingeben.")
else:
    st.info("Schließe das Abo ab oder nutze Dev-Modus ohne Paywall (Stripe-Secrets fehlen).")


