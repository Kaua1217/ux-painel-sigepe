"""Gerador de dados SINTÉTICOS (fictícios) do painel.

ÚNICO ponto de contato entre a aplicação e a origem dos dados. Para usar dados
oficiais, criar `official_loader.py` com a mesma função `carregar_dados()` e
trocar o import em `app/state.py` — nada mais muda (ver docs/arquitetura.md).

Problemas intencionais embutidos (para o painel ter o que mostrar):
- Sistema Beta: degradação nas últimas ~9 semanas (CSAT, disponibilidade, chamados, conclusão).
- Sistema Delta: baixa adoção no Órgão Regional Oeste.
- Sistema Alfa: sazonalidade em março/abril.
- Sistema Épsilon: incidente crítico (14h) há 32 semanas.
Tudo é determinístico (seed fixa; zlib.crc32 em vez de hash()).
"""
from __future__ import annotations

import zlib

import numpy as np
import pandas as pd
import streamlit as st

from config import settings as S
from data.schemas.schema_definitions import tabela_vazia, validar_todos

# Perfil-base de cada sistema fictício: público elegível, adoção, satisfação, chamados por usuário, TMR (h), disponibilidade (%), tempo de resposta (ms) e taxa de erro (%).
BASE = {
    "Sistema Alfa":   dict(elegiveis=60000, adocao=0.70, csat=0.80, chamados=0.010, tmr=34, uptime=99.92, resp=420, erro=0.4),
    "Sistema Beta":   dict(elegiveis=42000, adocao=0.66, csat=0.77, chamados=0.012, tmr=38, uptime=99.85, resp=520, erro=0.5),
    "Sistema Gama":   dict(elegiveis=52000, adocao=0.76, csat=0.83, chamados=0.008, tmr=30, uptime=99.95, resp=380, erro=0.3),
    "Sistema Delta":  dict(elegiveis=18000, adocao=0.52, csat=0.68, chamados=0.016, tmr=52, uptime=99.70, resp=700, erro=0.9),
    "Sistema Épsilon": dict(elegiveis=9000, adocao=0.58, csat=0.73, chamados=0.013, tmr=44, uptime=99.80, resp=610, erro=0.7),
}
# Distribuição do público por órgão, por perfil e multiplicador de adoção por perfil (somas de pesos = 1).
PESO_ORGAO = dict(zip(S.ORGAOS, [0.30, 0.22, 0.18, 0.12, 0.10, 0.08]))
PESO_PERFIL = dict(zip(S.PERFIS, [0.90, 0.07, 0.03]))
MULT_ADOCAO_PERFIL = dict(zip(S.PERFIS, [1.0, 1.10, 1.35]))

# Jornadas fictícias por sistema: (nome, taxa de conclusão base, tempo médio base em minutos).
JORNADAS = {
    "Sistema Alfa": [("Solicitar afastamento", 0.80, 9), ("Consultar contracheque", 0.92, 3)],
    "Sistema Beta": [("Atualizar dados cadastrais", 0.84, 7), ("Registrar frequência", 0.88, 4)],
    "Sistema Gama": [("Solicitar férias", 0.86, 8), ("Emitir declaração", 0.90, 3)],
    "Sistema Delta": [("Progressão funcional", 0.66, 18), ("Cadastro de dependentes", 0.72, 12)],
    "Sistema Épsilon": [("Concessão de benefício", 0.70, 15), ("Simulação de aposentadoria", 0.78, 10)],
}
# Etapas conceituais do funil de qualquer jornada.
ETAPAS = ["Acesso à funcionalidade", "Preenchimento dos dados", "Anexos e validação",
          "Revisão e envio", "Confirmação"]


def _grade_base(datas: pd.DatetimeIndex) -> pd.DataFrame:
    """Produto cartesiano data × sistema × órgão × perfil: uma linha por combinação, base de todas as tabelas diárias."""
    idx = pd.MultiIndex.from_product([datas, S.SISTEMAS, S.ORGAOS, S.PERFIS],
                                     names=["data", "sistema", "orgao", "perfil"])
    return idx.to_frame(index=False)


