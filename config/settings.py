"""Configuração central do painel (parâmetros, metas, limiares e identidade).

TODOS os limiares de alerta, pesos do índice e metas ficam aqui.
Nenhum desses valores é oficial: são parâmetros PROVISÓRIOS / CONCEITUAIS.
"""
from __future__ import annotations

# ------------------------------------------------------------------ identidade
APP_NAME = "Pulso"  # codinome técnico interno (não é o nome exibido ao usuário)
APP_MARCA_VISIVEL = "UX"
APP_NOME_COMPLETO = "Plano de Mensuração e Painel de Indicadores - UX (SIGEPE)"
APP_SUBTITLE = "Painel analítico de apoio à decisão sobre os sistemas estruturantes de gestão de pessoas"
APP_EDITAL = "Chamada de Desafio nº 02/2026"
# Usado só para ler a variável de ambiente PULSO_FONTE.
import os as _os

OFICIAL_TOP_ORGAOS = 8  # órgãos exibidos individualmente; demais viram "Demais órgãos"


def fonte_dados() -> str:
    """'sintetico' (padrão) ou 'oficial' (variável de ambiente PULSO_FONTE=oficial)."""
    return "oficial" if _os.environ.get("PULSO_FONTE", "sintetico").lower().startswith("of") else "sintetico"


def aviso_dados() -> str:
    if fonte_dados() == "oficial":
        return ("DADOS DA ORGANIZAÇÃO (PARCIAIS) · INDICADORES PROVISÓRIOS / CONCEITUAIS — "
                "uso restrito ao desafio; sem dado pessoal exibido.")
    return DADOS_PROVISORIOS_AVISO


# Aviso padrão exibido no cabeçalho (dados sintéticos).
DADOS_PROVISORIOS_AVISO = (
    "DADOS SINTÉTICOS · INDICADORES PROVISÓRIOS / CONCEITUAIS — "
    "não representam dados nem indicadores oficiais."
)
SELO_INDICADOR = "INDICADOR PROVISÓRIO / CONCEITUAL"
NAO_DISPONIBILIZADO = "INFORMAÇÃO NÃO DISPONIBILIZADA"

# ------------------------------------------------------------------ dados sintéticos
# Parâmetros do gerador de dados sintéticos (período e semente fixa → resultados reprodutíveis).
DATA_INICIO = "2025-02-01"
DATA_FIM = "2026-08-23"
SEED = 42
JANELA_PADRAO_DIAS = 120

# Atalhos de período da barra lateral (None = todo o histórico).
PERIODOS_ATALHO = {
    "Últimos 30 dias": 30,
    "Últimos 60 dias": 60,
    "Últimos 90 dias": 90,
    "Últimos 120 dias": 120,
    "Últimos 6 meses": 180,
    "Últimos 12 meses": 365,
    "Todo o histórico": None,
}

# Cadastros fictícios usados nos dados sintéticos. Com dados oficiais, vêm dos próprios arquivos.
SISTEMAS = ["Sistema Alfa", "Sistema Beta", "Sistema Gama", "Sistema Delta", "Sistema Épsilon"]
ORGAOS = [
    "Órgão Central",
    "Órgão Regional Sul",
    "Órgão Regional Norte",
    "Órgão Regional Leste",
    "Órgão Regional Oeste",
    "Autarquia Federal Modelo",
]
PERFIS = ["Servidor", "Gestor", "Operador de RH"]

# ------------------------------------------------------------------ índice de saúde (ISS)
# Pesos das três dimensões do ISS (somam 1,0).
PESOS_ISS = {"uso": 0.30, "satisfacao": 0.40, "estabilidade": 0.30}
# Cortes da classificação: ≥80 saudável; ≥60 atenção; abaixo disso crítico.
FAIXAS_ISS = {"saudavel": 80.0, "atencao": 60.0}  # >=80 saudável; >=60 atenção; <60 crítico

# ------------------------------------------------------------------ metas provisórias
# Metas PROVISÓRIAS: servem de referência visual, não são oficiais.
META_ADOCAO = 60.0          # %
META_CSAT = 75.0            # %
META_CONCLUSAO = 75.0       # %
META_DISPONIBILIDADE = 99.5  # %
META_TMR_HORAS = 48.0       # horas
META_TEMPO_RESPOSTA_MS = 800.0
META_REINCIDENCIA = 12.0    # %
META_TAXA_ERRO = 1.0        # %

# faixas de normalização 0-100 (min, max) usadas no ISS
# Faixas (mínimo, máximo) que levam cada indicador à escala 0–100 do ISS.
NORMALIZACAO = {
    "adocao": (0.0, 90.0),
    "csat": (40.0, 95.0),
    "disponibilidade": (95.0, 100.0),
    "conclusao": (50.0, 95.0),
    "tmr": (0.0, 3 * META_TMR_HORAS),  # invertido: menor é melhor
}

# ------------------------------------------------------------------ alertas (atenção / crítico)
# Piora mínima para gerar alerta de 'atenção' e 'crítico' (pp = pontos percentuais).
LIMIARES_ALERTA = {
    "queda_satisfacao_pp": {"atencao": 5.0, "critico": 10.0},
    "aumento_chamados_pct": {"atencao": 20.0, "critico": 40.0},
    "queda_conclusao_pp": {"atencao": 8.0, "critico": 15.0},
    "queda_disponibilidade_pp": {"atencao": 0.5, "critico": 1.5},
    "aumento_tempo_resposta_pct": {"atencao": 10.0, "critico": 25.0},
    "queda_usuarios_ativos_pct": {"atencao": 10.0, "critico": 20.0},
}
# Peso do nível na pontuação de severidade.
PESO_NIVEL_ALERTA = {"atenção": 1.5, "crítico": 3.0}

# esforço estimado (1 baixo … 5 alto) por dimensão, usado na matriz Impacto × Esforço
# Esforço estimado (1–5) usado na matriz Impacto × Esforço.
ESFORCO_POR_DIMENSAO = {
    "Suporte": 2,
    "Jornadas Digitais": 3,
    "Satisfação": 3,
    "Uso": 4,
    "Estabilidade": 5,
}
# Adoção abaixo deste valor (%) numa combinação sistema × órgão vira oportunidade.
LIMIAR_ADOCAO_ORGAO_BAIXA = 40.0  # % — célula sistema×órgão abaixo disso vira oportunidade

# ------------------------------------------------------------------ cores de estado (base)
# Cores-base legadas (a interface usa config/theme.py com a paleta gov.br).
COR_SAUDAVEL = "#1FAA59"
COR_ATENCAO = "#E8A83C"
COR_CRITICO = "#E2574C"
COR_PRIMARIA = "#0F5C66"
COR_DESTAQUE = "#7C6FE0"

# Páginas do painel: (arquivo, título, ícone). A ordem define o menu lateral.
PAGINAS = [
    ("pages/1_visao_geral.py", "Visão Geral", "◧"),
    ("pages/2_uso_dos_sistemas.py", "Uso dos Sistemas", "◨"),
    ("pages/3_experiencia_satisfacao.py", "Experiência e Satisfação", "◩"),
    ("pages/4_jornadas_digitais.py", "Jornadas Digitais", "◪"),
    ("pages/5_suporte_atendimento.py", "Suporte e Atendimento", "◫"),
    ("pages/6_estabilidade.py", "Estabilidade", "◬"),
    ("pages/7_alertas_oportunidades.py", "Alertas e Oportunidades", "◭"),
]
