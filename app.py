import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import hashlib
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# Funzione per cifrare la password (Hashing "Stile Blockchain")
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 1. CONFIGURAZIONE E STILI CSS (LA BIBBIA)
# ==========================================
st.set_page_config(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

st.markdown(
    """
    <style>
    .stAppDeployButton {display:none;}
    
    /* ESORCISMO UNIVERSALE DEL ROSSO */
    :root, .stApp { --primary-color: #555555 !important; --focus-ring-color: transparent !important; }
    * { -webkit-tap-highlight-color: transparent !important; transition: none !important; }

    /* Tasti Primary -> GRIGIO SCURO */
    button[kind="primary"] { background-color: #555555 !important; border-color: #555555 !important; color: white !important; }
    button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active { background-color: #666666 !important; border-color: #555555 !important; color: white !important; box-shadow: none !important; }

    /* Tasti Secondary -> GRIGIO STANDARD/CHIARO SU HOVER */
    button[kind="secondary"]:focus, button[kind="secondary"]:active { border-color: rgba(130, 130, 130, 0.4) !important; box-shadow: none !important; color: white !important; }
    button[kind="secondary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; color: white !important; }
    
    /* Stili Sidebar Grigia */
    section[data-testid="stSidebar"] button[kind="primary"], section[data-testid="stSidebar"] button[kind="primary"]:focus, section[data-testid="stSidebar"] button[kind="primary"]:active { background-color: rgba(130, 130, 130, 0.15) !important; border-color: rgba(130, 130, 130, 0.3) !important; color: inherit !important; }
    section[data-testid="stSidebar"] button[kind="primary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; }

    /* Tastini + e - Soglia Ribilanciamento */
    [data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:focus, [data-testid="stNumberInputStepDown"]:focus { background-color: rgba(130, 130, 130, 0.25) !important; color: inherit !important; }

    /* LA PILLOLA PERFETTA per D e W */
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) { gap: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1), div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) { width: 36px !important; min-width: 36px !important; max-width: 36px !important; flex: none !important; padding: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button { min-height: 28px !important; height: 28px !important; padding: 0 !important; margin: 0 !important; border-radius: 0 !important; font-size: 13px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1) button { border-top-left-radius: 6px !important; border-bottom-left-radius: 6px !important; border-right: none !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) button { border-top-right-radius: 6px !important; border-bottom-right-radius: 6px !important; }
    span#pill-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- GESTIONE STATI DI ACCESSO ---
if 'manual_email' not in st.session_state: st.session_state.manual_email = None
if 'registrazione_in_corso' not in st.session_state: st.session_state.registrazione_in_corso = False

# ==========================================
# 2. LOGICA DI REGISTRAZIONE (PRIMA DEL LOGIN)
# ==========================================
if st.session_state.registrazione_in_corso:
    st.title("Benvenuto 💎")
    st.markdown(f"Ciao **{st.session_state.reg_mail}**! Configura il tuo database.")
    st.info("💡 Incolla il link del tuo Foglio Google privato.")
    
    new_link = st.text_input("Link Foglio Google:")
    if st.button("Collega Database", type="primary"):
        if new_link.startswith("https://docs.google.com/spreadsheets/"):
            try:
                df_rubrica = conn.read(worksheet="Rubrica", ttl=0)
                if not df_rubrica.empty and 'Email' in df_rubrica.columns and st.session_state.reg_mail in df_rubrica['Email'].values:
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
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")
        else:
            st.error("Link non valido. Assicurati che sia un link di Google Sheets.")
    st.stop()

# ==========================================
# 3. SCHERMATA DI LOGIN BLINDATA
# ==========================================
if not st.session_state.manual_email:
    st.markdown("<br><br><h1 style='text-align: center;'>Monitoraggio Portafogli 📈</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Accesso Riservato</p><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.info("🔑 Inserisci le tue credenziali per accedere.")
            input_mail = st.text_input("Email", placeholder="es. nome.cognome@gmail.com")
            input_pass = st.text_input("Password", type="password")
            
            if st.button("Accedi", type="primary", width="stretch"):
                if input_mail and input_pass:
                    mail_pulita = input_mail.strip().lower()
                    h_pass = hash_password(input_pass)
                    
                    try:
                        df_rubrica = conn.read(worksheet="Rubrica", ttl=0)
                        if not df_rubrica.empty and 'Email' in df_rubrica.columns:
                            utente = df_rubrica[(df_rubrica['Email'] == mail_pulita) & (df_rubrica['Password'] == h_pass)]
                            
                            if not utente.empty:
                                st.session_state.manual_email = mail_pulita
                                st.rerun()
                            else:
                                if mail_pulita in df_rubrica['Email'].values:
                                    st.error("Password errata.")
                                else:
                                    st.session_state.registrazione_in_corso = True
                                    st.session_state.reg_mail = mail_pulita
                                    st.session_state.reg_pass = h_pass
                                    st.rerun()
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
                else:
                    st.error("Inserisci Email e Password.")
    st.stop()

# --- DA QUI IN POI L'UTENTE È LOGGATO ---
user_email = st.session_state.manual_email

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
# 4. GESTIONE DATABASE PRIVATO
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
# 5. MOTORE PREZZI
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
# 6. SIDEBAR
# ==========================================
st.sidebar.markdown(f"<div style='font-size: 0.7rem; color: #888; margin-bottom: -15px;'>Utente: {user_email}</div>", unsafe_allow_html=True)
st.sidebar.title("Portafogli Clienti")
st.sidebar.markdown("<hr style='margin-top: -15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(130,130,130,0.3);'>", unsafe_allow_html=True)

for nome in sorted(st.session_state.clienti_database.keys(), key=lambda x: x.split()[-1]):
    valore_tot = sum(prezzi_aggiornati.get(i["Ticker"], i["PMC"]) * i["Quantità"] for i in st.session_state.clienti_database[nome])
    costo_tot = sum(i["PMC"] * i["Quantità"] for i in st.session_state.clienti_database[nome])
    var_p = ((valore_tot - costo_tot) / costo_tot * 100) if costo_tot > 0 else 0
    if st.sidebar.button(f"{nome} | {var_p:+.2f}%", width="stretch", type="primary" if st.session_state.cliente_selezionato == nome else "secondary"):
        st.session_state.cliente_selezionato, st.session_state.timeframe_scelta = nome, "D"
        st.rerun()

st.sidebar.divider()
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_nome, nc_data = st.text_input("Nome Cliente"), st.date_input("Data Inizio Portafoglio")
    if st.button("Crea Cliente", width="stretch", type="primary") and nc_nome:
        st.session_state.clienti_database[nc_nome], st.session_state.date_inizio_clienti[nc_nome] = [], nc_data.strftime("%Y-%m-%d")
        salva_db_privato(); st.session_state.cliente_selezionato = nc_nome; st.rerun()

# RIPRISTINATA L'ELIMINAZIONE CON CONFERMA E NOME CLIENTE
if st.session_state.cliente_selezionato in st.session_state.clienti_database:
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        st.markdown(f"Rimuovere **{st.session_state.cliente_selezionato}**?")
        if st.button("Elimina", width="stretch", type="primary"):
            del st.session_state.clienti_database[st.session_state.cliente_selezionato]
            salva_db_privato()
            rimanenti = list(st.session_state.clienti_database.keys())
            st.session_state.cliente_selezionato = rimanenti[0] if rimanenti else ""
            st.rerun()

# ==========================================
# 7. DASHBOARD PRINCIPALE
# ==========================================
if not st.session_state.cliente_selezionato:
    st.info("👋 Benvenuto! Aggiungi il tuo primo cliente dalla barra laterale per iniziare.")
else:
    ptf_c = st.session_state.clienti_database[st.session_state.cliente_selezionato]
    d_inizio = st.session_state.date_inizio_clienti.get(st.session_state.cliente_selezionato, "2024-01-01")
    
    col_t, col_b = st.columns([0.85, 0.15])
    with col_t: st.title(f"📈 {st.session_state.cliente_selezionato}")
    with col_b:
        st.write("")
        if st.button("Aggiorna Prezzi", width="stretch"):
            st.cache_data.clear(); st.rerun()
    
    costo_totale_pmc, totale_controvalore = 0, 0
    ptf_el = []
    for i in ptf_c:
        px = prezzi_aggiornati.get(i["Ticker"], 0)
        c_b, cv = i["Quantità"] * i["PMC"], px * i["Quantità"]
        costo_totale_pmc += c_b; totale_controvalore += cv
        ptf_el.append({**i, "Ultimo Prezzo": round(px, 2), "Controvalore": round(cv, 2), "Var. €": round(cv - c_b, 2), "Var. %": round(((px - i["PMC"]) / i["PMC"] * 100), 2) if i["PMC"] > 0 else 0})
    
    df = pd.DataFrame(ptf_el)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitale Investito", f"{costo_totale_pmc:,.2f} €")
    c2.metric("Controvalore Totale", f"{totale_controvalore:,.2f} €")
    v_e = totale_controvalore - costo_totale_pmc
    v_p = (v_e / costo_totale_pmc * 100) if costo_totale_pmc > 0 else 0
    col_e = "#00c853" if v_e > 0 else "#ff4b4b"
    c3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione Totale (€)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_e:,.2f} €</div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Variazione Totale (%)</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_e};">{v_p:.2f}%</div>', unsafe_allow_html=True)

    st.divider()
    
    # LA PILLOLA PERFETTA
    col_d, col_w, col_vuota = st.columns([1, 1, 20])
    with col_d: 
        if st.button("D", type="primary" if st.session_state.timeframe_scelta == "D" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "D"; st.rerun()
    with col_w: 
        if st.button("W", type="primary" if st.session_state.timeframe_scelta == "W" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "W"; st.rerun()
    with col_vuota: st.markdown('<span id="pill-anchor"></span>', unsafe_allow_html=True)

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
        tf_da_usare = "1d" if st.session_state.timeframe_scelta == "D" else "1wk"
        dati_c = calcola_candele(list(set(i["Ticker"] for i in ptf_c)), ptf_c, d_inizio, tf_da_usare)
        
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
    
    col_sp, col_in = st.columns([0.85, 0.15])
    with col_in: 
        soglia = st.number_input("Soglia Ribilanciamento (%)", min_value=0.0, max_value=100.0, value=10.00, step=0.50, format="%.2f")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    if not df.empty:
        df["Peso %"] = round((df["Controvalore"] / totale_controvalore * 100), 2) if totale_controvalore > 0 else 0
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

        edited_df = st.data_editor(styled_df, width="stretch", hide_index=True, num_rows="fixed", disabled=["Ultimo Prezzo", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"], height=(len(df_sorted)+1)*35+10)
        
        changed = False
        for i in range(len(df_sorted)):
            try:
                new_q = float(str(edited_df.loc[i, "Quantità"]).replace(',', ''))
                new_p = float(str(edited_df.loc[i, "PMC"]).replace(',', ''))
                new_a = str(edited_df.loc[i, "Asset"])
                new_s = str(edited_df.loc[i, "Strumento"])
                
                orig_q = float(df_sorted.loc[i, "Quantità"])
                orig_p = float(df_sorted.loc[i, "PMC"])
                orig_a = str(df_sorted.loc[i, "Asset"])
                orig_s = str(df_sorted.loc[i, "Strumento"])
                
                if new_q != orig_q or new_p != orig_p or new_a != orig_a or new_s != orig_s:
                    changed = True
                    ticker = df_sorted.loc[i, "Ticker"]
                    if new_q <= 0:
                        st.session_state.clienti_database[st.session_state.cliente_selezionato] = [x for x in st.session_state.clienti_database[st.session_state.cliente_selezionato] if x["Ticker"] != ticker]
                    else:
                        for item in st.session_state.clienti_database[st.session_state.cliente_selezionato]:
                            if item["Ticker"] == ticker: item.update({"Quantità": new_q, "PMC": new_p, "Asset": new_a, "Strumento": new_s}); break
            except: continue
        if changed: salva_db_privato(); st.rerun()

    # TITOLO MODIFICATO: "➕ Nuovo Strumento"
    if not df.empty or len(ptf_c) == 0:
        with st.expander("➕ Nuovo Strumento"):
            c_t, c_n, c_q = st.columns(3)
            new_t, new_n, new_q = c_t.text_input("Ticker"), c_n.text_input("Strumento (Nome)"), c_q.number_input("Quantità", min_value=0.0, format="%.4f")
            c_p, c_as, c_ar, c_v = st.columns(4)
            new_p = c_p.number_input("PMC", min_value=0.0, format="%.2f")
            new_as = c_as.selectbox("Asset Class", ["Azionario", "Obbligazionario", "Monetario", "Commodity", "Crypto", "Bilanciato", "Immobiliare", "Altro"])
            new_ar = c_ar.selectbox("Area Geografica", ["USA", "Europa", "Emergenti", "Globale", "Pacifico", "Altro"])
            new_v = c_v.selectbox("Valuta", ["EUR", "USD", "Altro"])
            
            # TASTO MODIFICATO: type="secondary" per il grigio neutro
            if st.button("Aggiungi al Portafoglio", type="secondary", width="stretch") and new_t and new_q > 0:
                st.session_state.clienti_database[st.session_state.cliente_selezionato].append({
                    "Strumento": new_n if new_n else new_t, "Ticker": new_t.upper(),
                    "Quantità": new_q, "PMC": new_p, "Asset": new_as, "Area": new_ar, "Valuta": new_v
                })
                salva_db_privato(); st.rerun()

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
        df_asset = df.groupby("Asset").agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index().sort_values(by="Controvalore", ascending=False)
        tot_asset = df_asset["Controvalore"].sum()
        df_asset["Legenda"] = df_asset.apply(lambda r: allinea_legenda(r, tot_asset, "Asset"), axis=1)

        with c_pie1:
            with st.container(border=True):
                fig_asset = go.Figure(data=[go.Pie(labels=df_asset["Legenda"], values=df_asset["Controvalore"], customdata=df_asset.apply(lambda r: f"<b>{r['Asset']}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}", axis=1), hovertemplate="%{customdata}<extra></extra>", hole=.4, sort=False, textinfo='none', domain=dict(x=[0, 0.5]), marker=dict(colors=colori_torta, line=dict(color='#1e1e1e', width=2)))]) 
                fig_asset.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title_text="Asset Allocation", template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), showlegend=True, legend=dict(yanchor="middle", y=0.5, xanchor="left", x=0.52, font=dict(size=12)))
                st.plotly_chart(fig_asset, width="stretch")

        df_area = df.groupby("Area").agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index().sort_values(by="Controvalore", ascending=False)
        tot_area = df_area["Controvalore"].sum()
        df_area["Legenda"] = df_area.apply(lambda r: allinea_legenda(r, tot_area, "Area"), axis=1)

        with c_pie2:
            with st.container(border=True):
                fig_area = go.Figure(data=[go.Pie(labels=df_area["Legenda"], values=df_area["Controvalore"], customdata=df_area.apply(lambda r: f"<b>{r['Area']}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}", axis=1), hovertemplate="%{customdata}<extra></extra>", hole=.4, sort=False, textinfo='none', domain=dict(x=[0, 0.5]), marker=dict(colors=colori_torta, line=dict(color='#1e1e1e', width=2)))]) 
                fig_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title_text="Esposizione Geografica", template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), showlegend=True, legend=dict(yanchor="middle", y=0.5, xanchor="left", x=0.52, font=dict(size=12)))
                st.plotly_chart(fig_area, width="stretch")

        df_val = df.groupby("Valuta").agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index().sort_values(by="Controvalore", ascending=False)
        tot_val = df_val["Controvalore"].sum()
        df_val["Legenda"] = df_val.apply(lambda r: allinea_legenda(r, tot_val, "Valuta"), axis=1)

        with c_pie3:
            with st.container(border=True):
                fig_val = go.Figure(data=[go.Pie(labels=df_val["Legenda"], values=df_val["Controvalore"], customdata=df_val.apply(lambda r: f"<b>{r['Valuta']}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}", axis=1), hovertemplate="%{customdata}<extra></extra>", hole=.4, sort=False, textinfo='none', domain=dict(x=[0, 0.5]), marker=dict(colors=colori_torta, line=dict(color='#1e1e1e', width=2)))]) 
                fig_val.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title_text="Esposizione Valutaria", template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), showlegend=True, legend=dict(yanchor="middle", y=0.5, xanchor="left", x=0.52, font=dict(size=12)))
                st.plotly_chart(fig_val, width="stretch")
