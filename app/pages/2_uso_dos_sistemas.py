import sys
from pathlib import Path

# Raiz do projeto no sys.path: permite `from app...`, `from config...` mesmo rodando a página isolada.
_RAIZ = Path(__file__).resolve().parent.parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st

from app.components.heatmap import render_heatmap
from app.components.kpi_card import render_kpi_card
from app.components.linhas import render_linhas
from app.components.page_header import subtitulo
from app.components.ranking import render_ranking
from app.state import ir_para, anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from indicators import iss
from indicators import uso as usoi

dados, f, ant = preparar_pagina(
    "Uso dos Sistemas",
    "Quem está usando, quanto, e onde a adesão está abaixo do esperado para o público elegível.",
)
# Sem a fonte de uso, a página mostra 'INFORMAÇÃO NÃO DISPONIBILIZADA' e para.
exigir_tabela(f, "uso", "Uso e acesso", "Google/Serpro Analytics e registros internos")
tem_ant = anterior_disponivel(ant)
nan = float("nan")
u = f["uso"]
ua, ua_a = usoi.usuarios_ativos_medio(u), usoi.usuarios_ativos_medio(ant["uso"]) if tem_ant else nan
ad, ad_a = usoi.adocao(u), usoi.adocao(ant["uso"]) if tem_ant else nan
sp, sp_a = usoi.sessoes_por_usuario(u), usoi.sessoes_por_usuario(ant["uso"]) if tem_ant else nan
# Matriz de adoção e contagem de combinações sistema×órgão abaixo do limiar.
mat = usoi.matriz_adocao(u)
baixas = int((mat < S.LIMIAR_ADOCAO_ORGAO_BAIXA).sum().sum())

# KPIs de uso.
c = st.columns(4)
with c[0]:
    render_kpi_card("Usuários ativos / dia", f"{ua:,.0f}".replace(",", "."), ua, ua_a, "%", True, None,
                    usoi.serie_usuarios_semanal(u, None).set_index("semana")["usuarios_ativos"], "IND-02", "u_ua")
with c[1]:
    render_kpi_card("Taxa de adoção", f"{ad:.1f}%", ad, ad_a, "pp", True, iss.estado_vs_meta(ad, S.META_ADOCAO),
                    usoi.serie_adocao_semanal(u, None).set_index("semana")["adocao"], f"IND-03 · meta {S.META_ADOCAO:g}%", "u_ad")
with c[2]:
    render_kpi_card("Sessões por usuário", f"{sp:.2f}", sp, sp_a, "%", True, None, None, "profundidade de uso", "u_sp")
with c[3]:
    render_kpi_card("Combinações com adoção baixa", f"{baixas}", None, None, "abs", False,
                    "critico" if baixas else "saudavel", None, f"sistema×órgão abaixo de {S.LIMIAR_ADOCAO_ORGAO_BAIXA:g}%", "u_bx")

subtitulo("Onde a adesão é baixa", "Adoção = usuários ativos diários ÷ público elegível. Valores escritos em cada célula.")
# Mapas de calor: onde a adesão é baixa (por órgão e por perfil).
a, b = st.columns(2)
with a:
    render_heatmap(mat, "Adoção (%) · sistema × órgão", "u_h1", "saude", 0, 90, ".0f", "%")
with b:
    render_heatmap(usoi.matriz_adocao(u, "sistema", "perfil"), "Adoção (%) · sistema × perfil", "u_h2", "saude", 0, 90, ".0f", "%")

# Tendência de usuários ativos e ranking de adoção por órgão.
a, b = st.columns([3, 2])
with a:
    render_linhas(usoi.serie_usuarios_semanal(u), "semana", "usuarios_ativos", "sistema",
                  "Usuários ativos por dia (média semanal)", "u_l1", rotulo_y="usuários")
with b:
    render_ranking(usoi.ranking_adocao(u, "orgao"), "orgao", "adocao", "Adoção por órgão", "u_r1", ".1f", "%", S.META_ADOCAO)

subtitulo("Drill-down")
# Drill-down para as jornadas do sistema escolhido.
d1, d2 = st.columns([3, 1])
s = d1.selectbox("Sistema para investigar jornadas", dados["sistemas"], key="u_dd")
d2.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
if d2.button("Ver jornadas →", key="u_go", width="stretch"):
    ir_para("pages/4_jornadas_digitais.py", sistema=s)
