# Frontend do Atlas Web — Guia para alterações de UI

Guia de referência para quem (pessoa ou agente) for mexer na interface. Leia antes de alterar qualquer coisa em `views/`, `assets/css/` ou `services/map_service.py`.

> **Escopo:** Home (`views/home.py`), Ficha do empreendimento (`views/atlas.py`), tela do chatbot (`views/chatbot.py`) e Mapa (`services/map_service.py`).
> A **lógica** do chatbot (`services/chatbot_service.py`, `services/chat_logger.py`) está em desenvolvimento — não mexa nela sem pedido explícito. A tela do chatbot segue as mesmas regras de UI deste guia.

---

## 1. Contexto do produto (orienta todas as decisões)

- Visualização simples dos resultados do estudo do PELTMG. Dados **estáticos**, vindos de CSV, atualizados **no máximo uma vez por ano**.
- Poucos usuários. Objetivo: **manutenção praticamente zero** e **modularidade** (novas páginas/dados devem ser fáceis de adicionar).
- Prefira sempre a solução mais simples e centralizada. Refatorações de UI devem manter **o visual e o comportamento idênticos**, a menos que a mudança visual seja o pedido.

---

## 2. Ambiente — leia antes de rodar qualquer coisa

| Item | Valor |
|---|---|
| Versão do Streamlit | **1.36.0** (fixada em `requirements.txt`) |
| Ambiente virtual | `.venv/` na raiz. **Use sempre** `.venv/Scripts/python.exe` (Windows) |
| Rodar o app | `.venv/Scripts/python.exe -m streamlit run app.py` |

⚠️ O Python global da máquina de desenvolvimento pode ter outra versão do Streamlit (ex.: 1.52) e **não tem** `folium`. Rodar fora do `.venv` quebra o mapa e **muda o visual**, porque parte do CSS depende da estrutura interna do Streamlit 1.36 (ver seção 8).

---

## 3. Mapa dos arquivos de UI

```
app.py                      Roteamento pela URL (?id=123 → ficha; ?page=chatbot → chatbot; ?page=bi → BI; vazio → Home)
views/
├── ui.py                   inject_css()/read_css() + componentes comuns (render_navbar, render_back_button)
├── estado_url.py           Estado da Home (filtros, página, colunas) guardado na URL — ver seção 5.9
├── home.py                 Tela inicial: KPIs, filtros, tabela, paginação, modal de colunas
├── atlas.py                Ficha do empreendimento: cabeçalho, metadados, mapa, 4 tabelas
├── chatbot.py              Tela do assistente virtual (a lógica fica em services/chatbot_service.py)
└── bi.py                   Painel de Indicadores & BI (provisório: "em construção")
services/
├── map_service.py          Mapa Folium da ficha + aviso "sem geometria"
├── formatters.py           Formatação brasileira (R$, %, milhar, datas) — use sempre na UI
└── data_loader.py          Leitura dos parquets com cache (não é UI, mas as views dependem dele)
assets/css/
├── base.css                Tokens de cor + componentes compartilhados (carregado em TODAS as páginas)
├── home.css                Estilos exclusivos da Home
├── atlas.css               Estilos exclusivos da Ficha (inclui o aviso do mapa)
├── chatbot.css             Estilos exclusivos do chatbot (cabeçalho, balões, campo de digitação)
├── bi.css                  Estilos da página de BI (hoje só o aviso "em construção")
└── sortable_modal.css      Estilos do componente de arrastar colunas (roda dentro de um iframe)
```

---

## 4. Como a UI foi construída

### 4.1 Renderização
O Streamlit gera os widgets (selectbox, botões, text_input). Todo o resto (cabeçalhos, cards, tabelas, badges) é **HTML montado em strings Python** e exibido com:

```python
st.markdown(html, unsafe_allow_html=True)
```

Não usamos `st.dataframe` na tabela principal porque precisamos de badges coloridos, links e o layout do PELTMG.

### 4.2 Como o CSS chega à página
Cada página chama `inject_css` no início do seu `render()`:

```python
# views/home.py
def render():
    inject_css("home")      # injeta base.css + home.css

# views/atlas.py
def render(empreendimento_id):
    inject_css("atlas")     # injeta base.css + atlas.css
```

`views/ui.py` lê os arquivos e injeta um único bloco `<style>`:

```python
def inject_css(*page_styles: str) -> None:
    css = "\n".join(read_css(n) for n in ("base", *page_styles))
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)
```

