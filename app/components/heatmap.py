"""Heatmap/matriz de desempenho com valores escritos nas células (acessível: não depende só de cor)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from config.theme import (cor_texto_sobre_marca, heatmap_colorscale_neutro, heatmap_colorscale_saude, render_plotly, tokens_atuais)


# Mapa de calor com o valor escrito em cada célula (não depende só da cor).
# `escala`: 'saude' (baixo = ruim) ou 'neutro'; `invertida`: menor é melhor; `zmin`/`zmax` fixam a escala.
def render_heatmap(matriz: pd.DataFrame, titulo: str, key: str, escala: str = "saude",
                   zmin: float | None = None, zmax: float | None = None, fmt: str = ".1f",
                   sufixo: str = "", invertida: bool = False, altura: int | None = None) -> None:
    if matriz.empty or matriz.isna().all().all():
        st.info(f"{titulo}: INFORMAÇÃO NÃO DISPONIBILIZADA para o recorte selecionado.")
        return
    t = tokens_atuais()
    cs = heatmap_colorscale_saude() if escala == "saude" else heatmap_colorscale_neutro()
    # Inverte a escala de cores quando 'menor é melhor' (ex.: chamados por mil).
    if invertida:
        cs = [[1 - p, c] for p, c in reversed(cs)]
    # Texto de cada célula; célula sem dado mostra '—'.
    texto = matriz.map(lambda v: "—" if v != v else f"{v:{fmt}}{sufixo}")
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=list(matriz.columns), y=list(matriz.index), colorscale=cs, zmin=zmin, zmax=zmax,
        text=texto.values, texttemplate="%{text}", textfont=dict(color=cor_texto_sobre_marca() if escala == "saude" else t["text_primary"], size=12),
        hovertemplate="%{y} · %{x}<br>%{text}<extra></extra>", xgap=2, ygap=2, colorbar=dict(thickness=10, tickfont=dict(color=t["text_secondary"])),
    ))
    fig.update_layout(title=titulo)
    fig.update_yaxes(autorange="reversed")
    render_plotly(fig, key=key, height=altura or max(220, 60 * len(matriz) + 80))



