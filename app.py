import logging
import streamlit as st
import pandas as pd

from styles import apply as apply_styles
from security import assert_encryption_key
from auth import gate, logout_button
import data # Import data module
from charts import colora, candele_fig, performance_fig, pie_fig, planner_fig, format_legend_table, COLORI_TORTA # Import COLORI_TORTA

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

apply_styles()
assert_encryption_key()

user_email = gate()

user_sheet_link = data.get_user_link(user_email)
if not user_sheet_link:
    st.error("Impossibile recuperare il link al tuo foglio. Riprova fra qualche secondo o contatta l'amministratore.")
    st.stop()


# ---- Stato iniziale ----
# Fonte unica: scheda "Movimenti". Holdings, PMC, date inizio ed elenco clienti
# sono tutti derivati dalle operazioni. Il foglio "Portafogli" non viene più letto.
if "db_caricato" not in st.session_state:
    c_db, d_db, ops_db = data.load_movimenti(user_sheet_link)
    st.session_state.clienti_database, st.session_state.date_inizio_clienti = c_db, d_db
    st.session_state.operazioni_database = ops_db
    st.session_state.db_caricato = True

if "cliente_selezionato" not in st.session_state:
    lista_cl = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = lista_cl[0] if lista_cl else ""

# Se il cliente selezionato non esiste più (es. rimosso da Movimenti dopo un
# refresh), reimposta sul primo disponibile per evitare KeyError.
if st.session_state.cliente_selezionato and st.session_state.cliente_selezionato not in st.session_state.clienti_database:
    rimasti = list(st.session_state.clienti_database.keys())
    st.session_state.cliente_selezionato = rimasti[0] if rimasti else ""

if "metodo_scelta" not in st.session_state:
    st.session_state.metodo_scelta, st.session_state.metodo_control = "T", "T"

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
    var_p_total = ((valore_tot - costo_tot) / costo_tot * 100) if costo_tot > 0 else 0

    # Recupero logica freccia (variazione seduta precedente) da app.rtf
    var_p_prev_session = 0.0
    freccia = ""
    client_start_date = st.session_state.date_inizio_clienti.get(nome, "2024-01-01")
    ops_cliente = st.session_state.operazioni_database.get(nome)

    if ops_cliente is not None and len(ops_cliente) > 0:
        dati_sidebar = data.fetch_candele_storico(ops_cliente, client_start_date, "1d")
        if dati_sidebar is not None and len(dati_sidebar) >= 2:
            current_close = dati_sidebar["Close"].iloc[-1]
            previous_close = dati_sidebar["Close"].iloc[-2]
            if previous_close > 0:
                var_p_prev_session = ((current_close - previous_close) / previous_close * 100)

    if var_p_prev_session > 0: freccia = "▲"
    elif var_p_prev_session < 0: freccia = "▼"

    if st.sidebar.button(
        f"{nome} | {var_p_total:+.2f}% {freccia}",
        width="stretch",
        type="primary" if st.session_state.cliente_selezionato == nome else "secondary",
    ):
        st.session_state.cliente_selezionato, st.session_state.metodo_scelta, st.session_state.metodo_control = nome, "T", "T"
        st.rerun()

# Clienti, strumenti e operazioni si gestiscono direttamente dalla scheda
# "Movimenti" del Google Sheet (fonte unica). L'app è in sola lettura.

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
        if st.button("Aggiorna Dati", width="stretch"):
            # Ricarica sia i prezzi sia i dati dalla scheda Movimenti.
            st.cache_data.clear()
            st.session_state.pop("db_caricato", None)
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

    # Pillola T (Time-Weighted) / M (Money-Weighted)
    metodo = st.segmented_control(
        label="",
        options=["T", "M"],
        default=st.session_state.metodo_scelta,
        key="metodo_control",
        help="T = time-weighted (depura versamenti/prelievi) · M = money-weighted (P&L sul capitale investito)",
    )
    if metodo and metodo != st.session_state.metodo_scelta:
        st.session_state.metodo_scelta = metodo
        st.rerun()

    if not df.empty:
        ops_cliente = st.session_state.operazioni_database.get(cliente)
        if st.session_state.metodo_scelta == "M":
            perf = data.fetch_mwrr(ops_cliente, d_inizio, "1d")
        else:
            perf = data.fetch_performance(ops_cliente, d_inizio, "1d")
        if perf is not None:
            fig_perf = performance_fig(perf)
            fig_perf.update_layout(yaxis_title=None)
            st.plotly_chart(fig_perf, width="stretch")

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

        def _fmt_qty(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return v
            return f"{v:.0f}" if v.is_integer() else f"{v:.4f}".rstrip("0").rstrip(".")

        fmt_map = {c: "{:.2f}" for c in ["PMC", "Ultimo Prezzo", "Var. €", "Var. %", "Controvalore", "Peso %"]}
        fmt_map["Quantità"] = _fmt_qty

        try:
            styled_df = df_for_editor.style.map(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format(fmt_map)
        except AttributeError:
            styled_df = df_for_editor.style.applymap(colora, subset=["Var. %", "Var. €", "Ribilanc. (Pz)"]).format(fmt_map)

        # Tabella in sola lettura: la fonte è la scheda "Movimenti".
        st.data_editor(
            styled_df, width="stretch", hide_index=True, num_rows="fixed", disabled=True,
            height=(len(df_sorted) + 1) * 35 + 10,
        )

    st.divider()

    if not df.empty:
        c_pie1, c_pie2, c_pie3 = st.columns(3)
        
        def create_color_styler(colors_list):
            def style_func(row):
                # row.name is the index of the current row in the DataFrame
                color = colors_list[row.name % len(colors_list)] # Use modulo for safety if colors_list is shorter than df
                styles = [''] * len(row)
                # Assuming 'Colore' is the first column (index 0)
                styles[0] = f"color: {color}; font-size: 20px; text-align: center;"
                return styles
            return style_func

        with c_pie1:
            with st.container(border=True):
                fig_asset, df_asset_legend = pie_fig(df, "Asset", "Asset Allocation")
                df_asset_table, asset_colors = format_legend_table(df_asset_legend, "Asset")
                st.plotly_chart(fig_asset, use_container_width=True)
                st.dataframe(df_asset_table.style.apply(create_color_styler(asset_colors), axis=1), hide_index=True, use_container_width=True)
        with c_pie2:
            with st.container(border=True):
                fig_area, df_area_legend = pie_fig(df, "Area", "Esposizione Geografica")
                df_area_table, area_colors = format_legend_table(df_area_legend, "Area")
                st.plotly_chart(fig_area, use_container_width=True)
                st.dataframe(df_area_table.style.apply(create_color_styler(area_colors), axis=1), hide_index=True, use_container_width=True)
        with c_pie3:
            with st.container(border=True):
                fig_valuta, df_valuta_legend = pie_fig(df, "Valuta", "Esposizione Valutaria")
                df_valuta_table, valuta_colors = format_legend_table(df_valuta_legend, "Valuta")
                st.plotly_chart(fig_valuta, use_container_width=True)
                st.dataframe(df_valuta_table.style.apply(create_color_styler(valuta_colors), axis=1), hide_index=True, use_container_width=True)

    # ----- Pianificatore -----
    if not df.empty:
        st.divider()

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
