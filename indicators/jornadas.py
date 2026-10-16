"""Indicadores de JORNADAS — IND-06 Taxa de Conclusão, IND-07 Tempo de Conclusão. (PROVISÓRIOS)"""
from __future__ import annotations

import numpy as np
import pandas as pd


def taxa_conclusao(jc: pd.DataFrame) -> float:
    """% de jornadas concluídas sobre as iniciadas. NaN se nada foi iniciado."""
    if jc.empty or jc["iniciadas"].sum() == 0:
        return float("nan")
    return float(jc["concluidas"].sum() / jc["iniciadas"].sum() * 100)


def tempo_medio(jc: pd.DataFrame) -> float:
    """Tempo médio de conclusão (min), ponderado por jornadas concluídas."""
    if jc.empty or jc["concluidas"].sum() == 0:
        return float("nan")
    return float((jc["tempo_medio_min"] * jc["concluidas"]).sum() / jc["concluidas"].sum())


def total_iniciadas(jc: pd.DataFrame) -> int:
    """Total de jornadas iniciadas (tamanho da amostra)."""
    return int(jc["iniciadas"].sum()) if not jc.empty else 0


def ranking_jornadas(jc: pd.DataFrame) -> pd.DataFrame:
    """Resumo por jornada/sistema (iniciadas, conclusão, tempo), da pior conclusão para a melhor."""
    g = jc.groupby(["jornada", "sistema"]).apply(
        lambda d: pd.Series({
            "iniciadas": d["iniciadas"].sum(),
            "conclusao": taxa_conclusao(d),
            "tempo_medio_min": tempo_medio(d),
        }),
        include_groups=False,
    ).reset_index()
    return g.sort_values("conclusao").reset_index(drop=True)


def serie_conclusao_semanal(jc: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """Taxa de conclusão (%) por semana; semanas sem jornadas iniciadas são ignoradas."""
    chaves = ["semana"] + ([por] if por else [])
    g = jc.groupby(chaves, as_index=False).agg(c=("concluidas", "sum"), i=("iniciadas", "sum"))
    g = g[g["i"] > 0].copy()
    g["conclusao"] = g["c"] / g["i"] * 100
    return g[chaves + ["conclusao"]]


def matriz_conclusao(jc: pd.DataFrame, linhas: str = "jornada", colunas: str = "orgao") -> pd.DataFrame:
    """Conclusão % em formato jornada × órgão para o mapa de calor."""
    g = jc.groupby([linhas, colunas]).agg(c=("concluidas", "sum"), i=("iniciadas", "sum"))
    g = g[g["i"] > 0]
    g["v"] = g["c"] / g["i"] * 100
    return g["v"].unstack(colunas)


def funil(jc_jornada: pd.DataFrame, funil_dim: pd.DataFrame, jornada: str) -> pd.DataFrame:
    """Funil de uma jornada: iniciadas → … → concluídas.

    A conclusão final é a observada; o abandono intermediário é distribuído
    conforme `peso_abandono` (conceitual — etapas oficiais: INFORMAÇÃO NÃO DISPONIBILIZADA).
    """
    et = funil_dim[funil_dim["jornada"] == jornada].sort_values("etapa_ordem")
    ini = float(jc_jornada["iniciadas"].sum())
    con = float(jc_jornada["concluidas"].sum())
    if et.empty or ini == 0:
        return pd.DataFrame(columns=["etapa", "usuarios", "retencao_pct"])
    # Perda total observada entre o início e a conclusão.
    perda_total = 1 - con / ini
    # Fração acumulada do abandono até cada etapa, conforme os pesos conceituais.
    acum = et["peso_abandono"].cumsum() / et["peso_abandono"].sum()
    retencao = 1 - perda_total * acum  # a última etapa coincide com a conclusão observada
    out = pd.DataFrame({
        "etapa": et["etapa"].to_numpy(),
        "usuarios": np.round(ini * retencao.to_numpy()).astype(int),
        "retencao_pct": retencao.to_numpy() * 100,
    })
    return out
