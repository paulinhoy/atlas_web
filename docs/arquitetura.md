# Arquitetura e Fluxo de Desenvolvimento — Atlas Web (PELTMG / CODEMGE)

Documento de entrada do projeto. Leia antes de qualquer alteração. Ele descreve **como o sistema funciona hoje**, as **regras de negócio** que a interface deve respeitar e **como trabalhar** no repositório.

| Documento | Quando ler |
|---|---|
| `docs/arquitetura.md` (este) | Sempre, primeiro |
| `docs/frontend.md` | Antes de mexer em telas, CSS, tabelas, mapa ou navegação |
| `docs/erros_solucoes.md` | Ao encontrar comportamento estranho do Streamlit/pandas — e para registrar erros novos |
| `docs/chatbot_assistente_virtual.md`, `docs/seguranca_chatbot.md` | Antes de mexer na lógica do chatbot (em desenvolvimento) |
| `docs/queries_extracao.sql` | Ao extrair, atualizar ou incluir dados — contém todas as consultas ao banco |

---

## 1. Contexto do produto

- **O que é:** versão web (Python + Streamlit) do Atlas de Empreendimentos do **Plano Estadual de Logística e Transportes de Minas Gerais (PELTMG / CODEMGE)**, que antes era gerado no QGIS. Mostra a carteira priorizada de empreendimentos e uma ficha técnica por empreendimento.
- **Natureza dos dados:** estáticos. Vêm de CSVs exportados do banco PostGIS e são atualizados **no máximo uma vez por ano**.
- **Uso:** poucos usuários simultâneos.
- **Objetivo de engenharia:** **manutenção praticamente zero** e **modularidade** — adicionar uma página ou um conjunto de dados deve ser simples. Prefira sempre a solução mais simples e centralizada; nada de infraestrutura extra (banco, API, filas).
- **Estágio:** o projeto ainda **não está na forma final de publicação**. Tabelas, colunas e regras de negócio descritas aqui refletem o estado atual e podem mudar.
- **Responsável pelo projeto:** cientista de dados, conhece Python (por isso a escolha do Streamlit), mas **não trabalha com HTML/CSS**. Em Python e dados a conversa pode ser técnica; em HTML/CSS, explique em português simples e com exemplos curtos. **Apresente um plano com exemplo prático antes de alterar código** quando a mudança não for trivial.

---

## 2. Visão geral do fluxo

```
PostGIS (banco do estudo)
   │  docs/queries_extracao.sql  (todas as consultas de extração; exportação manual)
   ▼
data/raw/*.csv, *.json                      ← entrada bruta (fora do Git)
   │  scripts/process_data.py  (CSV → Parquet)
   │  scripts/process_geo.py   (JSON de geometrias → Parquet)
   ▼
data/processed/*.parquet                    ← dados prontos para o app (fora do Git)
   │  services/data_loader.py  (leitura com cache + regras de precedência)
   ▼
app.py  (roteia pela URL)
   ├── views/home.py     Home: KPIs, filtros, tabela da carteira
   ├── views/atlas.py    Ficha do empreendimento (+ services/map_service.py)
   ├── views/chatbot.py  Assistente virtual (lógica em services/chatbot_service.py)
   └── views/bi.py       Painel de Indicadores & BI (provisório: "em construção")
```

O app **nunca acessa o banco**: tudo é lido dos arquivos `.parquet`.

---

## 3. Estrutura de pastas

```
atlas_web/
├── app.py                  Roteador: ?page=chatbot → chatbot | ?page=bi → BI | ?id=N → ficha | vazio → Home
├── requirements.txt        Dependências (streamlit==1.36.0 fixo)
├── .streamlit/config.toml  Servidor (porta, XSRF/CORS, telemetria) e tema claro institucional
├── views/
│   ├── home.py             Home
│   ├── atlas.py            Ficha do empreendimento
│   ├── chatbot.py          Tela do assistente virtual
│   ├── bi.py               Painel de Indicadores & BI (provisório)
│   ├── ui.py               Carregador de CSS e componentes comuns (barra de navegação, botão Voltar)
│   └── estado_url.py       Filtros/paginação/colunas da Home guardados na URL
├── services/
│   ├── data_loader.py      Leitura dos parquets, cache e regras de precedência
│   ├── formatters.py       Formatação brasileira (R$, %, milhar, datas)
│   ├── map_service.py      Mapa Folium da ficha
│   ├── chatbot_service.py  Lógica do chatbot (LangChain) — em desenvolvimento
│   └── chat_logger.py      Log das conversas do chatbot
├── assets/css/             Todo o CSS (base.css + um arquivo por tela) — ver frontend.md
├── scripts/
│   ├── process_data.py     ETL dos CSVs
│   └── process_geo.py      ETL das geometrias
├── data/raw/, data/processed/   Dados (ignorados pelo Git)
├── logos/                  Logos institucionais (hoje não exibidos em nenhuma tela)
└── docs/                   Documentação
```

