"""Mini-gráfico de tendência para KPI cards."""
from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd

from config.theme import render_plotly, tokens_atuais


def render_sparkline(valores: pd.Series, cor: str | None, key: str) -> None:
    """Mini-gráfico (sem eixos) da tendência; não aparece com menos de 2 pontos."""
    t = tokens_atuais()
    cor = cor or t["accent"]
    y = list(valores.dropna())
    if len(y) < 2:
        return
    fig = go.Figure(go.Scatter(x=list(range(len(y))), y=y, mode="lines", line=dict(color=cor, width=2),
                               fill="tozeroy", fillcolor="rgba(128,128,128,0.08)", hoverinfo="skip"))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    fig.update_xaxes(visible=False)
    lo, hi = min(y), max(y)
    pad = (hi - lo) * 0.2 or 1
    fig.update_yaxes(visible=False, range=[lo - pad, hi + pad])
    render_plotly(fig, key=key, height=48)
