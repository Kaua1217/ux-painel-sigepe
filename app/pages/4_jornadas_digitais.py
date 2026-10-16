import sys
from pathlib import Path

# Raiz do projeto no sys.path: permite `from app...`, `from config...` mesmo rodando a página isolada.
_RAIZ = Path(__file__).resolve().parent.parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st

from app.components.funnel import render_funnel
from app.components.heatmap import render_heatmap
from app.components.kpi_card import render_kpi_card
from app.components.linhas import render_linhas
from app.components.page_header import subtitulo
from app.components.ranking import render_ranking
from app.state import K_FOCO_JOR, anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from indicators import iss
from indicators import jornadas as jor

dados, f, ant = preparar_pagina(
    "Jornadas Digitais",
    "Se os usuários conseguem concluir as tarefas, quanto tempo levam e em que etapa desistem.",
)
# Sem a fonte de jornadas, a página mostra 'INFORMAÇÃO NÃO DISPONIBILIZADA' e para.
exigir_tabela(f, "jornada_conclusao", "Eficiência da jornada", "Google/Serpro Analytics e eventos de navegação")
tem_ant = anterior_disponivel(ant)
nan = float("nan")
j = f["jornada_conclusao"]
co, co_a = jor.taxa_conclusao(j), jor.taxa_conclusao(ant["jornada_conclusao"]) if tem_ant else nan
tm, tm_a = jor.tempo_medio(j), jor.tempo_medio(ant["jornada_conclusao"]) if tem_ant else nan
# Ranking das jornadas e quantas estão abaixo da meta de conclusão.
rk = jor.ranking_jornadas(j)
abaixo = int((rk["conclusao"] < S.META_CONCLUSAO).sum())

# KPIs: conclusão, tempo médio, volume iniciado e jornadas abaixo da meta.
c = st.columns(4)
with c[0]:
    render_kpi_card("Taxa de conclusão", f"{co:.1f}%", co, co_a, "pp", True, iss.estado_vs_meta(co, S.META_CONCLUSAO),
                    jor.serie_conclusao_semanal(j, None).set_index("semana")["conclusao"], f"IND-06 · meta {S.META_CONCLUSAO:g}%", "j_co")
with c[1]:
    render_kpi_card("Tempo médio de conclusão", f"{tm:.1f} min", tm, tm_a, "%", False, None, None, "IND-07", "j_tm")
with c[2]:
    ini = jor.total_iniciadas(j)
    render_kpi_card("Jornadas iniciadas", f"{ini:,}".replace(",", "."), ini, jor.total_iniciadas(ant["jornada_conclusao"]) if tem_ant else None, "%", True, None, None, "volume", "j_in")
with c[3]:
    render_kpi_card("Jornadas abaixo da meta", f"{abaixo}/{len(rk)}", None, None, "abs", False, "critico" if abaixo else "saudavel", None, "conclusão < meta", "j_ab")

# Ranking de conclusão por jornada e mapa de calor jornada × órgão.
a, b = st.columns([3, 2])
with a:
    render_ranking(rk, "jornada", "conclusao", "Conclusão por jornada (pior → melhor)", "j_r", ".1f", "%", S.META_CONCLUSAO)
with b:
    render_heatmap(jor.matriz_conclusao(j), "Conclusão (%) · jornada × órgão", "j_h", "saude", 50, 95, ".0f", "%")

subtitulo("Investigar uma jornada", "Funil conceitual: a conclusão final é a observada; o abandono por etapa é distribuído por peso (etapas oficiais: INFORMAÇÃO NÃO DISPONIBILIZADA).")
# Seleção da jornada em foco (respeita o drill-down vindo de outra página).
opcoes = list(rk.sort_values("jornada")["jornada"])
foco = st.session_state.get(K_FOCO_JOR)
sel = st.selectbox("Jornada em foco", opcoes, index=opcoes.index(foco) if foco in opcoes else 0, key="j_sel")
# Recorte da jornada escolhida.
jj = j[j["jornada"] == sel]
# Funil conceitual da jornada e sua tendência comparada à média do sistema.
a, b = st.columns(2)
with a:
    render_funnel(jor.funil(jj, dados["jornada_funil"], sel), f"Funil · {sel}", "j_fun")
with b:
    sistema = jj["sistema"].iloc[0]
    serie = jor.serie_conclusao_semanal(jj, None).assign(serie=sel)
    serie_s = jor.serie_conclusao_semanal(j[j["sistema"] == sistema], None).assign(serie=f"Média {sistema}")
    import pandas as pd
    render_linhas(pd.concat([serie, serie_s]), "semana", "conclusao", "serie", "Conclusão semanal", "j_l", meta=S.META_CONCLUSAO, sufixo="%", rotulo_y="%")

# Tabela do ranking para consulta (transparência dos números).
with st.expander("Tabela do ranking de jornadas"):
    t = rk.copy()
    t["conclusao"] = t["conclusao"].round(1)
    t["tempo_medio_min"] = t["tempo_medio_min"].round(1)
    st.dataframe(t.rename(columns={"jornada": "Jornada", "sistema": "Sistema", "iniciadas": "Iniciadas",
                                    "conclusao": "Conclusão (%)", "tempo_medio_min": "Tempo médio (min)"}),
                 hide_index=True, width="stretch")
