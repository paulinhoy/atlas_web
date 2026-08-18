# 🏗️ Análise Arquitetural e Planejamento de Deploy — Atlas Web (PELTMG / CODEMGE)

**Contexto do Deploy:** Ubuntu Server · Nginx (reverse proxy) · Dados em disco local (.parquet) · 4–8 GB RAM

---

## 1. Inventário do Estado Atual

| Componente | Tecnologia | Observação |
|:---|:---|:---|
| Framework Web | Streamlit 1.36.0 (versão travada) | Single-process, multi-thread |
| Dados | Parquet em disco (Snappy) | 6 arquivos, **~116 MB** total |
| Geoespacial | Folium + Shapely + GeoPandas | Parsing WKT em runtime |
| Cache | `@st.cache_data` | Copia dados por chamada |
| Autenticação | **Nenhuma** | Acesso aberto |

### Inventário dos Dados em Disco

| Arquivo Parquet | Tamanho | Uso |
|:---|---:|:---|
| `empreendimento_geo.parquet` | **108.8 MB** | Geometrias WKT (linhas + pontos) |
| `alocacao_empreendimento.parquet` | 1.3 MB | Alocação por cenário |
| `obras_priorizacao.parquet` | 525 KB | Cadastro de obras |
| `custo_obra.parquet` | 519 KB | Custos detalhados |
| `empreendimentos_priorizacao.parquet` | 169 KB | Tabela mestra (~1.682 registros) |
| `dados_financeiro.parquet` | 96 KB | CAPEX/OPEX/Receita |

> ⚠️ **Importante:** O arquivo de geometrias representa **99%** da massa de dados. Todas as otimizações de memória devem focar nele prioritariamente.

---

## 2. Bloco 1 — Memória e Performance (Crítico para 4–8 GB)

### 2.1 `@st.cache_data` vs `@st.cache_resource`

* **Situação atual:** Todos os DataFrames são carregados com `@st.cache_data`. Este decorator **serializa e desserializa** uma cópia do dado a cada chamada de função — é seguro contra mutações, mas mais lento e consome mais memória temporária durante a cópia.
* **Alternativa:** `@st.cache_resource` mantém o **mesmo objeto em memória** compartilhado entre todas as sessões. Zero cópias, zero overhead de serialização.

| Aspecto | `@st.cache_data` (atual) | `@st.cache_resource` |
|:---|:---|:---|
| Cópias em memória | Sim (1 por chamada) | Não (objeto compartilhado) |
| Segurança contra mutação | ✅ Automática | ⚠️ Precisa disciplina no código |
| Overhead de RAM por sessão | Alto (~110 MB para geo) | Praticamente zero |
| Velocidade da 2ª+ chamada | Mais lenta (desserializa) | Instantânea |

* **Recomendação:** Trocar para `@st.cache_resource` nos dados read-only pesados (geo, empreendimentos, obras) e manter disciplina de visualização sem mutação in-place.

---

### 2.2 Projeção de Colunas no Parquet Geoespacial

* **Situação atual:** `pd.read_parquet(file_path)` carrega **TODAS** as colunas do arquivo de 108 MB.
* **Problema:** O `map_service.py` usa apenas 4 colunas: `id_empreendimento`, `geom_linha`, `geom_ponto`, `nome_empreendimento`.
* **Solução:** Usar o parâmetro `columns=` do PyArrow:
```python
df = pd.read_parquet(file_path, columns=["id_empreendimento", "geom_linha", "geom_ponto", "nome_empreendimento"])
```
* **Ganho estimado:** Redução de 30–60% no consumo de RAM deste arquivo.

---

### 2.3 Estimativa de Consumo de RAM

Cenário com as otimizações 2.1 + 2.2 aplicadas:

| Componente | RAM estimada |
|:---|---:|
| Ubuntu OS + serviços base | ~400–600 MB |
| Nginx | ~5–15 MB |
| Processo Streamlit (Python + libs) | ~150–200 MB |
| Cache compartilhado Geo (com projeção) | ~40–60 MB |
| Cache compartilhado outros Parquets | ~10–15 MB |
| **Overhead por sessão simultânea** | **~15–30 MB** |
| **Total com 5 usuários** | **~800 MB – 1.1 GB** |
| **Total com 10 usuários** | **~1.0 – 1.4 GB** |

