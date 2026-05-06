import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import hashlib
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ==========================================
# FUNZIONI DI SERVIZIO
# ==========================================
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 1. CONFIGURAZIONE E STILI CSS
# ==========================================
st.set_page_config(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

st.markdown(
    """
    <style>
    .stAppDeployButton {display:none;}
    :root, .stApp { --primary-color: #555555 !important; --focus-ring-color: transparent !important; }
    * { -webkit-tap-highlight-color: transparent !important; transition: none !important; }
    button[kind="primary"] { background-color: #555555 !important; border-color: #555555 !important; color: white !important; }
    button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active { background-color: #666666 !important; border-color: #555555 !important; color: white !important; box-shadow: none !important; }
    button[kind="secondary"]:focus, button[kind="secondary"]:active { border-color: rgba(130, 130, 130, 0.4) !important; box-shadow: none !important; color: white !important; }
    button[kind="secondary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; color: white !important; }
    section[data-testid="stSidebar"] button[kind="primary"], section[data-testid="stSidebar"] button[kind="primary"]:focus, section[data-testid="stSidebar"] button[kind="primary"]:active { background-color: rgba(130, 130, 130, 0.15) !important; border-color: rgba(130, 130, 130, 0.3) !important; color: inherit !important; }
    section[data-testid="stSidebar"] button[kind="primary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; }
    [data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:focus, [data-testid="stNumberInputStepDown"]:focus { background-color: rgba(130, 130, 130, 0.25) !important; color: inherit !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) { gap: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1), div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) { width: 36px !important; min-width: 36px !important; max-width: 36px !important; flex: none !important; padding: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button { min-height: 28px !important; height: 28px !important; padding: 0 !important; margin: 0 !important; border-radius: 0 !important; font-size: 13px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1) button { border-top-left-radius: 6px !important; border-bottom-left-radius: 6px !important; border-right: none !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) button { border-top-right-radius: 6px !important; border-bottom-right-radius: 6px !important; }
    span#pill-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
user_email = st.session_state.get('manual_email', None)

# ==========================================
# 2. LOGIN E REGISTRAZIONE (BUNKER)
# ==========================================
if not user_email:
    st.markdown("<br><br><h1 style='text-align: center;'>Monitoraggio Portafogli 📈</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Accesso Riservato</p><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.info("🔑 Inserisci le tue credenziali per accedere.")
            input_mail = st.text_input("Email", placeholder="es. nome.cognome@gmail.com")
            input_pass = st.text_input("Password", type="password")
            
            if st.button("Accedi", type="primary", width="stretch"):
                if "@" in input_mail and input_pass:
                    mail_pulita = input_mail.strip().lower()
                    h_pass = hash_password(input_pass)
                    
                    try:
                        df_rubrica = conn.read(worksheet="Rubrica", ttl=0)
                        utente = df_rubrica[(df_rubrica['Email'] == mail_pulita) & (df_rubrica['Password'] == h_pass)]
                        
                        if not utente.empty:
                            st.session_state.manual_email = mail_pulita
                            st.rerun()
                        else:
                            check_esistenza = df_rubrica[df_rubrica['Email'] == mail_pulita]
                            if not check_esistenza.empty:
                                st.error("Password errata.")
                            else:
                                st.session_state.registrazione_in_corso = True
                                st.session_state.reg_mail = mail_pulita
                                st.session_state.reg_pass = h_pass
                                st.rerun()
                    except:
                        st.session_state.registrazione_in_corso = True
                        st.session_state.reg_mail = mail_pulita
                        st.session_state.reg_pass = h_pass
                        st.rerun()
    st.stop()

if st.session_state.get('registrazione_in_corso'):
    st.title("Benvenuto 📈")
    st.markdown(f"Ciao **{st.session_state.reg_mail}**! Prima configurazione.")
    st.info("💡 Incolla il link del tuo Foglio Google privato (ricorda di condividerlo con il bot come Editor).")
    new_link = st.text_input("Link Foglio Google:")
    if st.button("Collega Database", type="primary"):
        if new_link.startswith("https://docs.google.com/spreadsheets/"):
            try:
                df_rubrica = conn.read(worksheet="Rubrica", ttl=0)
                if 'Email' in df_rubrica.columns and st.session_state.reg_mail in df_rubrica['Email'].values:
                    df_rubrica.loc[df_rubrica['Email'] == st.session_state.reg_mail, ['Link', 'Password']] = [new_link, st.session_state.reg_pass]
                    df_aggiornata = df_rubrica
                else:
                    nuova_riga = pd.DataFrame([{"Email": st.session_state.reg_mail, "Link": new_link, "Password": st.session_state.reg_pass}])
                    df_aggiornata = pd.concat([df_rubrica, nuova_riga], ignore_index=True)
                conn.update(worksheet="Rubrica", data=df_aggiornata)
                st.session_state.manual_email = st.session_state.reg_mail
                st.session_state.registrazione_in_corso = False
                st.cache_data.clear()
                st.rerun()
            except: pass
    st.stop()

@st.cache_data(ttl=5)
def get_user_link(email):
    try:
        df_r = conn.read(worksheet="Rubrica", ttl=0)
        u_row = df_r[df_r['Email'] == email]
        if not u_row.empty: return u_row.iloc[0]['Link']
    except: return None
    return None

user_sheet_link = get_user_link(user_email)

# ==========================================
# 3. GESTIONE DATABASE PRIVATO
# ==========================================
def salva_db_privato():
    rows = []
    for cliente, portafoglio in st.session_state.clienti_database.items():
        data_in = st.session_state.date_inizio_clienti.get(cliente, "2024-01-01")
        if not portafoglio:
            rows.append({'Cliente': cliente, 'Data_Inizio': data_in, 'Strumento': None, 'Ticker': None, 'Quantità': 0, 'PMC': 0, 'Asset': None, 'Area': None, 'Valuta': None})
        for item in portafoglio:
            rows.append({
                'Cliente': cliente, 'Data_Inizio': data_in,
                'Strumento': item['Strumento'], 'Ticker': item['Ticker'], 'Quantità': item['Quantità'],
                'PMC': item['PMC'], 'Asset': item['Asset'], 'Area': item['Area'], 'Valuta': item['Valuta']
            })
    conn.update(spreadsheet=user_sheet_link, worksheet="Portafogli", data=pd.DataFrame(rows))

def carica_db_privato():
    try:
        df_u = conn.read(spreadsheet=user_sheet_link, worksheet="Portafogli", ttl=0)
        if df_u.empty or 'Cliente' not in df_u.columns: return {}, {}
        c_db, d_db = {}, {}
        for cliente in df_u['Cliente'].dropna().unique():
            df_c = df_u[df_u['Cliente'] == cliente]
            d_db[cliente] = str(df_c['Data_Inizio'].iloc[0])
            ptf = []
            for _, row in df_c.iterrows():
                if pd.isna(row['Ticker']) or str(row['Ticker']).strip() == "": continue
                ptf.append({"Strumento": str(row['Strumento']), "Ticker": str(row['Ticker']), "Quantità": float(row['Quantità']), "PMC": float(row['PMC']), "Asset": str(row['Asset']), "Area": str(row['Area']), "Valuta": str(row['Valuta'])})
            c_db[cliente] = ptf
        return c_db, d_db
    except: return {}, {}

if 'db_caricato' not in st.session_state:
    c_db, d_db = carica_db_privato()
    st.session_state.clienti_database, st.session_state.date_inizio_clienti = c_db, d_db
    st.session_state.db_caricato = True

if 'cliente_selezionato' not in st.session_state:
    lista_cl = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = lista_cl[0] if lista_cl else ""

if 'timeframe_scelta' not in st.session_state:
    st.session_state.timeframe_scelta = "D"

# ==========================================
# 4. MOTORE PREZZI
# ==========================================
tutti_i_tickers = set()
for pt in st.session_state.clienti_database.values():
    for item in pt: tutti_i_tickers.add(item["Ticker"])

@st.cache_data(ttl=60)
def scarica_prezzi_globali(tickers):
    prices = {}
    if not tickers: return prices
    try:
        data = yf.download(list(tickers), period="5d", progress=False)
        for ticker in tickers:
            if len(tickers) == 1: valid_data = data['Close'].dropna()
            else: valid_data = data['Close'][ticker].dropna()
            if not valid_data.empty: prices[ticker] = float(valid_data.iloc[-1])
    except: pass
    return prices

prezzi_aggiornati = scarica_prezzi_globali(tutti_i_tickers)

# ==========================================
# 5. SIDEBAR
# ==========================================
st.sidebar.markdown(f"<div style='font-size: 0.7rem; color: #888;'>Utente: {user_email}</div>", unsafe_allow_html=True)
st.sidebar.title("Portafogli Clienti")

for nome in sorted(st.session_state.clienti_database.keys(), key=lambda x: x.split()[-1]):
    valore_tot = sum(prezzi_aggiornati.get(i["Ticker"], i["PMC"]) * i["Quantità"] for i in st.session_state.clienti_database[nome])
    costo_tot = sum(i["PMC"] * i["Quantità"] for i in st.session_state.clienti_database[nome])
    var_p = ((valore_tot - costo_tot) / costo_tot * 100) if costo_tot > 0 else 0
    if st.sidebar.button(f"{nome} | {var_p:+.2f}%", width="stretch", type="primary" if st.session_state.cliente_selezionato == nome else "secondary"):
        st.session_state.cliente_selezionato, st.session_state.timeframe_scelta = nome, "D"
        st.rerun()

st.sidebar.divider()
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_nome, nc_data = st.text_input("Nome Cliente"), st.date_input("Data Inizio")
    if st.button("Crea", width="stretch", type="primary") and nc_nome:
        st.session_state.clienti_database[nc_nome], st.session_state.date_inizio_clienti[nc_nome] = [], nc_data.strftime("%Y-%m-%d")
        salva_db_privato(); st.session_state.cliente_selezionato = nc_nome; st.rerun()

if st.session_state.cliente_selezionato in st.session_state.clienti_database:
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        if st.button("Elimina Cliente Corrente", width="stretch"):
            del st.session_state.clienti_database[st.session_state.cliente_selezionato]
            salva_db_privato()
            rimanenti = list(st.session_state.clienti_database.keys())
            st.session_state.cliente_selezionato = rimanenti[0] if rimanenti else ""
            st.rerun()

# ==========================================
# 6. DASHBOARD PRINCIPALE
# ==========================================
if not st.session_state.cliente_selezionato:
    st.info("👋 Benvenuto! Aggiungi il tuo primo cliente dalla barra laterale per iniziare.")
else:
    ptf_c = st.session_state.clienti_database[st.session_state.cliente_selezionato]
    d_inizio = st.session_state.date_inizio_clienti.get(st.session_state.cliente_selezionato, "2024-01-01")
    
    st.title(f"📈 {st.session_state.cliente_selezionato}")
    
    costo_tot, val_tot = 0, 0
    ptf_el = []
    for i in ptf_c:
        px = prezzi_aggiornati.get(i["Ticker"], 0)
        c_b, cv = i["Quantità"] * i["PMC"], px * i["Quantità"]
        costo_tot += c_b; val_tot += cv
        ptf_el.append({**i, "Ultimo Prezzo": round(px, 2), "Controvalore": round(cv, 2), "Var. €": round(cv - c_b, 2), "Var. %": round(((px - i["PMC"]) / i["PMC"] * 100), 2) if i["PMC"] > 0 else 0})
    
    df = pd.DataFrame(ptf_el)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitale Investito", f"{costo_tot:,.2f} €")
    c2.metric("Controvalore Totale", f"{val_tot:,.2f} €")
    v_e = val_tot - costo_tot
    v_p = (v_e / costo_tot * 100) if costo_tot > 0 else 0
    col_e = "#00c853" if v_e > 0 else "#ff4b4b"
    c3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione €</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_e:,.2f} €</div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione %</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_p:.2f}%</div>', unsafe_allow_html=True)

    st.divider()
    col_d, col_w, col_v = st.columns([1, 1, 20])
    with col_d: 
        if st.button("D", type="primary" if st.session_state.timeframe_scelta == "D" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "D"; st.rerun()
    with col_w: 
        if st.button("W", type="primary" if st.session_state.timeframe_scelta == "W" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "W"; st.rerun()
    st.markdown('<span id="pill-anchor"></span>', unsafe_allow_html=True)

    if not df.empty:
        dati_c = yf.download(list(set(i["Ticker"] for i in ptf_c)), start=d_inizio, interval="1d" if st.session_state.timeframe_scelta == "D" else "1wk", progress=False)
        if not dati_c.empty:
            df_c = pd.DataFrame(index=dati_c.index).fillna(0)
            df_c['Open'], df_c['High'], df_c['Low'], df_c['Close'] = 0, 0, 0, 0
            for i in ptf_c:
                t, q = i["Ticker"], i["Quantità"]
                is_single = len(set(x["Ticker"] for x in ptf_c)) == 1
                px_c = dati_c['Close'] if is_single else dati_c['Close'][t]
                df_c['Open'] += (dati_c['Open'] if is_single else dati_c['Open'][t]).ffill().bfill() * q
                df_c['High'] += (dati_c['High'] if is_single else dati_c['High'][t]).ffill().bfill() * q
                df_c['Low'] += (dati_c['Low'] if is_single else dati_c['Low'][t]).ffill().bfill() * q
                df_c['Close'] += px_c.ffill().bfill() * q
            fig = go.Figure(data=[go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], increasing_line_color='#00c853', decreasing_line_color='#ff4b4b', increasing_line_width=1, decreasing_line_width=1)])
            fig.update_layout(yaxis_title="Controvalore (€)", xaxis_rangeslider_visible=False, template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, width="stretch")

    st.divider()
    if not df.empty:
        df["Peso %"] = round((df["Controvalore"] / val_tot * 100), 2)
        soglia = st.sidebar.number_input("Soglia Ribilanc. (%)", value=10.0, step=0.5)
        df["Ribilanc. (Pz)"] = df.apply(lambda x: int(round((x["PMC"]*x["Quantità"] - x["Controvalore"])/prezzi_aggiornati.get(x["Ticker"], 1))) if abs(x["Var. %"]) >= soglia else 0, axis=1)
        df_sort = df.sort_values(by="Var. %", ascending=False)
        
        def colora(v):
            if isinstance(v, (int, float)): return 'color: #00c853' if v > 0 else 'color: #ff4b4b' if v < 0 else ''
            return 'color: #00c853' if str(v).startswith('+') else 'color: #ff4b4b' if str(v).startswith('-') else ''

        cols = ["Asset", "Strumento", "PMC", "Ultimo Prezzo", "Quantità", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"]
        ed_df = st.data_editor(df_sort[cols].style.applymap(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format("{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"]), width="stretch", hide_index=True, disabled=["Ultimo Prezzo", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"])
        
        if st.button("💾 Salva Modifiche Tabella", type="primary"):
            for idx, row in ed_df.iterrows():
                t_orig = df_sort.iloc[idx]["Ticker"]
                for item in st.session_state.clienti_database[st.session_state.cliente_selezionato]:
                    if item["Ticker"] == t_orig: item.update({"Quantità": row["Quantità"], "PMC": row["PMC"], "Asset": row["Asset"], "Strumento": row["Strumento"]})
            salva_db_privato(); st.rerun()

    with st.expander("➕ Aggiungi Strumento"):
        c1, c2, c3, c4 = st.columns(4)
        nt, nn, nq, np = c1.text_input("Ticker (es. BTC1.DE)"), c2.text_input("Nome Strumento"), c3.number_input("Quantità", min_value=0.0, format="%.4f"), c4.number_input("PMC", min_value=0.0, format="%.2f")
        nas, nar, nv = st.columns(3)
        na = nas.selectbox("Asset Class", ["Azionario", "Obbligazionario", "Monetario", "Commodity", "Crypto", "Immobiliare", "Altro"])
        nr = nar.selectbox("Area Geografica", ["USA", "Europa", "Emergenti", "Globale", "Pacifico", "Altro"])
        nvv = nv.selectbox("Valuta", ["EUR", "USD", "Altro"])
        if st.button("Aggiungi al Portafoglio", type="primary", width="stretch") and nt and nq > 0:
            st.session_state.clienti_database[st.session_state.cliente_selezionato].append({"Strumento": nn if nn else nt, "Ticker": nt.upper().strip(), "Quantità": nq, "PMC": np, "Asset": na, "Area": nr, "Valuta": nvv})
            salva_db_privato(); st.rerun()

    st.divider()
    if not df.empty:
        c_p1, c_p2, c_p3 = st.columns(3)
        col_t = ['#2979ff', '#00c853', '#aa00ff', '#ffcf33', '#ff4b4b', '#ff9100', '#00e5ff', '#f50057']
        for c, f, t in zip([c_p1, c_p2, c_p3], ["Asset", "Area", "Valuta"], ["Asset Allocation", "Esposizione Geografica", "Esposizione Valutaria"]):
            df_g = df.groupby(f).agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index()
            tot = df_g["Controvalore"].sum()
            df_g["Label"] = df_g.apply(lambda r: f"{(r['Controvalore']/tot*100):.1f}% {r[f]}", axis=1)
            with c:
                with st.container(border=True):
                    fig = go.Figure(data=[go.Pie(labels=df_g["Label"], values=df_g["Controvalore"], hole=.4, domain=dict(x=[0, 0.5]), marker=dict(colors=col_t, line=dict(color='#1e1e1e', width=2)), textinfo='none', sort=False)])
                    fig.update_layout(title_text=t, template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), legend=dict(y=0.5, x=0.52))
                    st.plotly_chart(fig, width="stretch")
