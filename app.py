import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURAZIONE E STILI CSS (LA BIBBIA)
# ==========================================
st.set_page_config(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

st.markdown(
    """
    <style>
    .stAppDeployButton {display:none;}
    
    /* ==========================================
       ESORCISMO UNIVERSALE DEL ROSSO
       ========================================== */
    :root, .stApp {
        --primary-color: #555555 !important;
        --focus-ring-color: transparent !important;
    }

    * {
        -webkit-tap-highlight-color: transparent !important;
        transition: none !important; 
    }

    /* Tasti Primary (Attivi/Selezionati) -> GRIGIO SCURO */
    button[kind="primary"] {
        background-color: #555555 !important;
        border-color: #555555 !important;
        color: white !important; 
    }
    button[kind="primary"]:hover, 
    button[kind="primary"]:focus, 
    button[kind="primary"]:active {
        background-color: #666666 !important;
        border-color: #555555 !important;
        color: white !important;
        box-shadow: none !important;
    }

    /* Tasti Secondary (Inattivi/Normali) -> GRIGIO CHIARO SU HOVER */
    button[kind="secondary"]:focus, 
    button[kind="secondary"]:active {
        border-color: rgba(130, 130, 130, 0.4) !important;
        box-shadow: none !important;
        color: white !important;
    }
    button[kind="secondary"]:hover {
        background-color: rgba(130, 130, 130, 0.25) !important;
        border-color: rgba(130, 130, 130, 0.4) !important;
        color: white !important;
    }
    
    /* Stili Sidebar Grigia */
    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="primary"]:focus,
    section[data-testid="stSidebar"] button[kind="primary"]:active {
        background-color: rgba(130, 130, 130, 0.15) !important;
        border-color: rgba(130, 130, 130, 0.3) !important;
        color: inherit !important; 
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: rgba(130, 130, 130, 0.25) !important;
        border-color: rgba(130, 130, 130, 0.4) !important;
    }

    /* Tastini + e - Soglia Ribilanciamento */
    [data-testid="stNumberInputStepUp"]:hover, 
    [data-testid="stNumberInputStepDown"]:hover,
    [data-testid="stNumberInputStepUp"]:focus, 
    [data-testid="stNumberInputStepDown"]:focus {
        background-color: rgba(130, 130, 130, 0.25) !important;
        color: inherit !important;
    }

    /* ==========================================
       LA PILLOLA PERFETTA (ANTI-OCCHIALI)
       ========================================== */
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) {
        gap: 0px !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1),
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) {
        width: 36px !important;
        min-width: 36px !important;
        max-width: 36px !important;
        flex: none !important;
        padding: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button {
        min-height: 28px !important;
        height: 28px !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 0 !important; 
        font-size: 13px !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1) button {
        border-top-left-radius: 6px !important;
        border-bottom-left-radius: 6px !important;
        border-right: none !important; 
    }
    
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) button {
        border-top-right-radius: 6px !important;
        border-bottom-right-radius: 6px !important;
    }
    
    span#pill-anchor { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. GESTIONE DATABASE GOOGLE SHEETS E MIGRAZIONE
# ==========================================
user_email = "Admin_Studio" 
try:
    if hasattr(st, "user") and st.user.email: user_email = st.user.email
    elif hasattr(st, "experimental_user") and st.experimental_user.email: user_email = st.experimental_user.email
except: pass

conn = st.connection("gsheets", type=GSheetsConnection)

# La tua Bibbia originale per il popolamento iniziale
db_iniziale = {
    "Vera Interlandi": [
        {"Strumento": "Bitwise Core Bitcoin ETP", "Ticker": "BTC1.DE", "Quantità": 235, "PMC": 6.38, "Asset": "Crypto", "Area": "Globale", "Valuta": "Altro"},
        {"Strumento": "iShares Core MSCI EM IMI", "Ticker": "IS3N.DE", "Quantità": 48, "PMC": 41.64, "Asset": "Azionario", "Area": "Emergenti", "Valuta": "Altro"},
        {"Strumento": "WisdomTree Global Efficient Core", "Ticker": "NTSG.DE", "Quantità": 248, "PMC": 26.18, "Asset": "Bilanciato", "Area": "Globale", "Valuta": "USD"}
    ],
    "Mauro Barzanò": [
        {"Strumento": "iShares Core S&P 500", "Ticker": "SXR8.DE", "Quantità": 8, "PMC": 394.47, "Asset": "Azionario", "Area": "USA", "Valuta": "USD"},
        {"Strumento": "iShares Core MSCI EM IMI", "Ticker": "IS3N.DE", "Quantità": 95, "PMC": 41.83, "Asset": "Azionario", "Area": "Emergenti", "Valuta": "Altro"},
        {"Strumento": "Xtrackers Euro Stoxx 50", "Ticker": "XESC.DE", "Quantità": 39, "PMC": 101.04, "Asset": "Azionario", "Area": "Europa", "Valuta": "EUR"},
        {"Strumento": "Invesco Physical Gold ETC", "Ticker": "8PSG.DE", "Quantità": 5, "PMC": 160.19, "Asset": "Commodity", "Area": "Globale", "Valuta": "USD"},
        {"Strumento": "Xtrackers II EUR Overnight Rate", "Ticker": "XEON.DE", "Quantità": 13, "PMC": 148.66, "Asset": "Monetario", "Area": "Europa", "Valuta": "EUR"}, 
        {"Strumento": "Xtrackers II Eurozone Gov. Bond", "Ticker": "DBXQ.DE", "Quantità": 14, "PMC": 206.37, "Asset": "Obbligazionario", "Area": "Europa", "Valuta": "EUR"}
    ],
    "Giorgio Seregni": [
        {"Strumento": "WisdomTree Physical Bitcoin", "Ticker": "WBTC.PA", "Quantità": 140, "PMC": 18.20, "Asset": "Crypto", "Area": "Globale", "Valuta": "Altro"}, 
        {"Strumento": "iShares Core MSCI EM IMI", "Ticker": "IS3N.DE", "Quantità": 102, "PMC": 38.56, "Asset": "Azionario", "Area": "Emergenti", "Valuta": "Altro"},
        {"Strumento": "Xtrackers Euro Stoxx 50", "Ticker": "XESC.DE", "Quantità": 71, "PMC": 98.44, "Asset": "Azionario", "Area": "Europa", "Valuta": "EUR"},
        {"Strumento": "SPDR S&P 500 UCITS ETF Acc", "Ticker": "SP5A.MI", "Quantità": 779, "PMC": 14.13, "Asset": "Azionario", "Area": "USA", "Valuta": "USD"}, 
        {"Strumento": "WisdomTree Core Physical Gold", "Ticker": "WGLD.MI", "Quantità": 4, "PMC": 318.25, "Asset": "Commodity", "Area": "Globale", "Valuta": "USD"}, 
        {"Strumento": "Franklin Euro Short Maturity", "Ticker": "FLESA.MI", "Quantità": 361, "PMC": 27.47, "Asset": "Monetario", "Area": "Europa", "Valuta": "EUR"}, 
        {"Strumento": "Xtrackers II Eurozone Gov. Bond", "Ticker": "X57E.DE", "Quantità": 25, "PMC": 234.06, "Asset": "Obbligazionario", "Area": "Europa", "Valuta": "EUR"},
        {"Strumento": "VanEck GL. Fallen Angel HY Bd", "Ticker": "GFEA.DE", "Quantità": 47, "PMC": 62.32, "Asset": "Obbligazionario", "Area": "Globale", "Valuta": "Altro"} 
    ],
    "Giulia Gavotto": [
        {"Strumento": "Amundi FTSE EPRA NAREIT Global", "Ticker": "EPRA.MI", "Quantità": 40, "PMC": 63.77, "Asset": "Immobiliare", "Area": "Globale", "Valuta": "Altro"},
        {"Strumento": "AXA IM Nasdaq 100", "Ticker": "ANAU.MI", "Quantità": 162, "PMC": 18.84, "Asset": "Azionario", "Area": "USA", "Valuta": "USD"},
        {"Strumento": "Invesco MSCI World EW", "Ticker": "MWEQ.MI", "Quantità": 965, "PMC": 5.18, "Asset": "Azionario", "Area": "Globale", "Valuta": "USD"},
        {"Strumento": "Xtrackers Euro Stoxx 50", "Ticker": "XESC.DE", "Quantità": 51, "PMC": 98.26, "Asset": "Azionario", "Area": "Europa", "Valuta": "EUR"},
        {"Strumento": "SPDR S&P 500 UCITS ETF", "Ticker": "SP5A.MI", "Quantità": 353, "PMC": 14.29, "Asset": "Azionario", "Area": "USA", "Valuta": "USD"},
        {"Strumento": "iShares Core MSCI EM IMI", "Ticker": "IS3N.DE", "Quantità": 133, "PMC": 37.81, "Asset": "Azionario", "Area": "Emergenti", "Valuta": "Altro"},
        {"Strumento": "WisdomTree Physical Silver", "Ticker": "PHAG.MI", "Quantità": 66, "PMC": 39.85, "Asset": "Commodity", "Area": "Globale", "Valuta": "USD"},
        {"Strumento": "WisdomTree Core Physical Gold", "Ticker": "WGLD.MI", "Quantità": 9, "PMC": 341.24, "Asset": "Commodity", "Area": "Globale", "Valuta": "USD"},
        {"Strumento": "Franklin Euro Short Maturity", "Ticker": "FLESA.MI", "Quantità": 1978, "PMC": 27.51, "Asset": "Monetario", "Area": "Europa", "Valuta": "EUR"}, 
        {"Strumento": "SPDR Blackstone Euro AAA CLO", "Ticker": "ECLO.MI", "Quantità": 120, "PMC": 25.10, "Asset": "Obbligazionario", "Area": "Europa", "Valuta": "EUR"}, 
        {"Strumento": "AXA IM US High Yield Opp", "Ticker": "AHYU.MI", "Quantità": 292, "PMC": 10.30, "Asset": "Obbligazionario", "Area": "USA", "Valuta": "USD"},
        {"Strumento": "iShares Treasury Bond 3-7yr", "Ticker": "CSBGU7.MI", "Quantità": 25, "PMC": 122.60, "Asset": "Obbligazionario", "Area": "USA", "Valuta": "USD"},
        {"Strumento": "Xtrackers Eurozone Gov. Bond", "Ticker": "X57E.DE", "Quantità": 21, "PMC": 235.03, "Asset": "Obbligazionario", "Area": "Europa", "Valuta": "EUR"}
    ]
}
date_iniziali = {"Giorgio Seregni": "2025-09-29", "Giulia Gavotto": "2025-10-10", "Vera Interlandi": "2026-03-17", "Mauro Barzanò": "2026-03-18"}

def salva_db():
    rows = []
    for cliente, portafoglio in st.session_state.clienti_database.items():
        data_in = st.session_state.date_inizio_clienti.get(cliente, "2024-01-01")
        if not portafoglio:
            rows.append({'Email': user_email, 'Cliente': cliente, 'Data_Inizio': data_in, 'Strumento': None, 'Ticker': None, 'Quantità': 0, 'PMC': 0, 'Asset': None, 'Area': None, 'Valuta': None})
        for item in portafoglio:
            rows.append({
                'Email': user_email, 'Cliente': cliente, 'Data_Inizio': data_in,
                'Strumento': item['Strumento'], 'Ticker': item['Ticker'], 'Quantità': item['Quantità'],
                'PMC': item['PMC'], 'Asset': item['Asset'], 'Area': item['Area'], 'Valuta': item['Valuta']
            })
    df_new = pd.DataFrame(rows)
    try:
        df_all = conn.read(worksheet="Portafogli", ttl=0)
        if not df_all.empty and 'Email' in df_all.columns:
            df_others = df_all[df_all['Email'] != user_email]
            df_final = pd.concat([df_others, df_new], ignore_index=True)
        else: df_final = df_new
    except: df_final = df_new
    conn.update(worksheet="Portafogli", data=df_final)

def carica_db():
    try:
        df_all = conn.read(worksheet="Portafogli", ttl=0)
        if df_all.empty or 'Email' not in df_all.columns: raise ValueError("Vuoto")
        df_user = df_all[df_all['Email'] == user_email]
        if df_user.empty: raise ValueError("Nessun dato utente")
        
        c_db, d_db = {}, {}
        for cliente in df_user['Cliente'].dropna().unique():
            if not cliente: continue
            df_c = df_user[df_user['Cliente'] == cliente]
            d_db[cliente] = str(df_c['Data_Inizio'].iloc[0])
            ptf = []
            for _, row in df_c.iterrows():
                if pd.isna(row['Ticker']) or str(row['Ticker']).strip() == "": continue
                ptf.append({
                    "Strumento": str(row['Strumento']), "Ticker": str(row['Ticker']),
                    "Quantità": float(row['Quantità']), "PMC": float(row['PMC']),
                    "Asset": str(row['Asset']), "Area": str(row['Area']), "Valuta": str(row['Valuta'])
                })
            c_db[cliente] = ptf
        return {"portafogli": c_db, "date_inizio": d_db}
    except:
        st.session_state.must_seed = True
        return {"portafogli": db_iniziale.copy(), "date_inizio": date_iniziali.copy()}

if 'db_caricato' not in st.session_state:
    dati = carica_db()
    st.session_state.clienti_database = dati["portafogli"]
    st.session_state.date_inizio_clienti = dati["date_inizio"]
    st.session_state.db_caricato = True
    if st.session_state.get('must_seed', False):
        salva_db()
        st.session_state.must_seed = False

if 'cliente_selezionato' not in st.session_state:
    lista_cl = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = lista_cl[0] if lista_cl else ""

if 'timeframe_scelta' not in st.session_state:
    st.session_state.timeframe_scelta = "D"

# ==========================================
# 3. MOTORE PREZZI
# ==========================================
tutti_i_tickers = set()
for pt in st.session_state.clienti_database.values():
    for item in pt:
        tutti_i_tickers.add(item["Ticker"])

@st.cache_data(ttl=60)
def scarica_prezzi_globali(tickers):
    prices = {}
    if not tickers: return prices
    try:
        data = yf.download(list(tickers), period="5d", progress=False)
        for ticker in tickers:
            if len(tickers) == 1:
                valid_data = data['Close'].dropna()
            else:
                valid_data = data['Close'][ticker].dropna()
            if not valid_data.empty: prices[ticker] = float(valid_data.iloc[-1])
    except: pass
    return prices

prezzi_aggiornati = scarica_prezzi_globali(tutti_i_tickers)

# ==========================================
# 4. SIDEBAR CON LISTA, NUOVO E ELIMINA
# ==========================================
st.sidebar.markdown("<h2 style='margin-top: 0px; margin-bottom: 0px; font-size: 1.8rem; font-weight: 700;'>Portafogli Clienti</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(130,130,130,0.3);'>", unsafe_allow_html=True)

for nome in sorted(st.session_state.clienti_database.keys(), key=lambda x: x.split()[-1]):
    valore_tot = sum(prezzi_aggiornati.get(i["Ticker"], i["PMC"]) * i["Quantità"] for i in st.session_state.clienti_database[nome])
    costo_tot = sum(i["PMC"] * i["Quantità"] for i in st.session_state.clienti_database[nome])
    var_p = ((valore_tot - costo_tot) / costo_tot * 100) if costo_tot > 0 else 0
    stile = "primary" if st.session_state.cliente_selezionato == nome else "secondary"
    
    if st.sidebar.button(f"{nome}  |  {var_p:+.2f}%", width="stretch", type=stile):
        st.session_state.cliente_selezionato = nome
        st.session_state.timeframe_scelta = "D"
        st.rerun()

st.sidebar.divider()

# Aggiunta Nuovo Cliente
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_nome = st.text_input("Nome Cliente")
    nc_data = st.date_input("Data Inizio Portafoglio")
    if st.button("Crea Cliente", width="stretch", type="primary"):
        if nc_nome and nc_nome not in st.session_state.clienti_database:
            st.session_state.clienti_database[nc_nome] = []
            st.session_state.date_inizio_clienti[nc_nome] = nc_data.strftime("%Y-%m-%d")
            salva_db()
            st.session_state.cliente_selezionato = nc_nome
            st.rerun()

# Eliminazione Cliente Esistente
if st.session_state.cliente_selezionato in st.session_state.clienti_database:
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        st.markdown(f"Rimuovere **{st.session_state.cliente_selezionato}**?")
        if st.button("Elimina", width="stretch", type="primary"):
            cliente_da_eliminare = st.session_state.cliente_selezionato
            del st.session_state.clienti_database[cliente_da_eliminare]
            if cliente_da_eliminare in st.session_state.date_inizio_clienti:
                del st.session_state.date_inizio_clienti[cliente_da_eliminare]
            salva_db()
            rimanenti = list(st.session_state.clienti_database.keys())
            st.session_state.cliente_selezionato = rimanenti[0] if rimanenti else ""
            st.rerun()

# ==========================================
# GESTIONE SCHERMATA VUOTA
# ==========================================
if st.session_state.cliente_selezionato == "":
    st.info("Nessun cliente presente nel database. Aggiungine uno dalla barra laterale sinistra.")
else:
    portafoglio_cliente = st.session_state.clienti_database[st.session_state.cliente_selezionato]
    data_inizio_selezionata = st.session_state.date_inizio_clienti.get(st.session_state.cliente_selezionato, "2024-01-01")

    # ==========================================
    # 5. HEADER E METRICHE
    # ==========================================
    col_t, col_b = st.columns([0.85, 0.15])
    with col_t: st.title(f"📈 {st.session_state.cliente_selezionato}")
    with col_b:
        st.write("")
        if st.button("Aggiorna Prezzi", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    portafoglio_elaborato = []
    costo_totale_pmc = 0 
    totale_controvalore = 0
    for item in portafoglio_cliente:
        new_item = item.copy()
        px = prezzi_aggiornati.get(item["Ticker"], 0)
        cost_basis = item["Quantità"] * item["PMC"]
        cv = px * item["Quantità"]
        costo_totale_pmc += cost_basis
        totale_controvalore += cv
        new_item["Ultimo Prezzo"] = round(px, 2)
        new_item["Controvalore"] = round(cv, 2)
        new_item["Var. €"] = round(cv - cost_basis, 2)
        new_item["Var. %"] = round(((px - item["PMC"]) / item["PMC"] * 100), 2) if item["PMC"] > 0 else 0
        portafoglio_elaborato.append(new_item)

    df = pd.DataFrame(portafoglio_elaborato)
    if not df.empty:
        df["Peso %"] = round((df["Controvalore"] / totale_controvalore * 100), 2) if totale_controvalore > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitale Investito", f"{costo_totale_pmc:,.2f} €")
    c2.metric("Controvalore Totale", f"{totale_controvalore:,.2f} €")
    v_euro = totale_controvalore - costo_totale_pmc
    v_perc = (v_euro / costo_totale_pmc * 100) if costo_totale_pmc > 0 else 0
    col_e = "#00c853" if v_euro > 0 else "#ff4b4b"
    c3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione Totale (€)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_euro:,.2f} €</div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione Totale (%)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_perc:.2f}%</div>', unsafe_allow_html=True)

    # ==========================================
    # 6. LA custom "PILLOLA" (D & W) E GRAFICO
    # ==========================================
    st.divider()
    col_d, col_w, col_vuota = st.columns([1, 1, 20])
    tf = st.session_state.timeframe_scelta
    with col_d:
        if st.button("D", type="primary" if tf == "D" else "secondary", width="stretch"):
            st.session_state.timeframe_scelta = "D"; st.rerun()
    with col_w:
        if st.button("W", type="primary" if tf == "W" else "secondary", width="stretch"):
            st.session_state.timeframe_scelta = "W"; st.rerun()
    with col_vuota:
        st.markdown('<span id="pill-anchor"></span>', unsafe_allow_html=True)

    mappa_tf = {"D": "1d", "W": "1wk"}
    tf_da_usare = mappa_tf.get(tf, "1d")

    @st.cache_data(ttl=3600)
    def calcola_candele(tickers_list, portfolio_data, start_date, tf):
        try:
            data = yf.download(tickers_list, start=start_date, interval=tf, progress=False)
            df_c = pd.DataFrame(index=data.index).fillna(0)
            df_c['Open'], df_c['High'], df_c['Low'], df_c['Close'] = 0, 0, 0, 0
            for item in portfolio_data:
                t, q = item["Ticker"], item["Quantità"]
                if len(tickers_list) == 1:
                    c_p = data['Close'].ffill().bfill()
                    df_c['Open'] += data['Open'].replace(0, np.nan).fillna(c_p) * q
                    df_c['High'] += data['High'].replace(0, np.nan).fillna(c_p) * q
                    df_c['Low'] += data['Low'].replace(0, np.nan).fillna(c_p) * q
                    df_c['Close'] += c_p * q
                else:
                    c_p = data['Close'][t].ffill().bfill()
                    df_c['Open'] += data['Open'][t].replace(0, np.nan).fillna(c_p) * q
                    df_c['High'] += data['High'][t].replace(0, np.nan).fillna(c_p) * q
                    df_c['Low'] += data['Low'][t].replace(0, np.nan).fillna(c_p) * q
                    df_c['Close'] += c_p * q
            df_c.index = pd.to_datetime(df_c.index).normalize()
            return df_c
        except: return None

    if not df.empty:
        dati_c = calcola_candele(list(set(i["Ticker"] for i in portafoglio_cliente)), portafoglio_cliente, data_inizio_selezionata, tf_da_usare)
        if dati_c is not None:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=dati_c.index, open=dati_c['Open'], high=dati_c['High'], low=dati_c['Low'], close=dati_c['Close'], 
                increasing_line_color='#00c853', decreasing_line_color='#ff4b4b', increasing_line_width=1, decreasing_line_width=1, 
                hovertemplate='Data: %{x|%d %b %Y}<br>Open: %{open:.2f}<br>High: %{high:.2f}<br>Low: %{low:.2f}<br>Close: %{close:.2f}<extra></extra>'
            ))
            fig.add_trace(go.Scatter(x=dati_c.index, y=[costo_totale_pmc]*len(dati_c), mode='lines', line=dict(color='rgba(150, 150, 150, 0.5)', width=2, dash='dash'), hoverinfo='skip'))
            fig.update_yaxes(autorange=True, fixedrange=False)
            fig.update_xaxes(tickformat="%b %Y", ticklabelmode="period")
            fig.update_layout(yaxis_title="Controvalore (€)", xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_dark", showlegend=False)
            st.plotly_chart(fig, width="stretch")

    st.divider()

    # ==========================================
    # 7. TABELLA STRUMENTI INTERATTIVA
    # ==========================================
    col_sp, col_in = st.columns([0.85, 0.15])
    with col_in: 
        soglia = st.number_input("Soglia Ribilanciamento (%)", min_value=0.0, max_value=100.0, value=10.00, step=0.50, format="%.2f")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    if not df.empty:
        df["Ribilanc. (Pz)"] = df.apply(lambda x: int(round((x["PMC"]*x["Quantità"] - x["Controvalore"])/prezzi_aggiornati.get(x["Ticker"], 1))) if abs(x["Var. %"]) >= soglia else 0, axis=1)
        df_sorted = df.sort_values(by="Var. %", ascending=False).reset_index(drop=True)
        df_sorted["Ribilanc. (Pz)"] = df_sorted["Ribilanc. (Pz)"].apply(lambda x: f"+{int(x)}" if x > 0 else (f"{int(x)}" if x < 0 else "-"))

        def colora(val):
            if isinstance(val, (int, float)): return 'color: #00c853' if val > 0 else 'color: #ff4b4b' if val < 0 else ''
            elif isinstance(val, str):
                if val.startswith('+'): return 'color: #00c853'
                if val.startswith('-') and len(val) > 1: return 'color: #ff4b4b'
            return ''

        colonne_view = ["Asset", "Strumento", "PMC", "Ultimo Prezzo", "Quantità", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"]
        df_for_editor = df_sorted[colonne_view].copy()

        try:
            styled_df = df_for_editor.style.map(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format("{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"])
        except AttributeError:
            styled_df = df_for_editor.style.applymap(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format("{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"])

        edited_df = st.data_editor(
            styled_df,
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            disabled=["Ultimo Prezzo", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"],
            height=(len(df_sorted)+1)*35+10
        )

        changed = False
        for i in range(len(df_sorted)):
            try:
                new_q = float(str(edited_df.loc[i, "Quantità"]).replace(',', ''))
                new_p = float(str(edited_df.loc[i, "PMC"]).replace(',', ''))
                new_a, new_s = str(edited_df.loc[i, "Asset"]), str(edited_df.loc[i, "Strumento"])
                orig_q, orig_p = float(df_sorted.loc[i, "Quantità"]), float(df_sorted.loc[i, "PMC"])
                orig_a, orig_s = str(df_sorted.loc[i, "Asset"]), str(df_sorted.loc[i, "Strumento"])
                
                if new_q != orig_q or new_p != orig_p or new_a != orig_a or new_s != orig_s:
                    changed = True
                    ticker = df_sorted.loc[i, "Ticker"]
                    if new_q <= 0:
                        st.session_state.clienti_database[st.session_state.cliente_selezionato] = [
                            x for x in st.session_state.clienti_database[st.session_state.cliente_selezionato] if x["Ticker"] != ticker
                        ]
                    else:
                        for item in st.session_state.clienti_database[st.session_state.cliente_selezionato]:
                            if item["Ticker"] == ticker:
                                item.update({"Quantità": new_q, "PMC": new_p, "Asset": new_a, "Strumento": new_s}); break
            except: continue
                
        if changed: salva_db(); st.rerun()

    # ==========================================
    # 8. AGGIUNTA NUOVO STRUMENTO MANUALE
    # ==========================================
    if not df.empty or len(portafoglio_cliente) == 0:
        with st.expander("➕ Nuovo Strumento"):
            c_t, c_n, c_q = st.columns(3)
            new_t, new_n, new_q = c_t.text_input("Ticker"), c_n.text_input("Strumento (Nome)"), c_q.number_input("Quantità", min_value=0.0, format="%.4f")
            c_p, c_as, c_ar, c_v = st.columns(4)
            new_p = c_p.number_input("PMC", min_value=0.0, format="%.2f")
            new_as = c_as.selectbox("Asset Class", ["Azionario", "Obbligazionario", "Monetario", "Commodity", "Crypto", "Bilanciato", "Immobiliare", "Altro"])
            new_ar = c_ar.selectbox("Area Geografica", ["USA", "Europa", "Emergenti", "Globale", "Pacifico", "Altro"])
            new_v = c_v.selectbox("Valuta", ["EUR", "USD", "Altro"])
            
            if st.button("Aggiungi al Portafoglio", type="primary", width="stretch") and new_t and new_q > 0:
                st.session_state.clienti_database[st.session_state.cliente_selezionato].append({
                    "Strumento": new_n if new_n else new_t, "Ticker": new_t.upper(),
                    "Quantità": new_q, "PMC": new_p, "Asset": new_as, "Area": new_ar, "Valuta": new_v
                })
                salva_db(); st.rerun()

    # ==========================================
    # 9. TRITTICO GRAFICI A TORTA (GRANDI E SIMMETRICI)
    # ==========================================
    st.divider() 
    c_pie1, c_pie2, c_pie3 = st.columns(3)
    colori_torta = ['#2979ff', '#00c853', '#aa00ff', '#ffcf33', '#ff4b4b', '#ff9100', '#00e5ff', '#f50057']

    def allinea_legenda(row, tot, col):
        p = (row["Controvalore"] / tot * 100) if tot > 0 else 0
        p_str = f"{p:.1f}%"
        if p < 10: p_str = "\u2007\u2007" + p_str
        elif p < 100: p_str = "\u2007" + p_str
        return f"{p_str} {row[col]}"

    if not df.empty:
        for c, field, title in zip([c_pie1, c_pie2, c_pie3], ["Asset", "Area", "Valuta"], ["Asset Allocation", "Esposizione Geografica", "Esposizione Valutaria"]):
            df_g = df.groupby(field).agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index().sort_values(by="Controvalore", ascending=False)
            tot_g = df_g["Controvalore"].sum()
            df_g["Legenda"] = df_g.apply(lambda r: allinea_legenda(r, tot_g, field), axis=1)
            with c:
                with st.container(border=True):
                    fig_p = go.Figure(data=[go.Pie(labels=df_g["Legenda"], values=df_g["Controvalore"], customdata=df_g.apply(lambda r: f"<b>{r[field]}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}", axis=1), hovertemplate="%{customdata}<extra></extra>", hole=.4, sort=False, textinfo='none', domain=dict(x=[0, 0.5]), marker=dict(colors=colori_torta, line=dict(color='#1e1e1e', width=2)))]) 
                    fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title_text=title, template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), showlegend=True, legend=dict(yanchor="middle", y=0.5, xanchor="left", x=0.52, font=dict(size=12)))
                    st.plotly_chart(fig_p, width="stretch")
