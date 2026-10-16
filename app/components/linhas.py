"""Gráfico de linhas de tendência com linha de meta opcional."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.theme import render_plotly, tokens_atuais


# Linhas de tendência (uma por categoria em `cor`) com linha de meta tracejada opcional.
def render_linhas(df: pd.DataFrame, x: str, y: str, cor: str | None, titulo: str, key: str,
                  meta: float | None = None, sufixo: str = "", rotulo_y: str | None = None, altura: int = 340) -> None:
    if df.empty:
        st.info("Sem dados para o recorte selecionado.")
        return
    fig = px.line(df, x=x, y=y, color=cor, markers=False, title=titulo)
    fig.update_traces(hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f}" + sufixo + "<extra>%{fullData.name}</extra>")
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=tokens_atuais()["text_muted"],
                      annotation_text=f"meta {meta:g}{sufixo}", annotation_font_color=tokens_atuais()["text_muted"])
    fig.update_yaxes(title=rotulo_y or "")
    fig.update_xaxes(title="")
    fig.update_layout(legend_title_text="", legend=dict(orientation="h", y=-0.15))
    render_plotly(fig, key=key, height=altura)
