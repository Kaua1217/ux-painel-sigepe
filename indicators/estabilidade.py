"""Indicadores de ESTABILIDADE — IND-10 Disponibilidade, IND-11 Incidentes por Severidade. (PROVISÓRIOS)

Não filtráveis por órgão/perfil (dado técnico por sistema). Taxa de erro e tempo de
resposta são proxies conceituais; recuperação oficial: INFORMAÇÃO NÃO DISPONIBILIZADA.
"""
from __future__ import annotations

import pandas as pd


def disponibilidade(disp: pd.DataFrame) -> float:
    """Disponibilidade média (%) no período."""
    return float(disp["uptime_pct"].mean()) if not disp.empty else float("nan")


def tempo_resposta(des: pd.DataFrame) -> float:
    """Tempo médio de resposta (ms) — indicador conceitual."""
    return float(des["tempo_resposta_ms"].mean()) if not des.empty else float("nan")


def taxa_erro(des: pd.DataFrame) -> float:
    """Taxa média de erro (%) — indicador conceitual."""
    return float(des["taxa_erro_pct"].mean()) if not des.empty else float("nan")


def total_incidentes(inc: pd.DataFrame) -> int:
    """Número de incidentes registrados."""
    return int(len(inc))


def tempo_medio_recuperacao(inc: pd.DataFrame) -> float:
    """MTTR conceitual: duração média dos incidentes (h)."""
    return float(inc["duracao_h"].mean()) if not inc.empty else float("nan")


def incidentes_por_severidade(inc: pd.DataFrame) -> pd.DataFrame:
    """Contagem de incidentes por severidade, sempre na ordem Crítica → Média → Baixa."""
    ordem = ["Crítica", "Média", "Baixa"]
    c = inc["severidade"].value_counts().reindex(ordem).fillna(0).astype(int)
    return c.rename_axis("severidade").reset_index(name="incidentes")


def serie_disponibilidade_semanal(disp: pd.DataFrame, por: str | None = "sistema") -> pd.DataFrame:
    """Disponibilidade média por semana (e por `por`, se informado)."""
    chaves = ["semana"] + ([por] if por else [])
    return disp.groupby(chaves, as_index=False)["uptime_pct"].mean()


def matriz_disponibilidade_mensal(disp: pd.DataFrame) -> pd.DataFrame:
    """Tabela sistema × mês com a disponibilidade média (mapa de calor)."""
    d = disp.assign(mes=disp["data"].dt.to_period("M").astype(str))
    return d.groupby(["sistema", "mes"])["uptime_pct"].mean().unstack("mes")


def total_erros_log(erros: pd.DataFrame) -> int:
    """Eventos de erro registrados em log (IN_CLASSIFICACAO: significado a confirmar)."""
    return int(erros["erros"].sum()) if not erros.empty else 0


def serie_erros_semanal(erros: pd.DataFrame, por: str | None = "modulo") -> pd.DataFrame:
    """Eventos de erro por semana, separados por módulo (ou outra dimensão)."""
    chaves = ["semana"] + ([por] if por else [])
    return erros.groupby(chaves, as_index=False)["erros"].sum()