A ordem importa: `base.css` vem **primeiro**; o CSS da página vem **depois** e pode sobrescrever/complementar o base.

### 4.3 Tokens de design (variáveis de cor)
Definidos no topo de `assets/css/base.css`. **Use sempre `var(--nome)` em vez de códigos hex novos:**

| Token | Valor | Uso |
|---|---|---|
| `--navy` | `#0b2545` | Azul institucional: cabeçalhos de tabela, títulos, botões |
| `--navy-2` | `#133b63` | Fim do degradê dos cabeçalhos; hover |
| `--navy-3` | `#134074` | Fim do degradê dos botões |
| `--blue-accent` | `#1d4ed8` | Destaque em hover (links, degradês) |
| `--pelt-teal` / `--pelt-lilac` | `#BAD6D9` / `#9BA0BF` | Tons claros da paleta PELT: borda dos botões flutuantes, balões do chatbot |
| `--text` / `--text-2` / `--text-3` | `#0f172a` / `#334155` / `#475569` | Texto principal → secundário |
| `--muted` / `--muted-2` | `#64748b` / `#94a3b8` | Textos auxiliares, legendas |
| `--border` / `--border-2` | `#e2e8f0` / `#cbd5e1` | Bordas |
| `--bg-soft` / `--bg-soft-2` | `#f8fafc` / `#f1f5f9` | Fundos claros, linhas zebradas |
| `--grad-header`, `--grad-header-hover` | degradês navy | Cabeçalhos e botões flutuantes |
| `--grad-button`, `--grad-button-hover` | degradês navy | Botões de ação (Salvar do modal). O botão "Personalizar Colunas" usa navy sólido a 80% (`rgba(11, 37, 69, 0.8)`) |
| `--font-mono` | pilha monoespaçada | Números (índice IC, valores) |
| `--navbar-height` | `42px` | Altura da barra de navegação; o topo do conteúdo é calculado a partir dela |

O tema base do Streamlit (cores de widgets nativos) fica em `.streamlit/config.toml` e usa os mesmos valores (`primaryColor = "#0b2545"`).

### 4.4 Catálogo de classes

**`base.css` (todas as páginas)**
| Classe | O que é |
|---|---|
| `.atlas-navbar`, `.atlas-navbar-inner`, `.atlas-navbar-item` (`.is-active`), `.atlas-navbar-sep` | Barra de navegação superior fixa; também esconde a faixa nativa do Streamlit (`stHeader`) e ajusta o topo do conteúdo |
| `.atlas-floating-back-btn` / `.atlas-floating-chat-btn` | Botões flutuantes "Voltar" (esquerda) e "Assistente Virtual" (direita); `.back-arrow` é a seta do Voltar |
| `.home-atlas-table`, `.atlas-table` | Estrutura comum das tabelas (cabeçalho navy, zebra, alinhamento) |
| `.font-mono` (dentro das tabelas) | Números em fonte monoespaçada |
| `.home-atlas-table .badge`, `.fonte-badge` | Base dos badges; `.badge-fed` e `.fonte-badge` compartilham o azul |

**`home.css`**
| Classe | O que é |
|---|---|
| `.main-header`, `.main-header-row`, `.header-title`, `.header-subtitle` | Cabeçalho institucional |
| `.kpi-card`, `.kpi-title`, `.kpi-value`, `.kpi-subtext` | Cartões de indicadores |
| `.home-atlas-table …` | Complementos da tabela da Home (padding, hover, links `.emp-link`, botão `.btn-action`) |
| `.badge-high/-med/-low/-neutral/-est/-mun/-priv` | Cores dos badges |
| `.tl`, `.tc`, `.tr` | Alinhamento de célula: esquerda / centro / direita |
| `.filter-panel-*` | Título do painel de filtros |
| `.carteira-header-title` | Título acima da tabela |
| `.divider-light`, `.divider-navy` | Linhas separadoras |
| `.pagination-info`, `.pagination-size-label`, `.pagination-ellipsis` | Textos da paginação |
| `.modal-hint` | Texto de instrução do modal de colunas |
| Seletores `div[data-testid=...]` | Estilização de widgets nativos do Streamlit (inputs, selects, botões da paginação e do modal) |