---

## 4. Dados

### 4.1 Arquivos de entrada e saída

> **Estado atual — sujeito a mudança.** A referência oficial do que é extraído do banco é `docs/queries_extracao.sql`, onde ficam **todas** as consultas. Ao adicionar ou alterar uma tabela, atualize o `TARGET_FILES` em `scripts/process_data.py`, a tabela abaixo e, se a regra de exibição mudar, a seção 5.

O ETL escolhe, para cada destino, o arquivo de `data/raw/` cujo nome começa com o **primeiro prefixo da lista que existir**; se houver vários, usa o **último em ordem alfabética** (os nomes exportados terminam com data/hora, então é o mais recente). Arquivos antigos podem continuar na pasta.

| Prefixo(s) em `data/raw/` | Parquet gerado | Chaves | Conteúdo |
|---|---|---|---|
| `priorizacao`, `mvw_8_calcula_impacto` | `empreendimentos_priorizacao` | `id_empreendimento`, `fonte_priorizacao` | Tabela mestra: metadados e notas de priorização nas 3 carteiras |
| `vw_empreendimento_custo_economico_lp` | `dados_financeiro` | `id_empreendimento` | Custo Econômico LP: CAPEX, OPEX, receita, mês base |
| `resumo_financeiro` | `resumo_financeiro` | `id_empreendimento`, `id_cenario` | Resumo financeiro por cenário (o app usa 7 e 10): CAPEX, OPEX, receita e TIRM CODEMGE |
| `alocacao_total`, `tbl_alocacaoempreendimento` | `alocacao_empreendimento` | `id_empreendimento`, `id_cenario` | Alocação de fluxos 2055 por cenário |
| `vw_obra` | `obras_priorizacao` | `id_obra`, `id_empreendimento` | Obras de cada empreendimento (+ `valor_calculado`) |
| `vw_custo_economico` | `custo_obra` | `id_obra`, `id_cenario` | Custos de cada obra por cenário |
| `capacidade_satur_aero_cenarios` | `demanda_pax_aero_ano` | `id_empreendimento`, `id_cenario` | Demanda de passageiros — aeroviário |
| `demanda_duto` | `demanda_duto_ano` | `id_empreendimento` | Volume e TKU — dutoviário |
| `demanda_ferro_passageiro` | `demanda_pax_ferro_ano` | `id_empreendimento` | Demanda de passageiros — ferroviário |
| `mvw_empreendimento_geo` (JSON) | `empreendimento_geo` | `id_empreendimento` | Geometrias WKT: `geom_linha` e `geom_ponto` |

Relações: um empreendimento tem até 3 linhas na tabela mestra (uma por carteira), N obras, N custos por obra/cenário e N linhas de alocação/demanda por cenário.

### 4.2 Regras do ETL (`scripts/process_data.py`)
1. **Encoding:** os CSVs exportados são UTF-8 e são lidos como UTF-8 (`utf-8-sig`); Latin-1 só é usado se o arquivo não for UTF-8. **Não existe correção de acentuação em tempo de execução.** Se o ETL imprimir `[AVISO] ... possivel acentuacao corrompida`, o problema está na exportação — corrija na origem, não no texto.
2. **Tipo do ID:** `id_empreendimento` é gravado como inteiro que aceita vazio (`Int64`) em todas as tabelas. O app compara o ID diretamente, sem conversões.
3. **Custo das obras:** `valor_calculado` = soma dos custos da obra em cada cenário, adotando o **cenário mais caro**; se não houver custo, usa `valor_global` da obra.
4. **`resumo_financeiro`:** duplicatas de (`id_empreendimento`, `id_cenario`) são removidas.

### 4.3 Leitura e cache (`services/data_loader.py`)
- Parquets pequenos: `@st.cache_data` — cada chamada recebe uma cópia; um usuário não altera o dado de outro.
- `empreendimento_geo` (~114 MB em disco, ~255 MB em memória): `@st.cache_resource` — **um único objeto compartilhado** por todas as sessões. É **somente leitura**: nunca altere o DataFrame retornado por `get_empreendimento_geo()` (use `.copy()` se precisar).
- Buscas por empreendimento usam sempre `data_loader.filtrar_por_empreendimento(df, id)`.
- O cache não percebe arquivos novos: **reinicie o Streamlit** depois de regenerar os parquets.

---

## 5. Regras de negócio

