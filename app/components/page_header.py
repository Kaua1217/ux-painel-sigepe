"""Cabeçalho padrão: identidade do produto + seção atual + selo de provisoriedade."""
from __future__ import annotations

import streamlit as st

from config import settings as S


def render_header(secao: str, descricao: str) -> None:
    """Cabeçalho de toda página: marca, título 'UX - <Seção>', descrição e selo de dado provisório/sintético."""
    st.markdown(
        f"""<p class="ux-kicker">{S.APP_MARCA_VISIVEL} · {S.APP_NOME_COMPLETO}</p>
<h1 class="ux-title">{S.APP_MARCA_VISIVEL} - {secao}</h1>
<p class="ux-desc">{descricao}</p>
<span class="ux-selo">{S.SELO_INDICADOR}</span><span class="ux-muted">{S.aviso_dados()}</span>""",
        unsafe_allow_html=True,
    )


def subtitulo(texto: str, nota: str | None = None) -> None:
    """Subtítulo de bloco, com nota explicativa opcional logo abaixo."""
    st.markdown(f'<div class="ux-h2">{texto}</div>', unsafe_allow_html=True)
    if nota:
        st.markdown(f'<span class="ux-muted">{nota}</span>', unsafe_allow_html=True)
