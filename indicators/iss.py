"""IND-01 Índice de Saúde do Sistema (ISS) — PROVISÓRIO / CONCEITUAL.

ISS = 0,30·Uso&Jornada + 0,40·Satisfação + 0,30·Estabilidade&Suporte  (pesos em config.settings)
 - Uso&Jornada       = média( adoção normalizada, conclusão normalizada )
 - Satisfação        = CSAT normalizado
 - Estabilidade&Sup. = média( disponibilidade normalizada, TMR invertido normalizado )
Cada componente é levado a 0–100 pelas faixas de config.settings.NORMALIZACAO.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings as S

# Dimensões exibidas no radar e nas tabelas do ISS.
DIMENSOES = ["Uso", "Satisfação", "Jornadas", "Suporte", "Estabilidade"]


def normalizar(valor, minimo: float, maximo: float, inverter: bool = False):
    """Normaliza para 0–100 (limitado). Aceita escalar ou Series; NaN permanece NaN."""
    # Regra de três para a escala 0–100, limitada aos extremos; `inverter` vale para 'quanto menor, melhor' (ex.: TMR).
    v = (valor - minimo) / (maximo - minimo) * 100
    v = np.clip(v, 0, 100) if not np.isscalar(v) else float(min(max(v, 0.0), 100.0)) if v == v else v
    return 100 - v if inverter else v


def classificar(valor: float) -> str:
    """Traduz a nota em faixa: saudável, atenção, crítico (ou indisponível se NaN)."""
    if valor != valor:
        return "indisponivel"
    if valor >= S.FAIXAS_ISS["saudavel"]:
        return "saudavel"
    if valor >= S.FAIXAS_ISS["atencao"]:
        return "atencao"
    return "critico"


def _agregar(dados: dict, chaves: list[str]) -> pd.DataFrame:
    """Agrega as tabelas de dados por `chaves` e junta, numa só tabela, os indicadores-base
    (adoção, CSAT, conclusão, TMR e disponibilidade).
    """
    uso = dados["uso"].groupby(chaves).agg(a=("usuarios_ativos", "sum"), e=("elegiveis", "sum"))
    uso["adocao"] = uso["a"] / uso["e"] * 100
    sat = dados["satisfacao"].groupby(chaves).agg(s=("satisfeitos", "sum"), r=("respostas", "sum"))
    sat["csat"] = sat["s"] / sat["r"].where(sat["r"] > 0) * 100
    jc = dados["jornada_conclusao"].groupby(chaves).agg(c=("concluidas", "sum"), i=("iniciadas", "sum"))
    jc["conclusao"] = jc["c"] / jc["i"].where(jc["i"] > 0) * 100
    sp = dados["suporte"].assign(_p=lambda d: d["tmr_horas"] * d["chamados"])
    sp = sp.groupby(chaves).agg(p=("_p", "sum"), ch=("chamados", "sum"))
    sp["tmr"] = sp["p"] / sp["ch"].where(sp["ch"] > 0)
    up = dados["disponibilidade"].groupby(chaves).agg(uptime=("uptime_pct", "mean"))
    return pd.concat([uso[["adocao", "a"]], sat[["csat"]], jc[["conclusao"]], sp[["tmr"]], up], axis=1)


def _scores(m: pd.DataFrame) -> pd.DataFrame:
    """Converte indicadores-base em notas 0–100 por dimensão e combina no ISS com os pesos de settings."""
    N = S.NORMALIZACAO
    out = pd.DataFrame(index=m.index)
    out["Uso"] = normalizar(m["adocao"], *N["adocao"])
    out["Satisfação"] = normalizar(m["csat"], *N["csat"])
    out["Jornadas"] = normalizar(m["conclusao"], *N["conclusao"])
    out["Suporte"] = normalizar(m["tmr"], *N["tmr"], inverter=True)
    out["Estabilidade"] = normalizar(m["uptime"], *N["disponibilidade"])
    # Agrupa as dimensões em três blocos do ISS: Uso&Jornada e Estabilidade&Suporte (médias simples) e Satisfação.
    uso_j = out[["Uso", "Jornadas"]].mean(axis=1)
    est_s = out[["Estabilidade", "Suporte"]].mean(axis=1)
    w = S.PESOS_ISS
    # Combinação final ponderada. Se faltar qualquer dimensão, o ISS fica NaN (não inventamos nota).
    out["ISS"] = w["uso"] * uso_j + w["satisfacao"] * out["Satisfação"] + w["estabilidade"] * est_s
    out["usuarios_ativos"] = m["a"]
    return out


def calcular_iss_por_sistema(dados: dict) -> pd.DataFrame:
    """Linhas = sistemas; colunas = 5 dimensões (0–100), ISS e usuarios_ativos."""
    return _scores(_agregar(dados, ["sistema"]))


def iss_geral(dados: dict) -> float:
    """ISS geral = média dos ISS por sistema ponderada pelos usuários ativos."""
    t = calcular_iss_por_sistema(dados)
    t = t.dropna(subset=["ISS"])
    if t.empty or t["usuarios_ativos"].sum() == 0:
        return float("nan")
    return float(np.average(t["ISS"], weights=t["usuarios_ativos"]))


def iss_serie_semanal(dados: dict) -> pd.DataFrame:
    """Colunas: semana, sistema, ISS."""
    t = _scores(_agregar(dados, ["semana", "sistema"])).reset_index()
    return t[["semana", "sistema", "ISS"]].dropna()


def estado_vs_meta(valor: float, meta: float, maior_melhor: bool = True, tolerancia: float = 0.10) -> str:
    """saudável se cumpre a meta; atenção se a até `tolerancia` (relativa) dela; senão crítico."""
    if valor != valor:
        return "indisponivel"
    if maior_melhor:
        if valor >= meta:
            return "saudavel"
        return "atencao" if valor >= meta * (1 - tolerancia) else "critico"
    if valor <= meta:
        return "saudavel"
    return "atencao" if valor <= meta * (1 + tolerancia) else "critico"
