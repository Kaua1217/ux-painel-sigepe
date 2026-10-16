"""Estado global: filtros (session_state), drill-down e preparação padrão de cada página."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from app.components.page_header import render_header
from config import settings as S
from config.theme import aplicar_estilo_global
from indicators import comum

def carregar_dados() -> dict:
    """Único ponto de seleção da fonte: sintética (padrão) ou oficial (PULSO_FONTE=oficial)."""
    if S.fonte_dados() == "oficial":
        from data.loaders.official_loader import carregar_dados as _c
    else:
        from data.loaders.mock_loader import carregar_dados as _c
    return _c()


# Chaves do st.session_state: o estado dos filtros sobrevive à troca de página.
K_INI, K_FIM = "pulso_data_inicio", "pulso_data_fim"
K_SIS, K_ORG, K_PER = "pulso_sistemas_selecionados", "pulso_orgaos_selecionados", "pulso_perfis_selecionados"
# Chaves do 'foco' (drill-down): sistema/jornada escolhidos em outra página.
K_FOCO_SIS, K_FOCO_JOR = "pulso_sistema_foco", "pulso_jornada_foco"
K_ATALHO = "pulso_atalho"


def inicializar_estado(dados: dict) -> None:
    """Define valores iniciais dos filtros (últimos N dias, sem seleção = 'todos'). Não sobrescreve o que já existe."""
    mn, mx = comum.intervalo_datas(dados)
    fim = mx.date()
    ini = max(fim - timedelta(days=S.JANELA_PADRAO_DIAS - 1), mn.date())
    st.session_state.setdefault(K_INI, ini)
    st.session_state.setdefault(K_FIM, fim)
    st.session_state.setdefault(K_SIS, [])
    st.session_state.setdefault(K_ORG, [])
    st.session_state.setdefault(K_PER, [])
    st.session_state.setdefault(K_FOCO_SIS, None)
    st.session_state.setdefault(K_FOCO_JOR, None)
    st.session_state.setdefault(K_ATALHO, "Últimos 120 dias")


def _cb_periodo():
    """Callback: o usuário editou o período manualmente → guarda as datas e marca o atalho como 'Personalizado'."""
    v = st.session_state.get("w_periodo")
    if isinstance(v, (tuple, list)) and len(v) == 2:
        st.session_state[K_INI], st.session_state[K_FIM] = v
        st.session_state[K_ATALHO] = "Personalizado"


def _cb_atalho(dados):
    """Callback: o usuário escolheu um atalho (ex.: 'Últimos 30 dias') → recalcula as datas a partir do fim dos dados."""
    escolha = st.session_state.get("w_atalho")
    st.session_state[K_ATALHO] = escolha
    dias = S.PERIODOS_ATALHO.get(escolha, "x")
    if dias == "x":
        return
    mn, mx = comum.intervalo_datas(dados)
    fim = mx.date()
    ini = mn.date() if dias is None else max(fim - timedelta(days=dias - 1), mn.date())
    st.session_state[K_INI], st.session_state[K_FIM] = ini, fim


def _espelho(chave_w: str, chave_estado: str):
    """Cria um callback que copia o valor do widget para o estado global (evita perder o filtro ao navegar)."""
    return lambda: st.session_state.__setitem__(chave_estado, list(st.session_state[chave_w]))


def renderizar_sidebar_filtros(dados: dict) -> None:
    """Desenha a barra lateral: identidade, período, filtros de sistema/órgão/perfil e foco ativo."""
    mn, mx = (x.date() for x in comum.intervalo_datas(dados))
    with st.sidebar:
        st.markdown(f'<div class="ux-side-sec">IDENTIDADE</div><div class="ux-brand">{S.APP_MARCA_VISIVEL}</div>'
                    f'<div class="ux-brand-sub">{S.APP_NOME_COMPLETO}</div>', unsafe_allow_html=True)
        st.markdown('<div class="ux-side-sec">FILTROS</div>', unsafe_allow_html=True)
        opcoes = ["Personalizado"] + list(S.PERIODOS_ATALHO)
        # Sincroniza o widget com o estado global antes de desenhá-lo.
        st.session_state["w_atalho"] = st.session_state[K_ATALHO] if st.session_state[K_ATALHO] in opcoes else "Personalizado"
        st.selectbox("Atalho de período", opcoes, key="w_atalho", on_change=_cb_atalho, args=(dados,))
        st.session_state["w_periodo"] = (st.session_state[K_INI], st.session_state[K_FIM])
        st.date_input("Período", min_value=mn, max_value=mx, key="w_periodo", format="DD/MM/YYYY", on_change=_cb_periodo)
        for rotulo, lista, k_estado, k_w in [
            ("Sistema", dados["sistemas"], K_SIS, "w_sis"),
            ("Órgão", dados["orgaos"], K_ORG, "w_org"),
            ("Perfil", dados["perfis"], K_PER, "w_per"),
        ]:
            st.session_state[k_w] = [x for x in st.session_state[k_estado] if x in lista]
            st.multiselect(rotulo, lista, key=k_w, placeholder="Todos", on_change=_espelho(k_w, k_estado))
        foco_s, foco_j = st.session_state[K_FOCO_SIS], st.session_state[K_FOCO_JOR]
        if foco_s or foco_j:
            st.markdown('<div class="ux-side-sec">FOCO (DRILL-DOWN)</div>', unsafe_allow_html=True)
            if foco_s:
                st.caption(f"Sistema: **{foco_s}**")
            if foco_j:
                st.caption(f"Jornada: **{foco_j}**")
            if st.button("Limpar foco", key="btn_limpar_foco", width="stretch"):
                st.session_state[K_FOCO_SIS] = None
                st.session_state[K_FOCO_JOR] = None
                st.rerun()
        st.caption(f"{S.SELO_INDICADOR} · {S.aviso_dados()}")


def filtros_ativos() -> dict:
    """Lê os filtros do estado. Se há foco em um sistema, ele prevalece sobre a seleção manual."""
    sis = st.session_state[K_SIS]
    if st.session_state.get(K_FOCO_SIS):
        sis = [st.session_state[K_FOCO_SIS]]
    return dict(ini=pd.Timestamp(st.session_state[K_INI]), fim=pd.Timestamp(st.session_state[K_FIM]),
                sistemas=list(sis), orgaos=list(st.session_state[K_ORG]), perfis=list(st.session_state[K_PER]))


def _aplicar_filtros_com(dados: dict, f: dict) -> dict:
    """Aplica os filtros a todas as tabelas: só filtra por colunas que a tabela realmente possui."""
    out = {}
    for nome, df in dados.items():
        if not isinstance(df, pd.DataFrame):
            out[nome] = df
            continue
        if "data" in df.columns:
            m = (df["data"] >= f["ini"]) & (df["data"] <= f["fim"])
            df = df[m]
        if f["sistemas"] and "sistema" in df.columns:
            df = df[df["sistema"].isin(f["sistemas"])]
        if f["orgaos"] and "orgao" in df.columns:
            df = df[df["orgao"].isin(f["orgaos"])]
        if f["perfis"] and "perfil" in df.columns:
            df = df[df["perfil"].isin(f["perfis"])]
        out[nome] = df
    return out


def aplicar_filtros(dados: dict) -> dict:
    """Aplica os filtros atuais a todas as tabelas."""
    return _aplicar_filtros_com(dados, filtros_ativos())


def obter_dados_periodo_anterior(dados: dict) -> dict:
    """Mesma seleção, porém no período imediatamente anterior e de igual duração (base das variações dos KPIs)."""
    f = filtros_ativos()
    n = (f["fim"] - f["ini"]).days + 1
    g = dict(f, ini=f["ini"] - pd.Timedelta(days=n), fim=f["ini"] - pd.Timedelta(days=1))
    return _aplicar_filtros_com(dados, g)


def ir_para(pagina: str, sistema: str | None = None, jornada: str | None = None) -> None:
    """Navega para outra página levando o foco (sistema/jornada) — é o drill-down."""
    if sistema is not None:
        st.session_state[K_FOCO_SIS] = sistema
    if jornada is not None:
        st.session_state[K_FOCO_JOR] = jornada
    st.switch_page(pagina)


def preparar_pagina(secao: str, descricao: str):
    """Rotina comum às páginas. Retorna (dados_completos, dados_filtrados, dados_período_anterior)."""
    dados = carregar_dados()
    inicializar_estado(dados)
    aplicar_estilo_global()
    renderizar_sidebar_filtros(dados)
    render_header(secao, descricao)
    f = aplicar_filtros(dados)
    if not comum.algum_dado(f):
        st.warning("Nenhum dado para a combinação de filtros selecionada. Ajuste o período, sistema, órgão ou perfil.")
        st.stop()
    return dados, f, obter_dados_periodo_anterior(dados)


def anterior_disponivel(ant: dict) -> bool:
    """True se existem dados no período anterior (senão não se exibe variação)."""
    return comum.algum_dado(ant)


def exigir_tabela(f: dict, tabela: str, dimensao: str, fonte: str) -> None:
    """Interrompe a página com aviso claro quando a fonte não foi disponibilizada / está vazia no recorte."""
    if not comum.tem_dados(f[tabela]):
        st.info(f"**{dimensao}** — {S.NAO_DISPONIBILIZADO} para o recorte selecionado. "
                f"Fonte esperada: {fonte}. Verifique também os filtros (período, sistema, órgão, perfil).")
        st.stop()
