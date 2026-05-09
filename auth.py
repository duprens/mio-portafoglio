import time
import logging
import streamlit as st

import data
from security import (
    InvalidToken,
    hash_password, verify_password, dec,
    extract_sheet_id, is_valid_email, is_valid_sheets_link,
)

logger = logging.getLogger("portafogli.auth")

SESSION_TIMEOUT_SECONDS = 30 * 60
_VOLATILE_KEYS = (
    "manual_email", "login_time",
    "db_caricato", "clienti_database", "date_inizio_clienti", "cliente_selezionato",
)


def _ensure_state():
    st.session_state.setdefault("manual_email", None)
    st.session_state.setdefault("registrazione_in_corso", False)
    st.session_state.setdefault("login_time", None)


def _clear_session():
    for k in _VOLATILE_KEYS:
        st.session_state.pop(k, None)
    st.cache_data.clear()


def _render_registration():
    st.title("Benvenuto 💎")
    st.markdown(f"Ciao **{st.session_state.reg_mail}**!")
    st.info("💡 Incolla il link del tuo Foglio Google privato.")

    new_link = st.text_input("Link Foglio Google:")
    if st.button("Collega Database", type="primary"):
        if not is_valid_sheets_link(new_link):
            st.error("Link non valido. Assicurati che sia un link di Google Sheets.")
            return
        new_sheet_id = extract_sheet_id(new_link)
        try:
            df_rubrica = data.load_rubrica()
            if data.link_conflict(df_rubrica, new_sheet_id, st.session_state.reg_mail):
                st.error("Questo foglio è già collegato ad un altro utente.")
                return
            data.upsert_user(df_rubrica, st.session_state.reg_mail, new_link, st.session_state.reg_pass)
            st.session_state.manual_email = st.session_state.reg_mail
            st.session_state.login_time = time.time()
            st.session_state.registrazione_in_corso = False
            st.cache_data.clear()
            st.rerun()
        except Exception:
            logger.exception("Errore salvataggio Rubrica per %s", st.session_state.reg_mail)
            st.error("Servizio temporaneamente non disponibile. Riprova fra qualche secondo.")


def _render_login():
    st.markdown("<br><br><h1 style='text-align: center;'>Monitoraggio Portafogli 📈</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Accesso Riservato</p><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            input_mail = st.text_input("Email", placeholder="es. nome.cognome@gmail.com")
            input_pass = st.text_input("Password", type="password")

            if st.button("Accedi", type="primary", width="stretch"):
                if not (input_mail and input_pass):
                    st.error("Inserisci Email e Password.")
                    return
                mail_pulita = input_mail.strip().lower()
                if not is_valid_email(mail_pulita):
                    st.error("Email non valida.")
                    return
                try:
                    df_rubrica = data.load_rubrica()
                    enc_hash = data.get_user_password_hash(df_rubrica, mail_pulita)
                    if enc_hash is not None:
                        try:
                            stored_hash = dec(enc_hash)
                        except InvalidToken:
                            logger.error("PasswordHash Rubrica non decifrabile per %s", mail_pulita)
                            st.error("Account non leggibile. Contatta l'amministratore.")
                            return
                        if verify_password(input_pass, stored_hash):
                            st.session_state.manual_email = mail_pulita
                            st.session_state.login_time = time.time()
                            st.rerun()
                        else:
                            st.error("Password errata.")
                    else:
                        # Utente assente sul branch nuovo: parte registrazione,
                        # che scriverà solo LinkEnc/PasswordHash. La riga legacy
                        # (se esiste) rimane intatta per il main.
                        st.session_state.registrazione_in_corso = True
                        st.session_state.reg_mail = mail_pulita
                        st.session_state.reg_pass = hash_password(input_pass)
                        st.rerun()
                except Exception:
                    logger.exception("Errore lettura Rubrica al login per %s", mail_pulita)
                    st.error("Servizio temporaneamente non disponibile. Riprova fra qualche secondo.")


def gate() -> str:
    """Blocca l'esecuzione finché l'utente non è autenticato. Ritorna l'email."""
    _ensure_state()

    if st.session_state.registrazione_in_corso:
        _render_registration()
        st.stop()

    if not st.session_state.manual_email:
        _render_login()
        st.stop()

    if st.session_state.get("login_time") is None:
        st.session_state.login_time = time.time()
    elif time.time() - st.session_state.login_time > SESSION_TIMEOUT_SECONDS:
        _clear_session()
        st.warning("Sessione scaduta. Accedi di nuovo.")
        st.rerun()

    return st.session_state.manual_email


def logout_button():
    st.sidebar.markdown('<div id="logout-btn-anchor" style="display:none"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Esci", width="stretch"):
        _clear_session()
        st.rerun()
