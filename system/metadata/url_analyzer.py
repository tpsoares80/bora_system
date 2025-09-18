# Módulo: url_analyzer.py
# Função: detectar plataforma (WordPress/Yupoo) e entidade (produto|categoria).
# Chamadas: usado por DataProcessor/CategoryCrawler. Atualizado p/ tratar Yupoo search como categoria.

from urllib.parse import urlparse, parse_qs

class URLAnalyzer:
    @staticmethod
    def analyze(url: str) -> dict:
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        qs = parse_qs(urlparse(url).query)

        # WordPress
        if host.endswith(("soccer-jersey-yupoo.com",)):
            if "/product/" in path:
                return {"platform": "wordpress", "entity": "produto"}
            # buscas e coleções
            if path.endswith(("/search/", "/search")) or "s" in qs or "post_type" in qs or "/category/" in path or "/categories" in path or "/collection" in path:
                return {"platform": "wordpress", "entity": "categoria"}
            return {"platform": "wordpress", "entity": "desconhecido"}

        # Yupoo
        if ".yupoo.com" in host:
            if "/albums/" in path:
                return {"platform": "yupoo", "entity": "produto"}
            # buscas de álbum (categoria)
            if "/search/album" in path or "q" in qs:
                return {"platform": "yupoo", "entity": "categoria"}
            return {"platform": "yupoo", "entity": "categoria"}

        return {"platform": "desconhecido", "entity": "desconhecido"}
