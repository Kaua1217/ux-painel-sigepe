"""Design system CENTRALIZADO (claro e escuro). Nenhum valor visual deve ficar espalhado pelo código.

Hierarquia espacial: SIDEBAR (navegação) ≠ CONTEÚDO (análise) nos DOIS temas,
por tonalidade de fundo + divisória fina + item ativo + espaçamento.
"""
from __future__ import annotations

import streamlit as st

# Paleta: Padrão Digital de Governo (gov.br/ds) v3.7.0 — tokens oficiais de cor (core-tokens).
# O DS v3.7.0 define apenas o tema CLARO; o tema ESCURO abaixo é uma derivação com a mesma paleta (não é oficial).
DS = dict(
    blue_warm_vivid_90="#071D41", blue_warm_vivid_80="#0C326F", blue_warm_vivid_70="#1351B4", blue_warm_vivid_60="#155BCB",
    blue_warm_vivid_40="#5992ED", blue_warm_vivid_30="#81AEFC", blue_warm_vivid_10="#D4E5FF",
    blue_warm_90="#13171F", blue_warm_80="#252F3E", blue_warm_70="#2F4668", blue_warm_50="#4A77B4", blue_warm_30="#98AFD2",
    blue_warm_10="#E1E7F1", blue_warm_5="#ECF1F7",
    gray_90="#1B1B1B", gray_80="#333333", gray_70="#555555", gray_60="#636363", gray_30="#ADADAD", gray_20="#CCCCCC",
    gray_10="#E6E6E6", gray_2="#F8F8F8", gray_1="#FCFCFC",
    green_cool_vivid_50="#168821", green_cool_vivid_30="#21C834", green_vivid_50="#538200",
    yellow_vivid_50="#947100", yellow_vivid_40="#B38C00", yellow_vivid_20="#FFCD07",
    orange_vivid_50="#C05600", orange_vivid_20="#FFBC78",
    red_vivid_50="#E52207", red_vivid_40="#FB5A47",
)
# Tokens do tema CLARO: cada papel visual (fundo, texto, cor de estado...) recebe uma cor do DS.
TOKENS_LIGHT = dict(
    sidebar_bg=DS["blue_warm_5"], content_bg="#FFFFFF", card_bg="#FFFFFF", divider=DS["gray_20"],
    text_primary=DS["gray_80"], text_secondary=DS["gray_70"], text_muted=DS["gray_60"],
    active_bg=DS["blue_warm_vivid_10"], hover_bg=DS["blue_warm_10"], input_bg="#FFFFFF", accent=DS["blue_warm_vivid_70"],
    saudavel=DS["green_cool_vivid_50"], atencao=DS["yellow_vivid_50"], critico=DS["red_vivid_50"], info=DS["blue_warm_vivid_60"],
    grid=DS["gray_10"], sombra="0 1px 2px rgba(51,51,51,0.08)",
)
# Tokens do tema ESCURO (derivação não oficial, mantendo contraste mínimo de 4,5:1 verificado em testes).
TOKENS_DARK = dict(
    sidebar_bg=DS["blue_warm_vivid_90"], content_bg=DS["blue_warm_90"], card_bg=DS["blue_warm_80"], divider=DS["blue_warm_70"],
    text_primary=DS["gray_1"], text_secondary=DS["gray_20"], text_muted=DS["gray_30"],
    active_bg=DS["blue_warm_vivid_80"], hover_bg=DS["blue_warm_70"], input_bg=DS["blue_warm_90"], accent=DS["blue_warm_vivid_30"],
    saudavel=DS["green_cool_vivid_30"], atencao=DS["yellow_vivid_20"], critico="#FF8D7B", info=DS["blue_warm_vivid_40"],
    grid=DS["blue_warm_70"], sombra="none",
)
# Tipografia e espaçamento padrão.
TIPOGRAFIA = dict(familia="Rawline, Raleway, Verdana, Arial, sans-serif",
                  h1="1.65rem", h2="1.15rem", corpo="0.95rem", pequeno="0.8rem")
ESPACAMENTO = dict(pad_conteudo="2rem", raio="8px", raio_pequeno="4px")
# Cores das séries dos gráficos (distinguíveis entre si além da cor: o gráfico também usa rótulos/símbolos).
SERIES_LIGHT = [DS["blue_warm_vivid_70"], DS["orange_vivid_50"], DS["green_vivid_50"], DS["blue_warm_50"], DS["yellow_vivid_40"], DS["gray_60"]]
SERIES_DARK = [DS["blue_warm_vivid_30"], DS["orange_vivid_20"], "#98D035", DS["blue_warm_30"], DS["yellow_vivid_20"], DS["gray_30"]]
# Símbolo + rótulo acompanham a cor do estado: acessibilidade para quem não distingue cores.
SIMBOLO_ESTADO = {"saudavel": "●", "atencao": "▲", "critico": "✖", "indisponivel": "○"}
ROTULO_ESTADO = {"saudavel": "Saudável", "atencao": "Atenção", "critico": "Crítico", "indisponivel": "Sem dados"}


