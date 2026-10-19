# Contexto

Estou construindo no QGIS (Atlas / Layout de impressão) uma ficha técnica por empreendimento do PELTMG (Plano Estadual de Logística e Transportes de Minas Gerais). A mesma ficha já existe numa aplicação web, e o QGIS deve reproduzir as mesmas colunas, fontes e regras. Os dados são os **mesmos arquivos Parquet** que a aplicação web usa, para as duas ficarem consistentes.

Abaixo está a especificação completa: de qual arquivo e coluna vem cada dado, como escolher quando há mais de uma fonte e como formatar.

- Uma página por empreendimento.
- A chave entre todos os arquivos é `id_empreendimento` (inteiro).
- Antes de propor a implementação, confirme comigo qualquer ponto ambíguo. Não invente regras que não estão aqui.

---

# 1. Arquivos de dados (Parquet)

| Arquivo | Chave | Conteúdo / uso na ficha |
|---|---|---|
| `carteiras.parquet` | `id_empreendimento` + `carteira` | Tabela mestra: dados gerais, metadados, notas, IC, viabilidade e TIRM. A coluna `carteira` vale `recomendada`, `otimizada` ou `analise`; o mesmo empreendimento pode aparecer em até 3 linhas (uma por carteira). |
| `resumo_financeiro.parquet` | `id_empreendimento` + `id_cenario` | Financeiro dos cenários Recomendado e Otimizado |
| `dados_financeiro.parquet` | `id_empreendimento` | Financeiro de reserva (Custo Econômico LP) |
| `alocacao_empreendimento.parquet` | `id_empreendimento` + `id_cenario` | Alocação 2055: rodoviário, ferroviário de cargas, hidroviário. Cenários 1, 2, 3, 4, 8 (Otimizado) e 10 (Recomendado) |
| `demanda_pax_aero_ano.parquet` | `id_empreendimento` + `id_cenario` | Alocação 2055 do aeroportuário |
| `demanda_duto_ano.parquet` | `id_empreendimento` (1 linha, sem cenário) | Alocação 2055 do dutoviário |
| `demanda_pax_ferro_ano.parquet` | `id_empreendimento` (1 linha, sem cenário) | Alocação 2055 do ferroviário de passageiros |
| `empreendimento_geo.parquet` | `id_empreendimento` | Mapa: geometrias em WKT, `geom_linha` (linhas) e `geom_ponto` (pontos) |
| `observacoes_empreendimentos.csv` (opcional) | `id_empreendimento` | Observação em texto livre (coluna `observacao`) |

Valores ausentes chegam como nulos. Anos (`data_inicio`, `data_conclusao`) chegam como número decimal (ex.: `2034.0`).

---

# 2. Registro base do empreendimento (precedência das carteiras)

Para cabeçalho, metadados, notas, viabilidade e TIRM, use **uma linha só** de `carteiras.parquet`, escolhida nesta ordem:

1. A linha com `carteira = 'recomendada'`, se existir. Nome da fonte: "Carteira Recomendada".
2. Senão, a linha com `carteira = 'otimizada'` ("Carteira Otimizada").
3. Senão, a linha com `carteira = 'analise'` ("Carteira de Análise"). Esta carteira contém todos os empreendimentos.

**Complemento das notas:** se, na linha escolhida, algum dos campos abaixo estiver nulo, use o valor da próxima carteira na ordem acima que o tenha preenchido:
`dimensao_estrategica`, `dimensao_financeira`, `dimensao_socioeconomica_pond`, `dimensao_comercial`, `dimensao_gerencial`, `ic_3_pond`, `impacto_avaliado_3_pond_cenario`.

Os demais campos vêm sempre da linha escolhida, sem complemento.

---

# 3. Seções da ficha

## 3.1 Cabeçalho
- Título: `{id_empreendimento} - {nome_empreendimento}`
- Subtítulo: `Setor: {setor} | Esfera: {esfera_acao}`

Setores (`id_setor` → `setor`): 1 Rodoviário, 2 Ferroviário, 3 Hidroviário, 4 Portuário, 5 Aeroportuário, 6 Dutoviário. Esferas: Federal, Estadual, Municipal.

## 3.2 Painel de metadados (lado esquerdo, ao lado do mapa)
Todos os campos vêm do registro base (seção 2):

