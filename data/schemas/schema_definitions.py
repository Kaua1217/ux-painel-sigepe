"""Contrato de dados: colunas e tipos esperados por tabela.

Qualquer loader (sintético hoje, oficial amanhã) deve devolver tabelas que
respeitem este contrato. Se um dado oficial não existir, a coluna deve ser
preenchida com NaN e a limitação registrada em docs/ ("INFORMAÇÃO NÃO DISPONIBILIZADA").
Kinds: 'M' datetime, 'O' texto, 'i' inteiro, 'f' decimal.
"""
from __future__ import annotations

import pandas as pd

# Colunas-chave comuns às tabelas diárias: período, sistema, órgão e perfil.
_CHAVES = {"data": "M", "semana": "M", "sistema": "O", "orgao": "O", "perfil": "O"}

SCHEMA_USO = {**_CHAVES, "elegiveis": "i", "usuarios_ativos": "i", "sessoes": "i"}
SCHEMA_SATISFACAO = {**_CHAVES, "respostas": "i", "satisfeitos": "i", "ces_medio": "f"}
SCHEMA_SUPORTE = {**_CHAVES, "chamados": "i", "tmr_horas": "f", "tpr_horas": "f", "reincidentes": "i"}
SCHEMA_JORNADA_CONCLUSAO = {
    **_CHAVES, "jornada": "O", "iniciadas": "i", "concluidas": "i", "tempo_medio_min": "f",
}
SCHEMA_JORNADA_DIM = {"jornada": "O", "sistema": "O"}
SCHEMA_JORNADA_FUNIL = {"jornada": "O", "etapa_ordem": "i", "etapa": "O", "peso_abandono": "f"}
SCHEMA_DISPONIBILIDADE = {"data": "M", "semana": "M", "sistema": "O", "uptime_pct": "f"}
SCHEMA_DESEMPENHO = {
    "data": "M", "semana": "M", "sistema": "O", "tempo_resposta_ms": "f", "taxa_erro_pct": "f",
}
SCHEMA_INCIDENTES = {
    "incidente_id": "O", "sistema": "O", "data": "M", "duracao_h": "f", "severidade": "O",
}

SCHEMA_ERROS_LOG = {
    "data": "M", "semana": "M", "sistema": "O", "modulo": "O", "classificacao": "O", "erros": "i",
}

# Registro de todas as tabelas do contrato (nome → colunas e tipos).
SCHEMAS = {
    "uso": SCHEMA_USO,
    "satisfacao": SCHEMA_SATISFACAO,
    "suporte": SCHEMA_SUPORTE,
    "jornada_conclusao": SCHEMA_JORNADA_CONCLUSAO,
    "jornada_dim": SCHEMA_JORNADA_DIM,
    "jornada_funil": SCHEMA_JORNADA_FUNIL,
    "disponibilidade": SCHEMA_DISPONIBILIDADE,
    "desempenho": SCHEMA_DESEMPENHO,
    "incidentes": SCHEMA_INCIDENTES,
    "erros_log": SCHEMA_ERROS_LOG,
}


def tabela_vazia(nome: str) -> pd.DataFrame:
    """Tabela sem linhas, com as colunas/tipos do contrato (fonte não disponibilizada)."""
    # Tipo pandas correspondente a cada 'kind' do contrato.
    tipos = {"M": "datetime64[ns]", "i": "int64", "f": "float64", "O": "object"}
    return pd.DataFrame({c: pd.Series(dtype=tipos[k]) for c, k in SCHEMAS[nome].items()})


def validar_schema(df: pd.DataFrame, nome: str) -> list[str]:
    """Retorna lista de problemas (vazia = válido)."""
    problemas: list[str] = []
    esperado = SCHEMAS[nome]
    # Confere presença e tipo de cada coluna esperada.
    for col, kind in esperado.items():
        if col not in df.columns:
            problemas.append(f"{nome}: coluna ausente '{col}'")
            continue
        k = df[col].dtype.kind
        if kind == "M" and k != "M":
            problemas.append(f"{nome}.{col}: esperado datetime, obtido {df[col].dtype}")
        elif kind == "i" and k not in "iu":
            problemas.append(f"{nome}.{col}: esperado inteiro, obtido {df[col].dtype}")
        elif kind == "f" and k not in "fiu":
            problemas.append(f"{nome}.{col}: esperado numérico, obtido {df[col].dtype}")
        elif kind == "O" and k not in "OUS" and not pd.api.types.is_string_dtype(df[col]):
            problemas.append(f"{nome}.{col}: esperado texto, obtido {df[col].dtype}")
    return problemas


def validar_todos(dados: dict) -> list[str]:
    problemas: list[str] = []
    for nome in SCHEMAS:
        if nome not in dados:
            problemas.append(f"tabela ausente: {nome}")
        else:
            problemas += validar_schema(dados[nome], nome)
    return problemas