def tema_ativo() -> str:
    """'dark' ou 'light', respeitando a opção System/Light/Dark do Streamlit quando disponível."""
    try:
        t = st.context.theme.type
        return "dark" if t == "dark" else "light"
    except Exception:
        return "light"


def eh_dark() -> bool:
    """True se o tema ativo é escuro."""
    return tema_ativo() == "dark"


def tokens_atuais() -> dict:
    """Devolve o conjunto de tokens do tema ativo."""
    return TOKENS_DARK if eh_dark() else TOKENS_LIGHT


def cor_por_estado(estado: str) -> str:
    """Cor correspondente a 'saudavel', 'atencao' ou 'critico' (neutra para qualquer outro valor)."""
    t = tokens_atuais()
    return {"saudavel": t["saudavel"], "atencao": t["atencao"], "critico": t["critico"]}.get(estado, t["text_muted"])


def cor_texto_sobre_marca() -> str:
    """Cor de texto legível sobre as cores de estado/marca do tema atual."""
    return DS["blue_warm_90"] if eh_dark() else "#FFFFFF"


def cores_grafico_atuais() -> list[str]:
    """Paleta de séries do tema ativo."""
    return SERIES_DARK if eh_dark() else SERIES_LIGHT


def heatmap_colorscale_neutro() -> list:
    """Escala do mapa de calor para valores sem juízo de bom/ruim (do fundo do card ao acento)."""
    t = tokens_atuais()
    return [[0, t["card_bg"]], [1, t["accent"]]]


def heatmap_colorscale_saude() -> list:
    """Escala do mapa de calor onde baixo = crítico, médio = atenção, alto = saudável."""
    t = tokens_atuais()
    return [[0, t["critico"]], [0.5, t["atencao"]], [1, t["saudavel"]]]


def plotly_layout_atual() -> dict:
    """Layout base dos gráficos Plotly (fundo transparente, fonte, cores, margens, hover)."""
    t = tokens_atuais()
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_secondary"], family=TIPOGRAFIA["familia"], size=12),
        colorway=cores_grafico_atuais(),
        legend=dict(font=dict(color=t["text_secondary"]), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=36, b=10),
        hoverlabel=dict(bgcolor=t["card_bg"], font=dict(color=t["text_primary"]), bordercolor=t["divider"]),
        title=dict(font=dict(color=t["text_primary"], size=14), x=0.0),
    )


def aplicar_tema_figura(fig, height: int | None = None):
    """Aplica o layout, grades e eixos do tema a uma figura e, opcionalmente, a altura."""
    t = tokens_atuais()
    fig.update_layout(**plotly_layout_atual())
    fig.update_xaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], linecolor=t["divider"],
                     tickfont=dict(color=t["text_secondary"]), title_font=dict(color=t["text_secondary"]))
    fig.update_yaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], linecolor=t["divider"],
                     tickfont=dict(color=t["text_secondary"]), title_font=dict(color=t["text_secondary"]))
    if height:
        fig.update_layout(height=height)
    return fig


def render_plotly(fig, key: str, height: int | None = None, mostrar_barra: bool = False):
    """Ponto ÚNICO de renderização de gráficos: aplica o tema atual e exibe."""
    aplicar_tema_figura(fig, height)
    st.plotly_chart(fig, key=key, width="stretch",
                    config={"displayModeBar": mostrar_barra, "displaylogo": False})


