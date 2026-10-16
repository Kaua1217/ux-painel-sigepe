"""Indicadores de SUPORTE — IND-08 Volume de Suporte, IND-09 Tempo Médio de Resolução. (PROVISÓRIOS)"""
from __future__ import annotations

import pandas as pd


def chamados_total(sup: pd.DataFrame) -> int:
    """Total de chamados no recorte."""
    return int(sup["chamados"].sum()) if not sup.empty else 0


def chamados_por_mil(sup: pd.DataFrame, uso: pd.DataFrame) -> float:
    """Chamados por 1.000 usuários-dia ativos (normaliza pelo tamanho da base)."""
    if sup.empty or uso.empty or uso["usuarios_ativos"].sum() == 0:
        return float("nan")
    return float(sup["chamados"].sum() / uso["usuarios_ativos"].sum() * 1000)


def _ponderada(sup: pd.DataFrame, col: str) -> float:
    """Média ponderada pelo número de chamados (um dia com mais chamados pesa mais)."""
    if sup.empty or sup["chamados"].sum() == 0:
        return float("nan")
    return float((sup[col] * sup["chamados"]).sum() / sup["chamados"].sum())


def tmr(sup: pd.DataFrame) -> float:
    """Tempo médio de resolução (horas), ponderado por chamados."""
    return _ponderada(sup, "tmr_horas")


def tpr(sup: pd.DataFrame) -> float:
    """Tempo médio até a primeira resposta (h)."""
    return _ponderada(sup, "tpr_horas")


def reincidencia(sup: pd.DataFrame) -> float:
    """% de chamados reincidentes (ligados a chamado anterior)."""
    if sup.empty or sup["chamados"].sum() == 0:
        return float("nan")
    return float(sup["reincidentes"].sum() / sup["chamados"].sum() * 100)


def serie_chamados_semanal(sup: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """Volume de chamados por semana."""
    chaves = ["semana"] + ([por] if por else [])
    return sup.groupby(chaves, as_index=False)["chamados"].sum()


def serie_por_mil_semanal(sup: pd.DataFrame, uso: pd.DataFrame, por: str = "sistema") -> pd.DataFrame:
    """Chamados por mil usuários ativos, por semana (comparável entre sistemas de tamanhos diferentes)."""
    a = sup.groupby(["semana", por], as_index=False)["chamados"].sum()
    b = uso.groupby(["semana", por], as_index=False)["usuarios_ativos"].sum()
    m = a.merge(b, on=["semana", por])
    m["por_mil"] = m["chamados"] / m["usuarios_ativos"].where(m["usuarios_ativos"] > 0) * 1000
    return m[["semana", por, "por_mil"]]


def matriz_por_mil(sup: pd.DataFrame, uso: pd.DataFrame, linhas: str = "sistema", colunas: str = "orgao") -> pd.DataFrame:
    """Chamados por mil usuários-dia em formato sistema × órgão."""
    a = sup.groupby([linhas, colunas])["chamados"].sum()
    b = uso.groupby([linhas, colunas])["usuarios_ativos"].sum()
    return (a / b.where(b > 0) * 1000).unstack(colunas)


def ranking_tmr(sup: pd.DataFrame, por: str = "sistema") -> pd.DataFrame:
    """Tempo médio de resolução por categoria, do pior (maior) para o melhor."""
    rows = [(k, tmr(d)) for k, d in sup.groupby(por)]
    return pd.DataFrame(rows, columns=[por, "tmr_horas"]).sort_values("tmr_horas", ascending=False).reset_index(drop=True)
