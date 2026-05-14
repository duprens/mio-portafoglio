import plotly.graph_objects as go
import numpy as np

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


def _allinea_legenda(row, tot, col):
    p = (row["Controvalore"] / tot * 100) if tot > 0 else 0
    p_str = f"{p:.1f}%"
    if p < 10:
        p_str = "  " + p_str
    elif p < 100:
        p_str = " " + p_str
    return f"{p_str} {row[col]}"


def candele_fig(dati_c, costo_totale_pmc):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dati_c.index, open=dati_c["Open"], high=dati_c["High"], low=dati_c["Low"], close=dati_c["Close"],
        increasing_line_color="#00c853", decreasing_line_color="#ff4b4b",
        increasing_line_width=1, decreasing_line_width=1,
        hovertemplate="Data: %{x|%d %b %Y}<br>Open: %{open:.2f}<br>High: %{high:.2f}<br>Low: %{low:.2f}<br>Close: %{close:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=dati_c.index, y=[costo_totale_pmc] * len(dati_c), mode="lines",
        line=dict(color="rgba(150, 150, 150, 0.5)", width=2, dash="dash"), hoverinfo="skip",
    ))
    fig.update_yaxes(autorange=True, fixedrange=False)
    fig.update_xaxes(tickformat="%b %Y", ticklabelmode="period")
    fig.update_layout(
        yaxis_title="Controvalore (€)", xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_dark", showlegend=False,
    )
    return fig


def pie_fig(df, group_col: str, title: str):
    df_g = df.groupby(group_col).agg(
        Controvalore=("Controvalore", "sum"),
        Strumenti=("Strumento", lambda x: "<br>• " + "<br>• ".join(x)),
    ).reset_index().sort_values(by="Controvalore", ascending=False)

    # Calcolo posizioni "pseudo-fluttuanti" (disposizione a spirale per evitare sovrapposizioni)
    n = len(df_g)
    indices = np.arange(n)
    phi = indices * np.pi * (3 - np.sqrt(5))  # Angolo aureo
    r = np.sqrt(indices) # Raggio crescente
    x_pos = r * np.cos(phi)
    y_pos = r * np.sin(phi)

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_pos, y=y_pos,
        mode="markers+text",
        text=df_g[group_col],
        textposition="middle center",
        textfont=dict(size=14, color="white"),
        marker=dict(
            size=df_g["Controvalore"],
            sizemode='area',
            sizeref=2. * df_g["Controvalore"].max() / (100**2), # Normalizzazione raggio bolle
            sizemin=20,
            color=COLORI_TORTA[:n],
            line=dict(color="#0e1117", width=2),
            opacity=0.9
        ),
        customdata=df_g.apply(
            lambda r: f"<b>{r[group_col]}</b><br>Controvalore: {r['Controvalore']:,.2f} €<br><b>Strumenti:</b>{r['Strumenti']}",
            axis=1,
        ),
        hovertemplate="%{customdata}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, x=0.5, y=0.98, xanchor="center", font=dict(size=18)),
        template="plotly_dark", height=450,
        margin=dict(l=10, r=10, t=60, b=10),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(x_pos)-1, max(x_pos)+1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(y_pos)-1, max(y_pos)+1]),
        hovermode='closest'
    )

    return fig


def planner_fig(a_l, c_v_l, v_f_l):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=a_l, y=c_v_l, mode="lines", line=dict(width=0),
        fillcolor="rgba(150, 150, 150, 0.3)", fill="tozeroy",
        name="Capitale Versato", hovertemplate="%{y:,.2f} €",
    ))
    fig.add_trace(go.Scatter(
        x=a_l, y=v_f_l, mode="lines", line=dict(color="#00c853", width=3),
        fillcolor="rgba(0, 200, 83, 0.2)", fill="tonexty",
        name="Interesse Composto", hovertemplate="%{y:,.2f} €",
    ))
    fig.update_layout(
        template="plotly_dark", height=380, margin=dict(l=0, r=0, t=30, b=10),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(30, 30, 30, 0.95)", font_size=14, bordercolor="#555"),
        xaxis=dict(spikedash="solid", spikemode="across", showspikes=True, spikethickness=1),
    )
    return fig
