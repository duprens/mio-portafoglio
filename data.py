import logging
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from streamlit_gsheets import GSheetsConnection

from security import enc, dec, extract_sheet_id, InvalidToken

logger = logging.getLogger("portafogli.data")

# Colonne nuove usate da QUESTO branch (cifrate con Fernet).
# Le colonne legacy "Link" / "Password" restano intoccate per la compatibilità
# con la versione main (SHA-256 + URL in chiaro).
LINK_COL = "LinkEnc"
PASS_COL = "PasswordHash"


@st.cache_resource
def _conn():
    return st.connection("gsheets", type=GSheetsConnection)


# ----- Rubrica -----

def load_rubrica() -> pd.DataFrame:
    df = _conn().read(worksheet="Rubrica", ttl=0)
    if df is None:
        return pd.DataFrame(columns=["Email", LINK_COL, PASS_COL])
    return df


def find_user(rubrica_df: pd.DataFrame, email: str):
    if rubrica_df is None or rubrica_df.empty or "Email" not in rubrica_df.columns:
        return None
    rows = rubrica_df[rubrica_df["Email"] == email]
    return rows.iloc[0] if not rows.empty else None


def get_user_password_hash(rubrica_df: pd.DataFrame, email: str):
    """Ritorna il blob cifrato Fernet della password (bcrypt) per la nuova colonna,
    oppure None se l'utente non è ancora stato migrato a questo branch."""
    row = find_user(rubrica_df, email)
    if row is None or PASS_COL not in row.index:
        return None
    val = row[PASS_COL]
    if pd.isna(val) or not str(val).strip():
        return None
    return str(val)


def link_conflict(rubrica_df: pd.DataFrame, sheet_id: str, current_email: str) -> bool:
    if rubrica_df.empty or LINK_COL not in rubrica_df.columns or "Email" not in rubrica_df.columns:
        return False
    for _, r in rubrica_df.iterrows():
        if pd.isna(r.get(LINK_COL)) or pd.isna(r.get("Email")):
            continue
        if str(r["Email"]) == current_email:
            continue
        try:
            existing = dec(str(r[LINK_COL]))
        except InvalidToken:
            continue
        if extract_sheet_id(existing) == sheet_id:
            return True
    return False


def upsert_user(rubrica_df: pd.DataFrame, email: str, link: str, hashed_pwd: str):
    """Aggiorna SOLO le colonne nuove (LinkEnc / PasswordHash). Le colonne legacy
    'Link' e 'Password' eventualmente presenti per quell'email vengono lasciate
    intatte, così il main branch continua a funzionare in parallelo."""
    enc_link, enc_pass = enc(link), enc(hashed_pwd)
    if LINK_COL not in rubrica_df.columns:
        rubrica_df[LINK_COL] = pd.NA
    if PASS_COL not in rubrica_df.columns:
        rubrica_df[PASS_COL] = pd.NA

    if not rubrica_df.empty and "Email" in rubrica_df.columns and email in rubrica_df["Email"].values:
        rubrica_df.loc[rubrica_df["Email"] == email, [LINK_COL, PASS_COL]] = [enc_link, enc_pass]
        out = rubrica_df
    else:
        nuova = pd.DataFrame([{"Email": email, LINK_COL: enc_link, PASS_COL: enc_pass}])
        out = pd.concat([rubrica_df, nuova], ignore_index=True)
    _conn().update(worksheet="Rubrica", data=out)


@st.cache_data(ttl=5)
def get_user_link(email: str):
    try:
        df = load_rubrica()
        row = find_user(df, email)
        if row is None or LINK_COL not in row.index:
            return None
        val = row[LINK_COL]
        if pd.isna(val) or not str(val).strip():
            return None
        try:
            return dec(str(val))
        except InvalidToken:
            logger.error("LinkEnc non decifrabile per %s", email)
            return None
    except Exception:
        logger.exception("Errore lettura link utente %s", email)
        return None


# ----- Portafogli -----