| Rótulo | Coluna de `carteiras.parquet` | Formato |
|---|---|---|
| Origem | `origem_ajustada` | texto (ex.: PELT 2007, ANTT, DNIT, PNL 2035, DER-MG) |
| Status | `descr_status_empreendimento` | texto |
| Natureza | `natureza_empreendimento` | "Transporte de Cargas", "Transporte de Pessoas" ou "Transporte de Cargas e Pessoas" |
| Extensão (Km) | `extensao_km` | 2 casas decimais; "-" se nulo ou zero. **Use a extensão do empreendimento; não some a extensão das obras.** |
| Grupo de Modelagem | `grupo_modelagem` | texto |
| Resp. atual da infraestrutura | `responsavel_gestao_infraestrutura` | texto |
| Duração | `data_inicio` e `data_conclusao` | `{data_inicio} – {data_conclusao}` como anos inteiros (ex.: "2034 – 2064"); "-" se faltar um dos dois |


## 3.3 Tabela "Resultados da Priorização"
Título com um selo à direita: `Fonte: {Carteira Recomendada | Carteira Otimizada | Carteira de Análise}`, conforme a seção 2.

| Coluna | Coluna de `carteiras.parquet` | Casas decimais |
|---|---|---|
| Estratégica | `dimensao_estrategica` | 1 |
| Financeira | `dimensao_financeira` | 5 |
| Socioeconômica | `dimensao_socioeconomica_pond` | 5 |
| Comercial | `dimensao_comercial` | 4 |
| Gerencial | `dimensao_gerencial` | 4 |
| Índice de Classificação | `ic_3_pond` | 5 |
| Impacto | `impacto_avaliado_3_pond_cenario` (Alto / Médio / Baixo impacto) | texto |

## 3.4 Tabela "Dados Financeiros — Mês Base: ago/24"
O mês base é **fixo para todos os empreendimentos: agosto de 2024** (`2024-08-01`), exibido como "ago/24".

**Escolha da fonte, em ordem:**
1. `resumo_financeiro.parquet` com `id_cenario = 10` → "Cenário Recomendado"
2. Senão, `resumo_financeiro.parquet` com `id_cenario = 8` → "Cenário Otimizado". **Se não houver cenário 8, use `id_cenario = 7`**, que é a numeração antiga do Otimizado; o arquivo atual ainda usa o 7.
3. Senão, `dados_financeiro.parquet` → "Custo Econômico LP"

| Coluna | Fontes 1 e 2 (`resumo_financeiro.parquet`) | Fonte 3 (`dados_financeiro.parquet`) |
|---|---|---|
| CAPEX (R$) | `capex` | `capex_empreendimento_atualizado` |
| OPEX (R$) | `opex` | `opex_empreendimento_atualizado` |
| Valor Total (R$) | CAPEX + OPEX (só quando os dois existem; senão "-") | idem |
| Receita Total (R$) | `receita_codemge` | `receita` |
| TIRM (%) | `tirm_codemge` (**já em %**: 5.44 significa 5,4%). Se nulo, `tirm` do registro base × 100 | `tirm` do registro base × 100 (**`tirm` está em fração**: 0.0527 significa 5,3%) |
| Viabilidade | `viabilidade` do registro base (Alta / Média / Baixa viabilidade, Não se aplica) | idem |

TIRM com 1 casa decimal e o símbolo "%".

## 3.5 Tabela "Dados de Alocação 2055" (depende do setor, da natureza e do grupo)
**Cenários exibidos:** só **1, 2, 3, 4, 8 e 10**, em ordem crescente. A coluna Cenário mostra 1, 2, 3, 4, **"8 (Otimizado)"** e **"10 (Recomendado)"**. Fontes sem cenário mostram uma única linha, sem a coluna Cenário.

**Ordem das regras:** avalie as regras abaixo nessa ordem; vale a primeira que se aplicar.

**Campos de decisão,** todos do registro base:
- `id_setor`;
- `natureza_empreendimento`: "Passageiros" significa exatamente "Transporte de Pessoas"; "Transporte de Cargas e Pessoas" conta como cargas;
- `id_grupo_modelagem`, número já calculado em `carteiras.parquet`:
  - 1 = "Caso geral - infraestruturas lineares";
  - 2 = "Caso geral - infraestruturas pontuais".

