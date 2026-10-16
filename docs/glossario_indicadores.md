# Glossário de indicadores — **INDICADOR PROVISÓRIO / CONCEITUAL**

> Nenhum indicador abaixo faz parte do Plano de Mensuração oficial. São propostas conceituais calculadas sobre
> **dados sintéticos** até a minuta oficial e as bases serem disponibilizadas. Itens sem definição: **INFORMAÇÃO NÃO DISPONIBILIZADA**.
> "Fonte esperada" alinha-se às fontes citadas na pauta de 19/09/2026 (a confirmar).

| ID | Indicador | Objetivo | Fórmula conceitual | Unidade / periodicidade | Interpretação | Fonte esperada (a confirmar) | Visualização |
|---|---|---|---|---|---|---|---|
| IND-01 | Índice de Saúde do Sistema (ISS) | Síntese executiva | 0,30·média(adoção, conclusão) + 0,40·CSAT + 0,30·média(disponibilidade, suporte), cada um normalizado 0–100 | índice 0–100 / semanal | ≥80 saudável · ≥60 atenção · <60 crítico | Derivado dos demais | KPI + matriz + linhas |
| IND-02 | Usuários Ativos | Escala de uso | Σ usuários ativos ÷ nº de dias | usuários/dia / diária | Queda sustentada indica abandono | Google/Serpro Analytics; logs de eventos | KPI + linhas |
| IND-03 | Taxa de Adoção | Uso relativo ao público | Σ usuários ativos ÷ Σ elegíveis × 100 | % / semanal | Abaixo da meta (60%) indica baixa adesão | Analytics + cadastro de elegíveis (**INFORMAÇÃO NÃO DISPONIBILIZADA**) | Heatmap sistema×órgão |
| IND-04 | Índice de Satisfação (CSAT) | Percepção | satisfeitos ÷ respostas × 100 | % / semanal | Meta provisória 75% | Pesquisa de satisfação; avaliações em lojas | Linhas + heatmap + box |
| IND-05 | Índice de Esforço (CES) | Fricção | média ponderada (1–7) | nota / semanal | Maior = mais fácil | Pesquisa de satisfação / interna | KPI |
| IND-06 | Taxa de Conclusão | Eficácia da jornada | concluídas ÷ iniciadas × 100 | % / semanal | Meta provisória 75% | Logs de eventos / Analytics | Ranking + funil |
| IND-07 | Tempo de Conclusão | Eficiência | média ponderada por concluídas | minutos / semanal | Alta = fricção | Logs de eventos | KPI |
| IND-08 | Volume de Suporte | Demanda | chamados ÷ usuários-dia ativos × 1000 | chamados/1.000 / semanal | Sintoma de usabilidade/instabilidade | Central SIPEC | Linhas + heatmap |
| IND-09 | Tempo Médio de Resolução (TMR) | Eficiência do atendimento | média ponderada por chamados | horas / semanal | Meta provisória 48 h | Central SIPEC | Ranking vs meta |
| IND-10 | Disponibilidade | Condição básica | média de uptime diário | % / diária | Meta provisória 99,5% | Monitoramento Serpro (**INFORMAÇÃO NÃO DISPONIBILIZADA**) | Linhas + heatmap mensal |
| IND-11 | Incidentes por Severidade | Contexto de quedas | contagem por severidade; duração média | un. / evento | Prioriza ação | Registro de incidentes | Linha do tempo |
| IND-12 | Score de Severidade | Priorizar alertas | peso_nível × (\|variação\|/10 + 1) × (1 + usuários/5000) | pontos / por comparação | Ordena a lista de alertas | Derivado | Lista de alertas |

**Complementares:** primeira resposta (h), reincidência (%), tempo de resposta (ms), taxa de erro (%).
**Lacunas frente à pauta (INFORMAÇÃO NÃO DISPONIBILIZADA):** dispositivos/origem de acesso, SUS, confiança/clareza, percepção espontânea (lojas de aplicativos), funcionalidades críticas, tempo de recuperação oficial, indicador de acessibilidade.