def save_portfolio(sheet_link: str, clienti_database: dict, date_inizio_clienti: dict):
    rows = []
    for cliente, portafoglio in clienti_database.items():
        data_in = date_inizio_clienti.get(cliente, "2024-01-01")
        if not portafoglio:
            rows.append({
                "Cliente": cliente, "Data_Inizio": data_in,
                "Strumento": None, "Ticker": None, "Quantità": 0, "PMC": 0,
                "Asset": None, "Area": None, "Valuta": None,
            })
        for item in portafoglio:
            rows.append({
                "Cliente": cliente, "Data_Inizio": data_in,
                "Strumento": item["Strumento"], "Ticker": item["Ticker"],
                "Quantità": item["Quantità"], "PMC": item["PMC"],
                "Asset": item["Asset"], "Area": item["Area"], "Valuta": item["Valuta"],
            })
    _conn().update(spreadsheet=sheet_link, worksheet="Portafogli", data=pd.DataFrame(rows))


def load_portfolio(sheet_link: str):
    try:
        df_u = _conn().read(spreadsheet=sheet_link, worksheet="Portafogli", ttl=0)
        if df_u.empty or "Cliente" not in df_u.columns:
            return {}, {}
        c_db, d_db = {}, {}
        for cliente in df_u["Cliente"].dropna().unique():
            df_c = df_u[df_u["Cliente"] == cliente]
            d_db[cliente] = str(df_c["Data_Inizio"].iloc[0])
            ptf = []
            for _, row in df_c.iterrows():
                if pd.isna(row["Ticker"]) or str(row["Ticker"]).strip() == "":
                    continue
                ptf.append({
                    "Strumento": str(row["Strumento"]),
                    "Ticker": str(row["Ticker"]),
                    "Quantità": float(row["Quantità"]),
                    "PMC": float(row["PMC"]),
                    "Asset": str(row["Asset"]),
                    "Area": str(row["Area"]),
                    "Valuta": str(row["Valuta"]),
                })
            c_db[cliente] = ptf
        return c_db, d_db
    except Exception:
        logger.exception("Errore load_portfolio")
        return {}, {}


# ----- Pricing -----

@st.cache_data(ttl=60)
def fetch_prices(tickers):
    prices = {}
    if not tickers:
        return prices
    try:
        data = yf.download(list(tickers), period="5d", progress=False)
        for ticker in tickers:
            if len(tickers) == 1:
                valid = data["Close"].dropna()
            else:
                valid = data["Close"][ticker].dropna()
            if not valid.empty:
                prices[ticker] = float(valid.iloc[-1])
    except Exception:
        logger.exception("Errore fetch_prices")
    return prices


@st.cache_data(ttl=3600)
def fetch_candele(tickers_list, portfolio_data, start_date, tf):
    try:
        data = yf.download(tickers_list, start=start_date, interval=tf, progress=False)
        df_c = pd.DataFrame(index=data.index).fillna(0)
        df_c["Open"], df_c["High"], df_c["Low"], df_c["Close"] = 0, 0, 0, 0
        for item in portfolio_data:
            t, q = item["Ticker"], item["Quantità"]
            if len(tickers_list) == 1:
                c_p = data["Close"].ffill().bfill()
                df_c["Open"]  += data["Open"].replace(0, np.nan).fillna(c_p) * q
                df_c["High"]  += data["High"].replace(0, np.nan).fillna(c_p) * q
                df_c["Low"]   += data["Low"].replace(0, np.nan).fillna(c_p) * q
                df_c["Close"] += c_p * q
            else:
                c_p = data["Close"][t].ffill().bfill()
                df_c["Open"]  += data["Open"][t].replace(0, np.nan).fillna(c_p) * q
                df_c["High"]  += data["High"][t].replace(0, np.nan).fillna(c_p) * q
                df_c["Low"]   += data["Low"][t].replace(0, np.nan).fillna(c_p) * q
                df_c["Close"] += c_p * q
        df_c.index = pd.to_datetime(df_c.index).normalize()
        return df_c
    except Exception:
        logger.exception("Errore fetch_candele")
        return None