1. **Carteiras (coluna `fonte_priorizacao`):**
   | Carteira | Valor em `fonte_priorizacao` | Empreendimentos (base atual) | Na URL |
   |---|---|---|---|
   | Recomendada (padrão da Home) | `cenario recomendado` | 1.044 | `carteira=recomendada` |
   | Otimizada | `cenario otimizado` | 1.059 | `carteira=otimizada` |
   | Completa | `priorizacao geral` | 1.682 | `carteira=completa` |

   A carteira escolhida na Home define KPIs, opções dos filtros, tabela, índice (IC) e impacto exibidos. A listagem é ordenada por `ic_3_pond` decrescente.
2. **Notas da ficha (Resultados da Priorização):** vêm da carteira **Recomendada**; se o empreendimento não estiver nela, da **Otimizada**; senão, da **Completa** (`get_empreendimento_resolvido`). Dimensões vazias são completadas pela próxima fonte. Um badge mostra a fonte usada.
3. **Dados financeiros da ficha:** CAPEX, OPEX, receita e TIRM vêm do **cenário 10 (Recomendado)** do `resumo_financeiro`; senão do **cenário 7 (Otimizado)**; senão do **Custo Econômico LP** (`dados_financeiro`) com a TIRM da priorização (`get_dados_financeiro_resolvido`). Valor Total = CAPEX + OPEX. O mês base vem sempre do Custo Econômico LP. Um badge mostra a fonte usada.
4. **Card "Investimento Total" da Home:** soma do `capex_empreendimento_atualizado` do **Custo Econômico LP** dos empreendimentos da carteira ativa, em bilhões arredondados (ex.: `R$ 460 Bi`), subtexto fixo "CAPEX".
5. **Alocação 2055 (ficha):** mostra os cenários **1 a 4, 7 (Otimizado) e 10 (Recomendado)**. A fonte e as colunas dependem do setor:
   | Setor (`id_setor`) | Condição | Fonte | Colunas |
   |---|---|---|---|
   | 1 Rodoviário | — | alocação | Carga, Ônibus, Automóvel, Total Veículos, TKU Total |
   | 2 Ferroviário | Transporte de pessoas | demanda ferro | Demanda anual de passageiros |
   | 2 Ferroviário | Cargas, grupo de modelagem 2 | alocação | Toneladas por grupo de carga + TON Total |
   | 2 Ferroviário | Cargas, grupo de modelagem 1 | alocação | TKU por grupo de carga + TKU Total |
   | 3 Hidroviário/Portuário | — | alocação | Toneladas por grupo de carga + TON Total |
   | 4 | — | — | Tabela não exibida |
   | 5 Aeroviário | — | demanda aero | Demanda de passageiros/ano |
   | 6 Dutoviário | — | demanda duto | **"Tonelada Total"** (`volume_2055`) e TKU Total |
6. **Obras:** a ficha mostra **todas** as obras do empreendimento (o QGIS limitava a 4), ordenadas pelo `valor_calculado` decrescente. Extensão total = soma de `extensao_km`; duração = menor início – maior conclusão.
7. **Formatação brasileira:** milhar com ponto (`1.682`), decimais com vírgula (`0,4031`), moeda `R$ 289.892.422,00` — sempre pelos helpers de `services/formatters.py`.
8. **Dados ausentes:** sempre exibidos como hífen `-` (nunca "N/D" ou "N/A").
9. **Tom institucional:** sem emojis em títulos, botões e tabelas; ícones em SVG simples.

---

## 6. Telas e navegação

| URL | Tela |
|---|---|
| `?` (vazio) | Home |
| `?id=1042` | Ficha do empreendimento 1042 (ID inválido → mensagem de "não encontrado") |
| `?page=chatbot` | Assistente virtual |
| `?page=bi` | Painel de Indicadores & BI (provisório, "em construção") |

- **A URL é a fonte da verdade.** Links internos são relativos (começam com `?`).
- **Barra de navegação superior** (todas as telas, `render_navbar` em `views/ui.py`): Página Inicial, Painel de Indicadores & BI e Assistente Virtual, com destaque na tela aberta (na ficha, destaca Página Inicial). Substitui a faixa nativa do Streamlit (menu ⋮), que fica escondida.
- **Estado da Home na URL:** carteira, busca, filtros, página, itens por página e colunas vão para a URL (`views/estado_url.py`), e os links da tabela, do chatbot e dos botões "Voltar" os carregam. Assim, abrir uma ficha e voltar não perde os filtros, e o link pode ser compartilhado. Detalhes e como incluir um filtro novo: `docs/frontend.md`, seção 5.9.
- **Home:** 4 KPIs, 8 controles de filtro (busca, setor, esfera, carteira, classificação, viabilidade, origem, vocação), tabela paginada com colunas configuráveis (modal de arrastar), botão flutuante do assistente.
- **Ficha:** cabeçalho, metadados + mapa (mesma altura, 520px), e as tabelas Resultados da Priorização, Dados Financeiros, Alocação 2055 e Detalhamento das Obras.
- **Mapa (`services/map_service.py`):** Folium com base OpenStreetMap (sem chave de API), traçado linear e pontos do empreendimento, enquadramento automático; aviso quando não há geometria. A legenda QGIS está preservada em `render_legenda_qgis()` (desativada).
- **Visual:** todo o CSS em `assets/css/`, com cores centralizadas — ver `docs/frontend.md`.

