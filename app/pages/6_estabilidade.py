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
from app.components.timeline import render_timeline_incidentes
from app.state import anterior_disponivel, exigir_tabela, preparar_pagina
from config import settings as S
from indicators import estabilidade as est
from indicators import iss

dados, f, ant = preparar_pagina(
    "Estabilidade",
    "Se os serviços estão disponíveis e rápidos, e quando e onde ocorreram incidentes.",
)
tem_ant = anterior_disponivel(ant)
nan = float("nan")
# Tabelas técnicas (disponibilidade, desempenho, incidentes) e indicadores do período atual.
d, p, inc = f["disponibilidade"], f["desempenho"], f["incidentes"]
dp, dp_a = est.disponibilidade(d), est.disponibilidade(ant["disponibilidade"]) if tem_ant else nan
tr, tr_a = est.tempo_resposta(p), est.tempo_resposta(ant["desempenho"]) if tem_ant else nan
te, te_a = est.taxa_erro(p), est.taxa_erro(ant["desempenho"]) if tem_ant else nan

e = f["erros_log"]


# Bloco opcional: erros de log (fonte oficial). Só aparece se houver dados.
def bloco_erros() -> None:
    if e.empty:
        return
    subtitulo("Erros registrados em log", "Contagem de eventos por módulo (log de eventos). Significado de IN_CLASSIFICACAO: a confirmar com a organização.")
    k1, k2 = st.columns([1, 3])
    with k1:
        render_kpi_card("Eventos de erro no período", f"{est.total_erros_log(e):,}".replace(",", "."), None, None, "abs", False, None,
                        est.serie_erros_semanal(e, None).set_index("semana")["erros"], "log de eventos", "e_er")
    with k2:
        render_linhas(est.serie_erros_semanal(e), "semana", "erros", "modulo", "Eventos de erro por semana e módulo", "e_el", rotulo_y="eventos")


tem_mon = not (d.empty and p.empty)  # há monitoramento técnico (disponibilidade/desempenho)?
n = est.total_incidentes(inc)
mttr = est.tempo_medio_recuperacao(inc) if not inc.empty else nan
n_ant = est.total_incidentes(ant["incidentes"]) if tem_ant else None

if not tem_mon:
    st.info(f"Disponibilidade e tempo de resposta: {S.NAO_DISPONIBILIZADO} (fonte esperada: monitoramento técnico). "
            "Incidentes não medem disponibilidade: não é possível derivar uptime deles.")
else:
    # KPIs de disponibilidade, tempo de resposta e taxa de erro.
    c = st.columns(3)
    with c[0]:
        render_kpi_card("Disponibilidade", f"{dp:.2f}%", dp, dp_a, "pp", True, iss.estado_vs_meta(dp, S.META_DISPONIBILIDADE, tolerancia=0.005),
                        est.serie_disponibilidade_semanal(d, None).set_index("semana")["uptime_pct"], f"IND-10 · meta {S.META_DISPONIBILIDADE:g}%", "e_dp")
    with c[1]:
        render_kpi_card("Tempo de resposta", f"{tr:.0f} ms", tr, tr_a, "%", False, iss.estado_vs_meta(tr, S.META_TEMPO_RESPOSTA_MS, False), None, f"meta ≤ {S.META_TEMPO_RESPOSTA_MS:g} ms", "e_tr")
    with c[2]:
        render_kpi_card("Taxa de erro", f"{te:.2f}%", te, te_a, "%", False, iss.estado_vs_meta(te, S.META_TAXA_ERRO, False), None, f"meta ≤ {S.META_TAXA_ERRO:g}%", "e_te")
    render_linhas(est.serie_disponibilidade_semanal(d), "semana", "uptime_pct", "sistema", "Disponibilidade semanal por sistema", "e_l",
                  meta=S.META_DISPONIBILIDADE, sufixo="%", rotulo_y="%")

# Incidentes: aparecem mesmo sem monitoramento.
if inc.empty:
    st.info(f"Incidentes: {S.NAO_DISPONIBILIZADO} no recorte selecionado.")
else:
    subtitulo("Incidentes", "Severidade PROVISÓRIA: definida pela duração (≥6 h Crítica, ≥3 h Média, demais Baixa), até a organização informar a classificação oficial.")
    k = st.columns(3)
    with k[0]:
        render_kpi_card("Incidentes no período", f"{n}", n, n_ant, "abs", False, None, None, "IND-11", "e_in")
    with k[1]:
        render_kpi_card("Recuperação média", "—" if mttr != mttr else f"{mttr:.1f} h", None, None, "abs", False, None, None, "IND-11 · duração média", "e_mt")
    with k[2]:
        render_kpi_card("Horas em incidente", f"{inc['duracao_h'].sum():.1f} h", None, None, "abs", False, None, None, "soma das durações · conceitual", "e_hi")
    render_timeline_incidentes(inc, "Linha do tempo de incidentes (símbolo = severidade · tamanho = duração)", "e_t")
    a, b = st.columns([3, 2]) if tem_mon else (st.container(), st.container())
    with a:
        if tem_mon:
            render_heatmap(est.matriz_disponibilidade_mensal(d), "Disponibilidade mensal (%)", "e_h", "saude", 98, 100, ".2f")
        else:
            sev = est.incidentes_por_severidade(inc)
            subtitulo("Incidentes por severidade")
            st.dataframe(sev, hide_index=True, width="stretch")
    with b:
        subtitulo("Incidentes recentes")
        t = inc.sort_values("data", ascending=False).head(8).copy()
        t["data"] = t["data"].dt.strftime("%d/%m/%Y")
        st.dataframe(t.rename(columns={"incidente_id": "ID", "sistema": "Sistema", "data": "Data", "duracao_h": "Duração (h)", "severidade": "Severidade"}),
                     hide_index=True, width="stretch")
bloco_erros()
st.caption("Dados técnicos por sistema: filtros de órgão e perfil não se aplicam a esta página. Tempo de recuperação oficial e funcionalidades críticas: INFORMAÇÃO NÃO DISPONIBILIZADA.")
