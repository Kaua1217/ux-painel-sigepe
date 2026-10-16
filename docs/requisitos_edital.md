# Rastreabilidade dos Requisitos do Edital — Chamada de Desafio nº 02/2026

**Fonte:** resumo `04_Requisitos_Edital_SIGEPE_EquipeUX_UDF_10out26_Kadidja.pdf`
(elaborado em 10/10/2026), que cita o `EDITAL SIGEPE 2.pdf`.
Este documento se baseia no **resumo**, não no texto integral do edital:
os números de itens citados são os que o resumo informa e devem ser
conferidos no original.

**Minuta do Plano de Mensuração e bases de dados:** INFORMAÇÃO NÃO
DISPONIBILIZADA (segundo o resumo, serão liberadas após a confirmação da
inscrição). Todos os indicadores e dados do projeto seguem
**PROVISÓRIOS / CONCEITUAIS** e **SINTÉTICOS**.

---

## 1. Matriz requisito → atendimento

| Requisito (itens 4.1–4.4, 5, 6, 9) | Onde está no projeto | Status | Pendência |
|---|---|---|---|
| Problema e público-alvo | Especificação conceitual (seções 3 e 5), entregue fora do repositório | Parcial | Incorporar a `docs/` |
| Pelo menos 3 indicadores, com justificativa | 12 indicadores em `docs/glossario_indicadores.md`; justificativas na seção 3 abaixo | Atendido (provisório) | Revisar com a minuta |
| Metodologia de cálculo | `docs/glossario_indicadores.md`, `docs/metodologia.md`, `indicators/` | Atendido (provisório) | Recalibrar com dados oficiais |
| Organização visual (filtros, cortes, detalhamento) | Filtros globais, 7 páginas, drill-down (`app/state.py`) | Atendido | — |
| Fontes de dados por indicador | Campo "fonte esperada" do glossário | Pendente | INFORMAÇÃO NÃO DISPONIBILIZADA |
| Interpretação (alertas, comparações, priorização) | `config/settings.py`, `indicators/alertas.py`, página 7, `docs/metodologia.md` §4 | Atendido (limiares provisórios) | Calibrar limiares |
| Protótipo (estático ou navegável) | Aplicação Streamlit | Atendido | Definir como o avaliador acessa |
| Relatório técnico (até 30 páginas, estrutura do item 5.3) | Mapa na seção 4 abaixo | Não iniciado | Aguarda minuta e dados |

## 2. Checklist da entrega intermediária (14/10/2026)

Exigido: esboço do painel + versão preliminar da metodologia dos indicadores.

- [ ] Capturas de tela das 7 páginas (ou vídeo curto), com selo "DADOS SINTÉTICOS" visível.
- [ ] `docs/metodologia.md` + `docs/glossario_indicadores.md` + este documento.
- [ ] Deixar explícito em tudo: dados sintéticos, indicadores provisórios.
- [ ] Confirmar com a organização o formato e o canal de envio (não consta no resumo).

## 3. Justificativa provisória da seleção dos indicadores

| Código | Indicador | Por que foi selecionado |
|---|---|---|
| IND-01 | Índice de Saúde do Sistema | Síntese para leitura executiva; permite ordenar sistemas por atenção |
| IND-02 | Usuários Ativos | Mede a escala real de uso |
| IND-03 | Taxa de Adoção | Normaliza o uso pelo público elegível, revelando órgãos/perfis com baixa adesão |
| IND-04 | Índice de Satisfação | Captura a percepção do usuário, que métricas técnicas não mostram |
| IND-05 | Índice de Esforço | Aponta fricção em jornadas mesmo quando há conclusão |
| IND-06 | Taxa de Conclusão | Mostra se o usuário consegue realizar a tarefa |
| IND-07 | Tempo de Conclusão | Eficiência da jornada; exibido com distribuição, não só média |
| IND-08 | Volume de Suporte | Demanda reprimida e sintoma de problemas de usabilidade |
| IND-09 | Tempo Médio de Resolução | Eficiência do atendimento frente a uma meta |
| IND-10 | Disponibilidade | Condição básica para qualquer experiência |
| IND-11 | Incidentes por Severidade | Contextualiza quedas de disponibilidade e prioriza ação |
| IND-12 | Score de Severidade | Prioriza alertas por magnitude e usuários afetados |

Justificativas provisórias, a revisar quando a minuta definir os indicadores oficiais.

## 4. Mapa do relatório técnico (estrutura preferencial, item 5.3 do resumo)

| Seção do relatório | Insumo no projeto |
|---|---|
| 1. Capa e identificação da equipe | INFORMAÇÃO NÃO DISPONIBILIZADA (dados da equipe) |
| 2. Contextualização e objetivos | Especificação conceitual; `docs/metodologia.md` §1–2 |
| 3. Dados utilizados e tratamentos | `README.md` §5 (sintéticos); dados oficiais pendentes |
| 4. Metodologia de cálculo | `docs/glossario_indicadores.md`, `docs/metodologia.md` |
| 5. Arquitetura da informação e proposta visual | `docs/arquitetura.md`, `config/theme.py` |
| 6. Protótipo, capturas ou link | Aplicação + capturas a produzir |
| 7. Limitações, riscos e cuidados com os dados | `README.md` §8–9, `docs/metodologia.md` §7, seção 5 abaixo |
| 8. Considerações finais e referências | Pendente |

## 5. Proteção de dados e uso de IA (itens 8 e 13 do resumo)

- Os dados e documentos fornecidos pela organização só podem ser usados para
  as finalidades do desafio e não podem ser compartilhados com terceiros sem
  autorização expressa.
- Não inserir dados pessoais, sensíveis ou classificados em ferramentas de IA.
- **Antes de enviar a minuta ou qualquer base a um assistente de IA**,
  confirmar com a organização (copex@gestao.gov.br) o que é permitido.
  Alternativas: compartilhar apenas dicionário de dados (nomes de colunas,
  tipos, granularidade), sem registros, ou usar amostras sintéticas que
  espelhem a estrutura.
- Não tentar reidentificar indivíduos, nem a partir de dados agregados ou sintéticos.
- Não versionar dados oficiais: adicionar `data/official/` ao `.gitignore`.
- Garantir originalidade e respeitar direitos autorais.

## 6. A confirmar no edital integral

- Numeração exata dos itens citados.
- Formato e canal de envio da entrega intermediária.
- Se o protótipo precisa ser acessível por link.
- Eventual parametrização dos critérios de avaliação (o resumo informa que não há pesos).
