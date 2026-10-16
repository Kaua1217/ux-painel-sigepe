"""Smoke test: cada página executa sem exceções sob o AppTest do Streamlit."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
# Lista a página principal e todas as páginas da pasta app/pages.
PAGINAS = ["app/main.py"] + sorted(str(p.relative_to(RAIZ)) for p in (RAIZ / "app" / "pages").glob("*.py"))


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_executa(pagina):
    """Roda cada página no simulador do Streamlit; o teste falha se ocorrer qualquer exceção."""
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
