import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import hashlib
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# Funzione per cifrare la password (SHA-256)
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
    
    /* ESORCISMO TOTALE DEL ROSSO E TEMA GRIGIO STUDIO */
    :root, .stApp { --primary-color: #555555 !important; --focus-ring-color: transparent !important; }
    * { -webkit-tap-highlight-color: transparent !important; transition: none !important; }

    /* Slider: togliamo il rosso e mettiamo il grigio sulla traccia e sul pallino */
    .stSlider [data-baseweb="slider"] > div > div > div > div { background-color: #555555 !important; }
    .stSlider [data-baseweb="slider"] [role="slider"] { background-color: #555555 !important; border-color: #555555 !important; box-shadow: none !important; }

    /* Tasti Primary -> GRIGIO SCURO */
    button[kind="primary"] { background-color: #555555 !important; border-color: #555555 !important; color: white !important; }
    button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active { background-color: #666666 !important; border-color: #555555 !important; color: white !important; box-shadow: none !important; }

    /* Tasti Secondary -> GRIGIO NEUTRO */
    button[kind="secondary"]:focus, button[kind="secondary"]:active { border-color: rgba(130, 130, 130, 0.4) !important; box-shadow: none !important; color: white !important; }
    button[kind="secondary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; color: white !important; }
    
    /* Stili Sidebar Grigia */
    section[data-testid="stSidebar"] button[kind="primary"], section[data-testid="stSidebar"] button[kind="primary"]:focus, section[data-testid="stSidebar"] button[kind="primary"]:active { background-color: rgba(130, 130, 130, 0.15) !important; border-color: rgba(130, 130, 130, 0.3) !important; color: inherit !important; }
    section[data-testid="stSidebar"] button[kind="primary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; }

    /* Tastini + e - Soglia Ribilanciamento */
    [data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:focus, [data-testid="stNumberInputStepDown"]:focus { background-color: rgba(130, 130, 130, 0.25) !important; color: inherit !important; }

    /* LA PILLOLA PERFETTA (D / W) */
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) { gap: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1), div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) { width: 36px !important; min-width: 36px !important; max-width: 36px !important; flex: none !important; padding: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button { min-height: 28px !important; height: 28px !important; padding: 0 !important; margin: 0 !important; border-radius: 0 !important; font-size: 13px !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1) button { border-top-left-radius: 6px !important; border-bottom-left-radius: 6px !important; border-right: none !important; }
    div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) button { border-top-right-radius: 6px !important; border-bottom-right-radius: 6px !important; }
    span#pill-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- GESTIONE ACCESSO ---
if 'manual_email' not in st.session_state: st.session_state.manual_email = None
if 'registrazione_in_corso' not in st.session_state: st.session_state.registrazione_in_corso = False

# ==========================================
# 2. LOGICA REGISTRAZIONE / LOGIN
# ==========================================
if st.session_state.registrazione_in_corso:
    st.title("Benvenuto 📈")
    st.markdown(f"Ciao **{st.session_state.reg_mail}**! Configura il tuo database.")
    st.info("💡 Incolla il link del tuo Foglio Google privato (condividilo come Editor con l'email del bot).")
    new_link = st.text_input("Link Foglio Google:")
    if st.button("Collega Database", type="primary"):
        if new_link.startswith("https://docs.google.com/spreadsheets/"):
            try:
                df_r = conn.read(worksheet="Rubrica", ttl=0)
                if not df_r.empty and 'Email' in df_r.columns and st.session_state.reg_mail in df_r['Email'].values:
                    df_r.loc[df_r['Email'] == st.session_state.reg_mail, ['Link', 'Password']] = [new_link, st.session_state.reg_pass]
                    df_agg = df_r
                else:
                    df_agg = pd.concat([df_r, pd.DataFrame([{"Email": st.session_state.reg_mail, "Link": new_link, "Password": st.session_state.reg_pass}])], ignore_index=True)
                conn.update(worksheet="Rubrica", data=df_agg)
                st.session_state.manual_email = st.session_state.reg_mail
                st.session_state.registrazione_in_corso = False
                st.cache_data.clear(); st.rerun()
            except: st.error("Errore salvataggio.")
    st.stop()

if not st.session_state.manual_email:
    st.markdown("<br><br><h1 style='text-align: center;'>Monitoraggio Portafogli 📈</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Accesso Riservato</p><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.info("🔑 Inserisci le tue credenziali per accedere.")
            i_m = st.text_input("Email", placeholder="es. nome.cognome@gmail.com")
            i_p = st.text_input("Password", type="password")
            if st.button("Accedi", type="primary", width="stretch"):
                if i_m and i_p:
                    m_p = i_m.strip().lower(); h_p = hash_password(i_p)
                    try:
                        df_r = conn.read(worksheet="Rubrica", ttl=0)
                        ut = df_r[(df_r['Email'] == m_p) & (df_r['Password'] == h_p)]
                        if not ut.empty: st.session_state.manual_email = m_p; st.rerun()
                        else:
                            if not df_r.empty and m_p in df_r['Email'].values: st.error("Password errata.")
                            else: st.session_state.registrazione_in_corso = True; st.session_state.reg_mail = m_p; st.session_state.reg_pass = h_p; st.rerun()
                    except: st.session_state.registrazione_in_corso = True; st.session_state.reg_mail = m_p; st.session_state.reg_pass = h_p; st.rerun()
    st.stop()

# ==========================================
# 3. CARICAMENTO DATI
# ==========================================
user_email = st.session_state.manual_email

@st.cache_data(ttl=5)
def get_user_link(email):
    try:
        df_r = conn.read(worksheet="Rubrica", ttl=0)
        u_row = df_r[df_r['Email'] == email]
        if not u_row.empty: return u_row.iloc[0]['Link']
    except: return None

user_sheet_link = get_user_link(user_email)

def salva_db_privato():
    rows = []
    for cl, ptf in st.session_state.clienti_database.items():
        dt = st.session_state.date_inizio_clienti.get(cl, "2024-01-01")
        if not ptf: rows.append({'Cliente': cl, 'Data_Inizio': dt, 'Strumento': None, 'Ticker': None, 'Quantità': 0, 'PMC': 0, 'Asset': None, 'Area': None, 'Valuta': None})
        for i in ptf: rows.append({'Cliente': cl, 'Data_Inizio': dt, **i})
    conn.update(spreadsheet=user_sheet_link, worksheet="Portafogli", data=pd.DataFrame(rows))

def carica_db_privato():
    try:
        df_u = conn.read(spreadsheet=user_sheet_link, worksheet="Portafogli", ttl=0)
        if df_u.empty: return {}, {}
        c_db, d_db = {}, {}
        for cl in df_u['Cliente'].dropna().unique():
            df_c = df_u[df_u['Cliente'] == cl]
            d_db[cl] = str(df_c['Data_Inizio'].iloc[0])
            ptf = []
            for _, r in df_c.iterrows():
                if pd.isna(r['Ticker']): continue
                ptf.append({"Strumento": str(r['Strumento']), "Ticker": str(r['Ticker']), "Quantità": float(r['Quantità']), "PMC": float(r['PMC']), "Asset": str(r['Asset']), "Area": str(r['Area']), "Valuta": str(r['Valuta'])})
            c_db[cl] = ptf
        return c_db, d_db
    except: return {}, {}

if 'db_caricato' not in st.session_state:
    st.session_state.clienti_database, st.session_state.date_inizio_clienti = carica_db_privato()
    st.session_state.db_caricato = True

if 'cliente_selezionato' not in st.session_state:
    l_c = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = l_c[0] if l_c else ""

if 'timeframe_scelta' not in st.session_state: st.session_state.timeframe_scelta = "D"

# ==========================================
# 4. MOTORE PREZZI E SIDEBAR
# ==========================================
t_tickers = set()
for p in st.session_state.clienti_database.values():
    for i in p: t_tickers.add(i["Ticker"])

@st.cache_data(ttl=60)
def scarica_prezzi(tickers):
    if not tickers: return {}
    try:
        data = yf.download(list(tickers), period="5d", progress=False)['Close']
        return {t: float(data[t].dropna().iloc[-1]) if len(tickers)>1 else float(data.dropna().iloc[-1]) for t in tickers}
    except: return {}

prezzi_agg = scarica_prezzi(t_tickers)

st.sidebar.markdown(f"<div style='font-size: 0.7rem; color: #888; margin-bottom: -15px;'>Utente: {user_email}</div>", unsafe_allow_html=True)
st.sidebar.title("Portafogli Clienti")
st.sidebar.markdown("<hr style='margin-top: -15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(130,130,130,0.3);'>", unsafe_allow_html=True)

for n in sorted(st.session_state.clienti_database.keys(), key=lambda x: x.split()[-1]):
    v_t = sum(prezzi_agg.get(i["Ticker"], i["PMC"]) * i["Quantità"] for i in st.session_state.clienti_database[n])
    c_t = sum(i["PMC"] * i["Quantità"] for i in st.session_state.clienti_database[n])
    var = ((v_t - c_t) / c_t * 100) if c_t > 0 else 0
    if st.sidebar.button(f"{n} | {var:+.2f}%", width="stretch", type="primary" if st.session_state.cliente_selezionato == n else "secondary"):
        st.session_state.cliente_selezionato = n; st.rerun()

st.sidebar.divider()
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_n, nc_d = st.text_input("Nome"), st.date_input("Inizio")
    if st.button("Crea", width="stretch", type="primary") and nc_n:
        st.session_state.clienti_database[nc_n] = []; st.session_state.date_inizio_clienti[nc_n] = nc_d.strftime("%Y-%m-%d")
        salva_db_privato(); st.session_state.cliente_selezionato = nc_n; st.rerun()

if st.session_state.cliente_selezionato:
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        st.write(f"Eliminare **{st.session_state.cliente_selezionato}**?")
        if st.button("Conferma Elimina", type="primary", width="stretch"):
            del st.session_state.clienti_database[st.session_state.cliente_selezionato]
            salva_db_privato(); r = list(st.session_state.clienti_database.keys())
            st.session_state.cliente_selezionato = r[0] if r else ""; st.rerun()

# ==========================================
# 5. DASHBOARD (LA BIBBIA ESTETICA)
# ==========================================
if not st.session_state.cliente_selezionato:
    st.info("👋 Aggiungi un cliente per iniziare.")
else:
    cl_sel = st.session_state.cliente_selezionato
    ptf_c = st.session_state.clienti_database[cl_sel]
    d_in = st.session_state.date_inizio_clienti.get(cl_sel, "2024-01-01")
    
    col_t, col_b = st.columns([0.85, 0.15])
    with col_t: st.title(f"📈 {cl_sel}")
    with col_b:
        st.write("")
        if st.button("Aggiorna Prezzi", width="stretch"): st.cache_data.clear(); st.rerun()
    
    costo_tot, val_tot = 0, 0
    ptf_el = []
    for i in ptf_c:
        px = prezzi_agg.get(i["Ticker"], 0)
        cb, cv = i["Quantità"] * i["PMC"], px * i["Quantità"]
        costo_tot += cb; val_tot += cv
        ptf_el.append({**i, "Ultimo Prezzo": round(px, 2), "Controvalore": round(cv, 2), "Var. €": round(cv - cb, 2), "Var. %": round(((px - i["PMC"]) / i["PMC"] * 100), 2) if i["PMC"] > 0 else 0})
    
    df = pd.DataFrame(ptf_el)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitale Investito", f"{costo_tot:,.2f} €")
    c2.metric("Controvalore Totale", f"{val_tot:,.2f} €")
    ve, vp = val_tot - costo_tot, (val_tot - costo_tot)/costo_tot*100 if costo_tot > 0 else 0
    col_v = "#00c853" if ve > 0 else "#ff4b4b"
    c3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Var. €</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_v};">{ve:,.2f} €</div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Var. %</div><div style="font-size: 2.25rem; font-weight: 600; color: {col_v};">{vp:.2f}%</div>', unsafe_allow_html=True)

    st.divider()
    cd, cw, cvuota = st.columns([1, 1, 20])
    with cd: 
        if st.button("D", type="primary" if st.session_state.timeframe_scelta == "D" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "D"; st.rerun()
    with cw: 
        if st.button("W", type="primary" if st.session_state.timeframe_scelta == "W" else "secondary", width="stretch"): st.session_state.timeframe_scelta = "W"; st.rerun()
    with cvuota: st.markdown('<span id="pill-anchor"></span>', unsafe_allow_html=True)

    if not df.empty:
        tf = "1d" if st.session_state.timeframe_scelta == "D" else "1wk"
        try:
            dati = yf.download(list(set(i["Ticker"] for i in ptf_c)), start=d_in, interval=tf, progress=False)
            df_c = pd.DataFrame(index=dati.index).fillna(0)
            df_c['Open'], df_c['High'], df_c['Low'], df_c['Close'] = 0, 0, 0, 0
            for i in ptf_c:
                t, q = i["Ticker"], i["Quantità"]
                px_c = dati['Close'] if len(set(x["Ticker"] for x in ptf_c)) == 1 else dati['Close'][t]
                df_c['Open'] += (dati['Open'] if len(set(x["Ticker"] for x in ptf_c)) == 1 else dati['Open'][t]).ffill().bfill() * q
                df_c['High'] += (dati['High'] if len(set(x["Ticker"] for x in ptf_c)) == 1 else dati['High'][t]).ffill().bfill() * q
                df_c['Low'] += (dati['Low'] if len(set(x["Ticker"] for x in ptf_c)) == 1 else dati['Low'][t]).ffill().bfill() * q
                df_c['Close'] += px_c.ffill().bfill() * q
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], increasing_line_color='#00c853', decreasing_line_color='#ff4b4b', increasing_line_width=1, decreasing_line_width=1))
            fig.add_trace(go.Scatter(x=df_c.index, y=[costo_tot]*len(df_c), mode='lines', line=dict(color='rgba(150, 150, 150, 0.5)', width=2, dash='dash'), hoverinfo='skip'))
            fig.update_layout(yaxis_title="Controvalore (€)", xaxis_rangeslider_visible=False, template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified")
            st.plotly_chart(fig, width="stretch")
        except: pass

    st.divider()
    if not df.empty:
        col_s, col_i = st.columns([0.85, 0.15])
        with col_i: soglia = st.number_input("Soglia Ribilanciamento (%)", value=10.0, step=0.5)
        df["Peso %"] = round((df["Controvalore"] / val_tot * 100), 2)
        df["Ribilanc. (Pz)"] = df.apply(lambda x: int(round((x["PMC"]*x["Quantità"] - x["Controvalore"])/prezzi_agg.get(x["Ticker"], 1))) if abs(x["Var. %"]) >= soglia else 0, axis=1)
        df_s = df.sort_values(by="Var. %", ascending=False)
        def colora(v):
            if isinstance(v, (int, float)): return 'color: #00c853' if v > 0 else 'color: #ff4b4b' if v < 0 else ''
            return 'color: #00c853' if str(v).startswith('+') else 'color: #ff4b4b' if str(v).startswith('-') else ''
        cols_v = ["Asset", "Strumento", "PMC", "Ultimo Prezzo", "Quantità", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"]
        ed_df = st.data_editor(df_s[cols_v].style.applymap(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format("{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"]), width="stretch", hide_index=True, disabled=["Ultimo Prezzo", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"])
        if st.button("Salva Modifiche Tabella", type="primary"):
            for idx, r in ed_df.iterrows():
                t_o = df_s.iloc[idx]["Ticker"]
                for item in st.session_state.clienti_database[cl_sel]:
                    if item["Ticker"] == t_o: item.update({"Quantità": r["Quantità"], "PMC": r["PMC"], "Asset": r["Asset"], "Strumento": r["Strumento"]})
            salva_db_privato(); st.rerun()

    with st.expander("➕ Nuovo Strumento"):
        c_a, c_b, c_c, c_d = st.columns(4)
        nt, nn, nq, np = c_a.text_input("Ticker"), c_b.text_input("Nome"), c_c.number_input("Qta", min_value=0.0), c_d.number_input("PMC", min_value=0.0)
        if st.button("Aggiungi al Portafoglio", type="secondary", width="stretch") and nt and nq > 0:
            st.session_state.clienti_database[cl_sel].append({"Strumento": nn if nn else nt, "Ticker": nt.upper(), "Quantità": nq, "PMC": np, "Asset": "Azionario", "Area": "USA", "Valuta": "EUR"})
            salva_db_privato(); st.rerun()

    st.divider()
    if not df.empty:
        cp1, cp2, cp3 = st.columns(3)
        c_t = ['#2979ff', '#00c853', '#aa00ff', '#ffcf33', '#ff4b4b', '#ff9100', '#00e5ff', '#f50057']
        for c, f, t in zip([cp1, cp2, cp3], ["Asset", "Area", "Valuta"], ["Asset Allocation", "Esposizione Geografica", "Esposizione Valutaria"]):
            df_g = df.groupby(f).agg(Controvalore=("Controvalore", "sum"), Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x))).reset_index().sort_values(by="Controvalore", ascending=False)
            tot_g = df_g["Controvalore"].sum()
            def leg(r, tot, col):
                p = (r["Controvalore"]/tot*100) if tot > 0 else 0
                return f"{p:.1f}% {r[col]}"
            df_g["Legenda"] = df_g.apply(lambda r: leg(r, tot_g, f), axis=1)
            with c:
                with st.container(border=True):
                    fig_p = go.Figure(data=[go.Pie(labels=df_g["Legenda"], values=df_g["Controvalore"], customdata=df_g.apply(lambda r: f"<b>{r[f]}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}", axis=1), hovertemplate="%{customdata}<extra></extra>", hole=.4, sort=False, textinfo='none', domain=dict(x=[0, 0.5]), marker=dict(colors=c_t, line=dict(color='#1e1e1e', width=2)))]) 
                    fig_p.update_layout(title_text=t, template="plotly_dark", height=380, margin=dict(l=0, r=0, t=40, b=10), legend=dict(y=0.5, x=0.52))
                    st.plotly_chart(fig_p, width="stretch")

    # ==========================================
    # 8. PIANIFICATORE (SENZA EMOJI E CON PROFILI)
    # ==========================================
    if not df.empty:
        st.divider()
        st.subheader("Pianificatore")
        st.markdown("<p style='font-size: 14px; color: #a6a6a6;'>Simula l'andamento futuro. Inserisci il risparmio annuo stimato e scegli un profilo di rischio.</p>", unsafe_allow_html=True)
        with st.container(border=True):
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1: anni_p = st.slider("Orizzonte (Anni)", 1, 40, 15)
            with col_p2:
                prof = st.selectbox("Profilo di Investimento", ["Prudente (3%)", "Bilanciato (5%)", "Azionario (8%)"], index=1)
                mapping = {"Prudente (3%)": 3.0, "Bilanciato (5%)": 5.0, "Azionario (8%)": 8.0}
                tasso_p = mapping[prof] / 100
            with col_p3: agg_annua = st.number_input("Risparmio Annuo Totale (€)", min_value=0.0, value=5000.0, step=1000.0)
            
            a_l = list(range(0, anni_p + 1))
            c_v_l, v_f_l = [], []
            for a in a_l:
                v_fin = val_tot + (agg_annua * a); c_v_l.append(v_fin)
                if a == 0: v_f_l.append(val_tot)
                else: v_f_l.append(val_tot * (1 + tasso_p)**a + agg_annua * (((1 + tasso_p)**a - 1) / tasso_p) if tasso_p > 0 else v_fin)
            
            fig_pr = go.Figure()
            fig_pr.add_trace(go.Scatter(x=a_l, y=c_v_l, mode='lines', line=dict(width=0), fillcolor='rgba(150, 150, 150, 0.3)', fill='tozeroy', name='Capitale Versato'))
            fig_pr.add_trace(go.Scatter(x=a_l, y=v_f_l, mode='lines', line=dict(color='#00c853', width=3), fillcolor='rgba(0, 200, 83, 0.2)', fill='tonexty', name='Valore Proiettato'))
            fig_pr.update_layout(template="plotly_dark", height=380, margin=dict(l=0, r=0, t=30, b=10), hovermode="x unified", xaxis=dict(spikedash='solid', spikemode='across', showspikes=True, spikethickness=1))
            st.plotly_chart(fig_pr, width="stretch")
            
            res1, res2, res3 = st.columns(3)
            res1.metric("Versato Stimato", f"{c_v_l[-1]:,.2f} €")
            res2.metric("Interessi Generati", f"{(v_f_l[-1] - c_v_l[-1]):,.2f} €")
            res3.markdown(f'<div style="font-size: 14px; color: #a6a6a6;">Valore Finale</div><div style="font-size: 2.25rem; font-weight: 600; color: #00c853;">{v_f_l[-1]:,.2f} €</div>', unsafe_allow_html=True)
