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
data/observacoes/observacoes_empreendimentos.csv  ← observações da ficha, mantidas à mão; lidas direto, sem ETL (fora do Git)
   │  services/data_loader.py  (leitura com cache + regras de precedência)
   ▼
app.py  (roteia pela URL)
   ├── views/home.py     Home: KPIs, filtros, tabela da carteira
   ├── views/atlas.py    Ficha do empreendimento (+ services/map_service.py)
   ├── views/chatbot.py  Assistente virtual (lógica em services/chatbot_service.py)
   └── views/bi.py       Painel de Indicadores & BI (protótipo; cálculos em services/bi_service.py)
```

O app **nunca acessa o banco**: tudo é lido dos arquivos `.parquet`, mais o CSV de observações da ficha (mantido à mão, fora do ETL).

---

## 3. Estrutura de pastas

```
atlas_web/
├── app.py                  Roteador: ?page=chatbot → chatbot | ?page=bi → BI | ?id=N → ficha | vazio → Home
├── requirements.txt        Versões exatas de todos os pacotes (streamlit==1.51.0); instalar com uv
├── .streamlit/config.toml  Servidor (porta, XSRF/CORS, telemetria) e tema claro institucional
├── views/
│   ├── home.py             Home
│   ├── atlas.py            Ficha do empreendimento
│   ├── chatbot.py          Tela do assistente virtual
│   ├── bi.py               Painel de Indicadores & BI (protótipo em validação)
│   ├── ui.py               Carregador de CSS e componentes comuns (barra de navegação, botão Voltar)
│   └── estado_url.py       Estado da Home e do BI guardado na URL; links internos e origem do Voltar
├── services/
│   ├── data_loader.py      Leitura dos parquets e do CSV de observações, cache e regras de precedência
│   ├── bi_service.py       Cálculos do BI: rankings por recorte, perfil, fronteira de eficiência
│   ├── formatters.py       Formatação brasileira (R$, %, milhar, datas)
│   ├── map_service.py      Mapa Folium da ficha
│   ├── chatbot_service.py  Lógica do chatbot (LangChain) — em desenvolvimento
│   └── chat_logger.py      Log das conversas do chatbot
├── assets/css/             Todo o CSS (base.css + um arquivo por tela) — ver frontend.md
├── scripts/
│   ├── process_data.py     ETL dos CSVs
│   └── process_geo.py      ETL das geometrias
├── data/raw/, data/processed/, data/observacoes/   Dados (ignorados pelo Git)
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
| `cenario_recomendado_2_vw_dadosgerais` (Recomendada), `cenario_recomendado_1_vw_dadosgerais` (Otimizada), `priorizacao_peltlp_vw_dadosgerais` (de Análise) + `natureza_empreendimento_legado` | `carteiras` | `id_empreendimento`, `carteira` | Tabela mestra: metadados, notas, IC, CAPEX/OPEX/TIRM e listas (municípios, regiões, intervenções, tipos de infraestrutura) de cada carteira |
| `vw_empreendimento_custo_economico_lp` | `dados_financeiro` | `id_empreendimento` | Custo Econômico LP: CAPEX, OPEX, receita, mês base |
| `resumo_financeiro` | `resumo_financeiro` | `id_empreendimento`, `id_cenario` | Resumo financeiro por cenário (o app usa 7 e 10): CAPEX, OPEX, receita e TIRM CODEMGE |
| `alocacao_total`, `tbl_alocacaoempreendimento` | `alocacao_empreendimento` | `id_empreendimento`, `id_cenario` | Alocação de fluxos 2055 por cenário |
| `vw_obra` | `obras_priorizacao` | `id_obra`, `id_empreendimento` | Obras de cada empreendimento (+ `valor_calculado`) |
| `vw_custo_economico` | `custo_obra` | `id_obra`, `id_cenario` | Custos de cada obra por cenário |
| `capacidade_satur_aero_cenarios` | `demanda_pax_aero_ano` | `id_empreendimento`, `id_cenario` | Demanda de passageiros — aeroviário |
| `demanda_duto` | `demanda_duto_ano` | `id_empreendimento` | Volume e TKU — dutoviário |
| `demanda_ferro_passageiro` | `demanda_pax_ferro_ano` | `id_empreendimento` | Demanda de passageiros — ferroviário |
| `mvw_empreendimento_geo` (JSON) | `empreendimento_geo` | `id_empreendimento` | Geometrias WKT: `geom_linha` e `geom_ponto` |

