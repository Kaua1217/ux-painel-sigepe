# Arquitetura

```
data (loaders, schemas) → indicators (funções puras, sem Streamlit) → regras (config/settings.py) → app (páginas + componentes)
```
Dependência em **um sentido**: `indicators/` não importa Streamlit; `app/` não calcula indicadores, apenas chama `indicators/`.

| Pasta | Responsabilidade |
|---|---|
| `config/settings.py` | Metas, pesos, limiares, listas de sistemas, identidade (centralizado) |
| `config/theme.py` | Design system claro/escuro, CSS global, tema Plotly, `render_plotly` |
| `data/loaders/mock_loader.py` | Geração sintética; interface `carregar_dados()` |
| `data/schemas/schema_definitions.py` | Contrato de colunas/tipos e `validar_schema` |
| `data/official/` | Reservado a bases oficiais (**ignorado pelo git**) |
| `indicators/` | uso, satisfação, jornadas, suporte, estabilidade, iss, alertas |
| `app/state.py` | Filtros globais (`session_state`), drill-down (`ir_para`), `preparar_pagina` |
| `app/components/` | kpi_card, sparkline, heatmap, ranking, funnel, timeline, alert_list, linhas, page_header |
| `app/pages/` | 7 páginas; roteadas por `st.navigation` em `app/main.py` |

## Fonte de dados
`PULSO_FONTE=oficial` seleciona `data/loaders/official_loader.py` (ver `docs/mapeamento_fontes_oficiais.md`); sem a variável, usa o gerador sintético.
Tabelas sem fonte ficam vazias e as páginas exibem "INFORMAÇÃO NÃO DISPONIBILIZADA".

## Trocar dados sintéticos por oficiais (passo a passo genérico)
1. Criar `data/loaders/official_loader.py` com `carregar_dados()` devolvendo as mesmas tabelas/colunas do schema (`validar_todos` deve retornar `[]`).
2. Trocar o import em `app/state.py` (`from data.loaders.mock_loader import carregar_dados`).
3. Colunas sem fonte oficial: preencher com NaN e registrar "INFORMAÇÃO NÃO DISPONIBILIZADA".

## Trocar indicador provisório por oficial
Alterar a função em `indicators/<dimensão>.py` e as metas/pesos em `config/settings.py`; páginas e componentes não mudam.

## Filtros e drill-down
Estado canônico em `st.session_state` (`pulso_*`); widgets espelham via `on_change`. `ir_para(pagina, sistema, jornada)` grava o foco e chama `st.switch_page`. "Limpar foco" na sidebar.

## Tema
Paleta do **Padrão Digital de Governo v3.7.0** (gov.br/ds): tokens em `config/theme.py` (`DS`). O DS 3.7.0 só define tema claro; o escuro é derivação não oficial. Contraste WCAG ≥ 4,5:1 verificado em `tests/test_theme.py`.
Detecção por `st.context.theme.type` (System/Light/Dark). Sidebar e conteúdo têm fundos distintos nos dois temas (tokens `sidebar_bg` × `content_bg`), divisória fina e item ativo destacado. Estados nunca dependem só de cor (símbolos ● ▲ ✖ e texto).
