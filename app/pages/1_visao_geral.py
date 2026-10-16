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

from app.components.alert_list import render_alert_list
from app.components.heatmap import render_heatmap
from app.components.kpi_card import render_kpi_card
from app.components.linhas import render_linhas
from app.components.page_header import subtitulo
from app.state import ir_para, anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from indicators import alertas as al
from indicators import estabilidade as est
from indicators import iss
from indicators import jornadas as jor
from indicators import satisfacao as sat
from indicators import suporte as sup
from indicators import uso as usoi

dados, f, ant = preparar_pagina(
    "Visão Geral",
    "O que está acontecendo com os sistemas, onde estão os principais problemas e quais pontos precisam de atenção?",
)
# Só mostra variações se houver dados no período anterior.
tem_ant = anterior_disponivel(ant)
nan = float("nan")

# Valor atual e do período anterior de cada indicador (NaN quando não há fonte).
iss_g = iss.iss_geral(f)
iss_a = iss.iss_geral(ant) if tem_ant else nan
ad, ad_a = usoi.adocao(f["uso"]), usoi.adocao(ant["uso"]) if tem_ant else nan
cs, cs_a = sat.csat(f["satisfacao"]), sat.csat(ant["satisfacao"]) if tem_ant else nan
co, co_a = jor.taxa_conclusao(f["jornada_conclusao"]), jor.taxa_conclusao(ant["jornada_conclusao"]) if tem_ant else nan
pm, pm_a = sup.chamados_por_mil(f["suporte"], f["uso"]), sup.chamados_por_mil(ant["suporte"], ant["uso"]) if tem_ant else nan
dp, dp_a = est.disponibilidade(f["disponibilidade"]), est.disponibilidade(ant["disponibilidade"]) if tem_ant else nan

# séries semanais agregadas (sparklines)
# Séries semanais agregadas, usadas nos mini-gráficos dos cartões.
s_iss = iss.iss_serie_semanal(f).groupby("semana")["ISS"].mean()
s_ad = usoi.serie_adocao_semanal(f["uso"], None).set_index("semana")["adocao"]
s_cs = sat.serie_csat_semanal(f["satisfacao"], None).set_index("semana")["csat"]
s_co = jor.serie_conclusao_semanal(f["jornada_conclusao"], None).set_index("semana")["conclusao"]
s_pm = sup.serie_por_mil_semanal(f["suporte"].assign(g="t"), f["uso"].assign(g="t"), "g").set_index("semana")["por_mil"]
s_dp = est.serie_disponibilidade_semanal(f["disponibilidade"], None).set_index("semana")["uptime_pct"]

# Linha de 6 KPIs: ISS, adoção, CSAT, conclusão, chamados/mil e disponibilidade.
cols = st.columns(6)
with cols[0]:
    render_kpi_card("Índice de Saúde (ISS)", f"{iss_g:.0f}/100", iss_g, iss_a, "abs", True, iss.classificar(iss_g), s_iss, "IND-01 · 0–100", "k_iss")
with cols[1]:
    render_kpi_card("Taxa de adoção", f"{ad:.1f}%", ad, ad_a, "pp", True, iss.estado_vs_meta(ad, S.META_ADOCAO), s_ad, f"meta {S.META_ADOCAO:g}%", "k_ad")
with cols[2]:
    render_kpi_card("Satisfação (CSAT)", f"{cs:.1f}%", cs, cs_a, "pp", True, iss.estado_vs_meta(cs, S.META_CSAT), s_cs, f"meta {S.META_CSAT:g}%", "k_cs")
with cols[3]:
    render_kpi_card("Conclusão de jornadas", f"{co:.1f}%", co, co_a, "pp", True, iss.estado_vs_meta(co, S.META_CONCLUSAO), s_co, f"meta {S.META_CONCLUSAO:g}%", "k_co")
with cols[4]:
    render_kpi_card("Chamados / 1.000 usuários", f"{pm:.1f}", pm, pm_a, "%", False, None, s_pm, "demanda de suporte", "k_pm")
with cols[5]:
    render_kpi_card("Disponibilidade", f"{dp:.2f}%", dp, dp_a, "pp", True, iss.estado_vs_meta(dp, S.META_DISPONIBILIDADE, tolerancia=0.005), s_dp, f"meta {S.META_DISPONIBILIDADE:g}%", "k_dp")

# Matriz sistema × dimensão (0–100), do mais crítico para o mais saudável.
tab = iss.calcular_iss_por_sistema(f).sort_values("ISS")
subtitulo("Matriz de desempenho por sistema", "Escore 0–100 por dimensão; ordenado do que mais precisa de atenção para o mais saudável. Normalização provisória (ver docs/metodologia.md).")
render_heatmap(tab[iss.DIMENSOES + ["ISS"]], "Escore por dimensão (0–100)", "h_matriz", "saude", 0, 100, ".0f")

# Tendência do ISS (esquerda) e os 3 alertas mais graves (direita).
c1, c2 = st.columns([3, 2])
with c1:
    subtitulo("Tendência do Índice de Saúde")
    render_linhas(iss.iss_serie_semanal(f), "semana", "ISS", "sistema", "ISS semanal por sistema", "l_iss",
                  meta=S.FAIXAS_ISS["saudavel"], rotulo_y="ISS (0–100)")
with c2:
    subtitulo("Principais alertas")
    alertas = al.gerar_alertas(f)
    render_alert_list(alertas, "home_alert", maximo=3)
    st.caption("Todos os alertas e oportunidades em “Alertas e Oportunidades”.")

subtitulo("Aprofundar a investigação", "Visão geral → sistema → dimensão → período → jornada → problema → oportunidade")
# Drill-down guiado: escolhe sistema e dimensão e abre a página correspondente.
d1, d2, d3 = st.columns([2, 2, 1])
sis = d1.selectbox("Sistema", dados["sistemas"], key="dd_sis")
destinos = {t: p for p, t, _ in S.PAGINAS[1:]}
dim = d2.selectbox("Dimensão", list(destinos), key="dd_dim")
d3.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
if d3.button("Abrir →", key="dd_go", width="stretch"):
    ir_para(destinos[dim], sistema=sis)

# Mostra quais fontes foram carregadas (útil com dados oficiais parciais).
cob = dados.get("cobertura")
if cob:
    with st.expander("Cobertura das fontes de dados"):
        st.dataframe(pd.DataFrame({"Fonte": list(cob), "Situação": list(cob.values())}), hide_index=True, width="stretch")