Relações: um empreendimento tem até 3 linhas na tabela mestra (uma por carteira; a Recomendada e a Otimizada estão contidas na de Análise), N obras, N custos por obra/cenário e N linhas de alocação/demanda por cenário.

### 4.2 Regras do ETL (`scripts/process_data.py`)
1. **Encoding:** os CSVs exportados são UTF-8 e são lidos como UTF-8 (`utf-8-sig`); Latin-1 só é usado se o arquivo não for UTF-8. **Não existe correção de acentuação em tempo de execução.** Se o ETL imprimir `[AVISO] ... possivel acentuacao corrompida`, o problema está na exportação — corrija na origem, não no texto.
2. **Tipo do ID:** `id_empreendimento` é gravado como inteiro que aceita vazio (`Int64`) em todas as tabelas. O app compara o ID diretamente, sem conversões.
3. **Custo das obras:** `valor_calculado` = soma dos custos da obra em cada cenário, adotando o **cenário mais caro**; se não houver custo, usa `valor_global` da obra.
4. **`resumo_financeiro`:** duplicatas de (`id_empreendimento`, `id_cenario`) são removidas.
5. **`carteiras`:** os 3 CSVs da view `vw_dadosgerais_plataformaonline` (um por schema) viram uma tabela com a coluna `carteira` (`recomendada`, `otimizada`, `analise`). As colunas em formato de array do PostgreSQL (`{Araporã,Prata}`) viram listas Python: `intervencoes`, `tipos_infraestruturas`, `municipios`, `regioes_intermediarias`.
6. **Natureza e grupo de modelagem (provisório):** a view ainda não traz `natureza_empreendimento` nem `id_grupo_modelagem`, usados na tabela de Alocação da ficha. A natureza vem de `data/raw/natureza_empreendimento_legado.csv` (id → natureza, extraído da tabela antiga `mvw_8_calcula_impacto_3_pond_cenario` em 25/09/2026; a natureza não mudou) e o `id_grupo_modelagem` é deduzido do nome do grupo (`ID_GRUPO_MODELAGEM` em `process_data.py`). O ETL avisa se algum empreendimento ficar sem natureza ou se surgir um grupo desconhecido. **Não apague o CSV legado** enquanto a view não for revisada (seção 10).

### 4.3 Leitura e cache (`services/data_loader.py`)
- Parquets pequenos: `@st.cache_data` — cada chamada recebe uma cópia; um usuário não altera o dado de outro.
- `empreendimento_geo` (~114 MB em disco, ~255 MB em memória): `@st.cache_resource` — **um único objeto compartilhado** por todas as sessões. É **somente leitura**: nunca altere o DataFrame retornado por `get_empreendimento_geo()` (use `.copy()` se precisar).
- Buscas por empreendimento usam sempre `data_loader.filtrar_por_empreendimento(df, id)`.
- Observações da ficha (`get_observacoes`): o CSV é lido com o módulo `csv` (não pandas) e guardado em `@st.cache_data` como `{id: [textos]}`; regras na seção 6.
- O cache não percebe arquivos novos: **reinicie o Streamlit** depois de regenerar os parquets ou editar o CSV de observações.

---

## 5. Regras de negócio

