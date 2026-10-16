# Metodologia (preliminar) — Plano de Mensuração e Painel de Indicadores - UX (SIGEPE)

**Status:** versão preliminar para a entrega intermediária. Dados **sintéticos**; indicadores **PROVISÓRIOS / CONCEITUAIS**.

## 1. Pergunta orientadora
"O que está acontecendo com os sistemas, onde estão os principais problemas e quais pontos precisam de atenção?"
Público: gestores e tomadores de decisão (não profissionais de TI).

## 2. Dimensões
Uso e acesso · Eficiência da jornada · Satisfação e experiência · Demandas de suporte · Performance e confiabilidade
(alinhadas à pauta de 19/09/2026). Percepção espontânea: **INFORMAÇÃO NÃO DISPONIBILIZADA**.

## 3. Dados sintéticos
Gerados por `data/loaders/mock_loader.py` com `numpy.random.default_rng(42)` (determinístico). 569 dias (01/02/2025–23/08/2026),
5 sistemas fictícios, 6 órgãos, 3 perfis, 10 jornadas. Anomalias intencionais: degradação do Sistema Beta nas últimas ~9 semanas;
baixa adoção do Delta no Órgão Regional Oeste; sazonalidade do Alfa em mar/abr; incidente crítico (14 h) do Épsilon.
Os dados **não representam** nenhum sistema real; não há dados pessoais. Nenhuma tentativa de reidentificação é admitida.

## 4. Normalização e ISS
Faixas (config/settings.py → NORMALIZACAO): adoção 0–90%, CSAT 40–95%, conclusão 50–95%, disponibilidade 95–100%, TMR invertido 0–144 h.
`ISS = 0,30·Uso&Jornada + 0,40·Satisfação + 0,30·Estabilidade&Suporte`. ISS geral = média dos sistemas ponderada por usuários ativos.
Faixas: ≥80 saudável, ≥60 atenção, <60 crítico. **Pesos e faixas são hipóteses a validar com a minuta oficial.**

## 5. Alertas
Compara a 2ª metade com a 1ª do período selecionado. Limiares (atenção/crítico) em `LIMIARES_ALERTA`. Score de severidade (IND-12) ordena a lista.
Oportunidades: matriz Impacto (0–10, derivado do score) × Esforço (1–5, estimado por dimensão — **não** é levantamento real).

## 6. Comparação entre períodos
Variação vs. janela imediatamente anterior de mesmo tamanho (pp para percentuais, % relativa para volumes/tempos).

## 7. Limitações
Estabilidade não filtra por órgão/perfil; funil é conceitual; metas são provisórias; correlação suporte×satisfação não implica causalidade.

## 8. Migração para dados oficiais
Ver `docs/arquitetura.md`. Itens definidos pela organização substituem os provisórios; o que não for definido permanece "INFORMAÇÃO NÃO DISPONIBILIZADA".
