# 📋 Plano de Implementação: Novos Cenários de Alocação e Seletor de Carteiras de Priorização

Inclusão e processamento das novas bases de dados de **Priorização** e **Alocação**, habilitação dos novos **Cenários 7 (Otimizado)** e **10 (Recomendado)** na tabela de alocação, implementação da regra hierárquica de resolução de notas das dimensões (Recomendado ➔ Otimizado ➔ Geral) e adição de um seletor interativo de carteiras na página inicial.

---

## 1. Contexto e Diagnóstico dos Novos Dados

Na pasta `data/raw/`, foram disponibilizados dois novos arquivos de dados:
1. **`priorizacao202609091431.csv`** (3.785 registros):
   - Contém a nova coluna `fonte_priorizacao` com 3 categorias:
     - `priorizacao geral`: 1.682 empreendimentos (todos os projetos avaliados no processo inicial).
     - `cenario otimizado`: 1.059 empreendimentos (filtragem de alto/médio impacto, remoção de concorrentes e nova priorização).
     - `cenario recomendado`: 1.044 empreendimentos (avaliação de indicadores de desempenho, com entradas e saídas estratégicas).
   - As notas das dimensões (`dimensao_estrategica`, `dimensao_financeira`, `dimensao_socioeconomica_pond`, `dimensao_comercial`, `dimensao_gerencial`, `ic_3_pond`, `impacto_avaliado_3_pond_cenario`) variam de acordo com a `fonte_priorizacao`.

2. **`alocacao_total202609091500.csv`** (6.676 registros):
   - Mesma estrutura e colunas da tabela anterior de alocação de empreendimentos (`tbl_alocacaoempreendimento_*`).
   - Foram adicionados os dados referentes a dois novos cenários:
     - **Cenário 7**: Cenário Otimizado (1.005 alocações).
     - **Cenário 10**: Cenário Recomendado (962 alocações).
     - Cenários 1, 2, 3 e 4 permanecem preservados com exatamente as mesmas contagens.

---

## 2. Decisões de Design e Arquitetura

### 2.1. Criação de Nova Branch Git
Em conformidade estrita com o item 5 de `docs/regras_projeto.md` e a solicitação do usuário:
- Criação da branch temática: `feat/novos-cenarios-alocacao-priorizacao`.
- Nenhuma alteração será commitada antes do teste e aprovação expressa do usuário.

### 2.2. Atualização do Pipeline ETL (`scripts/process_data.py`)
- Mapeamento dinâmico para reconhecer os novos arquivos:
  - `priorizacao*` ➔ `data/processed/empreendimentos_priorizacao.parquet`
  - `alocacao_total*` ➔ `data/processed/alocacao_empreendimento.parquet`
  - Mantém retrocompatibilidade defensiva caso prefixos antigos (`mvw_8_calcula_impacto`, `tbl_alocacaoempreendimento`) sejam encontrados.
- Execução da conversão de CSV para Parquet com higienização de Mojibake e preservação da integridade de tipos.

### 2.3. Resolução Hierárquica das Notas de Dimensões (`views/atlas.py` e `services/data_loader.py`)
Conforme a regra solicitada:
> *"As notas para cada dimensão deve vim da nova tabela de priorizacao e a ordem deve ser: Mostrar a nota no cenario recomendado se não tiver mostrar do cenario otimizado se não tiver mostrar da priorizacao geral."*

- **Função de Resolução (`get_priorizacao_resolvida(empreendimento_id)`):**
  1. Busca registros do empreendimento por ID.
  2. Prioridade 1: Verifica existência do registro em `cenario recomendado`.
  3. Prioridade 2: Caso não exista ou a dimensão seja nula, busca em `cenario otimizado`.
  4. Prioridade 3: Caso não exista ou seja nula, faz fallback para `priorizacao geral`.
- **Identificação Visual no Atlas:** Na seção *Resultados da Priorização*, além das notas, exibiremos um badge sutil indicando a fonte adotada da nota (ex: `Fonte: Cenário Recomendado`, `Cenário Otimizado` ou `Priorização Geral`), trazendo transparência auditável para o usuário.

### 2.4. Atualização da Tabela de Alocação (`views/atlas.py`)
- Remoção da trava fixa que limitava aos cenários de 1 a 4 (`cenario_num.isin([1, 2, 3, 4])`).
- Expansão para incluir cenários `[1, 2, 3, 4, 7, 10]`.
- Identificação dos cenários na coluna da tabela:
  - `1`, `2`, `3`, `4`
  - `7 (Otimizado)`
  - `10 (Recomendado)`

