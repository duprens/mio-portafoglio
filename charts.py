import plotly.graph_objects as go
import pandas as pd

COLORI_TORTA = ["#64B5F6", "#81C784", "#BA68C8", "#FFD54F", "#E57373", "#FFB74D", "#4DD0E1", "#F06292"]


def colora(val):
    if isinstance(val, (int, float)):
        return "color: #00c853" if val > 0 else "color: #ff4b4b" if val < 0 else ""
    if isinstance(val, str):
        if val.startswith("+"):
            return "color: #00c853"
        if val.startswith("-") and len(val) > 1:
            return "color: #ff4b4b"
    return ""


def candele_fig(dati_c, costo_totale_pmc):
    fig = go.Figure()
    # Linea di raccordo sottile sulle chiusure: collega le candele anche quando il
    # controvalore "salta" per un acquisto o una vendita (niente più isole staccate).
    fig.add_trace(go.Scatter(
        x=dati_c.index, y=dati_c["Close"], mode="lines",
        line=dict(color="rgba(150, 150, 150, 0.45)", width=1), connectgaps=True,
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Candlestick(
        x=dati_c.index, open=dati_c["Open"], high=dati_c["High"], low=dati_c["Low"], close=dati_c["Close"],
        increasing_line_color="#00c853", decreasing_line_color="#ff4b4b",
        increasing_line_width=1, decreasing_line_width=1,
        hovertemplate="Data: %{x|%d %b %Y}<br>Open: %{open:.2f}<br>High: %{high:.2f}<br>Low: %{low:.2f}<br>Close: %{close:.2f}<extra></extra>",
    ))
    # Linea capitale investito: "a gradini" se è disponibile lo storico del costo
    # (sale sugli acquisti, scende sulle vendite); altrimenti piatta come prima.
    if "Costo" in dati_c.columns and float(dati_c["Costo"].abs().sum()) > 0:
        fig.add_trace(go.Scatter(
            x=dati_c.index, y=dati_c["Costo"], mode="lines", line_shape="hv",
            line=dict(color="rgba(150, 150, 150, 0.6)", width=2, dash="dash"),
            hovertemplate="Capitale investito: %{y:,.2f} €<extra></extra>", showlegend=False,
        ))
    else:
        fig.add_trace(go.Scatter(
            x=dati_c.index, y=[costo_totale_pmc] * len(dati_c), mode="lines",
            line=dict(color="rgba(150, 150, 150, 0.5)", width=2, dash="dash"), hoverinfo="skip", showlegend=False,
        ))
    fig.update_yaxes(autorange=True, fixedrange=False)
    fig.update_xaxes(tickformat="%b %Y", ticklabelmode="period")
    fig.update_layout(
        yaxis_title="Controvalore (€)", xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_dark", showlegend=False,
    )
    return fig


def performance_fig(perf):
    """Linea continua del rendimento (%). Verde sopra lo zero, rossa sotto.
    Vale sia per il TWRR sia per il MWRR: cambia solo la serie passata."""
    x = perf.index
    y = perf["Perf"].astype(float)
    y_pos = y.where(y >= 0, 0.0)   # parte positiva (verde), 0 dove negativa
    y_neg = y.where(y <= 0, 0.0)   # parte negativa (rossa), 0 dove positiva

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y_pos, mode="lines", line=dict(color="#00c853", width=2),
        fill="tozeroy", fillcolor="rgba(0, 200, 83, 0.12)", hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x, y=y_neg, mode="lines", line=dict(color="#ff4b4b", width=2),
        fill="tozeroy", fillcolor="rgba(255, 75, 75, 0.12)", hoverinfo="skip", showlegend=False,
    ))
    # Traccia trasparente solo per l'hover: mostra il valore reale a 2 decimali.
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color="rgba(0,0,0,0)", width=0),
        hovertemplate="%{x|%d %b %Y}<br>Performance: %{y:+.2f}%<extra></extra>", showlegend=False,
    ))
    fig.add_hline(y=0, line=dict(color="rgba(150, 150, 150, 0.5)", width=1, dash="dash"))
    fig.update_yaxes(autorange=True, fixedrange=False, ticksuffix="%")
    fig.update_xaxes(tickformat="%b %Y", ticklabelmode="period")
    fig.update_layout(
        yaxis_title="Performance (%)", xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_dark", showlegend=False,
    )
    return fig


