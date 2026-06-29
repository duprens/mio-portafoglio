import logging
import re
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


@st.cache_resource(show_spinner=False)
def _conn():
    return st.connection("gsheets", type=GSheetsConnection)


# ----- Rubrica -----

@st.cache_data(show_spinner=False)
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


@st.cache_data(ttl=5, show_spinner=False)
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


@st.cache_data(show_spinner=False)
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

@st.cache_data(ttl=60, show_spinner=False)
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


# ----- Movimenti (nuova fonte unica: scheda "Movimenti") -----

MOVIMENTI_WS = "Movimenti"


def _parse_num_it(val):
    """Converte un numero che può arrivare dal foglio in formato italiano
    (virgola decimale, punto migliaia) o internazionale. Esempi:
    '27,51'->27.51, '1.978'->1978, '1.978,50'->1978.5, '27.51'->27.51."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("\xa0", "").replace(" ", "")
    if not s:
        return np.nan
    if "," in s:                                    # virgola = decimale, punto = migliaia
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):   # solo punti raggruppati a 3 = migliaia
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def _cost_basis_step(ops_t: pd.DataFrame) -> pd.Series:
    """Serie del capitale investito (costo medio) di un ticker, con un valore per
    ogni data di operazione: cresce sugli acquisti, cala sulle vendite (le quote
    escono al costo medio). Usata per la linea 'a gradini' del grafico."""
    run_qty, cost = 0.0, 0.0
    recs = {}
    for _, r in ops_t.sort_values("Data").iterrows():
        q, p = float(r["Qty"]), float(r["Prezzo"])
        if q > 0:
            cost += q * p
            run_qty += q
        elif run_qty > 1e-9:
            avg = cost / run_qty
            cost += q * avg  # q negativo -> restituisce capitale
            run_qty += q
            if run_qty <= 1e-9:
                cost = 0.0
        recs[r["Data"]] = cost
    return pd.Series(recs, dtype=float).sort_index()


def _calcola_pmc(dft: pd.DataFrame) -> tuple[float, float]:
    """Costo medio ponderato (PMC) dalle operazioni di un singolo ticker,
    ordinate per data. Ogni acquisto aggiorna la media di carico; ogni vendita
    riduce le quantità ma NON cambia il PMC (le quote vendute escono al costo
    medio corrente). Ritorna (quantità_netta, pmc)."""
    run_qty, cost_basis = 0.0, 0.0
    for _, r in dft.iterrows():
        q, p = float(r["QtySigned"]), float(r["Prezzo"])
        if q > 0:  # acquisto
            cost_basis += q * p
            run_qty += q
        else:      # vendita: rimuove al costo medio corrente, PMC invariato
            if run_qty > 1e-9:
                avg = cost_basis / run_qty
                cost_basis += q * avg  # q è negativo -> riduce il monte costi
                run_qty += q
    pmc = (cost_basis / run_qty) if run_qty > 1e-9 else 0.0
    return run_qty, pmc


@st.cache_data(show_spinner=False)
def load_movimenti(sheet_link: str):
    """Legge la scheda 'Movimenti' (unica fonte) e ricostruisce:
      - clienti_database:   holdings correnti per cliente, con quantità netta e
                            PMC calcolato dal costo medio ponderato;
      - date_inizio_clienti: data inizio portafoglio per cliente;
      - operazioni_database: DataFrame operazioni per cliente (Ticker, Data, Qty
                            con segno) usato per ricostruire il grafico storico.
    Le posizioni interamente vendute (quantità netta 0) non compaiono nella
    tabella corrente ma restano nelle operazioni per la fedeltà del grafico."""
    try:
        df = _conn().read(spreadsheet=sheet_link, worksheet=MOVIMENTI_WS, ttl=0)
        if df is None or df.empty or "Cliente" not in df.columns:
            return {}, {}, {}

        df = df.copy()
        # dayfirst=True: le date arrivano come gg/mm/aaaa (formato italiano).
        df["Data Operazione"] = pd.to_datetime(df["Data Operazione"], errors="coerce", dayfirst=True).dt.normalize()
        df["Data Inizio"] = pd.to_datetime(df["Data Inizio"], errors="coerce", dayfirst=True)
        # Numeri robusti al formato italiano (virgola decimale / punto migliaia).
        df["Quantità"] = df["Quantità"].map(_parse_num_it)
        df["Prezzo"] = df["Prezzo"].map(_parse_num_it)

        # Segno robusto: vendita -> negativo, qualsiasi altra cosa -> positivo,
        # indipendentemente da come è scritta la quantità nel foglio.
        op = df["Operazione"].astype(str).str.strip().str.lower()
        df["QtySigned"] = np.where(op.eq("vendita"), -1.0, 1.0) * df["Quantità"].abs()

        c_db, d_db, ops_db = {}, {}, {}
        for cliente in df["Cliente"].dropna().unique():
            dfc = df[df["Cliente"] == cliente].dropna(subset=["Ticker", "Data Operazione", "QtySigned", "Prezzo"])
            if dfc.empty:
                continue

            di = dfc["Data Inizio"].min()
            if pd.isna(di):
                di = dfc["Data Operazione"].min()
            d_db[cliente] = di.strftime("%Y-%m-%d")

            ops_db[cliente] = (
                dfc[["Ticker", "Data Operazione", "QtySigned", "Prezzo"]]
                .rename(columns={"Data Operazione": "Data", "QtySigned": "Qty"})
                .reset_index(drop=True)
            )

            holdings = []
            for ticker in dfc["Ticker"].unique():
                dft = dfc[dfc["Ticker"] == ticker].sort_values("Data Operazione")
                net_qty, pmc = _calcola_pmc(dft)
                if net_qty <= 1e-9:  # posizione chiusa: fuori dal portafoglio attuale
                    continue
                last = dft.iloc[-1]
                holdings.append({
                    "Strumento": str(last["Strumento"]),
                    "Ticker": str(ticker),
                    "Quantità": float(net_qty),
                    "PMC": round(float(pmc), 4),
                    "Asset": str(last["Asset"]),
                    "Area": str(last["Area"]),
                    "Valuta": str(last["Valuta"]),
                })
            c_db[cliente] = holdings
        return c_db, d_db, ops_db
    except Exception:
        logger.exception("Errore load_movimenti")
        return {}, {}, {}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_candele_storico(ops_df, start_date, tf):
    """Ricostruisce le candele del controvalore di portafoglio usando le quantità
    REALMENTE detenute a ciascuna data (acquisti e vendite cumulati nel tempo),
    invece di proiettare all'indietro le quantità odierne. Nessuna conversione
    valutaria: gli strumenti sono quotati in EUR (come nel resto dell'app)."""
    try:
        if ops_df is None or len(ops_df) == 0:
            return None
        tickers_list = sorted(ops_df["Ticker"].dropna().unique().tolist())
        if not tickers_list:
            return None

        data = yf.download(tickers_list, start=start_date, interval=tf, progress=False)
        if data is None or data.empty:
            return None

        price_idx = data.index
        norm_idx = pd.DatetimeIndex(pd.to_datetime(price_idx).normalize())
        single = len(tickers_list) == 1

        has_price = "Prezzo" in ops_df.columns
        df_c = pd.DataFrame(index=price_idx)
        df_c["Open"], df_c["High"], df_c["Low"], df_c["Close"] = 0.0, 0.0, 0.0, 0.0
        df_c["Costo"] = 0.0  # capitale investito nel tempo (linea "a gradini")

        for t in tickers_list:
            ops_t = ops_df[ops_df["Ticker"] == t]
            cum = ops_t.groupby("Data")["Qty"].sum().sort_index().cumsum()
            if cum.empty:
                continue
            # Quantità detenuta a ciascuna data prezzo = ultimo cumulato con Data <= data prezzo
            full = cum.reindex(cum.index.union(norm_idx)).ffill().fillna(0.0)
            hold = full.reindex(norm_idx).fillna(0.0).values

            if single:
                cl = data["Close"].ffill().bfill()
                op_ = data["Open"].replace(0, np.nan).fillna(cl)
                hi = data["High"].replace(0, np.nan).fillna(cl)
                lo = data["Low"].replace(0, np.nan).fillna(cl)
            else:
                cl = data["Close"][t].ffill().bfill()
                op_ = data["Open"][t].replace(0, np.nan).fillna(cl)
                hi = data["High"][t].replace(0, np.nan).fillna(cl)
                lo = data["Low"][t].replace(0, np.nan).fillna(cl)

            df_c["Open"] += op_.values * hold
            df_c["High"] += hi.values * hold
            df_c["Low"] += lo.values * hold
            df_c["Close"] += cl.values * hold

            if has_price:
                steps = _cost_basis_step(ops_t)
                cfull = steps.reindex(steps.index.union(norm_idx)).ffill().fillna(0.0)
                df_c["Costo"] += cfull.reindex(norm_idx).fillna(0.0).values

        df_c.index = pd.to_datetime(df_c.index).normalize()
        return df_c
    except Exception:
        logger.exception("Errore fetch_candele_storico")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_performance(ops_df, start_date, tf):
    """Rendimento time-weighted (%) del portafoglio: neutralizza versamenti e
    prelievi, così la curva mostra solo come hanno reso gli strumenti e non i
    movimenti di capitale. Indice giornaliero concatenato (convenzione: il
    flusso del giorno avviene a fine seduta). Parte da 0%."""
    try:
        dati_c = fetch_candele_storico(ops_df, start_date, tf)
        if dati_c is None or dati_c.empty or "Prezzo" not in ops_df.columns:
            return None

        V = dati_c["Close"].astype(float).values
        price_dates = pd.DatetimeIndex(pd.to_datetime(dati_c.index).normalize())

        # Flusso di cassa per giorno = somma di Qty*Prezzo (acquisti +, vendite -).
        # Ogni flusso viene agganciato alla prima seduta di borsa >= data operazione,
        # coerentemente con quando le quantità entrano nel controvalore.
        cf = (ops_df["Qty"].astype(float) * ops_df["Prezzo"].astype(float))
        cf = cf.groupby(pd.to_datetime(ops_df["Data"]).dt.normalize()).sum()
        F = np.zeros(len(price_dates))
        for dt, amt in cf.items():
            pos = price_dates.searchsorted(dt)
            if pos < len(price_dates):
                F[pos] += float(amt)

        idx = np.ones(len(V))
        for t in range(1, len(V)):
            v0 = V[t - 1]
            r = ((V[t] - F[t]) / v0 - 1.0) if v0 > 1e-9 else 0.0
            idx[t] = idx[t - 1] * (1.0 + r)

        perf = pd.DataFrame(index=dati_c.index)
        perf["Perf"] = (idx - 1.0) * 100.0
        return perf
    except Exception:
        logger.exception("Errore fetch_performance")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
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
