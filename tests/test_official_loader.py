"""Testa o official_loader com planilhas FICTÍCIAS geradas em tmp (nenhum dado real no repositório)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from data.loaders import official_loader as L
from data.schemas.schema_definitions import validar_todos

RAIZ = Path(__file__).resolve().parent.parent
# Marcadores falsos: se aparecerem na saída, houve vazamento de texto livre ou IP.
SEGREDO = "TEXTO-LIVRE-NAO-DEVE-ENTRAR"
IP = "10.20.30.40"
# Cabeçalho típico dos logs (com colunas sensíveis que NÃO podem chegar ao painel).
CAB_LOG = ["ID_ERRO", "NO_MODULO", "IN_CLASSIFICACAO", "CO_TRANSACAO", "DS_ACAO_EVENTO", "DT_EVENTO",
           "CO_IP_REQUISITANTE", "CO_IP_SERVIDOR", "CO_ERRO", "CO_TICKET", "TX_VALOR_ANTERIOR", "TX_VALOR_ATUAL", "TX_STACKTRACE"]


@pytest.fixture()
def pasta(tmp_path):
    """Cria, em pasta temporária, planilhas FICTÍCIAS com a mesma estrutura das oficiais (avaliações, central e um log)."""
    rng = np.random.default_rng(1)
    n = 300
    pd.DataFrame({
        "Sistema": "SIGEPE", "Assunto": "x", "Mnemônico": "m", "Funcionalidade": "f", "Versão": 1,
        "Vínculo": rng.choice(["SER", "PEN"], n), "Órgão": rng.choice([101, 102, 103, 104], n),
        "UPAG": np.nan, "UORG": np.nan,
        "Data": pd.to_datetime("2026-05-01") + pd.to_timedelta(rng.integers(0, 90, n), unit="D"),
        "Nota": rng.integers(1, 6, n), "Comentário": SEGREDO, "Informações adicionais": SEGREDO,
    }).to_excel(tmp_path / "AvaliacoesInternas.xlsx", index=False)
    m = 30
    ab = pd.to_datetime("2026-06-01") + pd.to_timedelta(rng.integers(0, 60, m), unit="D")
    pd.DataFrame({
        "Id": range(m), "Título": SEGREDO, "Categoria": "SIGEPE - MÓDULOS > Teste", "Organização": rng.choice(["Org A", "Org B"], m),
        "Status": "Encerrado", "Unidade": "u", "Estado": "UF",
        "Data de abertura": [d.strftime("%m/%d/%Y %H:%M").replace("/0", "/") for d in ab],
        "Data de início de atendimento": [(d + pd.Timedelta(hours=2)).strftime("%m/%d/%Y %H:%M") for d in ab],
        "Dia": 1, "Mês": 1, "Ano": 2026, "Data de Solução": "7/1/2026 10:00", "Tempo em horas do atendimento": rng.integers(5, 100, m),
        "Time": "T", "Descrição do chamado": SEGREDO, "Última ação de acompanhamento": SEGREDO,
        "Título da ultima ação padrão": None, "Chamados Relacionados ": [("123" if i % 5 == 0 else None) for i in range(m)],
    }).to_excel(tmp_path / "CentraSIPEC_SIGEPE.xlsx", index=False)
    linhas = [f"{i}|AFD|FAT|T|acao|{d}|{IP}|{IP}||tk|ant|atu|{SEGREDO}|com|pipe"
              for i, d in enumerate(["01-SEP-25 08.02.26,000000 AM", "01-SEP-25 01.10.00,000000 PM", "03-SEP-25 11.59.59,000000 PM"])]
    pd.DataFrame({"|".join(CAB_LOG): linhas}).to_excel(tmp_path / "AFD.xlsx", index=False)
    return tmp_path


def test_classificacao_dos_arquivos(pasta):
    """Cada arquivo é reconhecido pelo nome ou pelo conteúdo."""
    a = L.classificar_arquivos(pasta)
    assert len(a["avaliacoes"]) == len(a["central"]) == len(a["logs"]) == 1


def test_montar_dados_valido_e_parcial(pasta):
    """O resultado respeita o contrato e as fontes ausentes ficam vazias com aviso."""
    d = L.montar_dados(pasta)
    assert validar_todos(d) == []
    assert d["uso"].empty and d["disponibilidade"].empty and d["jornada_conclusao"].empty
    assert not d["satisfacao"].empty and not d["suporte"].empty and not d["erros_log"].empty
    assert "INFORMAÇÃO NÃO DISPONIBILIZADA" in d["cobertura"]["Analytics → Uso e Jornadas"]


def test_satisfacao_regra_csat_e_perfis(pasta):
    """Regra de CSAT (nota ≥ 4), perfis mapeados e CES vazio."""
    d = L.montar_dados(pasta)["satisfacao"]
    assert d["respostas"].sum() == 300
    assert (d["satisfeitos"] <= d["respostas"]).all()
    assert set(d["perfil"]) <= {"Servidor", "Pensionista"}
    assert d["ces_medio"].isna().all()


def test_suporte_metricas(pasta):
    """Contagem de chamados, reincidência e tempo até a 1ª resposta."""
    d = L.montar_dados(pasta)["suporte"]
    assert d["chamados"].sum() == 30
    assert d["reincidentes"].sum() == 6
    assert d["tpr_horas"].dropna().between(1.9, 2.1).all()
    assert (d["perfil"] == "Não informado").all() and (d["sistema"] == "SIGEPE").all()


def test_logs_data_oracle_e_agregacao(pasta):
    """Datas Oracle são lidas (inclusive 12 h AM/PM) e os eventos são agregados por dia."""
    d = L.montar_dados(pasta)["erros_log"]
    assert d["erros"].sum() == 3
    assert set(d["data"].dt.strftime("%Y-%m-%d")) == {"2025-09-01", "2025-09-03"}
    h = L._data_oracle(pd.Series(["01-SEP-25 12.30.00,000000 AM", "01-SEP-25 12.30.00,000000 PM"]))
    assert list(h.dt.hour) == [0, 12]


def test_nenhum_dado_pessoal_ou_texto_livre_na_saida(pasta):
    """PRIVACIDADE: nenhum texto livre, IP ou coluna sensível chega às tabelas do painel."""
    d = L.montar_dados(pasta)
    for k, v in d.items():
        if isinstance(v, pd.DataFrame):
            blob = v.astype(str).to_csv()
            assert SEGREDO not in blob and IP not in blob, k
            assert not any(c.startswith(("TX_", "CO_IP")) or c in ("Comentário", "Título", "Descrição do chamado") for c in v.columns)


def test_top_n_orgaos():
    """Só os N órgãos mais frequentes ficam separados; o resto vira 'Demais órgãos'."""
    s = pd.Series(["a"] * 5 + ["b"] * 3 + ["c", "d"])
    assert set(L._top_n(s, 2)) == {"a", "b", "Demais órgãos"}


def test_sem_arquivos_erro_claro(tmp_path, monkeypatch):
    """Pasta sem arquivos → erro explicativo."""
    monkeypatch.setenv("PULSO_DADOS_OFICIAIS", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        L.carregar_dados()


@pytest.mark.parametrize("pagina", ["app/main.py"] + [f"app/pages/{p.name}" for p in sorted((RAIZ / "app" / "pages").glob("*.py"))])
def test_paginas_rodam_com_dados_parciais(pasta, monkeypatch, pagina):
    """Todas as páginas abrem sem exceção mesmo com apenas parte das fontes."""
    monkeypatch.setenv("PULSO_FONTE", "oficial")
    monkeypatch.setenv("PULSO_DADOS_OFICIAIS", str(pasta))
    st.cache_data.clear()
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]


def _log_df(linhas):
    """Monta um DataFrame de log no formato 'uma coluna com pipes'."""
    return pd.DataFrame({"|".join(CAB_LOG): linhas})


def test_log_colunas_normais_e_cabecalho_deslocado(tmp_path):
    """O leitor aceita colunas normais e cabeçalho que não está na 1ª linha."""
    corpo = [[1, "AFD", "FAT", "T", "a", "05-OCT-25 10.00.00,000000 AM", IP, IP, "", "tk", "x", "y", SEGREDO]]
    pd.DataFrame(corpo, columns=CAB_LOG).to_excel(tmp_path / "AFD.xlsx", index=False)
    d, motivo = L.ler_log_arquivo(tmp_path / "AFD.xlsx")
    assert motivo == "" and list(d.columns) == ["NO_MODULO", "IN_CLASSIFICACAO", "DT_EVENTO"]
    # título antes do cabeçalho
    bruto = pd.DataFrame([["Relatório de erros"] + [None] * 12, CAB_LOG, *corpo])
    bruto.to_excel(tmp_path / "REQ.xlsx", index=False, header=False)
    d2, motivo2 = L.ler_log_arquivo(tmp_path / "REQ.xlsx")
    assert motivo2 == "" and len(d2) == 1


def test_log_sem_dt_evento_nao_quebra(tmp_path):
    """Arquivos com estrutura diferente não derrubam o painel; viram aviso."""
    pd.DataFrame({"ID_ERRO|NO_MODULO|OUTRA": ["1|AFD|x"]}).to_excel(tmp_path / "AFD.xlsx", index=False)
    pd.DataFrame({"a": [1]}).to_excel(tmp_path / "AvaliacoesInternas.xlsx", index=False)  # estrutura errada
    d = L.montar_dados(tmp_path)  # não pode levantar exceção
    assert d["erros_log"].empty and d["satisfacao"].empty
    assert "ERRO" in d["cobertura"]["Avaliações internas → Satisfação"] or "NÃO" in d["cobertura"]["Avaliações internas → Satisfação"]


def _planilha_incidentes(pasta):
    """Planilha FICTÍCIA de incidentes (com linhas em branco, resumo sensível e uma linha inválida)."""
    pd.DataFrame({
        "TICKETID": ["T1", "T2", None, "T3", "T4"], "RESUMO": [SEGREDO] * 5,
        "SERPRODATAINICIO": pd.to_datetime(["2026-01-05 09:00", "2026-01-06 10:00", None, "2026-01-07 08:00", "2026-01-08 08:00"]),
        "DATAFIMOCORRENCIA": pd.to_datetime(["2026-01-05 09:30", "2026-01-06 14:00", None, "2026-01-07 16:00", "2026-01-08 07:00"]),
        "SP_CONTRACTEDSERVICE_PRODUCT_NAME": ["SIGEPE", "SOUGOV", None, "SIGEPE", "SIGEPE"],
    }).to_excel(pasta / "Lista_incidentes.xlsx", index=False)


def test_incidentes_carregam_com_severidade_provisoria(tmp_path):
    """Duração = fim − início; linhas vazias/negativas caem; severidade por duração; sistema fixo SIGEPE; sem texto livre."""
    _planilha_incidentes(tmp_path)
    ach = L.classificar_arquivos(tmp_path)
    assert len(ach["incidentes"]) == 1
    inc = L.carregar_incidentes(ach["incidentes"])
    assert sorted(inc["incidente_id"]) == ["T1", "T2", "T3"]
    assert set(inc["sistema"]) == {"SIGEPE"}
    sev = dict(zip(inc["incidente_id"], inc["severidade"]))
    assert sev == {"T1": "Baixa", "T2": "Média", "T3": "Crítica"}
    assert SEGREDO not in inc.to_csv()
    assert not [m for m in validar_todos({"incidentes": inc}) if "incidentes" in m]


def test_estabilidade_so_com_incidentes(tmp_path, monkeypatch):
    """Página Estabilidade mostra incidentes mesmo sem disponibilidade/desempenho."""
    _planilha_incidentes(tmp_path)
    monkeypatch.setenv("PULSO_FONTE", "oficial")
    monkeypatch.setenv("PULSO_DADOS_OFICIAIS", str(tmp_path))
    st.cache_data.clear()
    at = AppTest.from_file(str(RAIZ / "app/pages/6_estabilidade.py"), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Incidentes recentes" in str(x.value) for x in at.markdown) or len(at.dataframe) >= 1
