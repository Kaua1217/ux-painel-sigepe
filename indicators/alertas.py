"""Motor de ALERTAS e OPORTUNIDADES — IND-12 Score de Severidade. (PROVISÓRIO / CONCEITUAL)

Compara a 2ª metade do período selecionado com a 1ª e classifica pela
configuração de limiares em config.settings.LIMIARES_ALERTA.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from config import settings as S
from indicators import comum
from indicators import estabilidade as est
from indicators import jornadas as jor
from indicators import satisfacao as sat
from indicators import suporte as sup
from indicators import uso as usoi


@dataclass
class Alerta:
    """Um alerta gerado pelo motor: o que piorou, em qual sistema, quanto e com que gravidade."""
    sistema: str
    dimensao: str
    indicador: str
    descricao: str
    variacao: float
    unidade: str
    nivel: str  # "atenção" | "crítico"
    valor_anterior: float
    valor_atual: float
    usuarios_afetados: int
    score_severidade: float

    def to_dict(self) -> dict:
        """Converte o alerta em dicionário (usado para montar tabelas)."""
        return asdict(self)


def classificar_limiar(variacao_adversa: float, chave: str) -> str | None:
    """variacao_adversa > 0 significa piora. Retorna 'crítico', 'atenção' ou None."""
    if variacao_adversa != variacao_adversa:
        return None
    lim = S.LIMIARES_ALERTA[chave]
    if variacao_adversa >= lim["critico"]:
        return "crítico"
    if variacao_adversa >= lim["atencao"]:
        return "atenção"
    return None


def score_severidade(nivel: str, variacao_adversa: float, usuarios: float) -> float:
    """Pontuação de prioridade = peso do nível × tamanho da piora × alcance (usuários)."""
    return float(S.PESO_NIVEL_ALERTA[nivel] * (abs(variacao_adversa) / 10 + 1) * (1 + usuarios / 5000))


def _metade(dados: dict) -> tuple[dict, dict]:
    """Divide os dados em duas metades de tempo (1ª e 2ª) para comparar antes × depois.
    Incidentes não são divididos (não têm série diária comparável).
    """
    if not comum.algum_dado(dados):
        return dados, dados
    ini, fim = comum.intervalo_datas(dados)
    # Data que separa as duas metades do período.
    meio = ini + (fim - ini) / 2

    def corte(lado: str) -> dict:
        out = {}
        for k, v in dados.items():
            if isinstance(v, pd.DataFrame) and "data" in v.columns and k != "incidentes":
                out[k] = v[v["data"] <= meio] if lado == "a" else v[v["data"] > meio]
            else:
                out[k] = v
        return out

    return corte("a"), corte("b")


def _pct(novo: float, velho: float) -> float:
    """Variação percentual; NaN se faltar valor ou se o anterior for zero."""
    return (novo - velho) / velho * 100 if velho and velho == velho and novo == novo else float("nan")


def gerar_alertas(dados: dict) -> list[Alerta]:
    """Gera alertas por sistema, ordenados por score de severidade (desc)."""
    if not comum.algum_dado(dados):
        return []
    # a = 1ª metade (referência); b = 2ª metade (atual).
    a, b = _metade(dados)
    alertas: list[Alerta] = []
    for s in comum.sistemas_presentes(dados):
        # Filtra a tabela pelo sistema que está sendo avaliado no laço.
        def f(d, tabela):
            t = d[tabela]
            return t[t["sistema"] == s]

        ativos = int(round(usoi.usuarios_ativos_medio(f(b, "uso")))) if not f(b, "uso").empty else 0

        # Cria o alerta somente se a piora ultrapassar o limiar configurado.
        # `adverso` > 0 significa piora; `delta_exib` é o valor mostrado ao usuário.
        def add(dim, ind, desc, v_ant, v_atu, adverso, unidade, chave, delta_exib):
            nivel = classificar_limiar(adverso, chave)
            if nivel:
                alertas.append(Alerta(s, dim, ind, desc, float(delta_exib), unidade, nivel,
                                      float(v_ant), float(v_atu), ativos,
                                      score_severidade(nivel, adverso, ativos)))

        # Satisfação: queda em pontos percentuais.
        c0, c1 = sat.csat(f(a, "satisfacao")), sat.csat(f(b, "satisfacao"))
        add("Satisfação", "CSAT", f"Satisfação caiu de {c0:.1f}% para {c1:.1f}%.",
            c0, c1, c0 - c1, "pp", "queda_satisfacao_pp", c1 - c0)

        # Suporte: chamados por dia (normaliza pelos dias com registro).
        h0 = f(a, "suporte")["chamados"].sum() / max(f(a, "suporte")["data"].nunique(), 1)
        h1 = f(b, "suporte")["chamados"].sum() / max(f(b, "suporte")["data"].nunique(), 1)
        p = _pct(h1, h0)
        add("Suporte", "Chamados/dia", f"Chamados por dia subiram de {h0:.0f} para {h1:.0f}.",
            h0, h1, p, "%", "aumento_chamados_pct", p)

        # Jornadas: queda na taxa de conclusão.
        k0, k1 = jor.taxa_conclusao(f(a, "jornada_conclusao")), jor.taxa_conclusao(f(b, "jornada_conclusao"))
        add("Jornadas Digitais", "Taxa de conclusão", f"Conclusão das jornadas caiu de {k0:.1f}% para {k1:.1f}%.",
            k0, k1, k0 - k1, "pp", "queda_conclusao_pp", k1 - k0)

        # Estabilidade: queda de disponibilidade.
        d0, d1 = est.disponibilidade(f(a, "disponibilidade")), est.disponibilidade(f(b, "disponibilidade"))
        add("Estabilidade", "Disponibilidade", f"Disponibilidade caiu de {d0:.2f}% para {d1:.2f}%.",
            d0, d1, d0 - d1, "pp", "queda_disponibilidade_pp", d1 - d0)

        # Estabilidade: aumento do tempo de resposta.
        r0, r1 = est.tempo_resposta(f(a, "desempenho")), est.tempo_resposta(f(b, "desempenho"))
        pr = _pct(r1, r0)
        add("Estabilidade", "Tempo de resposta", f"Tempo de resposta subiu de {r0:.0f} ms para {r1:.0f} ms.",
            r0, r1, pr, "%", "aumento_tempo_resposta_pct", pr)

        # Uso: queda de usuários ativos (o sinal é invertido: queda = piora).
        u0, u1 = usoi.usuarios_ativos_medio(f(a, "uso")), usoi.usuarios_ativos_medio(f(b, "uso"))
        pu = _pct(u1, u0)
        add("Uso", "Usuários ativos", f"Usuários ativos diários caíram de {u0:.0f} para {u1:.0f}.",
            u0, u1, -pu if pu == pu else float("nan"), "%", "queda_usuarios_ativos_pct", pu)

    # Mais graves primeiro.
    return sorted(alertas, key=lambda x: x.score_severidade, reverse=True)


def alertas_para_df(alertas: list[Alerta]) -> pd.DataFrame:
    """Transforma a lista de alertas em DataFrame (com colunas fixas mesmo se a lista for vazia)."""
    cols = list(Alerta.__dataclass_fields__.keys())
    return pd.DataFrame([x.to_dict() for x in alertas], columns=cols)


def oportunidades_melhoria(dados: dict, alertas: list[Alerta]) -> pd.DataFrame:
    """Matriz Impacto × Esforço (provisória). Impacto 0–10 deriva do score; esforço 1–5 por dimensão."""
    # Oportunidade 1: cada alerta vira uma oportunidade (impacto proporcional ao score).
    linhas = []
    maximo = max([x.score_severidade for x in alertas], default=1.0)
    for x in alertas:
        linhas.append(dict(
            oportunidade=f"{x.sistema} · tratar {x.indicador.lower()} ({x.dimensao})",
            sistema=x.sistema, dimensao=x.dimensao, origem="Alerta",
            impacto=round(x.score_severidade / maximo * 10, 1),
            esforco=S.ESFORCO_POR_DIMENSAO.get(x.dimensao, 3),
        ))
    # Oportunidade 2: células sistema × órgão com adoção abaixo do limiar.
    if comum.tem_dados(dados["uso"]):
        m = usoi.matriz_adocao(dados["uso"])
        for sis in m.index:
            for org in m.columns:
                v = m.loc[sis, org]
                if v == v and v < S.LIMIAR_ADOCAO_ORGAO_BAIXA:
                    linhas.append(dict(
                        oportunidade=f"{sis} · ampliar adoção em {org} ({v:.0f}%)",
                        sistema=sis, dimensao="Uso", origem="Adoção baixa",
                        impacto=round(min(10.0, (S.META_ADOCAO - v) / 6), 1),
                        esforco=S.ESFORCO_POR_DIMENSAO["Uso"],
                    ))
    df = pd.DataFrame(linhas, columns=["oportunidade", "sistema", "dimensao", "origem", "impacto", "esforco"])
    if not df.empty:
        # Prioridade = impacto ÷ esforço (alto impacto e baixo esforço primeiro).
        df["prioridade"] = df["impacto"] / df["esforco"]
        df = df.sort_values("prioridade", ascending=False).reset_index(drop=True)
    else:
        df["prioridade"] = []
    return df
