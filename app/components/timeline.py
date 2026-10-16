"""Linha do tempo de incidentes (símbolo = severidade, tamanho = duração)."""
from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from config.theme import cor_por_estado, render_plotly

# Severidade → (estado de cor, símbolo). O símbolo distingue a severidade além da cor.
_ESTILO = {"Crítica": ("critico", "x"), "Média": ("atencao", "triangle-up"), "Baixa": ("saudavel", "circle")}


def render_timeline_incidentes(inc: pd.DataFrame, titulo: str, key: str) -> None:
    """Linha do tempo: cada incidente é um marcador (posição = data/sistema; tamanho = duração)."""
    if inc.empty:
        st.info("Nenhum incidente no recorte selecionado.")
        return
    fig = go.Figure()
    for sev, (estado, simbolo) in _ESTILO.items():
        d = inc[inc["severidade"] == sev]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["data"], y=d["sistema"], mode="markers", name=f"{sev}",
            marker=dict(symbol=simbolo, size=(d["duracao_h"] * 3 + 9).clip(upper=44), color=cor_por_estado(estado),
                        line=dict(width=1, color="rgba(255,255,255,0.6)")),
            customdata=d[["incidente_id", "duracao_h"]],
            hovertemplate="%{customdata[0]}<br>%{x|%d/%m/%Y}<br>%{customdata[1]:.1f} h<extra>" + sev + "</extra>"))
    fig.update_layout(title=titulo, legend_title_text="Severidade")
    fig.update_yaxes(autorange="reversed")
    render_plotly(fig, key=key, height=max(240, 55 * inc["sistema"].nunique() + 120))
