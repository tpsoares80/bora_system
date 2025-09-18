# Módulo: category_crawler.py (final revisado para WordPress categorias e buscas)
# Ajustes: _wordpress suporta páginas de busca (?s=...) e categorias (/products/.../) com paginação.

import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

class CategoryCrawler:
    def __init__(self, logger):
        self.logger = logger

    def collect_products(self, url: str) -> list[str]:
        host = urlparse(url).netloc.lower()
        if ".yupoo.com" in host:
            return self._yupoo(url)
        return self._wordpress(url)

    def _session(self):
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        s.timeout = 20
        return s

    def _is_valid_product_url(self, href: str) -> bool:
        if not href:
            return False
        product_indicators = ['/product/', '/produtos/', '/item/']
        ignore_indicators = [
            '/category/', '/tag/', '/author/', '/page/', '/cart/', '/checkout/', '/account/', '/login/',
            '.jpg', '.png', '.gif', '.pdf', '.zip', 'javascript:', 'mailto:', 'tel:', '#'
        ]
        href_lower = href.lower()
        has_product_indicator = any(ind in href_lower for ind in product_indicators)
        has_ignore_indicator = any(ind in href_lower for ind in ignore_indicators)
        return has_product_indicator and not has_ignore_indicator

    def _wordpress(self, url: str) -> list[str]:
        sess = self._session()
        produtos = set()

        def parse_page(html, base):
            soup = BeautifulSoup(html, "lxml")

            # Seletores abrangendo páginas de busca (?s=...) e categorias (/products/.../)
            product_selectors = [
                ".products .product a[href]",              # WooCommerce padrão (categorias e busca)
                "ul.products li.product a[href]",          # alternativa
                ".woocommerce-LoopProduct-link",           # link padrão WC
                "a[href*='/product/']", "a[href*='/produtos/']", "a[href*='/item/']"
            ]

            for selector in product_selectors:
                for a in soup.select(selector):
                    href = urljoin(base, a.get("href"))
                    if self._is_valid_product_url(href):
                        produtos.add(href)

            # Paginadores (funciona tanto em categorias quanto em buscas)
            next_selectors = [
                "a.next", "a.next.page-numbers", "a[rel='next']",
                ".pagination-next a", ".wp-pagenavi a.next",
                "[class*='next'] a", "a[aria-label*='Next']"
            ]
            for selector in next_selectors:
                nxt = soup.select_one(selector)
                if nxt and nxt.get("href"):
                    return urljoin(base, nxt.get("href"))
            return None

        current_url = url
        seen = set()
        page_count = 0
        max_pages = 20

        self.logger.log(f"🔍 Iniciando coleta WordPress: {url}", "INFO", "🔍")

        while current_url and current_url not in seen and page_count < max_pages:
            seen.add(current_url)
            page_count += 1
            try:
                self.logger.log(f"📄 Processando página {page_count}: {current_url}", "DEBUG", "📄")
                response = sess.get(current_url)
                response.raise_for_status()
                next_url = parse_page(response.text, current_url)
                if next_url and next_url != current_url:
                    current_url = next_url
                else:
                    break
            except Exception as e:
                self.logger.log(f"❌ Erro ao processar página {page_count}: {str(e)}", "ERROR", "❌")
                break

        resultado = [u for u in produtos if self._is_valid_product_url(u) and u != url]
        if not resultado:
            self.logger.log(f"⚠️ Nenhum produto encontrado na categoria WordPress: {url}", "WARNING", "⚠️")
        else:
            self.logger.log(f"✅ WordPress coleta concluída: {len(resultado)} produtos encontrados", "SUCCESS", "✅")
        return resultado

    def _yupoo(self, url: str) -> list[str]:
        sess = self._session()
        prod = set()

        def parse(html, base):
            soup = BeautifulSoup(html, "lxml")
            album_selectors = [
                "a[href*='/albums/']", ".album-item a", ".showalbum__children a", "[data-album-id] a"
            ]
            for selector in album_selectors:
                for a in soup.select(selector):
                    href = urljoin(base, a.get("href"))
                    if "/albums/" in href and href not in prod:
                        prod.add(href)
            next_selectors = ["a.next, a[rel='next']", ".pagination .next", "[class*='next'] a"]
            for selector in next_selectors:
                nxt = soup.select_one(selector)
                if nxt and nxt.get("href"):
                    return urljoin(base, nxt.get("href"))
            return None

        current_url = url
        seen = set()
        page_count = 0
        max_pages = 10

        self.logger.log(f"🔍 Iniciando coleta Yupoo: {url}", "INFO", "🔍")

        while current_url and current_url not in seen and page_count < max_pages:
            seen.add(current_url)
            page_count += 1
            try:
                self.logger.log(f"📄 Processando página {page_count}: {current_url}", "DEBUG", "📄")
                response = sess.get(current_url)
                response.raise_for_status()
                next_url = parse(response.text, current_url)
                if next_url and next_url != current_url:
                    current_url = next_url
                else:
                    break
            except Exception as e:
                self.logger.log(f"❌ Erro ao processar página {page_count}: {str(e)}", "ERROR", "❌")
                break

        result = [u for u in prod if "/albums/" in u and u != url]
        self.logger.log(f"✅ Yupoo coleta concluída: {len(result)} álbuns encontrados", "SUCCESS", "✅")
        return result