1. **Carteiras (coluna `carteira` de `carteiras.parquet`):**
   | Carteira (nome na tela) | Schema de origem | Empreendimentos (base 25/09/2026) | Na URL |
   |---|---|---|---|
   | Recomendada (padrão da Home) | `cenario_recomendado_2` | 1.044 | `carteira=recomendada` |
   | Otimizada | `cenario_recomendado_1` | 1.058 | `carteira=otimizada` |
   | De análise | `priorizacao_peltlp` | 1.682 | `carteira=analise` (o antigo `completa` continua aceito) |

   A carteira escolhida na Home define KPIs, opções dos filtros, tabela, índice (IC) e impacto exibidos. A listagem é ordenada por `ic_3_pond` decrescente.
2. **Notas da ficha (Resultados da Priorização):** vêm da carteira **Recomendada**; se o empreendimento não estiver nela, da **Otimizada**; senão, da **de Análise** (`get_empreendimento_resolvido`). Dimensões vazias são completadas pela próxima fonte. Um badge mostra a fonte usada.
3. **Dados financeiros da ficha:** CAPEX, OPEX, receita e TIRM vêm do **cenário 10 (Recomendado)** do `resumo_financeiro`; senão do **cenário 7 (Otimizado)**; senão do **Custo Econômico LP** (`dados_financeiro`) com a TIRM da priorização (`get_dados_financeiro_resolvido`). Valor Total = CAPEX + OPEX. O mês base vem sempre do Custo Econômico LP. Um badge mostra a fonte usada.
4. **KPIs da Home** (dependem só da carteira, não dos filtros): Empreendimentos, **Alta Viabilidade** (`viabilidade == "Alta viabilidade"`), **Alto Impacto** e **Investimento Total** = soma do `capex` da própria carteira, em bilhões arredondados (ex.: `R$ 530 Bi`).
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
| `?page=bi` | Painel de Indicadores & BI (protótipo; `carteira` na URL é a mesma da Home) |
| `?id=1042&de=bi&bi_aba=matriz` | Ficha aberta a partir do BI: o botão vira "Voltar para o Painel" e reabre a aba de origem |