**`atlas.css`**
| Classe | O que é |
|---|---|
| `.atlas-header` (+ `h2`, `.sub`) | Cabeçalho da ficha |
| `.meta-card`, `.meta-row`, `.meta-label`, `.meta-value` | Painel de metadados (altura fixa 520px) |
| `.map-placeholder`, `.map-placeholder-icon` | Aviso "sem geometria" (altura 520px, alinhado ao metadados) |
| `.section-title`, `.section-title--badge` | Título de seção; `--badge` alinha um badge à direita |
| `.atlas-table …` | Complementos das tabelas da ficha (`.tl`/`.tr` com `!important`, `.text-left`/`.text-right`) |
| `.obras-scroll` | Contêiner com rolagem e cabeçalho fixo da tabela de obras |
| `.fonte-badge` | Badge "Fonte: …" nos títulos de seção |
| `.legenda-*` | Legenda QGIS (código preservado, hoje desativado) |
| Seletores `iframe` / `stCustomComponentV1` | Altura e borda do mapa (520px) |

---

## 5. Receitas de alterações comuns

### 5.1 Mudar uma cor do sistema
Edite só o token em `assets/css/base.css`:
```css
:root {
    --navy: #0b2545;   /* troque aqui; tudo que usa var(--navy) acompanha */
}
```
Se a cor também aparece em widgets nativos, ajuste `primaryColor` em `.streamlit/config.toml`.
⚠️ `sortable_modal.css` **não enxerga os tokens** (roda dentro de um iframe) — atualize os hex dele manualmente.

### 5.2 Estilizar um elemento novo
1. No Python, dê uma **classe** ao elemento (nunca `style="..."`):
   ```python
   st.markdown('<div class="aviso-dados">Dados atualizados em 2026</div>', unsafe_allow_html=True)
   ```
2. No CSS da página (`home.css` ou `atlas.css`), defina a classe usando tokens:
   ```css
   .aviso-dados {
       color: var(--muted);
       font-size: 13px;
   }
   ```
3. Se a classe for usada em **mais de uma página**, coloque-a em `base.css`.

Exceção aceita: as larguras de coluna (`th_style`) em `AVAILABLE_COLUMNS` ficam no Python, porque fazem parte da configuração da coluna.

### 5.3 Criar uma página (view) nova
1. Crie `views/minha_view.py` com uma função `render()` que começa com `inject_css("minha_view")` e `render_navbar("minha_view")`.
2. Crie `assets/css/minha_view.css` (pode começar vazio — cores, tabelas e botões flutuantes já vêm do `base.css`).
3. Registre a rota em `app.py` (hoje é um `if/elif` sobre `st.query_params`):
   ```python
   elif page == "minha_view":
       minha_view.render()
   ```
4. Para aparecer na barra de navegação, acrescente uma linha em `NAV_ITENS` (`views/ui.py`) e crie o link em `views/estado_url.py` (ex.: `def link_minha_view(): return _link(page="minha_view")`).
5. Para voltar à Home, chame `render_back_button()` de `views/ui.py` — ele já devolve os filtros da Home (seção 5.9). Nunca use `href="?"` fixo: isso apaga os filtros do usuário.
6. Reaproveite `.atlas-table` para tabelas simples e `.section-title` para títulos (se a página não carregar `atlas.css`, mova essas classes para `base.css`).

### 5.4 Adicionar uma coluna na tabela da Home
Uma entrada em `AVAILABLE_COLUMNS` (`views/home.py`). Ela aparece automaticamente no modal "Personalizar Colunas":
```python
"tirm": {
    "label": "TIRM",                 # rótulo ÚNICO (o modal usa o rótulo como chave)
    "th_class": "tr",                # alinhamento do cabeçalho: tl / tc / tr
    "th_style": "text-align: right;",
    "td_class": "tr font-mono",      # alinhamento/estilo da célula
    "render": lambda r: fmt_pct_br(r.get("tirm")),   # r = linha do DataFrame
},
```
- Importe o formatador usado no topo de `home.py` (hoje só `fmt_int_br` e `fmt_bilhoes_br` são importados).
- Para exibir por padrão, inclua o id em `DEFAULT_ACTIVE_COLUMNS`.
- A coluna precisa existir em `empreendimentos_priorizacao.parquet`. Dados de outro parquet exigem merge antes de renderizar.
- Texto vindo dos dados **sempre** passa por `html_mod.escape(...)` (ou por um formatador de `services/formatters.py`).

### 5.5 Adicionar/alterar um badge colorido
Edite `BADGE_RULES` em `views/home.py`. Cada regra: *(trechos de texto a procurar, classe CSS)*. A primeira que casar vence; nada casou → `badge-neutral`.
```python
BADGE_RULES = {
    "impacto": [(("alto",), "badge-high"), (("médio", "medio"), "badge-med"), (("baixo",), "badge-low")],
    "status":  [(("concluído", "concluido"), "badge-high"), (("em obras",), "badge-med")],   # exemplo novo
}
```
Use com `_render_badge("status", r.get("descr_status_empreendimento"))`. Uma cor nova de badge = uma classe `.home-atlas-table .badge-xxx` em `home.css`.

