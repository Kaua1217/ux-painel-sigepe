import numpy as np
import pandas as pd
import pytest

from config import settings as S
from data.loaders.mock_loader import gerar_todos_os_dados
from indicators import alertas as al
from indicators import estabilidade as est
from indicators import iss
from indicators import jornadas as jor
from indicators import satisfacao as sat
from indicators import suporte as sup
from indicators import uso as usoi


@pytest.fixture(scope="module")
def dados():
    """Dados sintéticos gerados uma vez por arquivo de teste."""
    return gerar_todos_os_dados()


def recorte(d, dias):
    """Mantém apenas os últimos `dias` dias de cada tabela com coluna de data."""
    ini = d["uso"]["data"].max() - pd.Timedelta(days=dias - 1)
    return {k: (v[v["data"] >= ini] if isinstance(v, pd.DataFrame) and "data" in v.columns else v) for k, v in d.items()}


# ---- uso
def test_adocao_calculo_simples():
    """Adoção = 80 ativos ÷ 200 elegíveis = 40%."""
    df = pd.DataFrame({"usuarios_ativos": [50, 30], "elegiveis": [100, 100], "data": pd.to_datetime(["2026-01-01"] * 2)})
    assert usoi.adocao(df) == pytest.approx(40.0)


def test_adocao_vazio_nan():
    """Sem dados, o indicador é NaN (não zero)."""
    assert np.isnan(usoi.adocao(pd.DataFrame(columns=["usuarios_ativos", "elegiveis"])))


def test_delta_oeste_tem_baixa_adocao(dados):
    """A anomalia do Delta no Oeste aparece na matriz de adoção."""
    m = usoi.matriz_adocao(recorte(dados, 120)["uso"])
    assert m.loc["Sistema Delta", "Órgão Regional Oeste"] < S.LIMIAR_ADOCAO_ORGAO_BAIXA
    assert m.loc["Sistema Gama", "Órgão Regional Oeste"] > 50


# ---- satisfação / jornadas / suporte
def test_csat_ponderado():
    """CSAT e CES são ponderados pelo número de respostas."""
    df = pd.DataFrame({"satisfeitos": [8, 1], "respostas": [10, 10], "ces_medio": [6, 2]})
    assert sat.csat(df) == pytest.approx(45.0)
    assert sat.ces(df) == pytest.approx(4.0)


def test_conclusao_e_tempo():
    """Taxa de conclusão e tempo médio ponderado por jornadas concluídas."""
    df = pd.DataFrame({"iniciadas": [100, 100], "concluidas": [80, 40], "tempo_medio_min": [10.0, 20.0]})
    assert jor.taxa_conclusao(df) == pytest.approx(60.0)
    assert jor.tempo_medio(df) == pytest.approx((10 * 80 + 20 * 40) / 120)


def test_funil_termina_na_conclusao_observada(dados):
    """A última etapa do funil coincide com a conclusão observada e a retenção só diminui."""
    j = recorte(dados, 90)["jornada_conclusao"]
    nome = "Solicitar férias"
    jj = j[j["jornada"] == nome]
    fn = jor.funil(jj, dados["jornada_funil"], nome)
    assert len(fn) == 5
    assert fn["retencao_pct"].is_monotonic_decreasing
    assert fn["retencao_pct"].iloc[-1] == pytest.approx(jor.taxa_conclusao(jj), abs=0.01)


def test_suporte_ponderacoes():
    """TMR ponderado por chamados, reincidência % e chamados por mil usuários."""
    sp = pd.DataFrame({"chamados": [10, 30], "tmr_horas": [10.0, 50.0], "tpr_horas": [1.0, 3.0], "reincidentes": [1, 6]})
    assert sup.tmr(sp) == pytest.approx(40.0)
    assert sup.reincidencia(sp) == pytest.approx(17.5)
    uso = pd.DataFrame({"usuarios_ativos": [4000]})
    assert sup.chamados_por_mil(sp, uso) == pytest.approx(10.0)


def test_beta_piora_nos_ultimos_60_dias(dados):
    """A degradação planejada do Beta reduz a disponibilidade."""
    r = recorte(dados, 60)
    b = {k: (v[v["sistema"] == "Sistema Beta"] if isinstance(v, pd.DataFrame) and "sistema" in v.columns else v) for k, v in r.items()}
    antes = recorte(dados, 200)
    bb = antes["disponibilidade"][antes["disponibilidade"]["sistema"] == "Sistema Beta"]
    assert est.disponibilidade(b["disponibilidade"]) < est.disponibilidade(bb[bb["data"] < "2026-04-01"]) - 0.5


