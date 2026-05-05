import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==========================================
# 1. CONFIGURAZIONE E STILI CSS (LA BIBBIA)
# ==========================================
st.set_page_config(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

# Fallback per l'email 
user_email = "test@gmail.com"  # Puoi mettere qui la tua email vera!
try:
    if hasattr(st, "user"):
        user_email = st.user.email
    elif hasattr(st, "experimental_user"):
        user_email = st.experimental_user.email
except AttributeError:
    pass

st.markdown(
    """
    <style>
    .stAppDeployButton {display:none;}
    :root, .stApp { --primary-color: #555555 !important; --focus-ring-color: transparent !important; }
    * { -webkit-tap-highlight-color: transparent !important; transition: none !important; }
    button[kind="primary"] { background-color: #555555 !important; border-color: #555555 !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #666666 !important; }
    button[kind="secondary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; }
    section[data-testid="stSidebar"] button[kind="primary"] { background-color: rgba(130, 130, 130, 0.15) !important; border-color: rgba(130, 130, 130, 0.3) !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) { gap: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"] { width: 36px !important; flex: none !important; padding: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button { min-height: 28px !important; height: 28px !important; border-radius: 0 !important; font-size: 13px !important; }
    span#pill-anchor { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CONNESSIONE A GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    try:
        # Carica il foglio "Portafogli"
        return conn.read(worksheet="Portafogli", ttl=0)
    except:
        # Se il foglio è vuoto, restituisce un dataframe con la struttura corretta
        return pd.DataFrame(columns=['Cliente', 'Email_Proprietario', 'Data_Inizio', 'Ticker', 'Strumento', 'Quantità', 'PMC', 'Asset', 'Area', 'Valuta'])

def salva_dati(df_completo):
    conn.update(worksheet="Portafogli", data=df_completo)

# Caricamento iniziale e filtraggio per PRIVACY
df_all = carica_dati()
# Filtriamo subito: vedi solo i TUOI clienti
df_user = df_all[df_all['Email_Proprietario'] == user_email].copy()

# ==========================================
# 3. SIDEBAR (LOGICA PRIVACY)
# ==========================================
st.sidebar.markdown(f"<div style='font-size: 0.8rem; color: #888;'>Logged in: {user_email}</div>", unsafe_allow_html=True)
st.sidebar.title("Portafogli Clienti")
st.sidebar.markdown("<hr style='margin-top: -15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(130,130,130,0.3);'>", unsafe_allow_html=True)

lista_clienti = sorted(df_user['Cliente'].unique()) if not df_user.empty else []

if 'cliente_sel' not in st.session_state and lista_clienti:
    st.session_state.cliente_sel = lista_clienti[0]

for nome in lista_clienti:
    stile = "primary" if st.session_state.get('cliente_sel') == nome else "secondary"
    if st.sidebar.button(nome, width="stretch", type=stile):
        st.session_state.cliente_sel = nome
        st.rerun()

st.sidebar.divider()

# NUOVO CLIENTE (assegna automaticamente la tua email)
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_nome = st.text_input("Nome Cliente")
    nc_data = st.date_input("Data Inizio")
    if st.button("Crea Cliente", width="stretch"):
        if nc_nome:
            nuova_riga = pd.DataFrame([{
                'Cliente': nc_nome, 'Email_Proprietario': user_email, 'Data_Inizio': str(nc_data),
                'Ticker': 'CASH', 'Strumento': 'Liquidità', 'Quantità': 1, 'PMC': 1,
                'Asset': 'Monetario', 'Area': 'Europa', 'Valuta': 'EUR'
            }])
            df_updated = pd.concat([df_all, nuova_riga], ignore_index=True)
            salva_dati(df_updated)
            st.session_state.cliente_sel = nc_nome
            st.rerun()

# ELIMINA CLIENTE
if st.session_state.get('cliente_sel'):
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        if st.button("Elimina", width="stretch", type="primary"):
            df_updated = df_all[~((df_all['Cliente'] == st.session_state.cliente_sel) & (df_all['Email_Proprietario'] == user_email))]
            salva_dati(df_updated)
            st.session_state.pop('cliente_sel', None)
            st.rerun()

# ==========================================
# 4. DASHBOARD (Sulla base della Bibbia)
# ==========================================
if not st.session_state.get('cliente_sel'):
    st.info("Benvenuto! Aggiungi il tuo primo cliente dalla barra laterale per iniziare.")
else:
    cliente = st.session_state.cliente_sel
    # Dati del cliente specifico
    df_cliente = df_user[df_user['Cliente'] == cliente].copy()
    data_inizio = df_cliente['Data_Inizio'].iloc[0] if not df_cliente.empty else "2024-01-01"
    
    st.title(f"📈 {cliente}")

    # Scarico prezzi
    tickers = [t for t in df_cliente['Ticker'].unique() if t != 'CASH']
    prezzi = {}
    if tickers:
        try:
            data_px = yf.download(tickers, period="5d", progress=False)['Close'].ffill().iloc[-1]
            prezzi = data_px.to_dict() if len(tickers) > 1 else {tickers[0]: float(data_px)}
        except: pass
    prezzi['CASH'] = 1.0

    # Calcoli Metriche
    df_cliente['Prezzo_Att'] = df_cliente['Ticker'].map(lambda x: prezzi.get(x, 0))
    df_cliente['Controvalore'] = df_cliente['Quantità'] * df_cliente['Prezzo_Att']
    df_cliente['Investito'] = df_cliente['Quantità'] * df_cliente['PMC']
    
    tot_inv = df_cliente['Investito'].sum()
    tot_att = df_cliente['Controvalore'].sum()
    var_e = tot_att - tot_inv
    var_p = (var_e / tot_inv * 100) if tot_inv > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitale Investito", f"{tot_inv:,.2f} €")
    c2.metric("Controvalore Totale", f"{tot_att:,.2f} €")
    col_v = "#00c853" if var_e >= 0 else "#ff4b4b"
    c3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Var. Totale (€)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_v};">{var_e:,.2f} €</div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Var. Totale (%)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_v};">{var_p:.2f}%</div>', unsafe_allow_html=True)

    st.divider()

    # TABELLA EDITABILE CON SALVATAGGIO CLOUD
    st.subheader("Gestione Strumenti")
    # Mostriamo le colonne della Bibbia
    df_view = df_cliente[['Asset', 'Strumento', 'Ticker', 'PMC', 'Quantità', 'Area', 'Valuta']].copy()
    
    edited_df = st.data_editor(df_view, width="stretch", hide_index=True, num_rows="fixed")

    if not edited_df.equals(df_view):
        # 1. Rimuoviamo i vecchi dati di questo cliente dal database globale
        df_other_clients = df_all[~((df_all['Cliente'] == cliente) & (df_all['Email_Proprietario'] == user_email))]
        # 2. Prepariamo i nuovi dati
        new_data_cliente = edited_df.copy()
        new_data_cliente['Cliente'] = cliente
        new_data_cliente['Email_Proprietario'] = user_email
        new_data_cliente['Data_Inizio'] = data_inizio
        # 3. Logica eliminazione (Quantità 0)
        new_data_cliente = new_data_cliente[new_data_cliente['Quantità'] > 0]
        # 4. Uniamo e salviamo su Google
        df_final = pd.concat([df_other_clients, new_data_cliente], ignore_index=True)
        salva_dati(df_final)
        st.rerun()

    # Sezione Aggiunta Strumento
    with st.expander("➕ Nuovo Strumento"):
        ca, cb, cc = st.columns(3)
        nt = ca.text_input("Ticker")
        nn = cb.text_input("Nome Strumento")
        nq = cc.number_input("Quantità", min_value=0.0)
        if st.button("Salva nel Portafoglio", type="primary"):
            if nt and nq > 0:
                nuovo = pd.DataFrame([{
                    'Cliente': cliente, 'Email_Proprietario': user_email, 'Data_Inizio': data_inizio,
                    'Ticker': nt.upper(), 'Strumento': nn if nn else nt, 'Quantità': nq, 'PMC': 0.0,
                    'Asset': 'Altro', 'Area': 'Globale', 'Valuta': 'EUR'
                }])
                df_final = pd.concat([df_all, nuovo], ignore_index=True)
                salva_dati(df_final)
                st.rerun()

    # GRAFICI (Torte) - Stesso stile della Bibbia
    st.divider()
    cp1, cp2, cp3 = st.columns(3)
    colori = ['#2979ff', '#00c853', '#aa00ff', '#ffcf33', '#ff4b4b', '#ff9100']
    
    for col, raggruppo, titolo in zip([cp1, cp2, cp3], ["Asset", "Area", "Valuta"], ["Asset Allocation", "Esposizione Geografica", "Esposizione Valutaria"]):
        with col:
            with st.container(border=True):
                df_g = df_cliente.groupby(raggruppo)['Controvalore'].sum().reset_index()
                fig = go.Figure(data=[go.Pie(labels=df_g[raggruppo], values=df_g['Controvalore'], hole=.4, marker=dict(colors=colori))])
                fig.update_layout(title_text=titolo, template="plotly_dark", height=350, showlegend=True, margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig, use_container_width=True)