### 5.6 Adicionar um cartão de KPI
Acrescente uma tupla em `cards` dentro de `render_kpis` e ajuste `st.columns(4)` para o novo total:
```python
cards = [
    ("Empreendimentos Priorizados", fmt_int_br(total_emp), "Carteira avaliada"),
    ...
    ("Extensão Total", fmt_decimal_br_2(km_total), "Km"),   # novo
]
```

### 5.7 Tabelas da ficha (`atlas.py`)
Seguem o mesmo molde: título `.section-title` + `<table class="atlas-table">`. A tabela de alocação escolhe fonte e colunas por setor em `render_tabela_alocacao` (cadeia `if/elif` com `col_map = {"Rótulo": "coluna_no_parquet"}`) — para um setor novo, adicione um ramo com seu `col_map`.

### 5.8 Mapa
Tudo em `services/map_service.py` (`render_map(id)`). Cores das linhas/pontos estão nos `style_function`/`CircleMarker`; altura em `folium_static(m, height=510)` casada com os 520px do CSS (`.meta-card`, `.map-placeholder`, regras de `iframe` em `atlas.css`). **Se mudar a altura, mude nos quatro lugares.**

### 5.9 Estado da Home na URL (filtros, página, colunas)
Links recarregam a página e zeram a sessão; a URL sobrevive. `views/estado_url.py` faz a ponte:

- **Início da sessão:** `semear_widget(chave, param, opcoes)` coloca o valor da URL no widget **se for válido** (senão ignora).
- **Toda execução:** `estado_url.gravar(valores, padroes)` escreve o estado na URL sem recarregar; valores iguais ao padrão ficam fora (URL limpa).
- **Links:** `link_empreendimento(id)`, `link_chatbot()`, `link_home()` montam o `href` com o estado atual.

Parâmetros atuais: `carteira` (recomendada/otimizada/completa), `q` (busca), `setor`, `esfera`, `classificacao`, `viabilidade`, `origem`, `vocacao`, `pg`, `itens`, `cols` (ids separados por vírgula).
Exemplo: `?id=1042&carteira=completa&setor=Rodoviário&q=BR&pg=2`.

**Para incluir um filtro novo na Home:**
1. Antes do widget: `estado_url.semear_widget("filtro_novo", "novo", opcoes)` (sem `opcoes` para campos de texto livre).
2. Inclua `"novo": filtro_novo` no dicionário de `estado_url.gravar(...)` e o valor padrão em `padroes`.
3. Inclua o filtro na tupla `assinatura` (para a listagem voltar à página 1 quando ele mudar).

A troca de qualquer filtro volta a paginação para a página 1.

---

## 6. Regras para não quebrar nada

1. **Nada de CSS no Python.** Nem bloco `<style>`, nem `style="..."`. Classe no HTML, regra em `assets/css/`.
2. **Não renomeie classes existentes** sem trocar todas as ocorrências em `views/` e `services/` (use busca por texto). CSS não avisa quando uma classe deixa de existir — o elemento só perde o estilo em silêncio.
3. **Escape de HTML:** qualquer valor vindo dos dados vai em `html_mod.escape()` antes de entrar numa string HTML.
4. **Formatação numérica** sempre pelos helpers de `services/formatters.py` (`fmt_brl`, `fmt_int_br`, `fmt_pct_br`, …).
5. **Classes de uma página só** ficam no CSS da página. Colocar em `base.css` faz a regra valer em todas — confira se o nome não colide com algo de outra tela.
6. **Não altere o DataFrame geoespacial** retornado por `data_loader.get_empreendimento_geo()` (é compartilhado entre usuários; use `.copy()` se precisar).
7. **Fins de linha:** `app.py`, `views/atlas.py` e `services/map_service.py` usam CRLF. Scripts que reescrevem arquivos devem preservar isso para não gerar diffs gigantes.
8. **Não mexa na lógica do chatbot** (`services/chatbot_service.py`, `services/chat_logger.py`) sem pedido explícito.
9. **Links internos** (`<a href>`) sempre por `estado_url.link_empreendimento()`, `link_chatbot()`, `link_home()` ou `render_back_button()`; nunca `?id=...` ou `?` escritos à mão.

