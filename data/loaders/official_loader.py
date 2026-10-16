"""Loader dos dados OFICIAIS (arquivos da organização, lidos LOCALMENTE em data/official/).

Ativação:  PowerShell  ->  $env:PULSO_FONTE="oficial"; python -m streamlit run app/main.py
Pasta alternativa:         $env:PULSO_DADOS_OFICIAIS="C:\\caminho\\da\\pasta"

Princípios de privacidade (LGPD / edital):
- só as colunas necessárias são lidas; texto livre (comentários, título/descrição de chamado,
  valores anterior/atual, stacktrace) e IPs NUNCA entram na memória do painel;
- nenhum registro individual é exposto: tudo é agregado por dia × sistema × órgão × perfil;
- o que não foi disponibilizado fica vazio ("INFORMAÇÃO NÃO DISPONIBILIZADA"), nunca inventado.

Mapeamento fonte → tabela do painel (detalhes em docs/mapeamento_fontes_oficiais.md):
  AvaliacoesInternas*.xlsx -> satisfacao   (CSAT provisório: nota >= 4 em escala 1–5)
  CentraSIPEC*.xlsx        -> suporte      (chamados, TMR, 1ª resposta, reincidência)
  logs com ID_ERRO (AFD, AFASTAMENTO, REQUERIMENTO, ACOES_JUDICIAIS…) -> erros_log
  PesquisaSigepe*.xlsx     -> não integrada (qualitativa; escala/instrumento a definir)
  *Lista_incidentes*.xlsx  -> incidentes   (duração = fim − início; severidade provisória; sistema = SIGEPE)
  Analytics (uso/jornadas) e monitoramento (disponibilidade/tempo de resposta) -> INFORMAÇÃO NÃO DISPONIBILIZADA
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from config import settings as S
from data.schemas.schema_definitions import tabela_vazia, validar_todos

# Raiz do projeto (dois níveis acima deste arquivo).
RAIZ = Path(__file__).resolve().parents[2]
NAO = S.NAO_DISPONIBILIZADO
# Código de vínculo da avaliação → perfil legível.
PERFIL_VINCULO = {"SER": "Servidor", "PEN": "Pensionista", "APO": "Aposentado"}
# Tabela de meses PT/EN: permite ler datas Oracle ('01-SEP-25') sem depender do idioma do Windows.
MESES = {"JAN": 1, "FEV": 2, "FEB": 2, "MAR": 3, "ABR": 4, "APR": 4, "MAI": 5, "MAY": 5, "JUN": 6,
         "JUL": 7, "AGO": 8, "AUG": 8, "SET": 9, "SEP": 9, "OUT": 10, "OCT": 10, "NOV": 11, "DEZ": 12, "DEC": 12}
COLS_LOG = ["NO_MODULO", "IN_CLASSIFICACAO", "DT_EVENTO"]  # as únicas colunas de log que interessam


def pasta_oficial() -> Path:
    """Pasta dos arquivos oficiais: variável PULSO_DADOS_OFICIAIS ou data/official/ (ignorada pelo Git)."""
    return Path(os.environ.get("PULSO_DADOS_OFICIAIS", RAIZ / "data" / "official"))


# ------------------------------------------------------------------ utilitários
def _semana(s: pd.Series) -> pd.Series:
    """Segunda-feira da semana de cada data (chave de agrupamento semanal)."""
    return s.dt.to_period("W").dt.start_time


def _top_n(serie: pd.Series, n: int = S.OFICIAL_TOP_ORGAOS) -> pd.Series:
    """Mantém os n valores mais frequentes; o restante vira 'Demais órgãos'."""
    topo = serie.value_counts().head(n).index
    return serie.where(serie.isin(topo), "Demais órgãos")


def _data_flex(s: pd.Series) -> pd.Series:
    """Datas 'M/D/AAAA H:MM' (formato da Central) ou qualquer formato ISO/Excel."""
    # Tenta o formato da Central; o que falhar é lido por formatos genéricos.
    out = pd.to_datetime(s, format="%m/%d/%Y %H:%M", errors="coerce")
    falta = out.isna()
    if falta.any():
        out[falta] = pd.to_datetime(s[falta], errors="coerce")
    return out


def _data_oracle(s: pd.Series) -> pd.Series:
    """'01-SEP-25 08.02.26,000000 AM' -> Timestamp, sem depender de locale (Windows pt-BR)."""
    # Extrai dia, mês (3 letras), ano, hora, minuto, segundo e AM/PM por expressão regular.
    x = s.astype("string").str.strip().str.upper().str.extract(
        r"^(\d{1,2})-([A-Z]{3})-(\d{2,4})\s+(\d{1,2})\.(\d{2})\.(\d{2})(?:[.,]\d+)?\s*(AM|PM)?")
    mes = x[1].map(MESES)
    ano = pd.to_numeric(x[2], errors="coerce")
    # Ano de 2 dígitos vira 20XX.
    ano = ano.where(ano >= 100, ano + 2000)
    hora = pd.to_numeric(x[3], errors="coerce")
    pm = x[6] == "PM"
    # Converte relógio de 12 h (AM/PM) para 24 h.
    hora = np.where(pm & (hora < 12), hora + 12, np.where((x[6] == "AM") & (hora == 12), 0, hora))
    out = pd.to_datetime(dict(year=ano, month=mes, day=pd.to_numeric(x[0], errors="coerce"),
                              hour=hora, minute=pd.to_numeric(x[4], errors="coerce")), errors="coerce")
    falta = out.isna()
    if falta.any():
        out[falta] = pd.to_datetime(s[falta], errors="coerce")
    return out


def _listar(pasta: Path) -> list[Path]:
    """Lista as planilhas (.xlsx/.xls/.csv) da pasta, ignorando arquivos temporários do Excel (~$)."""
    if not pasta.exists():
        return []
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() in (".xlsx", ".xls", ".csv") and not p.name.startswith("~$"))


def _ler(path: Path, **kw) -> pd.DataFrame:
    """Lê planilha ou CSV com a mesma interface; `kw` repassa opções ao pandas (ex.: usecols)."""
    if path.suffix.lower() == ".csv":
        kw.pop("sheet_name", None)
        return pd.read_csv(path, **{k: v for k, v in kw.items() if k != "nrows" or v is not None})
    return pd.read_excel(path, **kw)


def _eh_log(path: Path) -> bool:
    """Um arquivo é 'log' se o cabeçalho contiver ID_ERRO (lê só o cabeçalho)."""
    try:
        cab = _ler(path, nrows=0)
    except Exception:
        return False
    return "ID_ERRO" in "|".join(map(str, cab.columns)).upper()


def _eh_incidentes(path: Path) -> bool:
    """Lista de incidentes: cabeçalho com TICKETID e DATAFIMOCORRENCIA (lê só o cabeçalho)."""
    try:
        cab = "|".join(map(str, _ler(path, nrows=0).columns)).upper()
    except Exception:
        return False
    return "TICKETID" in cab and "DATAFIMOCORRENCIA" in cab


def classificar_arquivos(pasta: Path) -> dict:
    """Identifica cada arquivo pelo nome (avaliações, central, pesquisa) ou pelo conteúdo (logs)."""
    achados: dict = {"avaliacoes": [], "central": [], "pesquisa": [], "logs": [], "incidentes": []}
    for p in _listar(pasta):
        nome = p.name.lower()
        if "avalia" in nome and "esclarec" not in nome:
            achados["avaliacoes"].append(p)
        elif "centra" in nome or "sipec_sigepe" in nome:
            achados["central"].append(p)
        elif "pesquisa" in nome:
            achados["pesquisa"].append(p)
        elif "incidente" in nome or _eh_incidentes(p):
            achados["incidentes"].append(p)
        elif _eh_log(p):
            achados["logs"].append(p)
    return achados


# ------------------------------------------------------------------ incidentes
def _severidade_provisoria(h: float) -> str:
    """Regra PROVISÓRIA por duração (a organização não informou severidade): >=6 h Crítica, >=3 h Média, senão Baixa."""
    return "Crítica" if h >= 6 else "Média" if h >= 3 else "Baixa"


def carregar_incidentes(arquivos: list[Path]) -> pd.DataFrame:
    """Lista de incidentes -> tabela `incidentes`.
    Lê apenas ID, início e fim da ocorrência; o texto livre (RESUMO) NUNCA é lido.
    Opção B: `sistema` permanece SIGEPE (o módulo/produto não vira 'Sistema').
    Linhas em branco ou sem datas válidas são descartadas; duração negativa também.
    """
    if not arquivos:
        return tabela_vazia("incidentes")
    partes = []
    for p in arquivos:
        df = _ler(p, usecols=lambda c: str(c).strip().upper() in {"TICKETID", "SERPRODATAINICIO", "DATAFIMOCORRENCIA"})
        df.columns = [str(c).strip().upper() for c in df.columns]
        ini = pd.to_datetime(df["SERPRODATAINICIO"], errors="coerce")
        fim = pd.to_datetime(df["DATAFIMOCORRENCIA"], errors="coerce")
        dur = (fim - ini).dt.total_seconds() / 3600
        ok = df["TICKETID"].notna() & ini.notna() & fim.notna() & (dur >= 0)
        partes.append(pd.DataFrame({
            "incidente_id": df.loc[ok, "TICKETID"].astype(str).str.strip(),
            "sistema": "SIGEPE",
            "data": ini[ok].dt.normalize(),
            "duracao_h": dur[ok].round(2),
        }))
    out = pd.concat(partes, ignore_index=True).drop_duplicates("incidente_id")
    out["severidade"] = out["duracao_h"].map(_severidade_provisoria)
    return out[["incidente_id", "sistema", "data", "duracao_h", "severidade"]].reset_index(drop=True)


# ------------------------------------------------------------------ satisfação
def carregar_avaliacoes(arquivos: list[Path]) -> pd.DataFrame:
    """Avaliações internas (nota 1–5) -> tabela `satisfacao`. Comentários NÃO são lidos."""
    if not arquivos:
        return tabela_vazia("satisfacao")
    partes = []
    for p in arquivos:
        # Privacidade: só estas colunas são lidas; o texto livre (comentários) nunca entra na memória.
        df = _ler(p, usecols=lambda c: str(c).strip() in {"Sistema", "Data", "Nota", "Vínculo", "Órgão"})
        df.columns = [str(c).strip() for c in df.columns]
        partes.append(df)
    d = pd.concat(partes, ignore_index=True)
    d["data"] = pd.to_datetime(d["Data"], errors="coerce").dt.normalize()
    d["nota"] = pd.to_numeric(d["Nota"], errors="coerce")
    d = d.dropna(subset=["data", "nota"])
    d["sistema"] = d["Sistema"].astype("string").str.strip().fillna("SIGEPE").astype(object)
    d["orgao"] = _top_n("Órgão " + d["Órgão"].astype("string").str.replace(r"\.0$", "", regex=True).fillna("não informado")).astype(object)
    d["perfil"] = d["Vínculo"].astype("string").str.strip().str.upper().map(PERFIL_VINCULO).fillna("Não informado").astype(object)
    # Regra provisória de CSAT: nota 4 ou 5 (em 1–5) = satisfeito.
    d["satisfeito"] = (d["nota"] >= 4).astype(int)  # regra provisória de CSAT
    g = d.groupby(["data", "sistema", "orgao", "perfil"], as_index=False).agg(
        respostas=("nota", "size"), satisfeitos=("satisfeito", "sum"))
    # Esforço (CES) não existe nesta fonte → fica vazio, nunca inventado.
    g["ces_medio"] = np.nan  # esforço (CES) não disponibilizado nesta fonte
    g["semana"] = _semana(g["data"])
    return g[["data", "semana", "sistema", "orgao", "perfil", "respostas", "satisfeitos", "ces_medio"]]


# ------------------------------------------------------------------ suporte
def carregar_central(arquivos: list[Path]) -> pd.DataFrame:
    """Chamados da Central SIPEC -> tabela `suporte`. Título, descrição e ações NÃO são lidos."""
    if not arquivos:
        return tabela_vazia("suporte")
    # Privacidade: título, descrição e ações dos chamados não são lidos.
    uteis = {"Categoria", "Organização", "Data de abertura", "Data de início de atendimento",
             "Data de Solução", "Tempo em horas do atendimento", "Chamados Relacionados"}
    partes = []
    for p in arquivos:
        df = _ler(p, usecols=lambda c: str(c).strip() in uteis)
        df.columns = [str(c).strip() for c in df.columns]
        partes.append(df)
    d = pd.concat(partes, ignore_index=True)
    d["abertura"] = _data_flex(d["Data de abertura"])
    d = d.dropna(subset=["abertura"])
    d["data"] = d["abertura"].dt.normalize()
    # Sistema = texto da categoria antes de ' - '.
    d["sistema"] = (d["Categoria"].astype("string").str.split(" - ").str[0].str.strip().fillna("SIGEPE")).astype(object)
    d["orgao"] = _top_n(d["Organização"].astype("string").str.strip().fillna("Não informado")).astype(object)
    d["perfil"] = "Não informado"  # a Central não informa o perfil do solicitante
    d["tmr_horas"] = pd.to_numeric(d["Tempo em horas do atendimento"], errors="coerce")
    inicio = _data_flex(d["Data de início de atendimento"]) if "Data de início de atendimento" in d else pd.NaT
    # Tempo até a 1ª resposta = início do atendimento − abertura (em horas).
    d["tpr_horas"] = (inicio - d["abertura"]).dt.total_seconds() / 3600
    rel = d["Chamados Relacionados"] if "Chamados Relacionados" in d else pd.Series("", index=d.index)
    # Reincidente = chamado que possui 'Chamados Relacionados' preenchido.
    d["reinc"] = rel.notna() & (rel.astype("string").str.strip() != "")
    g = d.groupby(["data", "sistema", "orgao", "perfil"], as_index=False).agg(
        chamados=("data", "size"), tmr_horas=("tmr_horas", "mean"), tpr_horas=("tpr_horas", "mean"),
        reincidentes=("reinc", "sum"))
    g["reincidentes"] = g["reincidentes"].astype(int)
    g["semana"] = _semana(g["data"])
    return g[["data", "semana", "sistema", "orgao", "perfil", "chamados", "tmr_horas", "tpr_horas", "reincidentes"]]


# ------------------------------------------------------------------ logs de erro
def _norm(c) -> str:
    """Normaliza nome de coluna: sem espaços e em maiúsculas."""
    return re.sub(r"\s+", "", str(c)).upper()


def _extrair_log_folha(raw: pd.DataFrame) -> tuple[pd.DataFrame | None, str]:
    """Localiza o cabeçalho (qualquer linha das 15 primeiras) e devolve só NO_MODULO/IN_CLASSIFICACAO/DT_EVENTO.

    Aceita: colunas normais; ou UMA célula de cabeçalho 'A|B|C…' com linhas no mesmo formato.
    """
    for r in range(min(15, len(raw))):
        linha = raw.iloc[r].dropna().astype(str)
        if not linha.str.upper().str.contains("DT_EVENTO", regex=False).any():
            continue
        # Formato alternativo: cabeçalho e linhas em UMA coluna separada por '|'.
        if len(linha) == 1 and "|" in linha.iloc[0]:  # cabeçalho único com pipes
            nomes = [_norm(c) for c in linha.iloc[0].split("|")]
            dados = raw.iloc[r + 1:, 0].astype("string").str.split("|", n=len(nomes) - 1, expand=True)
            dados.columns = nomes[: dados.shape[1]]
        else:
            nomes = [_norm(c) for c in raw.iloc[r].tolist()]
            dados = raw.iloc[r + 1:].copy()
            dados.columns = nomes
        # Remove colunas repetidas. Daqui em diante só as 3 colunas úteis seguem (IPs e valores são descartados).
        dados = dados.loc[:, ~dados.columns.duplicated()]
        uteis = [c for c in COLS_LOG if c in dados.columns]
        if "DT_EVENTO" not in uteis:
            return None, f"cabeçalho sem DT_EVENTO (colunas: {', '.join(nomes[:15])})"
        return dados[uteis], ""
    return None, "cabeçalho com DT_EVENTO não encontrado nas 15 primeiras linhas"


def ler_log_arquivo(p: Path) -> tuple[pd.DataFrame | None, str]:
    """Lê um arquivo de log (xlsx/csv) devolvendo (dados úteis, motivo_da_falha)."""
    try:
        if p.suffix.lower() == ".csv":
            raw = pd.read_csv(p, header=None, sep="\x1f", dtype=str, on_bad_lines="skip", encoding_errors="replace", engine="python")
            folhas = {"csv": raw}
        else:
            folhas = pd.read_excel(p, sheet_name=None, header=None, dtype=str)
    except Exception as ex:  # noqa: BLE001
        return None, f"falha ao abrir ({type(ex).__name__})"
    # Tenta todas as abas; cada falha vira um motivo exibido na 'Cobertura das fontes'.
    partes, motivos = [], []
    for nome, raw in folhas.items():
        if raw.empty:
            continue
        df, motivo = _extrair_log_folha(raw)
        if df is not None:
            partes.append(df)
        else:
            motivos.append(f"aba '{nome}': {motivo}")
    if not partes:
        return None, "; ".join(motivos) or "arquivo vazio"
    return pd.concat(partes, ignore_index=True), ""


def carregar_logs(arquivos: list[Path], sistema: str = "SIGEPE", avisos: list | None = None) -> pd.DataFrame:
    """Eventos de log -> `erros_log` (contagem por dia × módulo × classificação). IPs/valores/stacktrace descartados."""
    avisos = avisos if avisos is not None else []
    partes = []
    for p in arquivos:
        df, motivo = ler_log_arquivo(p)
        if df is None:
            avisos.append(f"{p.name}: {motivo}")
            continue
        if "NO_MODULO" not in df:
            df["NO_MODULO"] = p.stem.split("-")[-1].upper()
        partes.append(df)
    if not partes:
        return tabela_vazia("erros_log")
    d = pd.concat(partes, ignore_index=True)
    # Converte DT_EVENTO para data (sem hora).
    d["data"] = _data_oracle(d["DT_EVENTO"]).dt.normalize()
    d = d.dropna(subset=["data"])
    if d.empty:
        avisos.append("nenhuma data de DT_EVENTO pôde ser interpretada")
        return tabela_vazia("erros_log")
    d["modulo"] = d["NO_MODULO"].astype("string").str.strip().str.upper().fillna("NÃO INFORMADO").astype(object)
    classe = d["IN_CLASSIFICACAO"] if "IN_CLASSIFICACAO" in d else pd.Series("NÃO INFORMADO", index=d.index)
    d["classificacao"] = classe.astype("string").str.strip().fillna("NÃO INFORMADO").astype(object)
    d["sistema"] = sistema
    # Agregação final: nenhum evento individual é mantido, só contagens.
    g = d.groupby(["data", "sistema", "modulo", "classificacao"], as_index=False).size().rename(columns={"size": "erros"})
    g["semana"] = _semana(g["data"])
    return g[["data", "semana", "sistema", "modulo", "classificacao", "erros"]]


# ------------------------------------------------------------------ orquestração
def montar_dados(pasta: Path) -> dict:
    """Lê todas as fontes disponíveis e monta o dicionário de tabelas no contrato do painel.
    Fontes ausentes viram tabelas vazias ('INFORMAÇÃO NÃO DISPONIBILIZADA').
    """
    ach = classificar_arquivos(pasta)
    problemas_leitura: dict[str, str] = {}

    # Executa a leitura de uma fonte; em caso de erro registra o motivo e devolve tabela vazia (o painel não cai).
    def seguro(chave: str, fn, nome_tabela: str):
        try:
            return fn()
        except Exception as ex:  # noqa: BLE001  — nunca derrubar o painel por uma fonte com estrutura diferente
            problemas_leitura[chave] = f"ERRO ao ler ({type(ex).__name__}: {str(ex)[:100]}) — estrutura diferente da amostra"
            return tabela_vazia(nome_tabela)

    avisos_logs: list[str] = []
    sat = seguro("avaliacoes", lambda: carregar_avaliacoes(ach["avaliacoes"]), "satisfacao")
    sup = seguro("central", lambda: carregar_central(ach["central"]), "suporte")
    logs = seguro("logs", lambda: carregar_logs(ach["logs"], avisos=avisos_logs), "erros_log")
    inc = seguro("incidentes", lambda: carregar_incidentes(ach["incidentes"]), "incidentes")
    # Tabelas sem fonte oficial (uso, jornadas, disponibilidade...) começam vazias.
    dados = dict(
        uso=tabela_vazia("uso"), satisfacao=sat, suporte=sup,
        jornada_conclusao=tabela_vazia("jornada_conclusao"), jornada_dim=tabela_vazia("jornada_dim"),
        jornada_funil=tabela_vazia("jornada_funil"), disponibilidade=tabela_vazia("disponibilidade"),
        desempenho=tabela_vazia("desempenho"), incidentes=inc, erros_log=logs,
    )

    # Valores distintos de uma coluna nas tabelas carregadas (alimentam os filtros).
    def uniq(col: str) -> list[str]:
        vals: set[str] = set()
        for k in ("satisfacao", "suporte"):
            vals |= set(dados[k][col].dropna().unique())
        return sorted(vals)

    sistemas = sorted(set(uniq("sistema")) | set(logs["sistema"].unique()))
    dados.update(sistemas=sistemas or ["SIGEPE"], orgaos=uniq("orgao"), perfis=uniq("perfil"))
    n = lambda k: len(ach[k])  # noqa: E731
    # Resumo mostrado na Visão Geral: o que foi lido, o que falhou e o que não foi disponibilizado.
    dados["cobertura"] = {
        "Avaliações internas → Satisfação": problemas_leitura.get("avaliacoes") or (f"{n('avaliacoes')} arquivo(s)" if n("avaliacoes") else NAO),
        "Central SIPEC → Suporte": problemas_leitura.get("central") or (f"{n('central')} arquivo(s)" if n("central") else NAO),
        "Logs de erro → Estabilidade (erros em log)": problemas_leitura.get("logs") or (
            (f"{n('logs')} arquivo(s)" if n("logs") else NAO) + (" · AVISO: " + " | ".join(avisos_logs) if avisos_logs else "")),
        "Pesquisa SIGEPE (qualitativa)": "arquivo localizado, não integrada (instrumento/escala a definir)" if n("pesquisa") else NAO,
        "Analytics → Uso e Jornadas": NAO,
        "Incidentes → Estabilidade (incidentes)": problemas_leitura.get("incidentes") or (
            f"{n('incidentes')} arquivo(s) · severidade PROVISÓRIA por duração" if n("incidentes") else NAO),
        "Monitoramento → Disponibilidade e tempo de resposta": NAO,
        "Perfil na Central / órgão (código × nome)": NAO,
    }
    # Garante que todas as tabelas respeitam o contrato antes de entregar ao painel.
    problemas = validar_todos(dados)
    if problemas:
        raise ValueError("Dados oficiais fora do contrato: " + "; ".join(problemas))
    return dados


# Cache: só relê os arquivos se nome, data de modificação ou tamanho mudarem (assinatura).
@st.cache_data(show_spinner="Lendo dados oficiais (local)…")
def _carregar_cacheado(pasta: str, assinatura: tuple) -> dict:
    return montar_dados(Path(pasta))


def carregar_dados() -> dict:
    """Interface estável consumida pela aplicação (mesma assinatura do mock_loader)."""
    pasta = pasta_oficial()
    # Assinatura dos arquivos da pasta (usada como chave do cache).
    assinatura = tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in _listar(pasta))
    if not assinatura:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em {pasta}. Copie as planilhas para data/official/ "
            "(pasta ignorada pelo Git) ou defina PULSO_DADOS_OFICIAIS.")
    return _carregar_cacheado(str(pasta), assinatura)
