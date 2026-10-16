# UX — Plano de Mensuração e Painel de Indicadores - UX (SIGEPE)

Painel analítico (Streamlit + Pandas + NumPy + Plotly) para a **Chamada de Desafio nº 02/2026**.

> ⚠️ **Dados sintéticos e indicadores PROVISÓRIOS / CONCEITUAIS.** Nada aqui é oficial nem representa dados reais.
> Não insira dados pessoais/sensíveis ou bases da organização em ferramentas de IA sem autorização expressa (ver `docs/requisitos_edital.md`).

## Executar
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app/main.py
```
Python 3.11+. Testes: `python -m pytest -q`.

## Publicar online (Streamlit Community Cloud)

1. Entre em https://share.streamlit.io com a conta do GitHub e clique em **New app**.
2. Escolha este repositório, o branch `main` e o arquivo principal `app/main.py`.
3. Clique em **Deploy**. O app usa **somente dados sintéticos** (padrão); nunca configure `PULSO_FONTE=oficial` na nuvem nem suba dados oficiais.

## Páginas
Visão Geral · Uso dos Sistemas · Experiência e Satisfação · Jornadas Digitais · Suporte e Atendimento · Estabilidade · Alertas e Oportunidades.
Filtros globais (período, sistema, órgão, perfil), drill-down entre páginas, alertas com limiares configuráveis em `config/settings.py`, temas claro/escuro/sistema.

## Usar os dados oficiais (local)
Copie as planilhas para `data/official/` e rode:
```powershell
$env:PULSO_FONTE="oficial"
python -m streamlit run app/main.py
```
Veja `docs/mapeamento_fontes_oficiais.md` (o que é lido, o que é descartado e as limitações).

## Documentação
- `docs/mapeamento_fontes_oficiais.md` — fontes oficiais → tabelas do painel
- `docs/arquitetura.md` — camadas e como trocar dados/indicadores
- `docs/metodologia.md` — metodologia preliminar
- `docs/glossario_indicadores.md` — IND-01 … IND-12
- `docs/requisitos_edital.md` — rastreabilidade com o resumo do edital

## Privacidade
`data/official/` está no `.gitignore`. Os dados sintéticos não contêm informação pessoal; é vedada qualquer tentativa de reidentificação.


## Código comentado
Todos os arquivos `.py` possuem docstrings (o que cada função faz) e comentários (por que e como), em português. Comece por `config/settings.py` (parâmetros), `indicators/` (cálculos) e `app/pages/` (telas).