- **A URL é a fonte da verdade.** Links internos são relativos (começam com `?`).
- **Barra de navegação superior** (todas as telas, `render_navbar` em `views/ui.py`): Página Inicial, Painel de Indicadores & BI e Assistente Virtual, com destaque na tela aberta (na ficha, destaca a página de origem: Página Inicial ou, com `de=bi`, o Painel). Substitui a faixa nativa do Streamlit (menu ⋮), que fica escondida.
- **Voltar da ficha conforme a origem:** links do BI para a ficha levam `de=bi` (origem, lista fechada em `estado_url.ORIGENS`; nunca um endereço livre) e `bi_aba` (aba de onde veio). Com `de=bi` o botão é "Voltar para o Painel" e leva ao BI com o estado dele; sem `de`, "Voltar para a Lista" (Home). `de` e `bi_aba` são parâmetros de navegação: o BI os lê ao abrir e os tira da URL, e a Home também os remove.
- **Estado do BI na URL:** `carteira` (a mesma da Home), `bi_setor`, `bi_emp` (empreendimento do Perfil) e `bi_eixo` (eixo Y da matriz). O prefixo `bi_` evita colisão com os filtros da Home; os dois estados convivem na URL, então Home → BI → ficha → BI → Home não perde nada. Detalhes: `docs/frontend.md`, seção 5.9.
- **Estado da Home na URL:** carteira, busca, filtros, página, itens por página e colunas vão para a URL (`views/estado_url.py`), e os links da tabela, do chatbot e dos botões "Voltar" os carregam. Assim, abrir uma ficha e voltar não perde os filtros, e o link pode ser compartilhado. Detalhes e como incluir um filtro novo: `docs/frontend.md`, seção 5.9.
- **Home:** 4 KPIs; filtros com carteira, busca e 8 filtros de seleção múltipla sempre visíveis (setor, status, origem, esfera, impacto, viabilidade, natureza, intervenção principal) e a seção recolhida **"Mais filtros"** (município, região intermediária e sliders de Valor Total = CAPEX + OPEX, TIRM e IC); botão redondo "Limpar filtros" (vassoura) ao lado de "Personalizar Colunas"; tabela paginada e ordenável pelo cabeçalho (clique: primeiro sentido → oposto → volta ao padrão IC decrescente; ordem na URL) com colunas configuráveis (modal de arrastar; padrão: ID, Nome, Status, Setor, Natureza, Origem, Esfera, CAPEX, OPEX, TIRM, Índice, Impacto; entre as ocultas, Valor Total e as notas das 5 dimensões), botão flutuante do assistente.
- **Regiões intermediárias:** a Home mostra (filtro e coluna) só as 13 regiões de MG (`REGIOES_INTERMEDIARIAS_MG` em `views/home.py`); regiões de estados vizinhos que aparecem nos dados são descartadas na exibição, sem alterar o parquet.
- **Ficha:** cabeçalho, metadados + mapa (mesma altura, 520px), balão de observação (só se houver) e as tabelas Resultados da Priorização, Dados Financeiros, Alocação 2055 e Detalhamento das Obras.
- **Observações da ficha:** `data/observacoes/observacoes_empreendimentos.csv`, colunas `id_empreendimento` e `observacao` (nome e local fixos; `OBSERVACOES_CSV` em `data_loader.py`). Lido uma vez por servidor: **editou o CSV, reinicie o Streamlit**. Aceita `,` ou `;` (detectado pelo cabeçalho), UTF-8 ou Windows-1252 (Excel). Várias linhas do mesmo id viram parágrafos do mesmo balão; id inválido ou texto vazio é ignorado; arquivo ausente = nenhum balão. O texto é exibido como texto puro (sem HTML), com as quebras de linha. Nos servidores, o arquivo é copiado manualmente, como os demais dados.
- **Mapa (`services/map_service.py`):** Folium com base OpenStreetMap (sem chave de API), traçado linear e pontos do empreendimento, enquadramento automático; aviso quando não há geometria. A legenda QGIS está preservada em `render_legenda_qgis()` (desativada).
- **Painel de Indicadores & BI (protótipo em validação):** seletores de carteira (padrão Recomendada) e setor (padrão "Todos os setores"). Números-resumo da seleção: Empreendimentos, Presente | Futuro (Contratado | Planejado), CAPEX e Alto Impacto. Cada empreendimento é comparado com os pares do mesmo setor (mesmo com "Todos os setores", cada setor é ranqueado à parte) em cada recorte (setor inteiro, intervenção principal, região intermediária de MG) nas métricas IC, 5 dimensões e TIRM; desempate pelo IC; nota zero numa dimensão = não pontuou (fica fora do ranking). Abas: Perfil do empreendimento (cartão com investimento total = CAPEX + OPEX), Impacto × Viabilidade (X = TIRM com linhas de referência em 0% e 11,2%; seletor do eixo Y: IC, investimento total = CAPEX + OPEX (escala logarítmica) ou nota da dimensão socioeconômica ou da estratégica; cor = classe de impacto; sem classificação de modelo de execução) e Panorama de Investimentos (só a tabela de intervenção principal por esfera: quantidade e CAPEX. Presente, usado nos números-resumo e no cartão = Contratado - execução não iniciada, Contratado - em execução, Paralisado; o resto é Futuro; CAPEX "-" quando CAPEX e OPEX do grupo somam zero = sem modelagem financeira completa).
- **Visual:** todo o CSS em `assets/css/`, com cores centralizadas — ver `docs/frontend.md`.

---

## 7. Ambiente de trabalho e branches

