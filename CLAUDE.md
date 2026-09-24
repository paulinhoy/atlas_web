# Atlas Web — orientações para agentes

Aplicação Streamlit que exibe os resultados do estudo do PELTMG (carteira priorizada de empreendimentos e ficha de cada um). Dados estáticos vindos de CSV; objetivo é simplicidade e manutenção quase zero.

## Leia antes de trabalhar
- `docs/arquitetura.md` — **leitura obrigatória**: fluxo dos dados, estrutura, regras de negócio, branches e fluxo de desenvolvimento.
- `docs/frontend.md` — antes de mexer em telas, CSS, tabelas, mapa ou navegação.
- `docs/erros_solucoes.md` — consulte ao encontrar comportamento estranho do Streamlit/pandas.

## Como colaborar com o responsável
- Responda em **português**.
- O responsável é cientista de dados (conhece Python), mas **não trabalha com HTML/CSS**: explique essa parte em linguagem simples, com exemplos curtos de código.
- Para mudanças não triviais, **apresente o problema com um exemplo prático e um plano, e espere aprovação** antes de alterar código.
- **Commit e push somente com aprovação explícita.** Trabalhe em branch própria (`feat/`, `fix/`, `refactor/`, `docs/`) criada a partir da `main`.

## Regras fixas
- Use sempre o `.venv` (`.venv/Scripts/python.exe`): Streamlit **1.36.0** é versão fixa. O Python global da máquina tem outra versão e não tem as dependências.
- Servidores (produção e staging publicados) **estão fora do alcance dos agentes**: tudo roda localmente; publicar é tarefa do responsável.
- `data/` não vai para o Git. Rodar o ETL (`scripts/process_data.py`) **sobrescreve** `data/processed/`: faça cópia antes se for comparar resultados.
- Nada de CSS no Python: estilos em `assets/css/`, links internos via `views/estado_url.py` (detalhes em `docs/frontend.md`).
- Lógica do chatbot (`services/chatbot_service.py`, `services/chat_logger.py`) está em desenvolvimento: só altere com pedido explícito.
- Vários arquivos usam fim de linha CRLF; preserve-o ao editar por script.

## Ao terminar uma tarefa
- Valide com o teste automático de telas (`docs/frontend.md`, seção 7.1) e, se a mudança for visual, peça conferência no navegador.
- **Registre em `docs/erros_solucoes.md`** qualquer erro difícil ou comportamento inesperado que encontrou e como resolveu.
- Se mudou regra de negócio, tabela de dados, rota ou fluxo, atualize `docs/arquitetura.md`; se mudou UI, `docs/frontend.md`.
