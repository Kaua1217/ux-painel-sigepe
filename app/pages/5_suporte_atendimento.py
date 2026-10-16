import sys
from pathlib import Path

# Raiz do projeto no sys.path: permite `from app...`, `from config...` mesmo rodando a página isolada.
_RAIZ = Path(__file__).resolve().parent.parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import numpy as np
import pandas as pd
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
from indicators import suporte as sup

dados, f, ant = preparar_pagina(
    "Suporte e Atendimento",
    "Quanto suporte os usuários demandam, com que rapidez são atendidos e se a demanda se relaciona com a satisfação.",
)
tem_ant = anterior_disponivel(ant)
nan = float("nan")
# Suporte e uso filtrados; os indicadores de chamados são normalizados pelos usuários ativos.
s, u = f["suporte"], f["uso"]
pm, pm_a = sup.chamados_por_mil(s, u), sup.chamados_por_mil(ant["suporte"], ant["uso"]) if tem_ant else nan
tm, tm_a = sup.tmr(s), sup.tmr(ant["suporte"]) if tem_ant else nan
tp, tp_a = sup.tpr(s), sup.tpr(ant["suporte"]) if tem_ant else nan
rc, rc_a = sup.reincidencia(s), sup.reincidencia(ant["suporte"]) if tem_ant else nan

# KPIs: chamados por mil usuários, tempo de resolução, primeira resposta e reincidência.
c = st.columns(4)
with c[0]:
    render_kpi_card("Chamados / 1.000 usuários", f"{pm:.1f}", pm, pm_a, "%", False, None,
                    sup.serie_por_mil_semanal(s.assign(g="t"), u.assign(g="t"), "g").set_index("semana")["por_mil"],
                    f"IND-08 · {sup.chamados_total(s):,} chamados".replace(",", "."), "p_pm")
with c[1]:
    render_kpi_card("Tempo médio de resolução", f"{tm:.1f} h", tm, tm_a, "%", False, iss.estado_vs_meta(tm, S.META_TMR_HORAS, False), None, f"IND-09 · meta {S.META_TMR_HORAS:g} h", "p_tm")
with c[2]:
    render_kpi_card("Primeira resposta", f"{tp:.1f} h", tp, tp_a, "%", False, None, None, "tempo até 1ª resposta", "p_tp")
with c[3]:
    render_kpi_card("Reincidência", f"{rc:.1f}%", rc, rc_a, "pp", False, iss.estado_vs_meta(rc, S.META_REINCIDENCIA, False), None, f"meta ≤ {S.META_REINCIDENCIA:g}%", "p_rc")

# Sem base de usuários ativos (Analytics não disponibilizado), exibe o volume absoluto.
serie_pm = sup.serie_por_mil_semanal(s, u)
if serie_pm.empty:  # sem base de usuários ativos (Analytics não disponibilizado): volume absoluto
    render_linhas(sup.serie_chamados_semanal(s), "semana", "chamados", "sistema", "Chamados por semana (sem normalização por usuários: INFORMAÇÃO NÃO DISPONIBILIZADA)", "p_l", rotulo_y="chamados")
else:
    render_linhas(serie_pm, "semana", "por_mil", "sistema", "Chamados por 1.000 usuários (semanal)", "p_l", rotulo_y="chamados / 1.000")
# Mapa de calor sistema × órgão (menos chamados = melhor) e ranking de tempo de resolução.
a, b = st.columns(2)
with a:
    render_heatmap(sup.matriz_por_mil(s, u), "Chamados / 1.000 usuários · sistema × órgão", "p_h", "saude", None, None, ".1f", invertida=True)
with b:
    render_ranking(sup.ranking_tmr(s), "sistema", "tmr_horas", "Tempo médio de resolução por sistema", "p_r", ".1f", " h", S.META_TMR_HORAS, maior_melhor=False)

subtitulo("Demanda de suporte × satisfação", "Cada ponto é um sistema em uma semana. Correlação não implica causalidade.")
# Cruza demanda de suporte e CSAT por semana/sistema; serve só para exploração (correlação não é causalidade).
m = serie_pm.merge(sat.serie_csat_semanal(f["satisfacao"]), on=["semana", "sistema"]).dropna()
if len(m) >= 5:
    r = float(np.corrcoef(m["por_mil"], m["csat"])[0, 1])
    fig = px.scatter(m, x="por_mil", y="csat", color="sistema", title=f"Correlação de Pearson r = {r:.2f}")
    # Reta de tendência (mínimos quadrados).
    a1, b1 = np.polyfit(m["por_mil"], m["csat"], 1)
    xs = np.linspace(m["por_mil"].min(), m["por_mil"].max(), 20)
    fig.add_scatter(x=xs, y=a1 * xs + b1, mode="lines", name="Tendência", line=dict(dash="dash"))
    fig.update_layout(xaxis_title="Chamados / 1.000 usuários", yaxis_title="CSAT (%)")
    render_plotly(fig, "p_sc", 340)
else:
    st.info("Pontos insuficientes para correlação no recorte selecionado.")
st.caption("Categorias de chamado, canais e causa raiz: INFORMAÇÃO NÃO DISPONIBILIZADA.")
