# -*- coding: utf-8 -*-
"""
YupooDownloader (Selenium)
- Lê diretamente os atributos `data-origin-src` na página do álbum.
- Mantém fallback por página de foto (botão "Imagem Original").
- Referer: 1ª imagem do álbum sempre; todas se `referer_all`=True (config).
- Manifest 1 por URL.
"""
from __future__ import annotations

import json, os, time
from pathlib import Path
from typing import List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class YupooDownloader:
    def __init__(self, logger, user_agent: Optional[str], timeout: float, delay: float,
                 referer_all: bool, headless: bool, min_kb: int, out_root: Path):
        self.log = (lambda m, l="INFO", e="ℹ️": logger.log(m, l, e)) if logger else (lambda *a, **k: None)
        self.ua = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        self.timeout = float(timeout)
        self.delay = float(delay)
        self.referer_all = bool(referer_all)
        self.headless = bool(headless)
        self.min_kb = int(min_kb)
        self.out_root = out_root

    # ----------------------------- Selenium -----------------------------
    def _driver(self):
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"user-agent={self.ua}")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=1280,1200")

        # 🔧 Caminho real do Chrome
        opts.binary_location = "/usr/bin/google-chrome"


        # 🔧 Caminho correto do Chromedriver
        service = Service("/usr/bin/chromedriver")
        return webdriver.Chrome(service=service, options=opts)






    # ----------------------------- Helpers ------------------------------
    def _album_folder(self, album_url: str, album_folder_name: Optional[str]) -> Path:
        base = (album_folder_name or album_url.split("/albums/")[-1].split("?")[0]).strip()
        safe = base.replace("/", "-")
        d = self.out_root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _download(self, url: str, referer: str, dest: Path) -> int:
        headers = {"User-Agent": self.ua, "Referer": referer}
        with requests.get(url, headers=headers, timeout=self.timeout, stream=True) as r:
            r.raise_for_status()
            size_kb = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(64 * 1024):
                    if chunk:
                        f.write(chunk)
                        size_kb += len(chunk) // 1024
        return size_kb

    def _wait(self, drv, by, sel, t=None):
        return WebDriverWait(drv, t or (self.timeout + 8)).until(
            EC.presence_of_element_located((by, sel))
        )

    def _scroll_until_loaded(self, drv, max_rounds: int = 8):
        last_h, stable = 0, 0
        for _ in range(max_rounds):
            drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)
            h = drv.execute_script("return document.body.scrollHeight || 0;")
            if h == last_h:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last_h = h
        try:
            self._wait(drv, By.CSS_SELECTOR, "[data-origin-src]", t=self.timeout)
        except Exception:
            pass

    def _collect_originals_from_album(self, drv) -> List[str]:
        els = drv.find_elements(By.CSS_SELECTOR, "[data-origin-src]")
        originals, seen = [], set()
        for el in els:
            v = (el.get_attribute("data-origin-src") or "").strip()
            if not v:
                continue
            if v.startswith("//"):
                v = "https:" + v
            elif v.startswith("/"):
                v = "https://photo.yupoo.com" + v
            if v not in seen:
                seen.add(v)
                originals.append(v)
        return originals

    # ------ Fallback (página da foto) ------
    def _gather_photo_links(self, drv) -> List[str]:
        try:
            self._wait(drv, By.CSS_SELECTOR, 'a[href*="?uid="] img', t=self.timeout)
        except Exception:
            pass
        hrefs = []
        for a in drv.find_elements(By.CSS_SELECTOR, 'a[href*="?uid="]'):
            h = a.get_attribute("href") or ""
            if h and "/albums/" not in h and h not in hrefs:
                hrefs.append(h)
        try:
            js = ("return Array.from(document.querySelectorAll('a'))"
                  ".map(a=>a.href).filter(h=>h && /\\/\\d+\\?uid=/.test(h) && !/\\/albums\\//.test(h));")
            extra = drv.execute_script(js) or []
            for h in extra:
                if h not in hrefs:
                    hrefs.append(h)
        except Exception:
            pass
        return hrefs

    def _extract_original_from_photo(self, drv) -> Optional[str]:
        try:
            el = WebDriverWait(drv, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="photo.yupoo.com"]'))
            )
            href = el.get_attribute("href")
            if href:
                return href
        except Exception:
            pass
        try:
            js = (
                "const pick=(srcset)=>{if(!srcset) return null; const arr=srcset.split(',').map(s=>s.trim());"
                "arr.sort((a,b)=>{const wa=(a.match(/(\\d+)w/)||[0,0])[1]|0; const wb=(b.match(/(\\d+)w/)||[0,0])[1]|0; return wb-wa;});"
                "return (arr[0]||'').split(' ')[0];};"
                "for (const img of document.querySelectorAll('img')) {"
                "  const cand = img.getAttribute('data-original')||img.getAttribute('data-raw')||img.getAttribute('data-src')||img.getAttribute('src');"
                "  if (cand && cand.includes('photo.yupoo.com')) return cand;"
                "  const ss = pick(img.getAttribute('srcset'));"
                "  if (ss && ss.includes('photo.yupoo.com')) return ss;"
                "}"
                "return null;"
            )
            href = drv.execute_script(js)
            if href:
                return href
        except Exception:
            pass
        try:
            js = (
                "let txt=''; for (const s of document.scripts){ txt += (s.textContent||'')+'\\n'; }"
                "const m = txt.match(/https:\\/\\/photo\\.yupoo\\.com\\/[^\"'\\s<>]+?\\.(?:jpe?g|png|webp)/i);"
                "return m?m[0]:null;"
            )
            href = drv.execute_script(js)
            if href:
                return href
        except Exception:
            pass
        return None

    # ------------------------------ Público ------------------------------
    def process_album(self, album_url: str, album_folder_name: Optional[str] = None, cancel_event=None):
        folder = self._album_folder(album_url, album_folder_name)

        drv = self._driver()
        try:
            drv.set_page_load_timeout(self.timeout + 15)
            drv.get(album_url)
            try:
                self._wait(drv, By.TAG_NAME, "body", t=self.timeout)
            except Exception:
                pass

            # 1) Preferido: data-origin-src no álbum
            self._scroll_until_loaded(drv)
            originals = self._collect_originals_from_album(drv)

            # 2) Fallback: páginas de foto
            if not originals:
                self.log("data-origin-src não encontrado; usando fallback por página de foto", "WARNING", "⚠️")
                for purl in self._gather_photo_links(drv):
                    if cancel_event and cancel_event.is_set():
                        break
                    try:
                        drv.get(purl)
                        try:
                            self._wait(drv, By.TAG_NAME, "body", t=self.timeout)
                        except Exception:
                            pass
                        href = self._extract_original_from_photo(drv)
                        if href:
                            originals.append(href)
                    except Exception as e:
                        self.log(f"Erro na página {purl}: {e}", "ERROR", "❌")

            if not originals:
                self.log("Nenhuma imagem original encontrada", "WARNING", "⚠️")
                return

            # Download serial mantendo a página do álbum aberta
            seq = 1
            pendentes = []
            name_map = {}
            for href in originals:
                if cancel_event and cancel_event.is_set():
                    break
                try:
                    base = os.path.basename(href.split("?")[0]) or f"img{seq:03d}"
                    root, ext = os.path.splitext(base)
                    if not ext:
                        ext = ".jpg"
                    name = f"imagem-{seq:03d}{ext}"
                    name_map[href] = name
                    dest = folder / name

                    ref = album_url if (seq == 1 or self.referer_all) else album_url
                    size_kb = self._download(href, referer=ref, dest=dest)
                    if size_kb < self.min_kb:
                        self.log(f"Descartada (pequena) {name} ({size_kb}KB)", "WARNING", "⚠️")
                        dest.unlink(missing_ok=True)
                        seq += 1
                        continue

                    man = {
                        "page_url": album_url,
                        "original_image_url": href,
                        "saved_path": str(dest),
                        "bytes": dest.stat().st_size,
                        "referer_applied": ref,
                    }
                    #with open(folder / f"manifest_{seq:03d}.json", "w", encoding="utf-8") as f:
                    #    json.dump(man, f, ensure_ascii=False, indent=2)

                    self.log(f"OK {name}", "SUCCESS", "✅")
                    seq += 1
                    time.sleep(self.delay)
                except Exception as e:
                    self.log(f"Falha download {href}: {e}", "ERROR", "❌")
                    pendentes.append(href)
                    seq += 1
                    continue
            # ## PATCH RETRY pendentes
            if pendentes:
                for delay in (0, 3, 2):
                    if not pendentes:
                        break
                    novos = []
                    if delay:
                        time.sleep(delay)
                    for href in pendentes:
                        try:
                            name = name_map.get(href) or os.path.basename(href.split("?")[0]) or "img.jpg"
                            dest = folder / name
                            ref = album_url
                            size_kb = self._download(href, referer=ref, dest=dest)
                            if size_kb < self.min_kb:
                                dest.unlink(missing_ok=True)
                                novos.append(href)
                            else:
                                self.log(f"OK (retry) {name}", "SUCCESS", "✅")
                        except Exception as e:
                            self.log(f"Falha retry {href}: {e}", "ERROR", "❌")
                            novos.append(href)
                    pendentes = novos

        finally:
            try:
                drv.quit()
            except Exception:
                pass
