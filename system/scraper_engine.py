
# Módulo: scraper_engine.py
# Função: extrai metadados mínimos de páginas de produto WordPress e Yupoo.
# Chamadas: DataProcessor -> get_metadata(url, platform)
# Atualização: fallbacks extras de título Yupoo; limpeza de sufixos; filtros de imagens.

import re
import requests
from bs4 import BeautifulSoup

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA_POOL[0]})
    return s

def _title_from_og(soup):
    og = soup.select_one('meta[property="og:title"]')
    return og.get("content", "").strip() if og else ""

def _images_from_meta(soup):
    out = []
    for m in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
        c = m.get("content")
        if c:
            out.append(c.strip())
    return out

def _clean_yupoo_suffix(txt: str) -> str:
    if not txt:
        return ""
    # Remover sufixos comuns
    txt = re.sub(r"\s*\|\s*又拍图片管家\s*$", "", txt)
    txt = re.sub(r"\s*\|\s*Yupoo\s*$", "", txt, flags=re.I)
    txt = re.sub(r"\s*-\s*相册\s*-\s*Yupoo\s*$", "", txt, flags=re.I)
    return txt.strip()

def scrape_wordpress(url: str) -> dict:
    r = _session().get(url, allow_redirects=True, timeout=20)
    soup = BeautifulSoup(r.text, "lxml")
    # título
    h1 = soup.select_one("h1")
    album_title = (h1.get_text(strip=True) if h1 else "") or _title_from_og(soup)
    page_title = (soup.title.get_text(strip=True) if soup.title else "") or _title_from_og(soup) or album_title

    # tamanhos (heurística simples)
    body_text = soup.get_text(" ", strip=True)
    raw_sizes = None
    m = re.search(r"\bS\s*-\s*(\dXL|X{1,4}L)\b", body_text, flags=re.I)
    if m:
        raw_sizes = m.group(0)

    # imagens
    imgs = []
    for sel in ["img[src]", ".woocommerce-product-gallery__image img[src]", ".wp-block-image img[src]"]:
        for im in soup.select(sel):
            src = im.get("src") or im.get("data-src")
            if src:
                imgs.append(src)
    imgs += _images_from_meta(soup)
    # filtros
    imgs = [u for u in imgs if not u.startswith("data:image")]
    imgs = [u for u in imgs if not re.search(r"-\d{2,4}x\d{2,4}\.", u)]

    return {
        "album_title": album_title or page_title,
        "page_title": page_title or album_title,
        "raw_sizes": raw_sizes,
        "images_candidates": imgs,
    }

def _yupoo_title_fallbacks(soup) -> str:
    # 1) <title>
    t = soup.title.get_text(strip=True) if soup.title else ""
    if t:
        return t
    # 2) og:title
    t = _title_from_og(soup)
    if t:
        return t
    # 3) meta[name=title]
    m = soup.select_one('meta[name="title"]')
    if m and m.get("content"):
        return m.get("content").strip()
    # 4) elementos comuns no template
    for sel in [".album__title", ".showalbum__title", "h1.album-title", "h1", ".title", ".page-title"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    # 5) data-title em nós
    el = soup.select_one("[data-title]")
    if el and el.get("data-title"):
        return el.get("data-title").strip()
    return ""

def scrape_yupoo(url: str) -> dict:
    r = _session().get(url, allow_redirects=True, timeout=20)
    soup = BeautifulSoup(r.text, "lxml")
    raw_title = _yupoo_title_fallbacks(soup)
    raw_title = _clean_yupoo_suffix(raw_title)

    # Page title com fallback
    page_title = _clean_yupoo_suffix((soup.title.get_text(strip=True) if soup.title else "") or raw_title)
    album_title = raw_title or page_title

    # tamanhos (heurística a partir de títulos)
    txt = f"{album_title} {page_title}".strip()
    raw_sizes = None
    m = re.search(r"\bS\s*-\s*(\dXL|X{1,4}L)\b", txt, flags=re.I)
    if m:
        raw_sizes = m.group(0)

    imgs = _images_from_meta(soup)
    imgs = [u for u in imgs if not u.startswith("data:image")]
    imgs = [u for u in imgs if not re.search(r"-\d{2,4}x\d{2,4}\.", u)]

    return {
        "album_title": album_title or page_title,
        "page_title": page_title or album_title,
        "raw_sizes": raw_sizes,
        "images_candidates": imgs,
    }

def get_metadata(url: str, platform: str) -> dict:
    try:
        if platform == "wordpress":
            return scrape_wordpress(url)
        if platform == "yupoo":
            return scrape_yupoo(url)
    except Exception:
        pass
    return {"album_title": "", "page_title": "", "raw_sizes": None, "images_candidates": []}
