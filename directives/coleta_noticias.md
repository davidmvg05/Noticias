# Diretiva: Coleta e Processamento de Notícias

Esta diretiva define o Procedimento Operacional Padrão (SOP) para a extração, limpeza, desduplicação e estruturação de notícias através de feeds RSS, em conformidade com a arquitetura descrita em `Agente.md`.

---

## 1. Categorias e Feeds RSS Recomendados

A recolha deve cobrir rigorosamente as 5 categorias delineadas no projeto, priorizando feeds abertos, estáveis e sem exigência de chaves de API.

### Categoria 1: Economia, Mercados Financeiros, ETFs e Ações (`economia`)
- **Jornal de Negócios (PT):** `https://www.jornaldenegocios.pt/rss`
- **InfoMoney (BR - Mercados):** `https://www.infomoney.com.br/mercados/feed/`
- **CNBC - Finance/Markets (Global):** `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664`
- **MarketWatch - Top Stories (Global):** `https://feeds.content.dowjones.io/public/rss/mw_topstories`

### Categoria 2: Novidades em Inteligência Artificial (`ia`)
- **TechCrunch - Artificial Intelligence:** `https://techcrunch.com/category/artificial-intelligence/feed/`
- **VentureBeat - AI:** `https://venturebeat.com/category/ai/feed/`
- **MIT Technology Review - AI:** `https://www.technologyreview.com/topic/artificial-intelligence/feed`
- **The Verge - AI:** `https://www.theverge.com/rss/ai/index.xml`

### Categoria 3: Automações e Workflows (`automacoes`)
- **Make Community & Blog:** `https://www.make.com/en/blog/rss.xml`
- **Zapier Blog:** `https://zapier.com/blog/feeds/latest/`
- **n8n Blog:** `https://blog.n8n.io/rss/`
- **Hacker News (Filtro Automation / Show HN):** `https://hnrss.org/frontpage?q=automation`

### Categoria 4: Marketing Digital (`marketing_digital`)
- **Search Engine Journal:** `https://www.searchenginejournal.com/feed/`
- **Marketing Dive:** `https://www.marketingdive.com/feeds/news/`
- **Social Media Today:** `https://www.socialmediatoday.com/feeds/news/`
- **HubSpot Blog:** `https://blog.hubspot.com/marketing/rss.xml`

### Categoria 5: Notícias Felizes / Boas Notícias (`noticias_felizes`)
- **Good News Network:** `https://www.goodnewsnetwork.org/feed/`
- **Positive News:** `https://www.positive.news/feed/`
- **Reasons to be Cheerful:** `https://reasonstobecheerful.world/feed/`
- **Só Notícia Boa (PT/BR):** `https://sonoticiaboa.com.br/feed/`

---

## 2. Regras de Requisição e Resiliência

1. **User-Agent Customizado:**
   - Muitos agregadores e servidores bloqueiam requisições padrão do `urllib` ou `requests`.
   - Utilizar sempre cabeçalho HTTP moderno:
     `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`
2. **Timeouts:**
   - Timeout máximo por feed: `10 segundos`.
   - Caso um feed falhe, registar o aviso/log e avançar para o próximo sem interromper a execução global.
3. **Parsing:**
   - Efetuar download via `requests` com timeout e repassar o conteúdo (`response.content`) para `feedparser.parse()`.

---

## 3. Critérios de Limpeza e Desduplicação

Para garantir qualidade editorial no dashboard:

1. **Desduplicação por URL:**
   - Normalizar URLs (remover parâmetros de tracking `utm_*`, `ref`, etc.).
   - Descartar itens com URL já processada na execução atual.
2. **Desduplicação por Título (Similaridade):**
   - Normalizar título: minúsculas, remoção de pontuações, remoção de espaços extras.
   - Comparação com artigos da mesma categoria: se similaridade léxica (ex: similaridade de Jaccard de palavras-chave ou razão de distância > 80%) for detectada, manter apenas o artigo mais recente ou da fonte de maior prioridade.
3. **Limpeza de Conteúdo:**
   - Remover tags HTML dos resumos/descrições (usar expressões regulares ou parser simples).
   - Limitar resumo a um lead limpo de até 250-300 caracteres, com reticências se truncado.
4. **Data e Ordenação:**
   - Padronizar data de publicação para formato ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) ou texto legível (`YYYY-MM-DD HH:MM`).
   - Ordenar cada categoria da notícia mais recente para a mais antiga.
   - Limitar a 10-15 notícias mais relevantes por categoria.

---

## 4. Estrutura e Formato de Saída (JSON)

O resultado final determinístico gerado pela camada de execução (`execution/`) deve ser gravado em:
`.tmp/noticias_filtradas.json`

### Schema do JSON:

```json
{
  "atualizado_em": "2026-09-16T01:00:00Z",
  "total_artigos": 50,
  "categorias": {
    "economia": [
      {
        "id": "hash_md5_ou_uuid",
        "titulo": "Título da Notícia de Economia",
        "resumo": "Lead conciso e limpo sem tags HTML explicando o tema...",
        "url": "https://fonte.com/artigo-original",
        "fonte": "Jornal de Negócios",
        "data_publicacao": "2026-09-15 20:30",
        "categoria": "economia"
      }
    ],
    "ia": [],
    "automacoes": [],
    "marketing_digital": [],
    "noticias_felizes": []
  }
}
```

---

## 5. Próximos Passos na Camada de Execução

- Criar o script determinístico em `execution/coletor.py` que consome esta diretiva, consulta os feeds RSS e gera o ficheiro `.tmp/noticias_filtradas.json`.
- A interface Streamlit (`app.py`) lerá este JSON e autenticará o utilizador via `MEU_PIN` de `st.secrets`.