| # | Condição | Arquivo | Colunas (rótulo ← coluna) |
|---|---|---|---|
| 0 | `id_setor = 4` (Portuário) | — | **Tabela não exibida** |
| 1 | `id_setor = 1` (Rodoviário) | `alocacao_empreendimento.parquet` | Cenário ← `id_cenario`; Carga ← `flt_vehcargafuturo`; Ônibus ← `flt_vehonibusfuturo`; Automóvel ← `flt_vehautofuturo`; Total Veículos ← `flt_vehtotalfuturo`; TKU Total ← `flt_tkutotalfuturo` |
| 2 | `id_setor = 2` e Passageiros | `demanda_pax_ferro_ano.parquet` | Demanda Anual (Passageiros/Ano) ← `demanda_ano` (sem cenário) |
| 3 | `id_setor = 2`, cargas e `id_grupo_modelagem = 2` | `alocacao_empreendimento.parquet` (toneladas) | Cenário ← `id_cenario`; CGC ← `flt_toncgcfuturo`; CGNC ← `flt_toncgncfuturo`; GL ← `flt_tonglfuturo`; GSA ← `flt_tongsafuturo`; GSM ← `flt_tongsmfuturo`; OGSM ← `flt_tonogsmfuturo`; TON Total ← `flt_tontotalfuturo` |
| 4 | `id_setor = 2`, cargas e `id_grupo_modelagem = 1` | `alocacao_empreendimento.parquet` (TKU) | Cenário ← `id_cenario`; CGC ← `flt_tkucgcfuturo`; CGNC ← `flt_tkucgncfuturo`; GL ← `flt_tkuglfuturo`; GSA ← `flt_tkugsafuturo`; GSM ← `flt_tkugsmfuturo`; OGSM ← `flt_tkuogsmfuturo`; TKU Total ← `flt_tkutotalfuturo` |
| 5 | `id_setor = 3` (Hidroviário) | `alocacao_empreendimento.parquet` (toneladas) | Mesmas colunas da regra 3 |
| 6 | `id_setor = 5` (Aeroportuário) | `demanda_pax_aero_ano.parquet` | Cenário ← `id_cenario`; Demanda (Passageiros/Ano) ← `demanda_pax_ano` |
| 7 | `id_setor = 6` (Dutoviário) | `demanda_duto_ano.parquet` | Tonelada Total ← `volume_2055`; TKU Total ← `tku` (sem cenário) |
| 8 | Qualquer outro caso (ex.: ferroviário de cargas com grupo diferente de 1 e 2) | `alocacao_empreendimento.parquet` (TKU) | Mesmas colunas da regra 4 |

Os valores são inteiros com separador de milhar, e as casas decimais são **truncadas**: 1234,9 vira "1.234". Se não houver linha para o empreendimento, mostrar "Sem dados de alocação para este empreendimento."

---

# 4. Formatação (padrão brasileiro)
- Milhar com ponto e decimal com vírgula: `1.682`, `0,40310`.
- Moeda: `R$ 289.892.422,00` (2 casas).
- Percentual: `5,4%`.
- Mês base: `ago/24`.
- Qualquer dado ausente aparece como hífen `-` (nunca "N/D", "N/A", "nan" ou "NULL").
- Tom institucional: sem emojis.

---

# 5. Pontos de atenção (casos de borda conhecidos)
1. **Aeroportuário:** `demanda_pax_aero_ano.parquet` tem cenários 0 a 5, mas a ficha mostra só os da lista 1, 2, 3, 4, 8, 10. Na prática aparecem os cenários 1 a 4.
2. **Ferroviário com natureza "Transporte de Cargas e Pessoas"** é tratado como cargas (regras 3, 4 ou 8).
3. **Grupo "Caso geral - transporte ferroviário de pessoas" (id 9):** a regra de passageiros olha a **natureza**, não o grupo. Um ferroviário desse grupo cuja natureza não seja "Transporte de Pessoas" cai na regra 8.
4. **Portuário (id_setor 4)** não tem tabela de alocação; o Hidroviário (3) tem.
5. **TIRM em duas unidades:** `tirm_codemge` (`resumo_financeiro.parquet`) já está em %; `tirm` (`carteiras.parquet`) está em fração e precisa ser multiplicada por 100.
6. **Cenário Otimizado:** é o 8 em `alocacao_empreendimento.parquet`; em `resumo_financeiro.parquet` ainda é o 7 (numeração antiga). Por isso a regra financeira aceita 8 e, na falta dele, 7.

