"""Utilitários comuns (sem Streamlit): intervalo de datas e checagem de disponibilidade de dados."""
from __future__ import annotations

import pandas as pd

# Tabelas que alimentam os indicadores. Usadas para descobrir o período e os sistemas presentes.
TABELAS_NUCLEO = ("uso", "satisfacao", "suporte", "jornada_conclusao", "disponibilidade", "desempenho", "incidentes", "erros_log")


def tem_dados(df) -> bool:
    """True se for um DataFrame com ao menos uma linha (tabelas não disponibilizadas vêm vazias)."""
    return isinstance(df, pd.DataFrame) and not df.empty


def algum_dado(dados: dict) -> bool:
    """True se pelo menos uma tabela núcleo tem dados; evita calcular indicadores sobre o vazio."""
    return any(tem_dados(dados.get(k)) for k in TABELAS_NUCLEO)


def intervalo_datas(dados: dict) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Menor e maior data entre todas as tabelas com dados."""
    # Coleta mínimo e máximo de data de cada tabela com dados.
    ini, fim = [], []
    for k in TABELAS_NUCLEO:
        df = dados.get(k)
        if tem_dados(df) and "data" in df.columns:
            ini.append(df["data"].min())
            fim.append(df["data"].max())
    if not ini:
        raise ValueError("Nenhuma tabela com dados.")
    return min(ini), max(fim)


def sistemas_presentes(dados: dict) -> list[str]:
    """Lista ordenada dos sistemas que aparecem em alguma tabela com dados."""
    s: set[str] = set()
    for k in TABELAS_NUCLEO:
        df = dados.get(k)
        if tem_dados(df) and "sistema" in df.columns:
            s |= set(df["sistema"].unique())
    return sorted(s)