def pie_fig(df, group_col: str, title: str):
    df_g = df.groupby(group_col).agg(
        Controvalore=("Controvalore", "sum"),
        Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x)),
    ).reset_index().sort_values(by="Controvalore", ascending=False).reset_index(drop=True)
    tot = df_g["Controvalore"].sum() # Calculate total here for percentage in hovertemplate

    fig = go.Figure(data=[go.Pie(
        labels=df_g[group_col], # Usa la colonna originale per le etichette
        values=df_g["Controvalore"],
        customdata=df_g.apply(
            # Hovertemplate con Controvalore, Peso % e Strumenti
            lambda r: f"<b>{r[group_col]}</b><br>Controvalore: {r['Controvalore']:,.2f} €<br>Peso: {(r['Controvalore']/tot*100):.1f}%<br><b>Strumenti:</b>{r['Strumenti']}",
            axis=1,
        ),
        hovertemplate="%{customdata}<extra></extra>",
        hole=.65, sort=False, textinfo="none", # Torta sottile, senza testo interno
        domain=dict(x=[0.1, 0.9], y=[0.1, 0.9]), # Rimpicciolita e centrata
        marker=dict(colors=COLORI_TORTA, line=dict(color="#0e1117", width=3)),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(
            text=title,
            x=0.5,
            y=1,
            xanchor="center",
            yanchor="top"
        ),
        template="plotly_dark", height=350, # Altezza ridotta
        margin=dict(l=10, r=10, t=30, b=10), # Margini adattati
        showlegend=False, # Nasconde la legenda interna di Plotly
    )
    return fig, df_g # Restituisce anche il DataFrame raggruppato per la legenda esterna

def format_legend_table(df_g: pd.DataFrame, group_col: str) -> tuple[pd.DataFrame, list[str]]:
    """Formatta il DataFrame raggruppato per la visualizzazione come tabella legenda."""
    tot = df_g["Controvalore"].sum()
    df_table = df_g[[group_col, "Controvalore"]].copy()
    df_table["Peso %"] = (df_table["Controvalore"] / tot * 100).round(1).astype(str) + "%"
    df_table["Controvalore"] = df_table["Controvalore"].apply(lambda x: f"{x:,.2f} €")
    df_table.rename(columns={group_col: "Categoria"}, inplace=True)

    # Add a 'Colore' column for styling
    df_table.insert(0, "#", "●") # Using a bullet point as a placeholder

    # Get the colors that will be used for these categories, in the order of df_table
    colors_for_table = [COLORI_TORTA[i % len(COLORI_TORTA)] for i in range(len(df_table))]

    return df_table, colors_for_table


def planner_fig(a_l, c_v_l, v_f_l):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=a_l, y=c_v_l, mode="lines", line=dict(width=0),
        fillcolor="rgba(150, 150, 150, 0.3)", fill="tozeroy",
        name="Capitale Versato", hovertemplate="%{y:,.2f} €", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=a_l, y=v_f_l, mode="lines", line=dict(color="#00c853", width=3),
        fillcolor="rgba(0, 200, 83, 0.2)", fill="tonexty",
        name="Interesse Composto", hovertemplate="%{y:,.2f} €", showlegend=False,
    ))
    fig.update_layout(
        template="plotly_dark", height=380, margin=dict(l=0, r=0, t=30, b=10),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(30, 30, 30, 0.95)", font_size=14, bordercolor="#555"),
        xaxis=dict(spikedash="solid", spikemode="across", showspikes=True, spikethickness=1),
        showlegend=False,
    )
    return fig
