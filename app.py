import os
import pandas as pd
import streamlit as st

# ---------- Basis ----------
st.set_page_config(page_title="Investio – KI-Invest-Bot", layout="wide")
st.title("📊 Investio – KI-Investitions-Bot")

# Stripe nur initialisieren, wenn Secrets da sind
HAS_STRIPE = all(k in st.secrets for k in ["STRIPE_SECRET_KEY", "APP_BASE_URL", "STRIPE_PRICE_ID_MONTHLY", "STRIPE_PRICE_ID_YEARLY"])
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
    "Jährlich":  st.secrets.get("STRIPE_PRICE_ID_YEARLY"),
}

# ---------- Helpers ----------
def _is_admin(email: str) -> bool:
    return bool(email) and email.lower() == ADMIN_EMAIL

def _set_user(email: str, customer_id: str | None, subscribed: bool):
    st.session_state["user_email"] = email
    st.session_state["customer_id"] = customer_id
    st.session_state["subscribed"] = bool(subscribed)
    st.session_state["logged_in"] = True

def _clear_user():
    for k in ["user_email", "customer_id", "subscribed", "logged_in"]:
        st.session_state.pop(k, None)

def start_checkout(email: str, plan_label: str) -> str | None:
    if not HAS_STRIPE:
        st.error("Stripe ist nicht konfiguriert.")
        return None
    price_id = PRICE_IDS.get(plan_label)
    if not price_id:
        st.error("Preis-ID fehlt. Prüfe deine Secrets.")
        return None
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{APP_BASE_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=APP_BASE_URL,
            customer_email=email if email else None,
            allow_promotion_codes=True,
        )
        return session.url
    except Exception as e:
        st.error(f"Checkout-Fehler: {e}")
        return None


def open_billing_portal(customer_id: str) -> str | None:
    if not HAS_STRIPE or not customer_id:
        return None
    try:
        portal = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=BILLING_RETURN or APP_BASE_URL,
        )
        return portal.url
    except Exception as e:
        st.error(f"Billing-Portal-Fehler: {e}")
        return None

# ---------- Sidebar ----------
# ---------- Sidebar ----------
with st.sidebar:
    st.header("Konto")

    if not st.session_state.get("logged_in"):
        tab = st.radio("Zugang", ["Einloggen", "Registrieren"], horizontal=True)

        if tab == "Einloggen":
            email_login = st.text_input("E-Mail")
            if st.button("Einloggen"):
                if not email_login:
                    st.warning("E-Mail eingeben.")
                elif _is_admin(email_login):
                    _set_user(email_login, customer_id=None, subscribed=True)
                    st.success("Admin-Zugang (kostenlos) ✔")
                else:
                    st.warning("Bitte registrieren und Abo abschließen.")

        else:  # Registrieren
            reg_email = st.text_input("E-Mail für Registrierung")

    # Plan-Auswahl mit Preisen aus Secrets
            plans = {
                f"Monatlich – {st.secrets.get('STRIPE_PRICE_MONTHLY', '')}": "Monatlich",
                f"Jährlich – {st.secrets.get('STRIPE_PRICE_YEARLY', '')}": "Jährlich",
            }
            plan_label = st.selectbox("Abo wählen", list(plans.keys()))
            plan = plans[plan_label]

    if st.button("Registrieren & bezahlen"):
        if not reg_email:
            st.warning("E-Mail angeben.")
        elif _is_admin(reg_email):
            _set_user(reg_email, customer_id=None, subscribed=True)
            st.success("Admin-Zugang (kostenlos) ✔")
        else:
            url = start_checkout(reg_email, plan)
            if url:
                st.markdown(f"[➡️ Weiter zur Bezahlung bei Stripe]({url})")


    else:
        email = st.session_state.get("user_email", "")
        subscribed = bool(st.session_state.get("subscribed"))
        customer_id = st.session_state.get("customer_id")

        st.markdown(f"**Eingeloggt als:** {email or 'unbekannt'}")
        if _is_admin(email):
            st.success("Status: Admin (kostenlos)")
        elif subscribed:
            st.success("Status: Abo aktiv")
        else:
            st.warning("Status: Kein aktives Abo")

        if subscribed and customer_id:
            if st.button("Abo verwalten / kündigen"):
                portal_url = open_billing_portal(customer_id)
                if portal_url:
                    st.markdown(f"[➡️ Zum Abo-Portal]({portal_url})")

        if st.button("Abmelden"):
            _clear_user()
            st.experimental_rerun()


# ---------- Inhalt ----------
if st.session_state.get("logged_in"):
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
    st.info("Bitte einloggen oder registrieren, um Zugriff zu erhalten.")
