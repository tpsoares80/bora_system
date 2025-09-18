# -*- coding: utf-8 -*-
"""
WordPressDownloader (HTTP)
- Extrai SOMENTE as imagens da galeria do produto (ignora relacionadas/upsells/rodapé).
- Escopo: bloco "div.product" → 
  [ .woocommerce-product-gallery | div.images | figure.woocommerce-product-gallery__wrapper ]
- Coleta: <a href>, <img src/srcset>, <source srcset>, e data-* (data-large_image, data-src, data-full, data-large_file)
- Normaliza URLs removendo sufixos -WxH e -scaled
- Referer: URL da página do produto
- Saída unificada com Yupoo: ./imagens/{album_folder_name}/
  * Para WordPress o nome do arquivo é: wp-imagem-nnn.ext
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import time
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class _Cfg:
    ua: str
    timeout: float
    delay: float
    referer_all: bool
    min_kb: int
    out_root: Path


class WordPressDownloader:
    def __init__(
        self,
        logger,
        user_agent: Optional[str],
        timeout: float,
        delay: float,
        referer_all: bool,
        min_kb: int,
        out_root: Path,
    ) -> None:
        # Logger compatível com logger.log(msg, level, emoji)
        self._log = (lambda m, l="INFO", e="ℹ️": logger.log(m, l, e)) if logger else (lambda *a, **k: None)
        cfg = _Cfg(
            ua=(
                user_agent
                or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            timeout=float(timeout),
            delay=float(delay),
            referer_all=bool(referer_all),  # compatibilidade
            min_kb=int(min_kb),
            out_root=Path(out_root) if out_root else Path("imagens"),
        )
        self.cfg = cfg

    # -------------------------- Helpers --------------------------
    @staticmethod
    def _sanitize_folder_from_url(page_url: str) -> str:
        """Fallback para album_folder_name, derivado da URL."""
        u = urlparse(page_url)
        base = f"{u.netloc}{u.path}"
        name = re.sub(r"[\\/:*?\"<>|]", "-", base)  # inválidos Windows
        name = re.sub(r"\s+", "-", name)
        name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
        name = re.sub(r"-+", "-", name).strip("-._")
        return name or "pagina"

    @staticmethod
    def _normalize_upload_url(url: str) -> str:
        # remove sufixos de resize do WordPress
        url = re.sub(r"-\d+x\d+(?=\.(?:jpg|jpeg|png|webp|gif|svg)\b)", "", url, flags=re.I)
        url = re.sub(r"-scaled(?=\.(?:jpg|jpeg|png|webp)\b)", "", url, flags=re.I)
        # remove query-string
        return url.split("?")[0]

    @staticmethod
    def _pick_biggest_from_srcset(srcset: str) -> Optional[str]:
        # pega maior largura listada
        try:
            parts: List[str] = [p.strip() for p in srcset.split(",") if p.strip()]
            best_url = None
            best_w = -1
            for p in parts:
                t = p.split()
                if not t:
                    continue
                url = t[0]
                w = 0
                if len(t) > 1 and t[1].lower().endswith("w"):
                    try:
                        w = int(re.sub(r"\D", "", t[1]))
                    except Exception:
                        w = 0
                if w >= best_w:
                    best_w = w
                    best_url = url
            return best_url
        except Exception:
            return None

    def _create_output_folder(self, album_folder_name: Optional[str], page_url: str) -> Path:
        name = album_folder_name or self._sanitize_folder_from_url(page_url)
        folder = self.cfg.out_root / name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @staticmethod
    def _is_upload(url: str) -> bool:
        return "/wp-content/uploads/" in url

    def _collect_from_container(self, root) -> List[str]:
        urls: List[str] = []
        seen: Set[str] = set()

        def add(u: Optional[str]):
            if not u:
                return
            u = self._normalize_upload_url(u.strip())
            if self._is_upload(u) and u not in seen:
                seen.add(u)
                urls.append(u)

        # <a href>
        for a in root.find_all("a", href=True):
            add(a["href"])

        # <img src> e srcset
        for img in root.find_all("img"):
            add(img.get("src"))
            srcset = img.get("srcset")
            if srcset:
                add(self._pick_biggest_from_srcset(srcset))
            # atributos comuns em WooCommerce/temas
            add(img.get("data-large_image"))
            add(img.get("data-src"))
            add(img.get("data-full"))
            add(img.get("data-large_file"))

        # <source srcset>
        for source in root.find_all("source"):
            srcset = source.get("srcset")
            if srcset:
                add(self._pick_biggest_from_srcset(srcset))

        return urls

    def _extract_image_urls(self, page_url: str) -> List[str]:
        headers = {"User-Agent": self.cfg.ua, "Referer": page_url}
        r = requests.get(page_url, headers=headers, timeout=self.cfg.timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # 1) Escopo: SOMENTE o bloco do produto
        product_root = soup.select_one("div.product, div[id^=product-].product")
        if not product_root:
            # fallback conservador: ainda assim removemos seções de relacionadas
            for s in soup.select(".related, .upsells, .cross-sells, section.related"):
                s.decompose()
            product_root = soup

        # 2) Preferir containers da galeria
        gallery = product_root.select_one(
            ".woocommerce-product-gallery, div.images, figure.woocommerce-product-gallery__wrapper"
        )
        container = gallery or product_root

        urls = self._collect_from_container(container)
        return urls

    def _download(self, img_url: str, referer: str, dest: Path) -> bool:
        headers = {"User-Agent": self.cfg.ua, "Referer": referer}
        with requests.get(img_url, headers=headers, timeout=self.cfg.timeout, stream=True) as r:
            r.raise_for_status()
            size_kb = int(r.headers.get("Content-Length", 0)) // 1024
            if size_kb and size_kb < self.cfg.min_kb:
                self._log(f"Ignorado (< {self.cfg.min_kb} KB): {img_url}", "WARNING", "🪶")
                return False
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1024 * 64):
                    if not chunk:
                        continue
                    f.write(chunk)
        return True

    # -------------------------- API pública --------------------------
    def process_page(
        self,
        page_url: str,
        cancel_event: Optional[object] = None,
        album_folder_name: Optional[str] = None,
    ) -> None:
        """Baixa somente as imagens da galeria do produto (ignora relacionadas).
        - Pasta: ./imagens/{album_folder_name}/ (mesma regra do Yupoo)
        - Arquivo: wp-imagem-nnn.ext
        """
        folder = self._create_output_folder(album_folder_name, page_url)
        urls = self._extract_image_urls(page_url)
        if not urls:
            self._log(f"Nenhuma imagem encontrada em {page_url}", "WARNING", "🫙")
            return

        self._log(f"{len(urls)} imagem(ns) em {page_url}", "INFO", "🖼️")
        pendentes = []
        name_map = {}
        seq = 1
        for u in urls:
            if cancel_event and getattr(cancel_event, "is_set", lambda: False)():
                self._log("Cancelado pelo usuário", "WARNING", "⏹️")
                break

            path_ext = Path(urlparse(u).path).suffix.lower() or ".jpg"
            dest = folder / f"wp-imagem-{seq:03d}{path_ext}"
            name_map[u] = dest.name

            try:
                ok = self._download(u, referer=page_url, dest=dest)
                if ok:
                    self._log(
                        f"OK {dest.name} | bytes={dest.stat().st_size} | src={u}",
                        "SUCCESS",
                        "✅",
                    )
                    seq += 1
            except Exception as e:
                pendentes.append(u)
                self._log(f"Erro ao baixar {u} → {e}", "ERROR", "❌")

            time.sleep(self.cfg.delay)
        # ## PATCH RETRY pendentes após loop
        if pendentes:
            for delay in (0, 3, 2):
                if not pendentes:
                    break
                novos = []
                if delay:
                    time.sleep(delay)
                for href in pendentes:
                    try:
                        name = name_map.get(href) or f"retry-{os.path.basename(href)}"
                        dest = folder / name
                        ok = self._download(href, referer=page_url, dest=dest)
                        if ok:
                            self._log(f"OK (retry) {dest.name}", "SUCCESS", "✅")
                        else:
                            novos.append(href)
                    except Exception as e:
                        self._log(f"Falha retry {href}: {e}", "ERROR", "❌")
                        novos.append(href)
                pendentes = novos
