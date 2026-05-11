import logging
import streamlit as st
import pandas as pd

from styles import apply as apply_styles
from security import assert_encryption_key
from auth import gate, logout_button
import data
from charts import colora, candele_fig, pie_fig, planner_fig

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

apply_styles()
assert_encryption_key()

user_email = gate()

user_sheet_link = data.get_user_link(user_email)
if not user_sheet_link:
    st.error("Impossibile recuperare il link al tuo foglio. Riprova fra qualche secondo o contatta l'amministratore.")
    st.stop()


def salva():
    data.save_portfolio(user_sheet_link, st.session_state.clienti_database, st.session_state.date_inizio_clienti)


# ---- Stato iniziale ----
if "db_caricato" not in st.session_state:
    c_db, d_db = data.load_portfolio(user_sheet_link)
    st.session_state.clienti_database, st.session_state.date_inizio_clienti = c_db, d_db
    st.session_state.db_caricato = True

if "cliente_selezionato" not in st.session_state:
    lista_cl = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = lista_cl[0] if lista_cl else ""

if "timeframe_scelta" not in st.session_state:
    st.session_state.timeframe_scelta = "D"

# ---- Prezzi ----
tutti_i_tickers = set()
for pt in st.session_state.clienti_database.values():
    for item in pt:
        tutti_i_tickers.add(item["Ticker"])

prezzi_aggiornati = data.fetch_prices(tutti_i_tickers)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown(f"<div style='font-size: 0.7rem; color: #888; margin-bottom: -15px;'>Utente: {user_email}</div>", unsafe_allow_html=True)
st.sidebar.title("Portafogli Clienti")
st.sidebar.markdown("<hr style='margin-top: -15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(130,130,130,0.3);'>", unsafe_allow_html=True)

for nome in sorted(st.session_state.clienti_database.keys(), key=lambda x: x.split()[-1]):
    valore_tot = sum(prezzi_aggiornati.get(i["Ticker"], i["PMC"]) * i["Quantità"] for i in st.session_state.clienti_database[nome])
    costo_tot = sum(i["PMC"] * i["Quantità"] for i in st.session_state.clienti_database[nome])
    var_p = ((valore_tot - costo_tot) / costo_tot * 100) if costo_tot > 0 else 0
    if st.sidebar.button(
        f"{nome} | {var_p:+.2f}%",
        width="stretch",
        type="primary" if st.session_state.cliente_selezionato == nome else "secondary",
    ):
        st.session_state.cliente_selezionato, st.session_state.timeframe_scelta = nome, "D"
        st.rerun()

st.sidebar.divider()
with st.sidebar.expander("➕ Nuovo Cliente"):
    nc_nome, nc_data = st.text_input("Nome Cliente"), st.date_input("Data Inizio Portafoglio")
    if st.button("Crea Cliente", width="stretch", type="primary") and nc_nome:
        st.session_state.clienti_database[nc_nome] = []
        st.session_state.date_inizio_clienti[nc_nome] = nc_data.strftime("%Y-%m-%d")
        salva()
        st.session_state.cliente_selezionato = nc_nome
        st.rerun()

if st.session_state.cliente_selezionato in st.session_state.clienti_database:
    with st.sidebar.expander("🗑️ Elimina Cliente"):
        st.markdown(f"Rimuovere **{st.session_state.cliente_selezionato}**?")
        if st.button("Elimina", width="stretch", type="primary"):
            del st.session_state.clienti_database[st.session_state.cliente_selezionato]
            salva()
            rimanenti = list(st.session_state.clienti_database.keys())
            st.session_state.cliente_selezionato = rimanenti[0] if rimanenti else ""
            st.rerun()

