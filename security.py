import re
import logging
import streamlit as st
import bcrypt
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("portafogli.security")

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
SHEET_ID_RE = re.compile(r"/spreadsheets/d/([A-Za-z0-9_\-]+)")


@st.cache_resource
def _get_fernet() -> Fernet:
    key = st.secrets["ENCRYPTION_KEY"]
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def assert_encryption_key():
    try:
        _get_fernet()
    except Exception as e:
        st.error(
            "Configurazione mancante: ENCRYPTION_KEY non impostata in .streamlit/secrets.toml. "
            "Genera una chiave con `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` "
            "e aggiungila ai secrets."
        )
        logger.error("ENCRYPTION_KEY mancante o invalida: %s", e)
        st.stop()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def enc(s: str) -> str:
    return _get_fernet().encrypt(s.encode("utf-8")).decode("utf-8")


def dec(s: str) -> str:
    return _get_fernet().decrypt(s.encode("utf-8")).decode("utf-8")


def extract_sheet_id(url: str):
    m = SHEET_ID_RE.search(url or "")
    return m.group(1) if m else None


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def is_valid_sheets_link(link: str) -> bool:
    return (link or "").startswith("https://docs.google.com/spreadsheets/") and extract_sheet_id(link) is not None


__all__ = [
    "InvalidToken", "assert_encryption_key",
    "hash_password", "verify_password",
    "enc", "dec",
    "extract_sheet_id", "is_valid_email", "is_valid_sheets_link",
]
