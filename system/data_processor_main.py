# -*- coding: utf-8 -*-
# Módulo: data_processor_main.py (corrigido)
# Ajustes: reconhecer categorias /products/.../ e reforçar logs quando não houver expansão.

import json, os, re
from pathlib import Path
from datetime import datetime

from .scraper_engine import get_metadata
from .metadata.url_analyzer import URLAnalyzer
from .metadata.size_rules import normalize_sizes
from .category_crawler import CategoryCrawler

FORBIDDEN = set('<>:"\\|?*')  # removemos '/' daqui para tratá-lo separadamente

def _intersecao_textual(a: str, b: str) -> str:
    a, b = (a or '').strip(), (b or '').strip()
    if not a: return b
    if not b: return a
    if a.lower() in b.lower(): base = a
    elif b.lower() in a.lower(): base = b
    else:
        aw, bw = a.split(), b.split()
        common = []
        for i in range(min(len(aw), len(bw))):
            if aw[i].lower() == bw[i].lower(): common.append(aw[i])
            else: break
        base = ' '.join(common) if common else a
    base = base.replace('25/26','25-26')
    base = re.sub(r'(S-\s*X{1,4}L)\d+', r'\1', base, flags=re.I)
    base = re.sub(r'(S-\s*\dXL)\d*', r'\1', base, flags=re.I)
    return base.strip()

def _sanitize_win(name: str) -> str:
    # Substitui '/' explicitamente por '-'
    name = name.replace('/', '-')
    # Remove demais caracteres proibidos
    cleaned = ''.join(ch for ch in name if ch not in FORBIDDEN).strip()
    while cleaned.endswith((' ', '.')):
        cleaned = cleaned[:-1]
    return cleaned[:120] if len(cleaned) > 120 else cleaned

def _dedupe(seq):
    seen, out = set(), []
    for s in seq or []:
        if s and s not in seen:
            seen.add(s); out.append(s)
    return out

class DataProcessor:
    def __init__(self, logger, config_manager):
        self.logger = logger
        self.config = config_manager
        self.category_crawler = CategoryCrawler(logger)

    def _is_category_url(self, url: str) -> bool:
        url_lower = url.lower()
        wordpress_patterns = [
            '/category/', '/product-category/', '/collection/', '/collections/',
            '/shop/', '/store/', '/catalogo/', '/produtos/', '/search/',
            '/products/'  # <- adicionado suporte explícito
        ]
        yupoo_patterns = ['/search/', '/categories/', 'search?', 'category?']
        for pattern in wordpress_patterns + yupoo_patterns:
            if pattern in url_lower:
                return True
        if "?s=" in url_lower:
            return True

        search_params = ['search=', 'q=', 'category=', 'cat=', 'tag=']
        for param in search_params:
            if param in url_lower:
                return True
        return False

    def _expand_category_urls(self, urls: list[str]) -> list[str]:
        expanded_urls = []
        for url in urls:
            if self._is_category_url(url):
                self.logger.log(f"📂 Detectada categoria: {url}", "INFO", "📂")
                try:
                    product_urls = self.category_crawler.collect_products(url)
                    if product_urls:
                        self.logger.log(f"✅ Expandida: {len(product_urls)} produtos encontrados", "SUCCESS", "✅")
                        expanded_urls.extend(product_urls)
                    else:
                        self.logger.log(f"⚠️ Nenhum produto encontrado na categoria: {url}", "WARNING", "⚠️")
                except Exception as e:
                    self.logger.log(f"❌ Erro ao expandir categoria: {str(e)}", "ERROR", "❌")
            else:
                expanded_urls.append(url)
        # Deduplicação e filtro para remover qualquer URL de categoria que tenha escapado
        unique_urls, seen = [], set()
        for url in expanded_urls:
            if url not in seen and not self._is_category_url(url):
                seen.add(url)
                unique_urls.append(url)
        return unique_urls

    def processar_metadados(self, urls: list[str]) -> dict:
        if not urls:
            self.logger.log("Nenhuma URL fornecida para processamento", "WARNING", "⚠️")
            return {"ok": False, "erro": "Lista de URLs vazia"}
        self.logger.log(f"🔍 Analisando {len(urls)} URL(s) de entrada...", "INFO", "🔍")
        expanded_urls = self._expand_category_urls(urls)
        if len(expanded_urls) != len(urls):
            self.logger.log(f"📈 Expansão concluída: {len(urls)} → {len(expanded_urls)} URLs", "INFO", "📈")
        itens, total = [], len(expanded_urls)
        self.logger.log(f"▶️ Iniciando processamento de {total} URL(s)...", "INFO", "▶️")
        for idx, url in enumerate(expanded_urls, 1):
            try:
                self.logger.log(f"🔎 Analisando URL {idx}/{total}: {url}", "INFO", "🔎")
                info = URLAnalyzer.analyze(url)
                self.logger.log(f"🧭 Plataforma: {info['platform']} | Entidade: {info['entity']}", "DEBUG", "🧭")
                meta = get_metadata(url, info["platform"])
                if not meta:
                    self.logger.log(f"❌ Falha ao extrair metadados de: {url}", "ERROR", "❌")
                    continue
                album_title = (meta.get("album_title") or "").strip()
                page_title = (meta.get("page_title") or "").strip()
                folder_base = _intersecao_textual(page_title, album_title) or album_title or page_title
                album_folder_name = _sanitize_win(folder_base)
                sizes = normalize_sizes(album_title, meta.get("raw_sizes"))
                images = _dedupe(meta.get("images_candidates", []))
                album_id = (url.split("/")[-1] or "").split("?")[0]
                itens.append({
                    "album_url": url,
                    "album_title": album_title,
                    "page_title": page_title,
                    "album_folder_name": album_folder_name,
                    "sizes": sizes,
                    "image_urls": images,
                    "album_id": album_id
                })
            except Exception as e:
                self.logger.log(f"❌ Erro no processamento da URL: {str(e)}", "ERROR", "❌")
                continue
        if not itens:
            return {"ok": False, "erro": "Nenhum metadado gerado"}
        outdir = Path("Metadados"); outdir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        outpath = outdir / f"metadados-{ts}.json"
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False, indent=2)
        return {"ok": True, "arquivo": str(outpath), "total_urls": len(expanded_urls), "sucessos": len(itens), "falhas": len(expanded_urls) - len(itens)}