# ==========================================
# DASHBOARD
# ==========================================
if st.session_state.cliente_selezionato:
    cliente = st.session_state.cliente_selezionato
    ptf_c = st.session_state.clienti_database[cliente]
    d_inizio = st.session_state.date_inizio_clienti.get(cliente, "2024-01-01")

    col_t, col_b = st.columns([0.85, 0.15])
    with col_t:
        st.title(f"📈 {cliente}")
    with col_b:
        st.write("")
        if st.button("Aggiorna Prezzi", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    costo_totale_pmc, totale_controvalore = 0, 0
    ptf_el = []
    for i in ptf_c:
        px = prezzi_aggiornati.get(i["Ticker"], 0)
        c_b, cv = i["Quantità"] * i["PMC"], px * i["Quantità"]
        costo_totale_pmc += c_b
        totale_controvalore += cv
        ptf_el.append({
            **i,
            "Ultimo Prezzo": round(px, 2),
            "Controvalore": round(cv, 2),
            "Var. €": round(cv - c_b, 2),
            "Var. %": round(((px - i["PMC"]) / i["PMC"] * 100), 2) if i["PMC"] > 0 else 0,
        })

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

    # Pillola D / W
    timeframe = st.segmented_control(
        label="", 
        options=["D", "W"], 
        default=st.session_state.timeframe_scelta,
        key="timeframe_control"
    )
    if timeframe != st.session_state.timeframe_scelta:
        st.session_state.timeframe_scelta = timeframe
        st.rerun()

    if not df.empty:
        tf_da_usare = "1d" if st.session_state.timeframe_scelta == "D" else "1wk"
        dati_c = data.fetch_candele(list(set(i["Ticker"] for i in ptf_c)), ptf_c, d_inizio, tf_da_usare)
        if dati_c is not None:
            st.plotly_chart(candele_fig(dati_c, costo_totale_pmc), width="stretch")

    st.divider()

    col_sp, col_in = st.columns([0.85, 0.15])
    with col_in:
        soglia = st.number_input("Soglia Ribilanciamento (%)", min_value=0.0, max_value=100.0, value=10.00, step=0.50, format="%.2f")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    if not df.empty:
        df["Peso %"] = round((df["Controvalore"] / totale_controvalore * 100), 2) if totale_controvalore > 0 else 0
        df["Ribilanc. (Pz)"] = df.apply(
            lambda x: int(round((x["PMC"] * x["Quantità"] - x["Controvalore"]) / prezzi_aggiornati.get(x["Ticker"], 1)))
            if abs(x["Var. %"]) >= soglia else 0,
            axis=1,
        )
        df_sorted = df.sort_values(by="Var. %", ascending=False).reset_index(drop=True)
        df_sorted["Ribilanc. (Pz)"] = df_sorted["Ribilanc. (Pz)"].apply(
            lambda x: f"+{int(x)}" if x > 0 else (f"{int(x)}" if x < 0 else "-")
        )

        colonne_view = ["Asset", "Strumento", "PMC", "Ultimo Prezzo", "Quantità", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"]
        df_for_editor = df_sorted[colonne_view].copy()

        try:
            styled_df = df_for_editor.style.map(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format(
                "{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"]
            )
        except AttributeError:
            styled_df = df_for_editor.style.applymap(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format(
                "{:.2f}", subset=["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"]
            )

        edited_df = st.data_editor(
            styled_df, width="stretch", hide_index=True, num_rows="fixed",
            disabled=["Ultimo Prezzo", "Ribilanc. (Pz)", "Var. €", "Var. %", "Controvalore", "Peso %"],
            height=(len(df_sorted) + 1) * 35 + 10,
        )

        changed = False
        for i in range(len(df_sorted)):
            try:
                new_q = float(str(edited_df.loc[i, "Quantità"]).replace(",", ""))
                new_p = float(str(edited_df.loc[i, "PMC"]).replace(",", ""))
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
                        st.session_state.clienti_database[cliente] = [
                            x for x in st.session_state.clienti_database[cliente] if x["Ticker"] != ticker
                        ]
                    else:
                        for item in st.session_state.clienti_database[cliente]:
                            if item["Ticker"] == ticker:
                                item.update({"Quantità": new_q, "PMC": new_p, "Asset": new_a, "Strumento": new_s})
                                break
            except Exception:
                continue
        if changed:
            salva()
            st.rerun()

    if not df.empty or len(ptf_c) == 0:
        with st.expander("➕ Nuovo Strumento"):
            c_t, c_n, c_q = st.columns(3)
            new_t = c_t.text_input("Ticker")
            new_n = c_n.text_input("Strumento")
            new_q = c_q.number_input("Quantità", min_value=0.0, step=1.0, format="%.4f")
            c_p, c_as, c_ar, c_v = st.columns(4)
            new_p = c_p.number_input("PMC", min_value=0.0, step=1.0, format="%.2f")
            new_as = c_as.selectbox("Asset Class", ["Azionario", "Obbligazionario", "Monetario", "Commodity", "Crypto", "Bilanciato", "Immobiliare", "Altro"])
            new_ar = c_ar.selectbox("Area Geografica", ["USA", "Europa", "Emergenti", "Globale", "Pacifico", "Altro"])
            new_v = c_v.selectbox("Valuta", ["EUR", "USD", "Altro"])

            if st.button("Aggiungi al Portafoglio", type="secondary", width="stretch") and new_t and new_q > 0:
                st.session_state.clienti_database[cliente].append({
                    "Strumento": new_n if new_n else new_t,
                    "Ticker": new_t.upper(),
                    "Quantità": new_q, "PMC": new_p,
                    "Asset": new_as, "Area": new_ar, "Valuta": new_v,
                })
                salva()
                st.rerun()

    st.divider()

    if not df.empty:
        c_pie1, c_pie2, c_pie3 = st.columns(3)
        with c_pie1:
            with st.container(border=True):
                st.plotly_chart(pie_fig(df, "Asset", "Asset Allocation"), width="stretch")
        with c_pie2:
            with st.container(border=True):
                st.plotly_chart(pie_fig(df, "Area", "Esposizione Geografica"), width="stretch")
        with c_pie3:
            with st.container(border=True):
                st.plotly_chart(pie_fig(df, "Valuta", "Esposizione Valutaria"), width="stretch")

    # ----- Pianificatore -----
    if not df.empty:
        st.divider()
        st.subheader("Pianificatore")
        st.markdown("<p style='font-size: 14px; color: #a6a6a6;'>Simula l'andamento futuro. Inserisci il risparmio annuo stimato e scegli un profilo di rischio.</p>", unsafe_allow_html=True)

        with st.container(border=True):
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                anni_p = st.slider("Orizzonte (Anni)", 1, 40, 15)
            with col_p2:
                prof = st.selectbox("Profilo di Investimento", ["Prudente (3%)", "Bilanciato (5%)", "Dinamico (8%)"], index=1)
                mapping = {"Prudente (3%)": 3.0, "Bilanciato (5%)": 5.0, "Dinamico (8%)": 8.0}
                tasso_p = mapping[prof] / 100
            with col_p3:
                agg_annua = st.number_input("Risparmio Annuo Totale (€)", min_value=0.0, value=5000.0, step=1000.0)

            a_l = list(range(0, anni_p + 1))
            c_v_l, v_f_l = [], []
            for a in a_l:
                v_fin = totale_controvalore + (agg_annua * a)
                c_v_l.append(v_fin)
                if a == 0:
                    v_f_l.append(totale_controvalore)
                else:
                    v_f_l.append(
                        totale_controvalore * (1 + tasso_p) ** a + agg_annua * (((1 + tasso_p) ** a - 1) / tasso_p)
                        if tasso_p > 0 else v_fin
                    )

            st.plotly_chart(planner_fig(a_l, c_v_l, v_f_l), width="stretch")

            val_fin = v_f_l[-1]
            cap_ver = c_v_l[-1]
            int_gen = val_fin - cap_ver
            perc_crescita = (int_gen / cap_ver * 100) if cap_ver > 0 else 0

            res1, res2, res3 = st.columns(3)
            res1.metric("Versato Stimato", f"{cap_ver:,.2f} €")
            res2.metric("Interessi Generati", f"{int_gen:,.2f} €")
            res3.markdown(
                f'<div style="font-size: 14px; color: #a6a6a6;">Valore Finale</div>'
                f'<div style="font-size: 2.25rem; font-weight: 600; color: #00c853;">{val_fin:,.2f} € '
                f'<span style="font-size: 1.25rem; font-weight: normal; opacity: 0.8;">(+{perc_crescita:.2f}%)</span></div>',
                unsafe_allow_html=True,
            )