---

## 7. Ambiente de trabalho e branches

- **Tudo roda no computador do responsável.** Servidores (inclusive produção) **não estão ao alcance dos agentes**: não há acesso, comandos de deploy ou configuração de servidor a fazer por aqui. A publicação no servidor é feita pelo responsável.
- **Rodar localmente:** `.venv/Scripts/python.exe -m streamlit run app.py` → `http://localhost:8501`.
- **Sempre use o `.venv`**: ele tem o Streamlit **1.36.0**, versão fixa exigida pelo servidor de hospedagem. O Python global da máquina pode ter outra versão, o que quebra o mapa e muda o visual.
- Não há dependências fora do `requirements.txt`.

| Branch | Papel |
|---|---|
| `main` | Versão aprovada e estável. Só recebe o que já foi aprovado. |
| `staging` | Vitrine de testes: recebe o que precisa ser **publicado no servidor para outras pessoas avaliarem**, sem mexer na `main`. Pode ficar temporariamente à frente da `main`. |
| `feat/...`, `fix/...`, `refactor/...`, `docs/...` | Uma por tarefa, criada a partir da `main`, apagada depois de integrada. |

Links internos são relativos (começam com `?`), por isso o app funciona igual em qualquer caminho de servidor (ex.: staging publicado em `/staging`).

---

## 8. Fluxo de desenvolvimento

1. **Branch por tarefa**, criada a partir da `main`.
2. **Plano antes do código** para mudanças não triviais: explicar o problema com um exemplo prático e o plano de correção; implementar só após aprovação.
3. **Validar localmente** antes de commitar:
   - teste automático das telas (script em `docs/frontend.md`, seção 7.1) rodando com o `.venv`;
   - em refatorações que prometem "nada muda", comparar o conteúdo gerado antes/depois (foi assim que as refatorações de CSS, ETL e URL foram validadas);
   - conferência visual no navegador quando a mudança é visual.
4. **Commits e push somente com aprovação do responsável**, mensagens em português no padrão Conventional Commits (`feat(home): ...`, `fix(etl): ...`, `docs: ...`), explicando o porquê.
5. **Integração:**
   - *Precisa de aprovação de outras pessoas?* Junte a branch na `staging` e envie ao GitHub; o responsável publica no servidor. Após a aprovação, junte a mesma branch na `main`.
   - *Não precisa?* Junte direto na `main`.
   - Em ambos os casos, ao final a `staging` volta a ficar idêntica à `main` e a branch da tarefa é apagada (no GitHub e local).
6. **Registrar erros difíceis** (comportamento estranho de biblioteca, bug que pode voltar) em `docs/erros_solucoes.md`.
7. **Manter a documentação viva:** mudou uma regra de negócio, rota, tabela de dados ou fluxo → atualizar este documento; mudou algo de UI → `docs/frontend.md`.

---

## 9. Atualização dos dados

1. Exportar do PostGIS os CSVs/JSON usando as consultas de `docs/queries_extracao.sql`, em **UTF-8**.
2. Copiar os arquivos para `data/raw/` mantendo os prefixos dos nomes (seção 4.1).
3. Rodar `.venv/Scripts/python.exe scripts/process_data.py` e conferir: todos os arquivos `[LIDO]`/`[SALVO]`, **nenhum `[AVISO]`** de acentuação, contagens de linhas plausíveis.
4. Se as geometrias mudaram: `.venv/Scripts/python.exe scripts/process_geo.py`.
5. **Atualizar as contagens escritas à mão** nos nomes das carteiras em `views/home.py` (`"Carteira Recomendada (1.044)"` etc.) e na tabela da seção 5 deste documento.
6. Reiniciar o Streamlit e conferir a Home nas 3 carteiras e algumas fichas de setores diferentes.

---

## 10. Pendências e limitações conhecidas

- Contagens das carteiras fixas no texto (seção 9, passo 5).
- O histórico de conversa do chatbot se perde ao navegar para outra tela.
- Algumas regras CSS dependem de detalhes internos do Streamlit 1.36 (ver `docs/frontend.md`, seção 8). Atualizar o Streamlit exige revisão visual.
- Legenda do mapa e camadas socioambientais adicionais: planejadas, ainda não ativas.
- Logos institucionais existem em `logos/`, mas não são exibidos.
