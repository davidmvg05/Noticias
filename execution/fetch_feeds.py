"""
Script determinístico para coleta, limpeza, desduplicação e exportação de notícias RSS.
Conforme especificado em directives/coleta_noticias.md e Agente.md.
"""

import os
import re
import html
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import feedparser

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("fetch_feeds")

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
OUTPUT_FILE = TMP_DIR / "noticias_filtradas.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt;q=0.8"
}

TIMEOUT = 10  # segundos por feed

FEEDS_BY_CATEGORY = {
    "economia": [
        {"nome": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"nome": "Jornal de Negócios", "url": "https://www.jornaldenegocios.pt/rss"},
        {"nome": "CNBC Finance", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"},
        {"nome": "InfoMoney Mercados", "url": "https://www.infomoney.com.br/mercados/feed/"}
    ],
    "ia": [
        {"nome": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
        {"nome": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
        {"nome": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
        {"nome": "The Verge AI", "url": "https://www.theverge.com/rss/ai/index.xml"}
    ],
    "automacoes": [
        {"nome": "Make Blog", "url": "https://www.make.com/en/blog/rss.xml"},
        {"nome": "Zapier Blog", "url": "https://zapier.com/blog/feeds/latest/"},
        {"nome": "n8n Blog", "url": "https://blog.n8n.io/rss/"},
        {"nome": "Hacker News Automation", "url": "https://hnrss.org/frontpage?q=automation"}
    ],
    "marketing_digital": [
        {"nome": "Search Engine Journal", "url": "https://www.searchenginejournal.com/feed/"},
        {"nome": "Search Engine Land", "url": "https://searchengineland.com/feed"},
        {"nome": "Marketing Dive", "url": "https://www.marketingdive.com/feeds/news/"},
        {"nome": "HubSpot Blog", "url": "https://blog.hubspot.com/marketing/rss.xml"}
    ],
    "noticias_felizes": [
        {"nome": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/"},
        {"nome": "Positive News", "url": "https://www.positive.news/feed/"},
        {"nome": "Reasons to be Cheerful", "url": "https://reasonstobecheerful.world/feed/"},
        {"nome": "Só Notícia Boa", "url": "https://sonoticiaboa.com.br/feed/"}
    ]
}


def clean_url(raw_url: str) -> str:
    """Remove parâmetros de tracking (utm_*, ref, etc.) de um URL."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        tracked_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "ref", "fbclid", "gclid", "source"
        }
        query_pairs = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in tracked_params
        ]
        new_query = urlencode(query_pairs)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ""))
    except Exception:
        return raw_url.strip()


def strip_html_and_clean(text: str, max_chars: int = 280) -> str:
    """Limpa tags HTML, desescapa entidades e normaliza espaços."""
    if not text:
        return ""
    cleaned = html.unescape(text)
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > max_chars:
        return cleaned[:max_chars].rsplit(" ", 1)[0] + "..."
    return cleaned


def normalize_title(title: str) -> str:
    """Normaliza o título para comparação e cálculo de similaridade."""
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return " ".join(cleaned.split())


def compute_token_similarity(title_a: str, title_b: str) -> float:
    """Calcula similaridade de Jaccard entre tokens dos títulos."""
    tokens_a = set(normalize_title(title_a).split())
    tokens_b = set(normalize_title(title_b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


def parse_entry_date(entry) -> tuple[str, float]:
    """Retorna data formatada (YYYY-MM-DD HH:MM) e timestamp numérico para ordenação."""
    time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if time_struct:
        try:
            ts = time.mktime(time_struct)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M"), ts
        except Exception:
            pass

    raw_date = entry.get("published") or entry.get("updated")
    if raw_date:
        return str(raw_date)[:25], 0.0

    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M"), now.timestamp()


def extract_image_from_entry(entry, raw_content: str = "") -> str:
    """Extrai imagem direta dos metadados RSS ou tags HTML."""
    media_content = entry.get("media_content")
    if isinstance(media_content, list):
        for m in media_content:
            u = m.get("url")
            if u and any(ext in u.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", "format=", "zenfs"]):
                return u

    media_thumb = entry.get("media_thumbnail")
    if isinstance(media_thumb, list):
        for t in media_thumb:
            u = t.get("url")
            if u:
                return u

    enclosures = entry.get("enclosures")
    if isinstance(enclosures, list):
        for enc in enclosures:
            href = enc.get("href") or enc.get("url")
            if href and any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                return href

    links = entry.get("links")
    if isinstance(links, list):
        for l in links:
            if "image" in l.get("type", "") and l.get("href"):
                return l["href"]

    corpus = (entry.get("summary") or "") + " " + (entry.get("description") or "") + " " + raw_content
    m = re.search(r'<img[^>]+src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', corpus, re.IGNORECASE)
    if m:
        return m.group(1)

    return ""


def fetch_og_image(url: str, timeout: float = 3.5) -> str:
    """Obtém a imagem real do artigo através de meta tags OpenGraph / Twitter."""
    if not url:
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            patterns = [
                r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]',
                r'<meta[^>]+name=[\'"]twitter:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+name=[\'"]twitter:image[\'"]'
            ]
            for p in patterns:
                m = re.search(p, resp.text, re.IGNORECASE)
                if m:
                    img_url = html.unescape(m.group(1).strip())
                    if img_url.startswith("http"):
                        if "100x100" in img_url:
                            img_url = img_url.replace("100x100", "800x450")
                        return img_url
    except Exception:
        pass
    return ""


def fetch_feed_items(feed_info: dict) -> list[dict]:
    """Efetua a requisição HTTP com timeout e analisa o feed RSS."""
    feed_url = feed_info["url"]
    fonte_nome = feed_info["nome"]
    items = []

    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} ao aceder a {fonte_nome} ({feed_url})")
            return []

        feed = feedparser.parse(response.content)
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout ({TIMEOUT}s) excedido ao obter {fonte_nome}")
        return []
    except Exception as e:
        logger.warning(f"Erro de conexão ao obter {fonte_nome}: {e}")
        return []

    if getattr(feed, "bozo", False) and not feed.entries:
        logger.warning(f"Feed malformatado ou vazio para {fonte_nome}")
        return []

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue

        raw_link = entry.get("link", "")
        link = clean_url(raw_link)
        if not link:
            continue

        summary_raw = entry.get("summary") or entry.get("description") or ""
        content_raw = ""
        if entry.get("content") and isinstance(entry.get("content"), list) and len(entry["content"]) > 0:
            content_raw = entry["content"][0].get("value", "")
            if not summary_raw:
                summary_raw = content_raw

        cleaned_summary = strip_html_and_clean(summary_raw)
        formatted_date, timestamp = parse_entry_date(entry)
        image_url = extract_image_from_entry(entry, content_raw)

        if "100x100" in image_url:
            image_url = image_url.replace("100x100", "800x450")

        item_id = hashlib.md5(f"{title}_{link}".encode("utf-8")).hexdigest()

        items.append({
            "id": item_id,
            "titulo": title,
            "resumo": cleaned_summary,
            "fonte": fonte_nome,
            "data_publicacao": formatted_date,
            "url": link,
            "imagem": image_url,
            "_timestamp": timestamp
        })

    return items


from execution.translator import get_article_translation


def enrich_article_image(item: dict) -> dict:
    """Se o artigo não tiver imagem, busca og:image da página original."""
    if not item.get("imagem"):
        img = fetch_og_image(item["url"], timeout=3.0)
        if img:
            item["imagem"] = img

    # Pré-computar verificação e tradução para PT-PT em segundo plano com cache persistente
    try:
        is_en, pt_title, pt_lead = get_article_translation(
            item.get("titulo", ""),
            item.get("resumo", ""),
            fonte=item.get("fonte", "")
        )
        item["is_en"] = is_en
        item["titulo_pt"] = pt_title
        item["resumo_pt"] = pt_lead
    except Exception as e:
        logger.debug(f"Erro ao traduzir artigo no feed: {e}")

    return item


def process_category(categoria: str, feeds: list[dict], limit: int = 10) -> list[dict]:
    """Coleta, desduplica, enriquece imagens e seleciona os artigos mais recentes."""
    logger.info(f"Iniciando coleta para categoria: {categoria.upper()}")
    raw_articles = []

    for feed_info in feeds:
        feed_items = fetch_feed_items(feed_info)
        raw_articles.extend(feed_items)

    raw_articles.sort(key=lambda x: x["_timestamp"], reverse=True)

    unique_articles = []
    seen_urls = set()

    for item in raw_articles:
        url = item["url"]
        if url in seen_urls:
            continue

        is_duplicate = False
        for approved in unique_articles:
            sim = compute_token_similarity(item["titulo"], approved["titulo"])
            if sim >= 0.75:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        seen_urls.add(url)
        item_copy = dict(item)
        del item_copy["_timestamp"]
        item_copy["categoria"] = categoria
        unique_articles.append(item_copy)

        if len(unique_articles) >= limit:
            break

    # Enriquecer imagens em paralelo para alta velocidade
    with ThreadPoolExecutor(max_workers=5) as executor:
        unique_articles = list(executor.map(enrich_article_image, unique_articles))

    com_imagem = sum(1 for x in unique_articles if x.get("imagem"))
    logger.info(f"Categoria '{categoria}': {len(unique_articles)} artigos ({com_imagem} com imagens reais).")
    return unique_articles


def run_collection() -> dict:
    """Executa o pipeline completo de coleta para todas as categorias."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    resultado = {
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_artigos": 0,
        "categorias": {}
    }

    total_count = 0
    for categoria, feeds in FEEDS_BY_CATEGORY.items():
        artigos = process_category(categoria, feeds, limit=10)
        resultado["categorias"][categoria] = artigos
        total_count += len(artigos)

    resultado["total_artigos"] = total_count

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    logger.info(f"Sucesso! Total de {total_count} artigos gravados em {OUTPUT_FILE}")
    return resultado


if __name__ == "__main__":
    run_collection()