def _semana(serie: pd.Series) -> pd.Series:
    """Segunda-feira da semana de cada data."""
    return serie.dt.to_period("W").dt.start_time


def _fatores(df: pd.DataFrame, datas: pd.DatetimeIndex) -> dict:
    """Fatores temporais/anomalias compartilhados entre as tabelas."""
    fim = pd.Timestamp(S.DATA_FIM)
    # A degradação do Sistema Beta começa 63 dias antes do fim e cresce gradualmente em 21 dias (rampa 0→1).
    ini_deg = fim - pd.Timedelta(days=63)
    dias = (df["data"] - datas[0]).dt.days.to_numpy()
    rampa = np.clip((df["data"] - ini_deg).dt.days.to_numpy() / 21.0, 0, 1)
    eh_beta = (df["sistema"] == "Sistema Beta").to_numpy()
    eh_alfa = (df["sistema"] == "Sistema Alfa").to_numpy()
    mes = df["data"].dt.month.to_numpy()
    return dict(
        dias=dias,
        total=len(datas),
        deg=np.where(eh_beta, rampa, 0.0),
        sazonal=np.where(eh_alfa & np.isin(mes, [3, 4]), 1.30, 1.0),
        fim_semana=np.where(df["data"].dt.dayofweek.to_numpy() >= 5, 0.55, 1.0),
    )


def _elegiveis(df: pd.DataFrame) -> np.ndarray:
    """Público elegível diário de cada linha = base do sistema × peso do órgão × peso do perfil (mínimo 20)."""
    base = df["sistema"].map({k: v["elegiveis"] for k, v in BASE.items()}).to_numpy(float)
    po = df["orgao"].map(PESO_ORGAO).to_numpy(float)
    pp = df["perfil"].map(PESO_PERFIL).to_numpy(float)
    return np.maximum(np.round(base * po * pp), 20).astype(int)


def _gerar_incidentes(rng: np.random.Generator, datas: pd.DatetimeIndex) -> pd.DataFrame:
    """Cria os incidentes fictícios: sorteados por sistema + os dois casos planejados (Épsilon e Beta)."""
    fim = pd.Timestamp(S.DATA_FIM)
    linhas = []
    for sis in S.SISTEMAS:
        n = 3
        escolhidos = rng.choice(len(datas) - 70, size=n, replace=False)
        for i in escolhidos:
            dur = float(np.round(rng.uniform(0.5, 4.0), 1))
            linhas.append((sis, datas[int(i)], dur))
    # Épsilon: incidente crítico, 32 semanas antes do fim
    linhas.append(("Sistema Épsilon", fim - pd.Timedelta(weeks=32), 14.0))
    # Beta: incidentes recentes (degradação)
    for dias_atras, dur in [(50, 2.5), (28, 4.0), (9, 5.0)]:
        linhas.append(("Sistema Beta", fim - pd.Timedelta(days=dias_atras), dur))
    inc = pd.DataFrame(linhas, columns=["sistema", "data", "duracao_h"]).sort_values("data")
    # Severidade pela duração: ≥6 h crítica; ≥3 h média; senão baixa.
    inc["severidade"] = np.select([inc.duracao_h >= 6, inc.duracao_h >= 3], ["Crítica", "Média"], "Baixa")
    inc = inc.reset_index(drop=True)
    inc.insert(0, "incidente_id", [f"INC-{i + 1:04d}" for i in range(len(inc))])
    return inc


