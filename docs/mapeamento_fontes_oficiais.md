# Mapeamento das fontes oficiais → painel

Base: "ESCUTA UX — Plano Geral de Mensuração dos Sistemas Estruturantes de Gestão de Pessoas do SIPEC" (COPEX/CGDIP/DESIN/SGP/MGI)
e amostras de planilhas (cabeçalho + exemplo). O loader (`data/loaders/official_loader.py`) lê tudo **localmente**.

**Ativar:** `$env:PULSO_FONTE="oficial"` (PowerShell) → `python -m streamlit run app/main.py`. Planilhas em `data/official/` (ignorada pelo Git) ou `PULSO_DADOS_OFICIAIS`.

| Fonte (arquivo) | Colunas usadas | Tabela / indicador | Regra provisória |
|---|---|---|---|
| Avaliações internas (`AvaliacoesInternas*.xlsx`) | Sistema, Data, Nota, Vínculo, Órgão | `satisfacao` → CSAT (IND-04) | satisfeito = nota ≥ 4 (escala 1–5); Vínculo SER/PEN → Servidor/Pensionista; Órgão → top 8 + "Demais órgãos" |
| Central SIPEC (`CentraSIPEC*.xlsx`) | Categoria, Organização, Data de abertura, Data de início de atendimento, Tempo em horas do atendimento, Chamados Relacionados | `suporte` → IND-08, IND-09, 1ª resposta, reincidência | sistema = texto antes de " - " na Categoria; perfil = "Não informado"; reincidência = chamado com "Chamados Relacionados" preenchido; unidade de "Tempo em horas" a confirmar |
| Logs (`AFD`, `AFASTAMENTO`, `REQUERIMENTO`, `ACOES_JUDICIAIS`…, cabeçalho com `ID_ERRO`) | NO_MODULO, IN_CLASSIFICACAO, DT_EVENTO | `erros_log` → "Erros registrados em log" (Estabilidade) | contagem por dia × módulo × classificação; significado de IN_CLASSIFICACAO a confirmar |
| Pesquisa SIGEPE (`PesquisaSigepe*.xlsx`) | — | **não integrada** | qualitativa; instrumento/escala por definir (plano 8.1/8.2 propõe Likert 1–5 → 0–100) |
| Analytics (uso, jornadas) | — | `uso`, `jornada_*` vazias | INFORMAÇÃO NÃO DISPONIBILIZADA |
| Monitoramento técnico | — | `disponibilidade`, `desempenho`, `incidentes` vazias | INFORMAÇÃO NÃO DISPONIBILIZADA |

## Privacidade (aplicado no código)
Nunca são lidos: comentários, título/descrição/ações de chamado, valores anterior/atual, stacktrace, IPs. Nada individual é exibido; tudo é agregado.

## Limitações conhecidas
- Órgão nas avaliações é **código**; na Central é **nome**: sem chave de conciliação, os filtros de órgão não cruzam as duas fontes.
- Central não informa perfil: ao filtrar por perfil, o suporte some do recorte.
- Sem Analytics: ISS fica "INFORMAÇÃO NÃO DISPONIBILIZADA" (exige uso, jornadas e disponibilidade); chamados são exibidos em volume absoluto.
- Indicadores 8.1/8.2 do plano (escore 0–100 por dimensões) dependem do questionário padronizado; ainda não há dados no formato.


## Lista de incidentes (MGI-SGP) → `incidentes`
- Identificação: nome contém "incidente" ou cabeçalho com TICKETID + DATAFIMOCORRENCIA.
- Colunas lidas: TICKETID, SERPRODATAINICIO, DATAFIMOCORRENCIA. O RESUMO (texto livre) nunca é lido.
- Duração (h) = DATAFIMOCORRENCIA − SERPRODATAINICIO; linhas em branco ou com duração negativa são descartadas.
- Severidade PROVISÓRIA por duração (≥6 h Crítica, ≥3 h Média, demais Baixa) — a organização não informou classificação.
- Sistema permanece "SIGEPE" (módulo/produto não vira Sistema). Incidentes não medem disponibilidade: uptime segue INFORMAÇÃO NÃO DISPONIBILIZADA.
- A confirmar: significado de PTEMPOREACAOVIEWALN (não usado).
