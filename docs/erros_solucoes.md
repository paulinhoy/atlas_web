# 🛠️ Base de Conhecimento: Erros, Diagnósticos e Soluções (Atlas Web)

Este documento registra o histórico de problemas técnicos complexos, comportamentos não triviais de bibliotecas e as soluções adotadas no projeto **Atlas Web**. 

> **Regra do Projeto:** Sempre que um erro complexo ou peculiar (com potencial de impacto futuro) for solucionado, este arquivo deve ser atualizado logo após o push ou merge na branch `main`.

---

## 📋 Índice de Casos Registrados

1. [Parser Markdown do Streamlit Exibindo Tags HTML Cruas (`<pre><code>`)](#caso-1-parser-markdown-do-streamlit-exibindo-tags-html-cruas-precode)
2. [Bloqueio de Navegação por Links Dentro de `components.html` (Sandbox de IFrame)](#caso-2-bloqueio-de-navegação-por-links-dentro-de-componentshtml-sandbox-de-iframe)
3. [Codificação Dupla (Mojibake) em Exportações de Banco PostGIS](#caso-3-codificação-dupla-mojibake-em-exportações-de-banco-postgis)
4. [Persistência de Query Params na URL ao Voltar do Atlas para a Home](#caso-4-persistência-de-query-params-na-url-ao-voltar-do-atlas-para-a-home)

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
