"""KPI card com valor, variação (sinal + texto, não só cor), estado e sparkline."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from app.components.sparkline import render_sparkline
from config.theme import SIMBOLO_ESTADO, ROTULO_ESTADO, cor_por_estado


def _ok(x) -> bool:
    """True se o valor existe (não é None nem NaN)."""
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def formatar_variacao(atual, anterior, unidade: str = "pp") -> str | None:
    """Texto da variação vs. período anterior. unidade: 'pp' (pontos), '%' (relativa) ou 'abs'."""
    if not (_ok(atual) and _ok(anterior)):
        return None
    if unidade == "%":
        if anterior == 0:
            return None
        v = (atual - anterior) / anterior * 100
        suf = "%"
    else:
        v = atual - anterior
        suf = " pp" if unidade == "pp" else ""
    seta = "▲" if v > 0 else ("▼" if v < 0 else "■")
    return f"{seta} {v:+.1f}{suf} vs. período anterior"


# Cartão de indicador: título, valor, variação, estado (símbolo + texto) e mini-gráfico.
# `maior_melhor`: se subir é bom (cor da variação); `estado`: resultado da comparação com a meta.
def render_kpi_card(titulo: str, valor: str, atual=None, anterior=None, unidade_delta: str = "pp",
                    maior_melhor: bool = True, estado: str | None = None, serie: pd.Series | None = None,
                    nota: str | None = None, key: str = "kpi") -> None:
    if "nan" in str(valor).lower():  # dado ausente: nunca exibir "nan"
        valor, estado, serie = "—", None, None
        nota = "INFORMAÇÃO NÃO DISPONIBILIZADA"
    # Texto da variação em relação ao período anterior.
    delta = formatar_variacao(atual, anterior, unidade_delta)
    cor_delta = ""
    if delta and _ok(atual) and _ok(anterior) and atual != anterior:
        # Variação 'boa' = subiu quando maior é melhor, ou desceu quando menor é melhor.
        bom = (atual > anterior) == maior_melhor
        cor_delta = f"color:{cor_por_estado('saudavel' if bom else 'critico')};"
    with st.container(border=True):
        html = f'<div class="ux-kpi-t">{titulo}</div><div class="ux-kpi-v">{valor}</div>'
        if delta:
            html += f'<div class="ux-kpi-d" style="{cor_delta}">{delta}</div>'
        else:
            html += '<div class="ux-kpi-d ux-muted">sem período anterior para comparar</div>'
        if estado:
            html += (f'<div class="ux-estado" style="color:{cor_por_estado(estado)}">'
                     f'{SIMBOLO_ESTADO.get(estado, "")} {ROTULO_ESTADO.get(estado, "")}</div>')
        if nota:
            html += f'<div class="ux-kpi-n">{nota}</div>'
        st.markdown(html, unsafe_allow_html=True)
        if serie is not None:
            render_sparkline(serie, cor_por_estado(estado) if estado else None, key=f"{key}_spark")
