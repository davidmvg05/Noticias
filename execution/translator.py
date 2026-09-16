"""
Módulo de Tradução Inteligente para Português de Portugal (pt-PT)
Com cache local persistente para máxima velocidade e fiabilidade.
"""

import json
import re
import urllib.parse
import urllib.request
import logging
from pathlib import Path

logger = logging.getLogger("translator")

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
TRANSLATIONS_CACHE_FILE = TMP_DIR / "traducoes_cache.json"

_cache = None


def load_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if TRANSLATIONS_CACHE_FILE.exists():
        try:
            with open(TRANSLATIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
                return _cache
        except Exception as e:
            logger.warning(f"Erro ao carregar cache de traduções: {e}")
    _cache = {}
    return _cache


def save_cache():
    global _cache
    if _cache is None:
        return
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRANSLATIONS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Erro ao salvar cache de traduções: {e}")


def is_english_text(text: str, fonte: str = "") -> bool:
    """Deteta de forma rápida se o texto/artigo está em inglês."""
    if not text:
        return False

    fontes_pt = {
        "jornal de negócios", "jornal de negocios", "infomoney",
        "infomoney mercados", "só notícia boa", "so noticia boa", "sapo", "publico"
    }
    if fonte and fonte.strip().lower() in fontes_pt:
        return False

    # Stopwords comuns em inglês
    en_words = {
        "the", "and", "is", "in", "to", "of", "with", "for", "on", "at",
        "by", "from", "that", "this", "it", "as", "are", "be", "has", "have",
        "new", "about", "will", "after", "its", "says", "more"
    }
    # Stopwords comuns em português
    pt_words = {
        "que", "não", "nao", "para", "uma", "com", "dos", "das", "por",
        "mais", "este", "esta", "são", "sao", "foi", "como", "sobre", "pelo", "pela"
    }

    tokens = set(re.findall(r"\b[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]+\b", text.lower()))
    en_matches = len(tokens.intersection(en_words))
    pt_matches = len(tokens.intersection(pt_words))

    if en_matches > pt_matches:
        return True
    if pt_matches > 0:
        return False

    # Se a fonte for estrangeira conhecida
    fontes_en = {
        "techcrunch", "venturebeat", "mit tech review", "the verge",
        "make blog", "zapier blog", "n8n blog", "hacker news",
        "search engine journal", "search engine land", "marketing dive",
        "hubspot blog", "good news network", "positive news", "reasons to be cheerful",
        "yahoo finance", "cnbc"
    }
    for f in fontes_en:
        if f in fonte.lower():
            return True

    return False


def translate_text_to_pt(text: str) -> str:
    """Traduz texto de inglês para português de Portugal (pt-PT)."""
    if not text or not text.strip():
        return text

    clean = text.strip()
    cache = load_cache()

    if clean in cache:
        return cache[clean]

    # 1. Tentativa primária: Google Translate API (rápido, fiável e sem bloqueios 429)
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt-PT&dt=t&q={urllib.parse.quote(clean[:1500])}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsRadar/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list) and data[0]:
                translated_parts = [part[0] for part in data[0] if part and part[0]]
                translated = "".join(translated_parts).strip()
                if translated:
                    cache[clean] = translated
                    save_cache()
                    return translated
    except Exception as e:
        logger.debug(f"Falha ao traduzir via Google Translate API: {e}")

    # 2. Tentativa secundária: MyMemory (especificando pt-PT)
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean[:500])}&langpair=en|pt-PT"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsRadar/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data.get("responseData") and data["responseData"].get("translatedText"):
                translated = data["responseData"]["translatedText"]
                if not translated.startswith("MYMEMORY WARNING:") and "QUERY LENGTH LIMIT" not in translated:
                    cache[clean] = translated
                    save_cache()
                    return translated
    except Exception as e:
        logger.debug(f"Falha ao traduzir via MyMemory: {e}")

    # Retorna o texto original se os serviços falharem
    return clean


def get_article_translation(title: str, lead: str, fonte: str = "") -> tuple[bool, str, str]:
    """
    Verifica se o artigo está em inglês e retorna:
    (is_en, translated_title, translated_lead)
    """
    is_en = is_english_text(f"{title} {lead}", fonte=fonte)
    if not is_en:
        return False, title, lead

    pt_title = translate_text_to_pt(title)
    pt_lead = translate_text_to_pt(lead)
    return True, pt_title, pt_lead
