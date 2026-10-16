"""Lista de alertas com drill-down (botão 'Investigar')."""
from __future__ import annotations

import streamlit as st

from config.theme import cor_por_estado

# Para qual página o botão 'Investigar' leva, conforme a dimensão do alerta.
_DESTINO = {
    "Satisfação": "pages/3_experiencia_satisfacao.py",
    "Suporte": "pages/5_suporte_atendimento.py",
    "Jornadas Digitais": "pages/4_jornadas_digitais.py",
    "Estabilidade": "pages/6_estabilidade.py",
    "Uso": "pages/2_uso_dos_sistemas.py",
}


def render_alert_list(alertas, key: str, maximo: int | None = None) -> None:
    """Desenha os alertas como cartões (nível + sistema + descrição + variação) com botão de drill-down.
    `maximo` limita quantos aparecem (ex.: 3 na Visão Geral).
    """
    from app.state import ir_para  # import tardio evita ciclo

    if not alertas:
        st.success("✔ Nenhum alerta ativo para o recorte selecionado (conforme limiares provisórios).")
        return
    for i, a in enumerate(alertas[:maximo] if maximo else alertas):
        # Nível e símbolo (✖ / ▲) acompanham a cor: o alerta é legível sem depender de cor.
        estado = "critico" if a.nivel == "crítico" else "atencao"
        simbolo = "✖" if estado == "critico" else "▲"
        with st.container(border=True):
            c1, c2 = st.columns([5, 1.3])
            with c1:
                st.markdown(
                    f'<span class="ux-estado" style="color:{cor_por_estado(estado)}">{simbolo} {a.nivel.upper()}</span> '
                    f'<span class="ux-muted">· {a.sistema} · {a.dimensao}</span><br>'
                    f'<b>{a.indicador}</b> — {a.descricao}<br>'
                    f'<span class="ux-muted">Variação {a.variacao:+.1f} {a.unidade} · severidade {a.score_severidade:.0f}</span>',
                    unsafe_allow_html=True)
            with c2:
                # Drill-down: abre a página da dimensão já focada no sistema do alerta.
                if st.button("Investigar →", key=f"{key}_{i}", width="stretch"):
                    ir_para(_DESTINO.get(a.dimensao, "pages/1_visao_geral.py"), sistema=a.sistema)
