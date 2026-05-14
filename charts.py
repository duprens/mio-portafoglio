import plotly.graph_objects as go

COLORI_TORTA = ["#2979ff", "#00c853", "#aa00ff", "#ffcf33", "#ff4b4b", "#ff9100", "#00e5ff", "#f50057"]


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
    tot = df_g["Controvalore"].sum()
    df_g["Legenda"] = df_g.apply(lambda r: _allinea_legenda(r, tot, group_col), axis=1)

    fig = go.Figure(data=[go.Pie(
        labels=df_g["Legenda"],
        values=df_g["Controvalore"],
        customdata=df_g.apply(
            lambda r: f"<b>{r[group_col]}</b><br>Totale: {r['Controvalore']:.2f} €<br><b>Strumenti:</b>{r['Strumenti']}",
            axis=1,
        ),
        hovertemplate="%{customdata}<extra></extra>",
        hole=.65, sort=True, textinfo="none",
        domain=dict(x=[0, 0.5]),
        marker=dict(colors=COLORI_TORTA, line=dict(color="#0e1117", width=3)),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark", height=380,
        margin=dict(l=0, r=0, t=40, b=10),
        showlegend=True, legend=dict(yanchor="middle", y=0.5, xanchor="left", x=0.52, font=dict(size=12)),
        annotations=[
            dict(
                text=f"<b>{title}</b><br>{tot/1000:.1f}k€",
                x=0.25, y=0.5,
                showarrow=False,
                font=dict(size=14, color="white"),
                align="center"
            )
        ]
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