- **Tudo roda no computador do responsável.** Servidores (inclusive produção) **não estão ao alcance dos agentes**: não há acesso, comandos de deploy ou configuração de servidor a fazer por aqui. A publicação no servidor é feita pelo responsável.
- **Rodar localmente:** `.venv/Scripts/python.exe -m streamlit run app.py` → `http://localhost:8501`.
- **Sempre use o `.venv`**: Python 3.12 e Streamlit **1.51.0** (versão fixa), criado com `uv venv -p 3.12 .venv` e instalado com `uv pip install -r requirements.txt`. Não é preciso ter o Python 3.12 instalado: o uv baixa o dele. Na máquina do responsável o uv foi instalado com `python -m pip install --user uv` e é chamado como `python -m uv ...`; o servidor (Ubuntu 20.04) usa o mesmo arquivo. O Python global da máquina pode ter outra versão, o que quebra o mapa e muda o visual.
- **Mudar versões:** o `requirements.txt` é o único arquivo de dependências e fixa a versão exata de tudo (os pacotes principais são os marcados com `# via -r requirements.txt`). Para trocar a versão de um pacote, edite a linha dele, reinstale no `.venv` com `uv pip install -r requirements.txt` e confira se o uv não acusa conflito; se a troca puxar dependências novas, ajuste as linhas delas também. Troca de versão do Streamlit (ou de outro pacote de tela) exige revisão visual (`docs/frontend.md`, seção 8).
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
5. Conferir o aviso do ETL sobre natureza/grupo de modelagem (seção 4.2, item 6) e atualizar as contagens da tabela da seção 5 deste documento.
6. Reiniciar o Streamlit e conferir a Home nas 3 carteiras e algumas fichas de setores diferentes.
7. Observações da ficha: não passam pelo ETL. Edite `data/observacoes/observacoes_empreendimentos.csv` quando quiser (Excel serve) e reinicie o Streamlit; confira se os ids continuam existindo depois de uma nova extração.

---

## 10. Pendências e limitações conhecidas

- **Revisar a view `vw_dadosgerais_plataformaonline`** para incluir `natureza_empreendimento` e `id_grupo_modelagem`. Hoje eles vêm de um CSV legado e de um dicionário no ETL (seção 4.2, item 6). Depois disso, remover `natureza_empreendimento_legado.csv` e `ID_GRUPO_MODELAGEM`.
- `data/processed/empreendimentos_priorizacao.parquet` (tabela antiga) não é mais usado pelo app nem gerado pelo ETL; pode ser apagado.
- O histórico de conversa do chatbot se perde ao navegar para outra tela.
- Algumas regras CSS dependem de detalhes internos do Streamlit 1.51 (ver `docs/frontend.md`, seção 8). Atualizar o Streamlit exige revisão visual.
- Legenda do mapa e camadas socioambientais adicionais: planejadas, ainda não ativas.
- Logos institucionais existem em `logos/`, mas não são exibidos.
- **Painel de BI (protótipo — pendências registradas em 28/09/2026):**
  - *Estado na URL (resolvido em 01/10/2026):* ver "Estado do BI na URL" acima. Limitações: o `st.tabs` (1.51) não informa a aba aberta, então a aba só é lembrada na volta de uma ficha (recarregar a página abre a primeira aba); o ponto clicado na matriz não é marcado de novo no gráfico, mas o perfil dele reaparece abaixo até um novo clique. O BI usa a mesma marca de "sessão iniciada" da Home (`estado_url.marcar_sessao_iniciada`).
  - *Dependência da Home:* `views/bi.py` importa `CARTEIRAS_HOME` de `views/home.py` e repete a lista das regiões de MG (`REGIOES_MG` em `bi_service.py`, igual a `REGIOES_INTERMEDIARIAS_MG` da Home). Centralizar (ex.: em `data_loader`) antes de publicar.
  - *Região intermediária:* um empreendimento que passa por várias regiões conta inteiro em cada uma. Aguardando a tabela de pertencimento (`id_empreendimento`, tamanho do empreendimento, RGI, tamanho na RGI) para ponderar.
  - *Retirado/oculto até nova definição:* métrica CAPEX por km (removida), aba "Eficiência do CAPEX" (`_render_eficiencia`, oculta). A aba "Destaques por recorte" e a lista "Destaques fora do topo do IC" foram apagadas em 29/09/2026.
  - *Gráficos:* clique só funcionava em gráfico Altair de camada única no Streamlit 1.36 (`erros_solucoes.md`, caso 13); a matriz ainda usa a solução de contorno — reavaliar no 1.51.
