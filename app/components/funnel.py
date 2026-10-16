"""Funil de jornada (retenção por etapa)."""
from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from config.theme import cor_texto_sobre_marca, render_plotly, tokens_atuais


def render_funnel(etapas: pd.DataFrame, titulo: str, key: str) -> None:
    """Gráfico de funil: quantos usuários chegam a cada etapa da jornada (valor + % do início)."""
    if etapas.empty:
        st.info("Sem dados para o recorte selecionado.")
        return
    t = tokens_atuais()
    fig = go.Figure(go.Funnel(
        y=etapas["etapa"], x=etapas["usuarios"], textinfo="value+percent initial",
        marker=dict(color=t["accent"]), textfont=dict(color=cor_texto_sobre_marca()),
        connector=dict(line=dict(color=t["divider"]))))
    fig.update_layout(title=titulo)
    render_plotly(fig, key=key, height=340)
