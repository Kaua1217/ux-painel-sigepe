import sys
from pathlib import Path

# Raiz do projeto no sys.path: permite `from app...`, `from config...` mesmo rodando a página isolada.
_RAIZ = Path(__file__).resolve().parent.parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.alert_list import render_alert_list
from app.components.page_header import subtitulo
from app.state import anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from config.theme import cor_texto_sobre_marca, render_plotly, tokens_atuais
from indicators import alertas as al

dados, f, ant = preparar_pagina(
    "Alertas e Oportunidades",
    "Onde agir primeiro: alertas por severidade e oportunidades de melhoria priorizadas por impacto e esforço.",
)
# Gera os alertas do recorte e aplica o filtro de nível escolhido.
alertas = al.gerar_alertas(f)
niveis = st.multiselect("Nível", ["crítico", "atenção"], default=["crítico", "atenção"], key="a_niv")
visiveis = [a for a in alertas if a.nivel in niveis]
# Resumo: críticos, atenção e sistemas afetados.
c = st.columns(3)
c[0].metric("Alertas críticos", sum(a.nivel == "crítico" for a in alertas))
c[1].metric("Alertas de atenção", sum(a.nivel == "atenção" for a in alertas))
c[2].metric("Sistemas com alerta", len({a.sistema for a in alertas}))

subtitulo("Alertas ativos", "Comparação entre a 2ª e a 1ª metade do período selecionado; limiares em config/settings.py.")
render_alert_list(visiveis, "a_lst")

# Oportunidades de melhoria (alertas + adoção baixa), já ordenadas por prioridade.
ops = al.oportunidades_melhoria(f, alertas)
subtitulo("Matriz Impacto × Esforço", "Oportunidades de melhoria PROVISÓRIAS. Esforço é estimado por dimensão (config/settings.py), não por levantamento real.")
if ops.empty:
    st.info("Sem oportunidades identificadas para o recorte.")
else:
    t = tokens_atuais()
    # Matriz Impacto × Esforço: cada ponto numerado corresponde à linha da tabela abaixo.
    fig = px.scatter(ops, x="esforco", y="impacto", color="dimensao", hover_name="oportunidade", text=ops.index + 1)
    fig.update_traces(marker=dict(size=16, line=dict(width=1, color=t["text_muted"])), textposition="middle center", textfont=dict(color=cor_texto_sobre_marca(), size=10))
    # Linhas que dividem os quadrantes (ganhos rápidos, estratégicos, rotina, reavaliar).
    fig.add_hline(y=5, line_dash="dot", line_color=t["text_muted"])
    fig.add_vline(x=3, line_dash="dot", line_color=t["text_muted"])
    for x, y, txt in [(1.2, 9.6, "Ganhos rápidos"), (4.8, 9.6, "Projetos estratégicos"), (1.2, 0.4, "Rotina"), (4.8, 0.4, "Reavaliar")]:
        fig.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(color=t["text_muted"], size=11))
    fig.update_xaxes(range=[0.5, 5.5], title="Esforço (1 baixo → 5 alto)", dtick=1)
    fig.update_yaxes(range=[0, 10.3], title="Impacto (0–10)")
    render_plotly(fig, "a_mx", 420)
    tab = ops.assign(rank=ops.index + 1)[["rank", "oportunidade", "dimensao", "origem", "impacto", "esforco", "prioridade"]].round(2)
    st.dataframe(tab.rename(columns={"rank": "#", "oportunidade": "Oportunidade", "dimensao": "Dimensão", "origem": "Origem",
                                      "impacto": "Impacto", "esforco": "Esforço", "prioridade": "Prioridade (impacto ÷ esforço)"}),
                 hide_index=True, width="stretch")

# Transparência: mostra os limiares usados para classificar os alertas.
with st.expander("Limiares de alerta vigentes (provisórios)"):
    linhas = [(k, v["atencao"], v["critico"]) for k, v in S.LIMIARES_ALERTA.items()]
    st.dataframe(pd.DataFrame(linhas, columns=["Regra", "Atenção ≥", "Crítico ≥"]), hide_index=True, width="stretch")
    st.caption("Edite config/settings.py → LIMIARES_ALERTA para ajustar. Nenhum limiar é oficial.")
