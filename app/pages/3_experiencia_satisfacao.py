import sys
from pathlib import Path

# Raiz do projeto no sys.path: permite `from app...`, `from config...` mesmo rodando a página isolada.
_RAIZ = Path(__file__).resolve().parent.parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import plotly.express as px
import streamlit as st

from app.components.heatmap import render_heatmap
from app.components.kpi_card import render_kpi_card
from app.components.linhas import render_linhas
from app.components.page_header import subtitulo
from app.components.ranking import render_ranking
from app.state import anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from config.theme import render_plotly
from indicators import iss
from indicators import satisfacao as sat

dados, f, ant = preparar_pagina(
    "Experiência e Satisfação",
    "Como os usuários percebem os sistemas e onde a experiência está se deteriorando.",
)
tem_ant = anterior_disponivel(ant)
nan = float("nan")
# Dados filtrados de satisfação e indicadores do período atual (_a = período anterior).
s = f["satisfacao"]
cs, cs_a = sat.csat(s), sat.csat(ant["satisfacao"]) if tem_ant else nan
ce, ce_a = sat.ces(s), sat.ces(ant["satisfacao"]) if tem_ant else nan
# Série semanal do CSAT e ranking por sistema.
serie = sat.serie_csat_semanal(s, None).set_index("semana")["csat"]
rk = sat.ranking_csat(s)

# KPIs: CSAT, esforço percebido (CES), tamanho da amostra e sistemas abaixo da meta.
c = st.columns(4)
with c[0]:
    render_kpi_card("Satisfação (CSAT)", f"{cs:.1f}%", cs, cs_a, "pp", True, iss.estado_vs_meta(cs, S.META_CSAT), serie, f"IND-04 · meta {S.META_CSAT:g}%", "s_cs")
with c[1]:
    render_kpi_card("Esforço percebido (CES)", f"{ce:.2f}/7", ce, ce_a, "abs", True, None, None, "IND-05 · maior = mais fácil", "s_ce")
with c[2]:
    render_kpi_card("Respostas no período", f"{sat.total_respostas(s):,}".replace(",", "."), sat.total_respostas(s), sat.total_respostas(ant["satisfacao"]) if tem_ant else None, "%", True, None, None, "base da amostra", "s_rs")
with c[3]:
    abaixo = int((rk["csat"] < S.META_CSAT).sum())
    render_kpi_card("Sistemas abaixo da meta", f"{abaixo}/{len(rk)}", None, None, "abs", False, "critico" if abaixo else "saudavel", None, "CSAT < meta", "s_ab")

# Tendência semanal do CSAT por sistema com a meta.
render_linhas(sat.serie_csat_semanal(s), "semana", "csat", "sistema", "CSAT semanal por sistema", "s_l", meta=S.META_CSAT, sufixo="%", rotulo_y="CSAT (%)")
# Mapa de calor sistema × órgão e ranking de satisfação.
a, b = st.columns(2)
with a:
    render_heatmap(sat.matriz_csat(s), "CSAT (%) · sistema × órgão", "s_h", "saude", 50, 95, ".0f", "%")
with b:
    render_ranking(rk, "sistema", "csat", "Ranking de satisfação", "s_r", ".1f", "%", S.META_CSAT)

subtitulo("Distribuição semanal do CSAT", "Cada ponto de caixa é uma semana do período; mostra estabilidade, não apenas a média.")
# Boxplot: mostra a variação semanal, não só a média.
dist = sat.serie_csat_semanal(s)
if not dist.empty:
    fig = px.box(dist, x="sistema", y="csat", color="sistema", points="all")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="CSAT (%)")
    render_plotly(fig, "s_box", 320)
st.caption("SUS, confiança, clareza e percepção espontânea (lojas de aplicativos): INFORMAÇÃO NÃO DISPONIBILIZADA.")
