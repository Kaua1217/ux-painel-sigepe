import pandas as pd
import pytest

from config import settings as S
from data.loaders.mock_loader import gerar_todos_os_dados
from data.schemas.schema_definitions import SCHEMAS, validar_schema, validar_todos


@pytest.fixture(scope="module")
def dados():
    """Gera os dados sintéticos uma única vez para todos os testes deste arquivo."""
    return gerar_todos_os_dados()


def test_contrato_de_dados_valido(dados):
    """Todas as tabelas respeitam o contrato (colunas e tipos)."""
    assert validar_todos(dados) == []


def test_todas_as_tabelas_presentes(dados):
    """Todas as tabelas do contrato existem e têm linhas (exceto erros_log, que só vem de dados oficiais)."""
    for nome in SCHEMAS:
        assert nome in dados
        if nome != "erros_log":  # logs de erro não existem na base sintética
            assert len(dados[nome]) > 0


def test_determinismo_com_seed():
    """Duas gerações com a mesma semente produzem exatamente os mesmos dados."""
    a, b = gerar_todos_os_dados(), gerar_todos_os_dados()
    pd.testing.assert_frame_equal(a["uso"], b["uso"])
    pd.testing.assert_frame_equal(a["incidentes"], b["incidentes"])


def test_cobertura_de_dimensoes(dados):
    """Aparecem todos os sistemas, órgãos e perfis configurados, e as 10 jornadas."""
    assert set(dados["uso"]["sistema"]) == set(S.SISTEMAS)
    assert set(dados["uso"]["orgao"]) == set(S.ORGAOS)
    assert set(dados["uso"]["perfil"]) == set(S.PERFIS)
    assert len(dados["jornada_dim"]) == 10


def test_periodo_dos_dados(dados):
    """O período gerado corresponde ao configurado."""
    assert dados["uso"]["data"].min() == pd.Timestamp(S.DATA_INICIO)
    assert dados["uso"]["data"].max() == pd.Timestamp(S.DATA_FIM)


def test_invariantes_numericas(dados):
    """Regras lógicas: ativos ≤ elegíveis, satisfeitos ≤ respostas, concluídas ≤ iniciadas, disponibilidade entre 0 e 100."""
    u, s, j = dados["uso"], dados["satisfacao"], dados["jornada_conclusao"]
    assert (u["usuarios_ativos"] <= u["elegiveis"]).all()
    assert (s["satisfeitos"] <= s["respostas"]).all()
    assert (j["concluidas"] <= j["iniciadas"]).all()
    assert dados["disponibilidade"]["uptime_pct"].between(0, 100).all()


def test_validar_schema_detecta_coluna_ausente(dados):
    """O validador de contrato realmente acusa coluna faltante."""
    assert validar_schema(dados["uso"].drop(columns=["elegiveis"]), "uso")


def test_problemas_intencionais_existem(dados):
    """As anomalias planejadas (queda do Beta, incidente do Épsilon) estão nos dados."""
    from indicators import satisfacao as sat
    s = dados["satisfacao"]
    beta = s[s["sistema"] == "Sistema Beta"]
    antes = beta[beta["data"] < "2026-05-01"]
    depois = beta[beta["data"] >= "2026-07-10"]
    assert sat.csat(antes) - sat.csat(depois) > 10
    inc = dados["incidentes"]
    assert ((inc["sistema"] == "Sistema Épsilon") & (inc["duracao_h"] == 14.0)).any()