---

## 7. Como verificar uma alteração

### 7.1 Teste automático (sem navegador)
O Streamlit renderiza as páginas em memória com `AppTest`. Salve como script temporário e rode com o Python do `.venv`:

```python
# smoke_ui.py — rode com: PYTHONPATH=. .venv/Scripts/python.exe smoke_ui.py
from streamlit.testing.v1 import AppTest

def run(params=None):
    at = AppTest.from_file("app.py", default_timeout=120)
    for k, v in (params or {}).items():
        at.query_params[k] = v
    at.run()
    return at

home = run()
assert not home.exception, home.exception
home.button(key="btn_abrir_modal_colunas").click().run()   # modal de colunas
assert not home.exception
home.button(key="btn_pg_2").click().run()                   # paginação
assert not home.exception

for params in [{"page": "bi"}, {"page": "chatbot"}]:     # barra de navegação nas outras telas
    assert not run(params).exception

for eid in ["1938", "726", "1042", "721", "1886", "707"]:  # um por setor + um sem geometria
    at = run({"id": eid})
    assert not at.exception, (eid, at.exception)
print("OK")
```

O AppTest pega erros de Python e confirma o conteúdo gerado, **mas não mostra o visual**.

### 7.2 Conferência visual (obrigatória para mudanças de estilo)
Rode o app pelo `.venv` e confira no navegador: barra de navegação (destaque da tela aberta), Home (KPIs, filtros, tabela, paginação, modal "Personalizar Colunas") e uma ficha com mapa e outra sem geometria.

### 7.3 Refatorações que prometem "visual idêntico"
Compare as declarações CSS efetivas antes/depois por seletor (resolvendo `var(--…)`), e o HTML gerado pelas funções de renderização contra a versão anterior (`git show main:views/home.py`). Foi assim que a centralização do CSS foi validada.

---

## 8. Armadilhas conhecidas

| Problema | Detalhe |
|---|---|
| **Seletores dependentes da versão do Streamlit** | A paginação usa `data-testid="column"` (1.36) e o alinhamento do mapa usa `data-testid="stColumn"` (1.37+). Com 1.36, as regras do mapa não se aplicam. Atualizar o Streamlit exige revisar todos os seletores `div[data-testid=...]`. |
| **`button[key="..."]` não funciona** | O Streamlit não coloca o atributo `key` no HTML do botão. O botão "Personalizar Colunas" é estilizado pela linha do título (`div[data-testid="stHorizontalBlock"]:has(.carteira-header-title)`). As regras `key` dos botões **dentro** do modal seguem sem efeito — mantidas porque o visual atual do modal está aprovado. Ver `docs/erros_solucoes.md`, caso 7. |
| **`onclick` em HTML é descartado** | `st.markdown` não executa JavaScript inline (ex.: `<tr onclick=...>` na tabela). Só links `<a href>` funcionam. |
| **Navegar reinicia a sessão** | Links `<a href>` recarregam a página e zeram o `st.session_state`. Por isso o estado da Home vive na URL (`views/estado_url.py`). O que ainda se perde ao navegar: o histórico de conversa do chatbot. |
| **Valor fora das opções derruba o selectbox** | Colocar em `st.session_state` um valor que não está nas `options` do selectbox gera `"... is not in iterable"` e a página quebra. Todo valor vindo da URL passa por `estado_url.ler(..., opcoes)`. |
| **Iframes não herdam CSS** | Componentes como `streamlit-sortables` e o mapa Folium rodam em iframe: o CSS da página e os tokens não chegam lá dentro. Por isso `sortable_modal.css` é passado via `custom_style=read_css("sortable_modal")` e usa cores literais. |
| **Barra de navegação e ordem de execução** | Na Home, a barra é desenhada num `st.empty()` preenchido **depois** de `estado_url.gravar(...)`; senão os links levariam os filtros da execução anterior. O mesmo vale para o botão flutuante do Assistente. |
| **Faixa nativa do Streamlit escondida** | `base.css` esconde `header[data-testid="stHeader"]` (menu ⋮, "Running…") e troca o `padding-top` de `stAppViewBlockContainer`. Ao atualizar o Streamlit, confira esses seletores. |
| **Cache após atualizar dados** | Os parquets ficam em cache; após trocar os arquivos em `data/processed/`, reinicie o servidor. |
| **Contagens fixas nos rótulos** | `"Carteira Recomendada (1.044)"` etc. em `views/home.py` são texto fixo — atualize na carga anual. |
