"""Ranking analítico horizontal com rótulo de valor e linha de meta."""
from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from config.theme import cor_por_estado, render_plotly, tokens_atuais


# Barras horizontais ordenadas. Com `meta`, a barra fica verde/vermelha e recebe ✔/✖ (acessível sem cor).
def render_ranking(df: pd.DataFrame, col_nome: str, col_valor: str, titulo: str, key: str, fmt: str = ".1f",
                   sufixo: str = "", meta: float | None = None, maior_melhor: bool = True) -> None:
    if df.empty:
        st.info("Sem dados para o recorte selecionado.")
        return
    d = df.sort_values(col_valor, ascending=maior_melhor)
    # Cor por barra: acento se não há meta; senão, estado conforme atinja a meta.
    cores_barras = []
    for v in d[col_valor]:
        if meta is None or v != v:
            cores_barras.append(tokens_atuais()["accent"])
        else:
            ok = v >= meta if maior_melhor else v <= meta
            cores_barras.append(cor_por_estado("saudavel" if ok else "critico"))
    # Rótulo de valor de cada barra, com ✔/✖ quando há meta.
    textos = [("—" if v != v else f"{v:{fmt}}{sufixo}" + ("" if meta is None else (" ✔" if ((v >= meta) if maior_melhor else (v <= meta)) else " ✖")))
              for v in d[col_valor]]
    fig = go.Figure(go.Bar(x=d[col_valor], y=d[col_nome], orientation="h", marker_color=cores_barras,
                           text=textos, textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{text}<extra></extra>"))
    if meta is not None:
        fig.add_vline(x=meta, line_dash="dash", line_color=tokens_atuais()["text_muted"],
                      annotation_text=f"meta {meta:g}{sufixo}", annotation_font_color=tokens_atuais()["text_muted"])
    fig.update_layout(title=titulo)
    fig.update_xaxes(showgrid=False, rangemode="tozero")
    render_plotly(fig, key=key, height=max(200, 46 * len(d) + 80))