def gerar_todos_os_dados(seed: int = S.SEED) -> dict:
    """Gera todas as tabelas sintéticas de forma determinística (mesma `seed` → mesmos números)."""
    rng = np.random.default_rng(seed)
    datas = pd.date_range(S.DATA_INICIO, S.DATA_FIM, freq="D")

    # ---------------- uso
    # USO: probabilidade diária de uso → usuários ativos (binomial) e sessões (Poisson).
    g = _grade_base(datas)
    f = _fatores(g, datas)
    eleg = _elegiveis(g)
    p = (g["sistema"].map({k: v["adocao"] for k, v in BASE.items()}).to_numpy(float)
         * g["perfil"].map(MULT_ADOCAO_PERFIL).to_numpy(float)
         * (1 + 0.10 * f["dias"] / f["total"]) * f["sazonal"] * f["fim_semana"]
         * (1 - 0.10 * f["deg"]))
    # Anomalia planejada: Sistema Delta tem metade da adoção no Órgão Regional Oeste.
    delta_oeste = ((g["sistema"] == "Sistema Delta") & (g["orgao"] == "Órgão Regional Oeste")).to_numpy()
    p = p * np.where(delta_oeste, 0.50, 1.0) * rng.lognormal(0, 0.04, len(g))
    p = np.clip(p, 0.02, 0.95)
    ativos = rng.binomial(eleg, p)
    uso = g.assign(elegiveis=eleg, usuarios_ativos=ativos,
                   sessoes=rng.poisson(ativos * 2.8))
    uso["semana"] = _semana(uso["data"])

    # ---------------- satisfação
    # SATISFAÇÃO: ~1,5% dos usuários ativos respondem; cada resposta é 'satisfeita' com probabilidade csat_p.
    resp = rng.binomial(ativos, 0.015)
    csat_p = (g["sistema"].map({k: v["csat"] for k, v in BASE.items()}).to_numpy(float)
              + rng.normal(0, 0.02, len(g)) - 0.18 * f["deg"]
              - np.where(g["orgao"] == "Órgão Regional Oeste", 0.04, 0.0))
    csat_p = np.clip(csat_p, 0.05, 0.98)
    satisfeitos = rng.binomial(resp, csat_p)
    ces = np.clip(5.2 + (csat_p - 0.75) * 3 + rng.normal(0, 0.15, len(g)), 1, 7)
    sat = g.assign(respostas=resp, satisfeitos=satisfeitos, ces_medio=ces)
    sat["semana"] = _semana(sat["data"])

    # ---------------- suporte
    # SUPORTE: chamados (Poisson) proporcionais aos usuários ativos; piora com a degradação do Beta.
    taxa = g["sistema"].map({k: v["chamados"] for k, v in BASE.items()}).to_numpy(float)
    lam = ativos * taxa * f["sazonal"] * (1 + 0.55 * f["deg"])
    chamados = rng.poisson(lam)
    tmr_b = g["sistema"].map({k: v["tmr"] for k, v in BASE.items()}).to_numpy(float)
    tmr = tmr_b * rng.lognormal(0, 0.08, len(g)) * (1 + 0.30 * f["deg"])
    reinc = rng.binomial(chamados, np.clip(0.10 + 0.12 * f["deg"], 0, 1))
    sup = g.assign(chamados=chamados, tmr_horas=tmr,
                   tpr_horas=tmr * 0.12 * rng.lognormal(0, 0.1, len(g)), reincidentes=reinc)
    sup["semana"] = _semana(sup["data"])

    # ---------------- jornadas
    # JORNADAS: tabelas de dimensão e do funil (a etapa mais fraca é escolhida de forma estável por CRC32 do nome).
    dim_linhas, funil_linhas = [], []
    for sis, js in JORNADAS.items():
        for nome, _, _ in js:
            dim_linhas.append((nome, sis))
            fraca = zlib.crc32(nome.encode("utf-8")) % len(ETAPAS)
            for i, et in enumerate(ETAPAS):
                funil_linhas.append((nome, i + 1, et, 3.0 if i == fraca else 1.0))
    jornada_dim = pd.DataFrame(dim_linhas, columns=["jornada", "sistema"])
    jornada_funil = pd.DataFrame(funil_linhas, columns=["jornada", "etapa_ordem", "etapa", "peso_abandono"])

    idx = pd.MultiIndex.from_product([datas, jornada_dim["jornada"], S.ORGAOS, S.PERFIS],
                                     names=["data", "jornada", "orgao", "perfil"])
    # Grade diária de jornadas × órgão × perfil.
    jg = idx.to_frame(index=False).merge(jornada_dim, on="jornada", how="left")
    fj = _fatores(jg, datas)
    base_j = {n: (c, t) for js in JORNADAS.values() for n, c, t in js}
    eleg_j = _elegiveis(jg)
    lam_j = (eleg_j * 0.012 * fj["fim_semana"] * fj["sazonal"]
             * np.where((jg["sistema"] == "Sistema Delta") & (jg["orgao"] == "Órgão Regional Oeste"), 0.5, 1.0))
    ini = rng.poisson(lam_j)
    pc = (jg["jornada"].map(lambda n: base_j[n][0]).to_numpy(float)
          + rng.normal(0, 0.02, len(jg)) - 0.14 * fj["deg"])
    con = rng.binomial(ini, np.clip(pc, 0.05, 0.99))
    tm = (jg["jornada"].map(lambda n: base_j[n][1]).to_numpy(float)
          * rng.lognormal(0, 0.10, len(jg)) * (1 + 0.25 * fj["deg"]))
    jc = jg.assign(iniciadas=ini, concluidas=con, tempo_medio_min=tm)
    jc["semana"] = _semana(jc["data"])

    # ---------------- estabilidade
    # ESTABILIDADE: incidentes reduzem a disponibilidade do dia e pioram tempo de resposta e erros.
    inc = _gerar_incidentes(rng, datas)
    ds = pd.MultiIndex.from_product([datas, S.SISTEMAS], names=["data", "sistema"]).to_frame(index=False)
    fd = _fatores(ds, datas)
    # Cada incidente derruba a disponibilidade do dia proporcionalmente à duração.
    queda = np.zeros(len(ds))
    mult_inc = np.ones(len(ds))
    chave = ds["data"].astype(str) + "|" + ds["sistema"]
    for _, r in inc.iterrows():
        m = (chave == f"{r.data}|{r.sistema}").to_numpy()
        queda[m] += r.duracao_h / 24 * 100
        mult_inc[m] = 1.8
    up_b = ds["sistema"].map({k: v["uptime"] for k, v in BASE.items()}).to_numpy(float)
    up = np.clip(up_b + rng.normal(0, 0.04, len(ds)) - 2.4 * fd["deg"] - queda, 0, 100)
    disp = ds[["data", "sistema"]].assign(uptime_pct=up)
    disp["semana"] = _semana(disp["data"])
    rb = ds["sistema"].map({k: v["resp"] for k, v in BASE.items()}).to_numpy(float)
    eb = ds["sistema"].map({k: v["erro"] for k, v in BASE.items()}).to_numpy(float)
    des = ds[["data", "sistema"]].assign(
        tempo_resposta_ms=rb * rng.lognormal(0, 0.08, len(ds)) * (1 + 0.6 * fd["deg"]) * mult_inc,
        taxa_erro_pct=eb * rng.lognormal(0, 0.15, len(ds)) * (1 + 2.0 * fd["deg"]) * mult_inc,
    )
    des["semana"] = _semana(des["data"])

    dados = dict(
        uso=uso, satisfacao=sat, suporte=sup, jornada_conclusao=jc, jornada_dim=jornada_dim,
        jornada_funil=jornada_funil, disponibilidade=disp, desempenho=des, incidentes=inc,
        erros_log=tabela_vazia("erros_log"),
        sistemas=list(S.SISTEMAS), orgaos=list(S.ORGAOS), perfis=list(S.PERFIS),
    )
    # Garante que as tabelas geradas respeitam o contrato.
    problemas = validar_todos(dados)
    if problemas:
        raise ValueError("Dados fora do contrato: " + "; ".join(problemas))
    return dados


# Cache do Streamlit: gera uma vez por sessão do servidor.
@st.cache_data(show_spinner="Gerando dados sintéticos…")
def carregar_dados() -> dict:
    """Interface estável consumida pela aplicação."""
    return gerar_todos_os_dados()
