# 🛠️ Base de Conhecimento: Erros, Diagnósticos e Soluções (Atlas Web)

Este documento registra o histórico de problemas técnicos complexos, comportamentos não triviais de bibliotecas e as soluções adotadas no projeto **Atlas Web**. 

> **Regra do Projeto:** Sempre que um erro complexo ou peculiar (com potencial de impacto futuro) for solucionado, este arquivo deve ser atualizado logo após o push ou merge na branch `main`.

---

## 📋 Índice de Casos Registrados

1. [Parser Markdown do Streamlit Exibindo Tags HTML Cruas (`<pre><code>`)](#caso-1-parser-markdown-do-streamlit-exibindo-tags-html-cruas-precode)
2. [Bloqueio de Navegação por Links Dentro de `components.html` (Sandbox de IFrame)](#caso-2-bloqueio-de-navegação-por-links-dentro-de-componentshtml-sandbox-de-iframe)
3. [Codificação Dupla (Mojibake) em Exportações de Banco PostGIS](#caso-3-codificação-dupla-mojibake-em-exportações-de-banco-postgis)
4. [Persistência de Query Params na URL ao Voltar do Atlas para a Home](#caso-4-persistência-de-query-params-na-url-ao-voltar-do-atlas-para-a-home)
5. [Desalinhamento Visual de Ordenação por IC devido a Limiares Setoriais de Impacto](#caso-5-desalinhamento-visual-de-ordenação-por-ic-devido-a-limiares-setoriais-de-impacto)
6. [Incompatibilidade de `@st.dialog` e Seletores DOM no Streamlit 1.36.0](#caso-6-incompatibilidade-de-stdialog-e-seletores-dom-no-streamlit-1360)
7. [Botão "Personalizar Colunas" sem Estilo (Seletor `button[key=...]`)](#caso-7-botão-personalizar-colunas-sem-estilo-seletor-buttonkey)
8. [Barra de Rolagem Vertical na Barra de Navegação (`overflow-x: auto`)](#caso-8-barra-de-rolagem-vertical-na-barra-de-navegação-overflow-x-auto)
9. [`select_slider` de Faixa Perde a Segunda Alça e Faixa "Completa" que Vira Filtro](#caso-9-select_slider-de-faixa-perde-a-segunda-alça-e-faixa-completa-que-vira-filtro)
10. [Prefixo de Arquivo do ETL Capturando o Arquivo Errado](#caso-10-prefixo-de-arquivo-do-etl-capturando-o-arquivo-errado)
11. [Servidor com Python Antigo e CSS Novo Após Editar o Código](#caso-11-servidor-com-python-antigo-e-css-novo-após-editar-o-código)
12. [Página "Dá um Tranco" a Cada Clique na Home (`st.empty` Vazio Durante o Rerun)](#caso-12-página-dá-um-tranco-a-cada-clique-na-home-stempty-vazio-durante-o-rerun)
13. [Clique em Gráfico Altair Quebra com "Selections are not yet supported for multi-view charts"](#caso-13-clique-em-gráfico-altair-quebra-com-selections-are-not-yet-supported-for-multi-view-charts)
14. [Migração do Streamlit 1.36 para 1.51: Seletores CSS Renomeados](#caso-14-migração-do-streamlit-136-para-151-seletores-css-renomeados)
15. [Ordenar a Tabela Recarregava a Página; `AppTest` Não Monta Componente v2](#caso-15-ordenar-a-tabela-recarregava-a-página-apptest-não-monta-componente-v2)
16. [Lista do Filtro (`st.multiselect`) Não Fecha ao Clicar de Novo na Caixa](#caso-16-lista-do-filtro-stmultiselect-não-fecha-ao-clicar-de-novo-na-caixa)

---

## Caso 1: Parser Markdown do Streamlit Exibindo Tags HTML Cruas (`<pre><code>`)

* **Data:** 13/08/2026
* **Componentes Afetados:** `views/atlas.py`, `views/home.py`
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
Ao renderizar tabelas e cartões HTML customizados via `st.markdown(..., unsafe_allow_html=True)`, blocos de código HTML (como `<tr>`, `<td>`, `<div>`) eram exibidos como texto cru na tela ao invés de serem renderizados visualmente como elementos formatados.

### 🔍 Causa Raiz
O parser de Markdown integrado ao Streamlit segue a especificação CommonMark, onde **qualquer linha com 4 ou mais espaços de indentação é interpretada como bloco de código pré-formatado** (`<pre><code>`). 
Ao usar f-strings multi-linha indentadas no código Python:
```python
# ❌ CAUSAVA O ERRO:
rows_html += f"""
    <tr>
        <td>{valor}</td>
    </tr>
"""
```
A indentação interna de 4 a 12 espaços fazia o Streamlit converter o trecho em texto puro.

### ✅ Solução Adotada
1. Construir strings HTML por **concatenação sem espaços no início da linha**:
   ```python
   # ✔️ CORRETO:
   rows_html += (
       '<tr>'
       f'<td>{valor}</td>'
       '</tr>'
   )
   ```
2. Aplicar `html.escape(str(valor))` em todo texto dinâmico para evitar que caracteres como `&`, `<`, `>` corrompam a estrutura das tags.
3. Utilizar **estilos inline** (`style="..."`) para painéis e cartões de metadados simples.

---

## Caso 2: Bloqueio de Navegação por Links Dentro de `components.html` (Sandbox de IFrame)

* **Data:** 13/08/2026
* **Componentes Afetados:** `views/home.py`, `app.py`
* **Tecnologia:** `streamlit.components.v1.html` vs `st.markdown`

### 🛑 Contexto e Sintoma
Para isolar a renderização da tabela da Home e evitar conflitos de CSS, foi utilizado `components.html()`. No entanto, ao clicar nos links dos empreendimentos ou nos botões "Ver Atlas ➔", a aplicação não navegava para a ficha técnica no Atlas.

### 🔍 Causa Raiz
O método `components.html()` encapsula o HTML gerado dentro de um `<iframe>` isolado. Devido às políticas de segurança e sandbox cross-origin de iframes no navegador, scripts como `window.top.location.href` ou links com `target="_top"` / `target="_self"` dentro do iframe não conseguem manipular o roteamento da janela principal da SPA (Single Page Application) do Streamlit.

### ✅ Solução Adotada
1. Renderizar a tabela diretamente no DOM principal utilizando `st.markdown(table_html, unsafe_allow_html=True)` (com a técnica de concatenação sem indentação do Caso 1).
2. Utilizar links nativos com `target="_self"`:
   ```html
   <a href="?id=113" target="_self" class="emp-link">Nome do Projeto</a>
   ```
3. No `app.py`, sincronizar os `st.query_params` diretamente com o estado da sessão:
   ```python
   query_id = st.query_params.get("id", None)
   if query_id:
       st.session_state["selected_empreendimento_id"] = query_id
   else:
       st.session_state["selected_empreendimento_id"] = None
   ```
4. Implementar paginação local para manter o DOM leve e a renderização instantânea.

---

## Caso 3: Codificação Dupla (Mojibake) em Exportações de Banco PostGIS

* **Data:** 13/08/2026
* **Componentes Afetados:** `scripts/process_data.py`, `services/data_loader.py`
* **Tecnologia:** `pandas`, `pyarrow`, `PostGIS`

### 🛑 Contexto e Sintoma
Ao carregar dados exportados do banco em CSV para visualização em telas web, caracteres acentuados apareciam corrompidos (ex: `OperaÃ§Ã£o`, `RodoviÃ¡rio`, `Furnas Ã©`).

### 🔍 Causa Raiz
Exportações legadas do banco PostGIS frequentemente exportam strings codificadas em UTF-8 mas salvas com cabeçalho ou leitor configurado em Latin1 (ISO-8859-1), gerando o padrão clássico de Mojibake (bytes UTF-8 interpretados individualmente em Latin1).

### ✅ Solução Adotada
1. Criar a função defensiva `fix_mojibake`:
   ```python
   def fix_mojibake(text):
       if not isinstance(text, str):
           return text
       if any(m in text for m in ["Ã", "Â", "â", "©"]):
           try:
               return text.encode("latin1").decode("utf-8")
           except (UnicodeEncodeError, UnicodeDecodeError):
               pass
       return text
   ```
2. Aplicar a limpeza tanto na esteira ETL (`scripts/process_data.py`) quanto na camada de leitura cached (`services/data_loader.py`).

### 🔄 Revisão (24/09/2026): causa real e correção na origem
A causa estava no próprio ETL, não no banco: os CSVs exportados **são UTF-8**, mas o `process_data.py` tentava ler primeiro com `encoding="latin1"`. Latin-1 aceita qualquer byte e nunca gera erro, então o fallback para UTF-8 nunca executava e todo acento era corrompido na leitura, para depois ser "consertado" pelo `fix_mojibake`.

Correção:
1. O ETL lê com `encoding="utf-8-sig"` e só recorre a Latin-1 se houver `UnicodeDecodeError` (UTF-8 falha de verdade quando o arquivo não é UTF-8).
2. `fix_mojibake` e `scripts/fix_encoding.py` foram removidos; o `data_loader.py` apenas lê os parquets.
3. No lugar do conserto silencioso, o ETL **avisa** quando encontra sequências típicas de mojibake (`Ã§`, `â€“`) no texto.

Validação: os parquets regenerados ficaram idênticos, célula a célula, ao que o app exibia antes.

---

## Caso 4: Persistência de Query Params na URL ao Voltar do Atlas para a Home

* **Data:** 14/08/2026
* **Componentes Afetados:** `app.py`, `views/atlas.py`, `views/home.py`
* **Tecnologia:** `streamlit==1.36.0` (Roteamento via URL e Session State)

### 🛑 Contexto e Sintoma
Após navegar da Home para o Atlas de um empreendimento (`?id=113`), ao clicar no botão de voltar e posteriormente interagir com a paginação na Home, o sistema inesperadamente reabria a tela do empreendimento.

### 🔍 Causa Raiz
O botão de voltar utilizava `st.button` executando `del st.query_params['id']` e `st.rerun()`. No Streamlit 1.36.0, o `del st.query_params` altera o estado interno via WebSocket mas nem sempre sincroniza a barra de endereços do navegador imediatamente antes de novas interações. Ao clicar em qualquer botão de paginação, a URL ainda continha o parâmetro `?id=...`, fazendo o roteador `app.py` restaurar a visualização do empreendimento.

### ✅ Solução Adotada
1. No `app.py`, transformar a URL (`st.query_params.get("id")`) na **única fonte da verdade**: se o `id` for nulo ou vazio, garantir `st.session_state["selected_empreendimento_id"] = None` e limpar qualquer chave residual.
2. No `views/atlas.py`, substituir o botão `st.button` por um link nativo estilizado `<a href="?" target="_self" class="atlas-back-btn">⬅ Voltar para a Lista de Empreendimentos</a>`. A navegação nativa do navegador para `?` limpa fisicamente os parâmetros de consulta da URL de forma síncrona e definitiva.

---

## Caso 5: Desalinhamento Visual de Ordenação por IC devido a Limiares Setoriais de Impacto

* **Data:** 10/09/2026
* **Componentes Afetados:** `views/home.py`, `services/data_loader.py`
* **Tecnologia:** `pandas`, `streamlit`

### 🛑 Contexto e Sintoma
Ao alternar entre as carteiras metodológicas (Cenário Otimizado ou Priorização Geral), badges de "Médio impacto" apareciam acima de "Alto impacto" na tabela, dando a impressão visual de que a listagem não estava ordenada pelo índice (`ic_3_pond`).

### 🔍 Causa Raiz
1. No PELTMG, a classificação em *Alto impacto* ou *Médio impacto* decorre de percentis e cortes calculados **por setor de transporte** (e não uma régua global única). Por exemplo, no Cenário Otimizado, os IDs 1066 e 1067 possuem IC 0,3543 e classificação 'Médio impacto', enquanto o ID 798 possui IC 0,3435 e 'Alto impacto'. A ordenação numérica pelo IC estava correta (`0,3543 > 0,3435`), mas o padrão de cores dos badges causava estranheza.
2. Na Carteira Recomendada, todos os projetos do topo eram coincidentemente de Alto impacto, gerando a percepção de que apenas ela estava ordenada.

### ✅ Solução Adotada
1. Forçar a conversão estrita de `ic_3_pond` para float com `pd.to_numeric(..., errors="coerce")` e reordenação decrescente `.sort_values(by="ic_3_pond", ascending=False).reset_index(drop=True)` tanto na seleção da carteira quanto logo antes do fatiamento da paginação no `df_filtrado`.
2. Registrar nos metadados que a ordenação prioritária é estritamente pelo valor contínuo do índice de priorização (IC), prevalecendo sobre as categorias qualitativas setoriais.

---

## Caso 6: Incompatibilidade de `@st.dialog` e Seletores DOM no Streamlit 1.36.0

* **Data:** 14/09/2026
* **Componentes Afetados:** `views/home.py`, `app.py`
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
1. Ao tentar utilizar o decorador `@st.dialog(...)`, a aplicação quebrou com `AttributeError: module 'streamlit' has no attribute 'dialog'`.
2. Botões renderizados dentro de colunas (`st.columns`) tiveram suas larguras esmagadas para 32px e o texto quebrado verticalmente, devido a regras de CSS globais da paginação que afetavam qualquer `button` em `div[data-testid="stHorizontalBlock"]`.
3. Estilos customizados para o modal do diálogo não surtiam efeito quando utilizavam `div[data-testid="stDialog"]`.

### 🔍 Causa Raiz
1. No **Streamlit 1.36.0**, a funcionalidade de modal ainda era experimental, registrada como **`st.experimental_dialog`**. O método oficial `st.dialog` só foi lançado no Streamlit 1.37.0.
2. O elemento do modal no DOM do Streamlit 1.36.0 possui o atributo `data-testid="stModal"`, e não `data-testid="stDialog"`.
3. O seletor CSS `div[data-testid="stHorizontalBlock"] button[kind="secondary"]` utilizado para a paginação tinha escopo amplo demais, atingindo qualquer botão inserido em `st.columns`.

### ✅ Solução Adotada
1. **Fallback automático de compatibilidade:**
   ```python
   if hasattr(st, "dialog"):
       _dialog_decorator = st.dialog("Personalizar Colunas da Tabela", width="large")
   elif hasattr(st, "experimental_dialog"):
       _dialog_decorator = st.experimental_dialog("Personalizar Colunas da Tabela", width="large")
   else:
       def _dialog_decorator(f): return f
   ```
2. **Escopo estrito nos seletores CSS:**
   - Paginação restrita a blocos com 5 ou mais colunas: `div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(5)) button`.
   - Modal estilizado aceitando ambos os seletores: `div[data-testid="stModal"]` e `div[data-testid="stDialog"]`.

---

## Caso 7: Botão "Personalizar Colunas" sem Estilo (Seletor `button[key=...]`)

* **Data:** 24/09/2026
* **Componentes Afetados:** `assets/css/home.css`, `views/home.py`
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
O botão "Personalizar Colunas" aparecia como o botão branco padrão do Streamlit, esticado por toda a coluna, destoando do visual navy do projeto — embora `home.css` tivesse um estilo completo para ele (degradê navy, ícone de engrenagem, largura automática).

### 🔍 Causa Raiz
Todas as regras usavam `button[key="btn_abrir_modal_colunas"]`. O parâmetro `key` do `st.button` fica só no Python: o Streamlit **não** escreve esse atributo no HTML. O seletor nunca casava e o navegador ignorava a regra em silêncio.

### ✅ Solução Adotada
Mirar a linha pelo título que está ao lado do botão, cuja classe existe de fato no HTML:
```css
/* "o botão que está na mesma linha do título da carteira" */
div[data-testid="stHorizontalBlock"]:has(.carteira-header-title) div[data-testid="stButton"] button { ... }
```
O modal não é afetado: no 1.36 ele é desenhado fora da linha (no fim da página, via portal do baseweb). As regras dos botões **dentro** do modal ainda usam `button[key=...]` e continuam sem efeito — mantidas de propósito, pois o visual atual do modal foi aprovado.

**Regra geral:** para estilizar um widget nativo, ancore o seletor em uma classe HTML própria vizinha (via `:has(...)`) ou em `data-testid`; nunca em `key`.

---

## Caso 8: Barra de Rolagem Vertical na Barra de Navegação (`overflow-x: auto`)

* **Data:** 24/09/2026
* **Componentes Afetados:** `assets/css/base.css` (`.atlas-navbar-inner`)
* **Tecnologia:** CSS (comportamento padrão dos navegadores)

### 🛑 Contexto e Sintoma
Apareceu uma barra de rolagem **vertical** no lado direito da barra de navegação superior, embora a regra pedisse só rolagem **horizontal** (`overflow-x: auto`, para telas estreitas).

### 🔍 Causa Raiz
Pela especificação do CSS, quando um eixo recebe `overflow` diferente de `visible`, o outro eixo deixa de ser `visible` e vira `auto`. O traço do item ativo fica 1px abaixo da faixa (`bottom: -1px`, para cobrir a linha cinza); esse 1px passou a contar como conteúdo "vazando" na vertical e o navegador desenhou a barra de rolagem.

### ✅ Solução Adotada
Remover o `overflow-x: auto` da `.atlas-navbar-inner` (os itens cabem na largura das telas em uso). Regra geral: ao usar `overflow-x`/`overflow-y`, lembre que o outro eixo muda junto; elementos posicionados para fora da caixa (traços, sombras, `::after`) passam a gerar rolagem.

---

## Caso 9: `select_slider` de Faixa Perde a Segunda Alça e Faixa "Completa" que Vira Filtro

* **Data:** 25/09/2026
* **Componentes Afetados:** `views/home.py`, `.streamlit/config.toml`
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
1. Sliders de faixa (CAPEX, OPEX, IC) inicializados só por `st.session_state[chave] = (min, max)`, sem `value=`, quebravam no segundo rerun com `TypeError: 'float' object is not iterable`: o widget passou a devolver um número só.
2. Com a faixa completa na Carteira Recomendada (IC 0,06–0,48), trocar para a de Análise (IC 0,04–0,50) escondia empreendimentos: a faixa antiga continuava válida nos novos degraus e passava a filtrar.

### 🔍 Causa Raiz
1. O `select_slider` decide se é faixa olhando **apenas o parâmetro `value`** (`_is_range_value(value)`), não o valor em `session_state`. Sem `value=`, é slider simples.
2. Os limites do slider dependem da carteira; "faixa completa" de uma carteira não é a completa da outra.

### ✅ Solução Adotada
1. Passar sempre `value=(opcoes[0], opcoes[-1])` e manter o valor atual/da URL em `st.session_state`. Como o Streamlit avisa quando os dois coexistem, `.streamlit/config.toml` tem `[global] disableWidgetStateDuplicationWarning = true`.
2. `_preparar_faixa` guarda a faixa completa da última carteira (`_filtro_<param>_padrao`); se o slider estava nela, passa para a faixa completa da nova carteira.
3. Os filtros usam o valor **devolvido pelo widget**, não o que foi preparado antes dele.

---

## Caso 10: Prefixo de Arquivo do ETL Capturando o Arquivo Errado

* **Data:** 25/09/2026
* **Componentes Afetados:** `scripts/process_data.py`
* **Tecnologia:** `pandas`

### 🛑 Contexto e Sintoma
Ao chegar o novo `priorizacao_peltlp_vw_dadosgerais_plataformaonline_*.csv`, a regra antiga da tabela mestra (prefixo `priorizacao`, último em ordem alfabética) passaria a escolher esse arquivo no lugar de `priorizacao202609091431.csv`, sem nenhum aviso.

### 🔍 Causa Raiz
Prefixos curtos casam com arquivos de outras consultas; `_` vem depois dos dígitos na ordem alfabética, então o arquivo novo "vence".

### ✅ Solução Adotada
Cada destino usa um prefixo que identifica a consulta de forma única (ex.: `priorizacao_peltlp_vw_dadosgerais`). Ao incluir um arquivo novo em `data/raw/`, confira na saída do ETL (`[LIDO] arquivo -> destino`) se cada destino leu o arquivo esperado.

---

## Caso 11: Servidor com Python Antigo e CSS Novo Após Editar o Código

* **Data:** 25/09/2026
* **Componentes Afetados:** `views/home.py`, `assets/css/home.css`
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
Depois de mover o "Limpar filtros" para a linha do título, o navegador mostrava o botão antigo ainda na linha de filtros e o "Personalizar Colunas" virado num círculo vazio, como se o estilo da vassoura tivesse caído no botão errado.

### 🔍 Causa Raiz
O servidor foi iniciado antes da edição. Os módulos Python já importados (`views/home.py`) continuaram na versão antiga, mas o CSS é relido do disco a cada execução (`inject_css`). Com o Python antigo a linha do título tinha 2 colunas, e a regra CSS da vassoura (`:nth-child(2)`) atingiu a coluna do "Personalizar Colunas".

### ✅ Solução Adotada
**Reiniciar o Streamlit** depois de mudar arquivos `.py` antes de conferir o visual (o "Rerun" da página não basta para módulos importados). Se o visual parecer misturar versão antiga e nova, desconfie primeiro de servidor desatualizado.

---

## Caso 12: Página "Dá um Tranco" a Cada Clique na Home (`st.empty` Vazio Durante o Rerun)

* **Data:** 25/09/2026
* **Componentes Afetados:** `views/home.py` (barra de navegação e botão do assistente)
* **Tecnologia:** `streamlit==1.36.0`

### 🛑 Contexto e Sintoma
Ao clicar no botão de limpar filtros (e em qualquer widget da Home), a página dava uma "flicada" para cima. Medindo no navegador: por ~150 ms a barra de navegação sumia, a página encolhia 16 px e a rolagem pulava de 381 para 365 e voltava.

### 🔍 Causa Raiz
A barra e o botão do assistente ficam em `st.empty()` criados no topo e preenchidos só no fim do script (os links precisam do estado já gravado na URL). A cada rerun o Streamlit troca o conteúdo antigo pelo placeholder **vazio** assim que passa por ele, e o espaço do elemento (16 px no fluxo da página) some até o fim do script.

### ✅ Solução Adotada
Desenhar a barra e o botão logo depois de criar os `st.empty()` (com os links da URL atual) e redesenhar no mesmo placeholder no fim, com os links atualizados. O espaço nunca fica vazio.

**Regra geral:** placeholder preenchido tarde deve receber um conteúdo provisório do mesmo tamanho logo ao ser criado. Obs.: o `AppTest` registra as duas escritas no placeholder; confira o último elemento.

---

## Caso 13: Clique em Gráfico Altair Quebra com "Selections are not yet supported for multi-view charts"

* **Data:** 28/09/2026
* **Componentes Afetados:** `views/bi.py` (matriz Impacto × Viabilidade e gráfico de eficiência)
* **Tecnologia:** Streamlit 1.36.0 + Altair 5.5

### 🛑 Contexto e Sintoma
A página de BI quebrava ao desenhar a matriz com `st.altair_chart(..., on_select="rerun")`. O gráfico era a soma de camadas (`linhas + textos + pontos`) para mostrar as linhas de corte da TIRM e os nomes das zonas.

### 🔍 Causa Raiz
No Streamlit 1.36 a seleção (clique) só funciona em gráfico de **uma única camada**. Qualquer composição (`+`, `|`, `&`, `layer`) com `on_select` levanta `StreamlitAPIException`.

### ✅ Solução Adotada
Manter um gráfico só de pontos e desenhar as referências de outro jeito:
```python
# as linhas de corte viram a grade do eixo X (só nos valores 0 e 11,2)
x=alt.X("tirm_pct:Q", axis=alt.Axis(values=[0, 11.2], grid=True, gridDash=[6, 4], gridColor=COR_NAVY))
```
Os nomes das zonas ficam num texto HTML acima do gráfico (`.bi-zonas`). Sem clique, camadas voltam a ser permitidas.

---

## Caso 14: Migração do Streamlit 1.36 para 1.51: Seletores CSS Renomeados

* **Data:** 30/09/2026
* **Componentes Afetados:** `assets/css/base.css`, `home.css`, `chatbot.css`, `bi.css`, `atlas.css`, `requirements.txt`
* **Tecnologia:** `streamlit==1.51.0` (antes 1.36.0), Python 3.12, `uv`

### 🛑 Contexto e Sintoma
Na troca de versão o Python rodou sem erro (só o aviso de `use_container_width`), mas parte do CSS deixaria de ter efeito: paginação e botões da linha do título da tabela, espaço do topo, barra de navegação, balões do chat. Também apareceram diferenças finas: subtítulo dos cabeçalhos mais fino e link do cartão do BI sublinhado.

### 🔍 Causa Raiz
O CSS depende de nomes internos (`data-testid`) que o Streamlit renomeou:

| 1.36 | 1.51 |
|---|---|
| `column` | `stColumn` |
| `element-container` | `stElementContainer` |
| `stAppViewBlockContainer` | `stMainBlockContainer` |
| `stModal` | `stDialog` |
| `chatAvatarIcon-user` / `-assistant` | `stChatMessageAvatarUser` / `Assistant` |
| `stDecoration` | não existe mais |

Além disso, o 1.51 carrega a fonte com peso 300 (o 1.36 caía no 400) e o estilo de link do markdown ganhou prioridade sobre `.bi-emp-link`.

### ✅ Solução Adotada
1. Conferir cada `data-testid` do CSS no código do frontend das duas versões (arquivos `streamlit/static/static/js/*.js` do pacote instalado): `grep -rlF '"stColumn"' .../static/js`. O que não existe mais foi trocado pelo nome novo.
2. `font-weight: 300` → `400` nos subtítulos dos cabeçalhos (mantém o visual aprovado); `a.bi-emp-link` para vencer o estilo de link do Streamlit.
3. `use_container_width=True` → `width="stretch"`.
4. Comparar capturas de tela das duas versões lado a lado (Playwright, dados sintéticos) antes de pedir a conferência no navegador.
5. Dependências: `requirements.txt` fixa os pacotes que afetam a tela; `requirements.lock.txt` (gerado com `uv pip compile --universal --python-version 3.12`) fixa tudo, igual no Windows e no Ubuntu 20.04 (glibc 2.31). **Atualização (30/09/2026):** o conteúdo do lock passou a ser o próprio `requirements.txt` e o `requirements.lock.txt` foi removido; instale com `uv pip install -r requirements.txt`.

---

## Caso 15: Ordenar a Tabela Recarregava a Página; `AppTest` Não Monta Componente v2

* **Data:** 30/09/2026
* **Componentes Afetados:** `views/home.py`, `assets/css/home.css`, teste automático (`docs/frontend.md`, 7.1)
* **Tecnologia:** `streamlit==1.51.0` (`st.components.v2`)

### 🛑 Contexto e Sintoma
1. A primeira versão da ordenação pelo cabeçalho usava links (`<a href="?ordem=...">`). Todo link recarrega a página: a tela inteira piscava e voltava ao topo a cada clique.
2. Ao trocar a tabela por um componente v2, o `AppTest` passou a falhar na Home com `TypeError: bad argument type for built-in operation` (em `bidi_component/main.py`, `js_content`), embora o app funcione no navegador.

### 🔍 Causa Raiz
1. `st.markdown` descarta JavaScript, então um clique no HTML só chegava ao Python por link (nova sessão). Botões do Streamlit não cabem dentro de uma tabela HTML.
2. O `AppTest` do 1.51 não monta componentes v2 (reproduzido com um componente mínimo, fora do nosso código).

### ✅ Solução Adotada
1. A tabela passou a ser exibida por `st.components.v2.component(...)` com `isolate_styles=False`: o HTML fica na própria página (o CSS da Home vale), e um script de poucas linhas chama `setTriggerValue("ordenar", {coluna, t: Date.now()})` no clique do `<th data-ordem>`. O `Date.now()` faz o segundo clique na mesma coluna também contar. O callback `on_ordenar_change` atualiza `st.session_state["home_ordem"]`; a URL é gravada como os filtros. Conferido no navegador (Playwright): um marcador em `window` sobrevive ao clique (não recarrega) e a rolagem não se move.
2. No teste automático, substituir o componente por `st.markdown` antes de rodar: `views.home._tabela_home = lambda data, **kw: st.markdown(data, unsafe_allow_html=True)`.

---

## Caso 16: Lista do Filtro (`st.multiselect`) Não Fecha ao Clicar de Novo na Caixa

* **Data:** 30/09/2026
* **Componentes Afetados:** `views/home.py` (filtros de seleção múltipla), `assets/css/home.css`
* **Tecnologia:** `streamlit==1.51.0` (Select do BaseWeb; `st.components.v2`)

### 🛑 Contexto e Sintoma
Abrir o filtro Setor, marcar "Ferroviário" e clicar de novo na caixa ou na setinha não fechava a lista: era preciso clicar num espaço vazio da página. Às vezes, logo depois de marcar um item, o clique fechava; em seguida, não.

### 🔍 Causa Raiz
O multiselect usa o Select do BaseWeb com busca: clicar no controle com a lista aberta mantém a lista aberta. O único gatilho de fechar confiável é o **clique fora**. Testado no navegador (Playwright): `blur()` no campo e tecla `Escape` simulada **não** fecham; um `click` simulado em `document.body` fecha. CSS não resolve.

### ✅ Solução Adotada
Script `_JS_FILTROS` em `views/home.py`, instalado por um componente v2 que não desenha nada (`_filtros_toggle`, chamado logo após o `inject_css`):
1. No `mousedown` (fase de captura) sobre a caixa de um multiselect **aberto** (`input[aria-expanded="true"]`), bloqueia o evento para o Streamlit não reabrir a lista. O "x" dos itens e o "limpar tudo" são ignorados.
2. No `click` seguinte, bloqueia o clique e dispara `document.body.dispatchEvent(new MouseEvent("click", {bubbles: true}))`, o mesmo que clicar fora.

**Armadilhas:** o script roda a cada rerun, por isso se protege com `window.__atlasFiltrosToggle` para instalar os ouvintes uma vez só. O contêiner vazio do componente somava 16px de espaçamento no topo: `.st-key-filtros_toggle { display: none; }` resolve e o script continua rodando. Como na tabela (caso 15), o `AppTest` não monta o componente: no teste, `home_view._filtros_toggle = lambda **kw: None`. Ao atualizar o Streamlit, confira `[data-baseweb="select"]`, `[data-baseweb="tag"]` e `aria-expanded`.

---

## 📝 Modelo de Registro para Novos Casos

Sempre que documentar um novo erro, utilize o padrão abaixo:

```markdown
## Caso X: [Título Resumido do Erro]

* **Data:** DD/MM/AAAA
* **Componentes Afetados:** `caminho/do/arquivo.py`
* **Tecnologia:** [Nome e versão da lib]

### 🛑 Contexto e Sintoma
[Descrição clara do comportamento observado e onde ocorreu]

### 🔍 Causa Raiz
[Explicação técnica do porquê o problema aconteceu]

### ✅ Solução Adotada
[Passo a passo da correção implementada, com trechos de código de exemplo]
```