### 2.5. Seletor de Carteiras na Página Inicial (`views/home.py`)
- Criação de um seletor visual em formato de botões segmentados (estilo *segmented control* / pills do Streamlit) no topo da Home:
  - 🌐 **Carteira Completa** (Priorização Geral — 1.682 projetos)
  - ⚡ **Carteira Otimizada** (Cenário Otimizado — 1.059 projetos)
  - ⭐ **Carteira Recomendada** (Cenário Recomendado — 1.044 projetos)
- Card explicativo dinâmico logo abaixo do seletor detalhando a metodologia da carteira ativa:
  - **Carteira Completa:** Primeiro processo onde são considerados todos os empreendimentos com priorização geral.
  - **Carteira Otimizada:** Empreendimentos de alto e médio impacto, sem concorrência mútua, com nova priorização.
  - **Carteira Recomendada:** Avaliação de indicadores e rebalanceamento de empreendimentos para maximização de benefícios.
- **Reatividade Total:**
  - Cartões de KPI recalculados automaticamente com base na carteira escolhida.
  - Filtros de Setor, Esfera e Classificação recalculados dinamicamente.
  - Tabela de empreendimentos exibe apenas os projetos da carteira selecionada, com o Índice (IC) e Impacto específicos daquela carteira.
  - Paginação ajustada conforme o tamanho da carteira.

---

## 3. Arquivos Afetados e Modificações

### Scripts ETL
- [`scripts/process_data.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/scripts/process_data.py): Adicionar prefixos `"priorizacao"` e `"alocacao_total"` ao `FILE_MAPPING`.
- [`scripts/fix_encoding.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/scripts/fix_encoding.py): Sincronizar o dicionário `FILE_MAPPING`.

### Camada de Serviços
- [`services/data_loader.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/services/data_loader.py):
  - Implementar `get_empreendimentos(carteira: str = None)` para permitir carregamento filtrado por carteira ou completo.
  - Implementar `get_empreendimento_resolvido(empreendimento_id: int)` com a lógica hierárquica de fallback: `Recomendado` ➔ `Otimizado` ➔ `Geral`.
- [`services/chatbot_service.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/services/chatbot_service.py):
  - Adaptar ferramentas do chatbot (`buscar_empreendimento`, `listar_empreendimentos`, `contar_empreendimentos`) para utilizar a base com desduplicação ou resolução hierárquica.

### Camada de Interface (Views)
- [`views/home.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/views/home.py):
  - Inserir o componente seletor de carteiras no topo da página.
  - Atualizar KPIs, opções dos dropdowns de filtros, contadores e listagem da tabela de acordo com a carteira ativa.
- [`views/atlas.py`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/views/atlas.py):
  - Atualizar `render_tabela_priorizacao` para utilizar a resolução hierárquica de dimensões e exibir o badge indicativo da fonte.
  - Atualizar `render_tabela_alocacao` para suportar os novos cenários 7 e 10, com rótulos `7 (Otimizado)` e `10 (Recomendado)`.

### Documentação
- [`docs/regras_projeto.md`](file:///c:/Users/paulo/OneDrive/Área%20de%20Trabalho/projetos/atlas_web/docs/regras_projeto.md):
  - Registrar os novos arquivos, a coluna `fonte_priorizacao` e os cenários 7 e 10.

---

## 4. Plano de Verificação

### Testes Automatizados e Scripts de Validação
1. **Validação do ETL:**
   ```bash
   python scripts/process_data.py
   ```
   - Verificar se `empreendimentos_priorizacao.parquet` possui 3.785 linhas e a coluna `fonte_priorizacao`.
   - Verificar se `alocacao_empreendimento.parquet` possui 6.676 linhas e cenários `[1, 2, 3, 4, 7, 10]`.
2. **Teste da Resolução Hierárquica:**
   - Script em Python testando IDs presentes em 3 fontes (ex: ID 1034), 2 fontes e apenas na priorização geral, validando se a ordem de fallback funciona rigorosamente.
3. **Teste do Seletor e KPIs da Home:**
   - Conferir contagens: Carteira Completa (1.682), Carteira Otimizada (1.059), Carteira Recomendada (1.044).

### Testes Visuais e Manuais
1. Abrir a aplicação local (`streamlit run app.py`).
2. Alternar entre as 3 carteiras na Home e verificar a atualização instantânea de KPIs, filtros e tabela.
3. Clicar em um empreendimento e verificar a tela do Atlas:
   - Tabela de Resultados da Priorização exibindo as notas resolvidas na ordem correta e badge da fonte.
   - Tabela de Alocação exibindo os novos cenários 7 e 10 quando aplicável.
