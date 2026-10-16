"""Ponto de entrada: `python -m streamlit run app/main.py`."""
import sys
from pathlib import Path

# Raiz do projeto, para que `config`, `data`, `indicators` e `app` sejam importáveis ao rodar `python -m streamlit run`.
_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from config import settings as S  # noqa: E402

# Configuração da aba do navegador (título e layout largo). Deve ser a 1ª chamada do Streamlit.
st.set_page_config(page_title=f"{S.APP_MARCA_VISIVEL} — {S.APP_NOME_COMPLETO}", page_icon="📊", layout="wide")

# Monta a navegação a partir da lista em config/settings.PAGINAS.
# A 1ª página é a padrão; as demais ganham uma URL curta derivada do nome do arquivo.
paginas = [
    st.Page(caminho, title=titulo, default=True) if i == 0
    else st.Page(caminho, title=titulo, url_path=caminho.split("/")[1][2:-3])
    for i, (caminho, titulo, _) in enumerate(S.PAGINAS)
]
# Exibe o menu lateral e executa a página selecionada.
st.navigation(paginas, position="sidebar").run()
