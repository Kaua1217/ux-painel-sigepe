"""Indicadores de SATISFAÇÃO — IND-04 Índice de Satisfação (CSAT), IND-05 Índice de Esforço (CES). (PROVISÓRIOS)

SUS, confiança, clareza e percepção espontânea: INFORMAÇÃO NÃO DISPONIBILIZADA.
"""
from __future__ import annotations

import pandas as pd


def csat(sat: pd.DataFrame) -> float:
    """% de respostas satisfeitas (ponderado por respostas)."""
    if sat.empty or sat["respostas"].sum() == 0:
        return float("nan")
    return float(sat["satisfeitos"].sum() / sat["respostas"].sum() * 100)


def ces(sat: pd.DataFrame) -> float:
    """Esforço médio (1-7, maior = mais fácil), ponderado por respostas."""
    if sat.empty or sat["respostas"].sum() == 0:
        return float("nan")
    return float((sat["ces_medio"] * sat["respostas"]).sum() / sat["respostas"].sum())


def total_respostas(sat: pd.DataFrame) -> int:
    """Quantidade de respostas na amostra; serve para indicar a confiança do CSAT."""
    return int(sat["respostas"].sum()) if not sat.empty else 0


def serie_csat_semanal(sat: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """CSAT (%) por semana; semanas sem respostas são descartadas para não gerar divisão por zero."""
    chaves = ["semana"] + ([por] if por else [])
    g = sat.groupby(chaves, as_index=False).agg(s=("satisfeitos", "sum"), r=("respostas", "sum"))
    g = g[g["r"] > 0].copy()
    g["csat"] = g["s"] / g["r"] * 100
    return g[chaves + ["csat"]]


def matriz_csat(sat: pd.DataFrame, linhas: str = "sistema", colunas: str = "orgao") -> pd.DataFrame:
    """CSAT % em formato linhas × colunas (sistema × órgão) para o mapa de calor."""
    g = sat.groupby([linhas, colunas]).agg(s=("satisfeitos", "sum"), r=("respostas", "sum"))
    g = g[g["r"] > 0]
    g["v"] = g["s"] / g["r"] * 100
    return g["v"].unstack(colunas)


def ranking_csat(sat: pd.DataFrame, por: str = "sistema") -> pd.DataFrame:
    """CSAT % por categoria (padrão: sistema), do maior para o menor."""
    g = sat.groupby(por).agg(s=("satisfeitos", "sum"), r=("respostas", "sum")).reset_index()
    g["csat"] = g["s"] / g["r"].where(g["r"] > 0) * 100
    return g[[por, "csat"]].sort_values("csat", ascending=False).reset_index(drop=True)