def gerar_css(t: dict) -> str:
    """Gera o CSS da aplicação a partir dos tokens. As classes `ux-*` são usadas pelos componentes.
    Seções do CSS: sidebar (navegação), tipografia, cards, campos de entrada.
    """
    # Raios de borda: normal e pequeno.
    r, rp = ESPACAMENTO["raio"], ESPACAMENTO["raio_pequeno"]
    return f"""
<style>
html, body, [class*="css"], .stApp {{ font-family: {TIPOGRAFIA['familia']}; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{
  background-color: {t['content_bg']} !important; color: {t['text_primary']} !important; }}
[data-testid="stHeader"] {{ background-color: {t['content_bg']} !important; }}
[data-testid="stMainBlockContainer"] {{ padding-left: {ESPACAMENTO['pad_conteudo']}; padding-right: {ESPACAMENTO['pad_conteudo']}; padding-top: 2.2rem; max-width: 1500px; }}
/* ---- sidebar: área de NAVEGAÇÃO ---- */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child, [data-testid="stSidebarContent"] {{
  background-color: {t['sidebar_bg']} !important; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {t['divider']} !important; }}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] label p {{ color: {t['text_secondary']}; }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{ border-radius: {rp}; border-left: 3px solid transparent; }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {{ background-color: {t['hover_bg']} !important; }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
  background-color: {t['active_bg']} !important; border-left: 3px solid {t['accent']}; }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] span {{ color: {t['text_primary']} !important; font-weight: 600; }}
[data-testid="stSidebar"] a:focus-visible, button:focus-visible {{ outline: 2px solid {t['accent']} !important; outline-offset: 1px; }}
.ux-side-sec {{ font-size: {TIPOGRAFIA['pequeno']}; letter-spacing: .08em; text-transform: uppercase; color: {t['text_muted']} !important;
  margin: .6rem 0 .3rem 0; padding-top: .6rem; border-top: 1px solid {t['divider']}; }}
.ux-brand {{ font-size: 1.5rem; font-weight: 800; color: {t['accent']} !important; line-height: 1; }}
.ux-brand-sub {{ font-size: {TIPOGRAFIA['pequeno']}; color: {t['text_secondary']} !important; margin-top: .25rem; }}
/* ---- tipografia ---- */
h1, h2, h3, h4 {{ color: {t['text_primary']} !important; }}
p, li, span, label, [data-testid="stMarkdownContainer"] {{ color: {t['text_secondary']}; }}
.ux-title {{ font-size: {TIPOGRAFIA['h1']}; font-weight: 700; color: {t['text_primary']}; margin: 0; }}
.ux-kicker {{ font-size: {TIPOGRAFIA['pequeno']}; color: {t['text_muted']}; margin: 0 0 .15rem 0; }}
.ux-desc {{ color: {t['text_secondary']}; margin: .2rem 0 .6rem 0; }}
.ux-selo {{ display:inline-block; font-size: .72rem; font-weight:600; padding: .1rem .5rem; border-radius: 999px;
  border: 1px solid {t['atencao']}; color: {t['atencao']}; margin-right: .4rem; }}
.ux-h2 {{ font-size: {TIPOGRAFIA['h2']}; font-weight: 600; color: {t['text_primary']}; margin: 1.1rem 0 .3rem 0; }}
.ux-muted {{ color: {t['text_muted']}; font-size: {TIPOGRAFIA['pequeno']}; }}
/* ---- cards e containers ---- */
[data-testid="stVerticalBlockBorderWrapper"] {{ background-color: {t['card_bg']} !important; border: 1px solid {t['divider']} !important;
  border-radius: {r} !important; box-shadow: {t['sombra']}; }}
.ux-kpi-t {{ font-size: {TIPOGRAFIA['pequeno']}; color: {t['text_muted']}; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }}
.ux-kpi-v {{ font-size: 1.9rem; font-weight: 700; color: {t['text_primary']}; line-height: 1.15; }}
.ux-kpi-d {{ font-size: .85rem; font-weight: 600; }}
.ux-kpi-n {{ font-size: .75rem; color: {t['text_muted']}; }}
.ux-estado {{ font-size: .78rem; font-weight: 600; }}
/* ---- inputs ---- */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-testid="stDateInput"] input, textarea {{
  background-color: {t['input_bg']} !important; color: {t['text_primary']} !important; border-color: {t['divider']} !important; }}
[data-baseweb="select"] span, [data-baseweb="input"] input {{ color: {t['text_primary']} !important; }}
[data-baseweb="tag"] {{ background-color: {t['active_bg']} !important; }}
[data-baseweb="tag"] span {{ color: {t['text_primary']} !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background-color: {t['card_bg']} !important; }}
[data-baseweb="popover"] li {{ color: {t['text_primary']} !important; }}
.stButton > button {{ background-color: {t['card_bg']}; color: {t['text_primary']}; border: 1px solid {t['divider']}; border-radius: {rp}; }}
.stButton > button:hover {{ border-color: {t['accent']}; color: {t['accent']}; background-color: {t['hover_bg']}; }}
[data-testid="stDataFrame"] {{ border: 1px solid {t['divider']}; border-radius: {rp}; }}
hr {{ border-color: {t['divider']} !important; }}
</style>
"""


def aplicar_estilo_global() -> None:
    """Injeta o CSS do tema ativo na página (chamado no início de cada página)."""
    st.markdown(gerar_css(tokens_atuais()), unsafe_allow_html=True)
