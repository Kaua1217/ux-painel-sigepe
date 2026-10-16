"""Indicadores de USO — IND-02 Usuários Ativos, IND-03 Taxa de Adoção. (PROVISÓRIOS)"""
from __future__ import annotations

import numpy as np
import pandas as pd


def adocao(uso: pd.DataFrame) -> float:
    """Usuários ativos diários / público elegível (%). NaN se não houver dados."""
    if uso.empty:
        return float("nan")
    return float(uso["usuarios_ativos"].sum() / uso["elegiveis"].sum() * 100)


def usuarios_ativos_medio(uso: pd.DataFrame) -> float:
    """Média diária de usuários ativos (somados nos recortes selecionados)."""
    if uso.empty:
        return float("nan")
    return float(uso["usuarios_ativos"].sum() / uso["data"].nunique())


def sessoes_por_usuario(uso: pd.DataFrame) -> float:
    """Média de sessões por usuário ativo (engajamento). NaN se não houver usuários."""
    if uso.empty or uso["usuarios_ativos"].sum() == 0:
        return float("nan")
    return float(uso["sessoes"].sum() / uso["usuarios_ativos"].sum())


def serie_adocao_semanal(uso: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """Adoção (%) por semana, opcionalmente separada por uma dimensão (`por`, ex.: sistema)."""
    chaves = ["semana"] + ([por] if por else [])
    # Soma ativos e elegíveis na semana e só então divide (média ponderada correta).
    g = uso.groupby(chaves, as_index=False).agg(a=("usuarios_ativos", "sum"), e=("elegiveis", "sum"))
    g["adocao"] = g["a"] / g["e"] * 100
    return g[chaves + ["adocao"]]


def serie_usuarios_semanal(uso: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """Média diária de usuários ativos por semana."""
    chaves = ["semana"] + ([por] if por else [])
    g = uso.groupby(chaves + ["data"], as_index=False)["usuarios_ativos"].sum()
    return g.groupby(chaves, as_index=False)["usuarios_ativos"].mean()


def matriz_adocao(uso: pd.DataFrame, linhas: str = "sistema", colunas: str = "orgao") -> pd.DataFrame:
    """Tabela linhas × colunas (padrão sistema × órgão) com a adoção %, usada no mapa de calor."""
    g = uso.groupby([linhas, colunas]).agg(a=("usuarios_ativos", "sum"), e=("elegiveis", "sum"))
    g["v"] = g["a"] / g["e"] * 100
    return g["v"].unstack(colunas)


def ranking_adocao(uso: pd.DataFrame, por: str = "orgao") -> pd.DataFrame:
    """Adoção % por categoria (padrão: órgão), da maior para a menor."""
    g = uso.groupby(por).agg(a=("usuarios_ativos", "sum"), e=("elegiveis", "sum")).reset_index()
    g["adocao"] = g["a"] / g["e"] * 100
    return g[[por, "adocao"]].sort_values("adocao", ascending=False).reset_index(drop=True)