---

### 2.4 Dados brutos (`data/raw/`) no servidor de produção

* A pasta `data/raw/` contém CSVs e JSONs (~280 MB), com o JSON geo sozinho em **267 MB**.
* **Recomendação:** Apenas os arquivos `data/processed/*.parquet` devem subir para o servidor de produção, mantendo `data/raw/` apenas no ambiente de desenvolvimento/ETL local.

---

## 3. Bloco 2 — Segurança da Aplicação e Servidor

### 3.1 Sanitização do `?id=` (query params)

* **Implementação defensiva no `app.py`:**
```python
import re
query_id = st.query_params.get("id", None)
if query_id and re.match(r"^\d{1,10}$", str(query_id).strip()):
    selected_id = str(query_id).strip()
    # prossegue com segurança
else:
    query_id = None
```

### 3.2 HTTPS/SSL (Terminação no Nginx)

* **Let's Encrypt (Certbot)** para domínios públicos ou certificado corporativo interno (CA da empresa).
* Todo tráfego HTTP redirecionado para HTTPS na porta 443.

### 3.3 Firewall (UFW)

* Apenas portas essenciais abertas:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```
* A porta interna `8501` do Streamlit **não** deve ser exposta publicamente.

### 3.4 Autenticação e Acesso

* **Cenário 1 (Rede Interna / VPN):** Acesso restrito pela própria infraestrutura de rede corporativa.
* **Cenário 2 (Web Pública / Externa):** Autenticação Nginx Basic Auth (`.htpasswd`) ou SSO/OAuth2-Proxy.

---

## 4. Bloco 3 — Infraestrutura e Deploy

### 4.1 Configuração do Nginx (com Suporte Obrigatório a WebSocket)

```nginx
server {
    listen 80;
    server_name atlas.suaempresa.com.br;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name atlas.suaempresa.com.br;

    ssl_certificate     /etc/ssl/certs/atlas.crt;
    ssl_certificate_key /etc/ssl/private/atlas.key;

    # Headers de Segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;

        # WebSocket obrigatório para o Streamlit
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

### 4.2 Systemd Service (Gerenciador de Processos)

```ini
# /etc/systemd/system/atlas-web.service
[Unit]
Description=Atlas Web - Streamlit Application
After=network.target

[Service]
Type=simple
User=atlas
Group=atlas
WorkingDirectory=/opt/atlas_web
ExecStart=/opt/atlas_web/.venv/bin/streamlit run app.py
Restart=always
RestartSec=5
Environment="STREAMLIT_SERVER_HEADLESS=true"
Environment="STREAMLIT_SERVER_PORT=8501"

# Circuit breaker de memória
MemoryMax=2G
MemoryHigh=1.5G

[Install]
WantedBy=multi-user.target
```

### 4.3 Estrutura de Pastas Sugerida no Servidor

```
/opt/atlas_web/
├── .venv/                # Ambiente virtual Python
├── app.py
├── views/
├── services/
├── data/
│   └── processed/        # Apenas Parquets
├── logos/
├── .streamlit/
│   └── config.toml
└── requirements.txt
```

---

## 5. Painel de Decisões do Deploy

| # | Pergunta / Decisão | Opções | Status |
|:---|:---|:---|:---:|
| **P1** | Usuários simultâneos esperados | 1–5 / 5–15 / 15+ | ⏳ A definir |
| **P2** | Exposição do servidor | Domínio público / Rede interna / VPN | ⏳ A definir |
| **P3** | Autenticação de acesso | Basic Auth / SSO / Nenhuma (Rede interna) | ⏳ A definir |
| **P4** | Manter `data/raw/` no servidor | Não (apenas processed) / Sim | ⏳ Recomendado: Não |
| **P5** | Estratégia de atualização | Git pull no servidor / rsync | ⏳ A definir |
| **P6** | `@st.cache_resource` para dados | Aprovado | ⏳ A implementar |
| **P7** | Certificado SSL | Let's Encrypt / CA Interna | ⏳ A definir |
| **P8** | Limite de memória do Systemd | 2 GB (em servidor de 4-8 GB) | ⏳ Aprovado |