def test_estabilidade_incidentes_por_severidade(dados):
    """A tabela de severidades vem na ordem certa e soma o total de incidentes."""
    t = est.incidentes_por_severidade(dados["incidentes"])
    assert list(t["severidade"]) == ["Crítica", "Média", "Baixa"]
    assert t["incidentes"].sum() == len(dados["incidentes"])


# ---- ISS
def test_normalizar_limites():
    """A normalização limita os valores a 0–100 e inverte quando pedido."""
    assert iss.normalizar(50, 0, 100) == pytest.approx(50)
    assert iss.normalizar(150, 0, 100) == 100
    assert iss.normalizar(-5, 0, 100) == 0
    assert iss.normalizar(0, 0, 100, inverter=True) == 100


def test_pesos_somam_um():
    """Os pesos do ISS somam 1."""
    assert sum(S.PESOS_ISS.values()) == pytest.approx(1.0)


def test_iss_entre_0_e_100_e_beta_pior_que_gama(dados):
    """ISS fica entre 0 e 100; o Beta (degradado) é pior que o Gama."""
    t = iss.calcular_iss_por_sistema(recorte(dados, 120))
    assert t["ISS"].between(0, 100).all()
    assert t.loc["Sistema Beta", "ISS"] < t.loc["Sistema Gama", "ISS"]


def test_classificar_faixas():
    """Faixas de classificação do ISS."""
    assert iss.classificar(85) == "saudavel"
    assert iss.classificar(70) == "atencao"
    assert iss.classificar(40) == "critico"


def test_estado_vs_meta():
    """Comparação com meta (maior ou menor é melhor) e tolerância de 10%."""
    assert iss.estado_vs_meta(80, 75) == "saudavel"
    assert iss.estado_vs_meta(70, 75) == "atencao"
    assert iss.estado_vs_meta(50, 75) == "critico"
    assert iss.estado_vs_meta(50, 48, maior_melhor=False) == "atencao"
    assert iss.estado_vs_meta(80, 48, maior_melhor=False) == "critico"


def test_serie_semanal_iss(dados):
    """A série semanal do ISS traz as colunas esperadas."""
    s = iss.iss_serie_semanal(recorte(dados, 90))
    assert {"semana", "sistema", "ISS"} <= set(s.columns) and len(s) > 0


# ---- alertas
def test_classificar_limiar():
    """Classificação em crítico/atenção/nenhum e tratamento de NaN."""
    assert al.classificar_limiar(12, "queda_satisfacao_pp") == "crítico"
    assert al.classificar_limiar(6, "queda_satisfacao_pp") == "atenção"
    assert al.classificar_limiar(2, "queda_satisfacao_pp") is None
    assert al.classificar_limiar(float("nan"), "queda_satisfacao_pp") is None


def test_score_cresce_com_nivel_e_usuarios():
    """Severidade maior para nível crítico e para mais usuários afetados."""
    assert al.score_severidade("crítico", 10, 1000) > al.score_severidade("atenção", 10, 1000)
    assert al.score_severidade("crítico", 10, 9000) > al.score_severidade("crítico", 10, 1000)


def test_alertas_concentrados_no_beta(dados):
    """Os alertas gerados são do Beta e vêm ordenados por severidade."""
    a = al.gerar_alertas(recorte(dados, 120))
    assert a and all(x.sistema == "Sistema Beta" for x in a)
    assert any(x.nivel == "crítico" for x in a)
    assert [x.score_severidade for x in a] == sorted([x.score_severidade for x in a], reverse=True)


def test_oportunidades(dados):
    """Oportunidades têm impacto 0–10, esforço 1–5 e incluem a adoção baixa do Oeste."""
    r = recorte(dados, 120)
    op = al.oportunidades_melhoria(r, al.gerar_alertas(r))
    assert not op.empty
    assert op["impacto"].between(0, 10).all() and op["esforco"].between(1, 5).all()
    assert op["oportunidade"].str.contains("Órgão Regional Oeste").any()


def test_limiares_configuraveis(monkeypatch, dados):
    """Alterar os limiares em settings muda a quantidade de alertas."""
    r = recorte(dados, 120)
    base = len(al.gerar_alertas(r))
    monkeypatch.setitem(S.LIMIARES_ALERTA, "queda_satisfacao_pp", {"atencao": 99, "critico": 100})
    assert len(al.gerar_alertas(r)) < base


def test_sem_pizza_em_componentes():
    """Regra do edital: nenhum gráfico de pizza no código."""
    from pathlib import Path
    for p in Path("app").rglob("*.py"):
        txt = p.read_text(encoding="utf-8").lower()
        assert "go.pie" not in txt and "px.pie" not in txt
