# -*- coding: utf-8 -*-
"""
image_downloader.py — Orquestrador do download de imagens
- Integra com a UI (bora.py/interface_manager.py)
- Lê configurações (config.json na raiz OU system/config.json)
- Roteia para Yupoo (Selenium) e WordPress (HTTP)
- Suporta cancelamento solicitado na UI
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

# Estado global simples
_CANCEL = False
_LOGGER = None


def set_system_logger(logger) -> None:
    global _LOGGER
    _LOGGER = logger


def request_cancel() -> None:
    global _CANCEL
    _CANCEL = True
    if _LOGGER:
        _LOGGER.log("Cancelamento solicitado pelo usuário", "WARNING", "⏹️")


def _log(msg: str, level: str = "INFO", emoji: str = "ℹ️") -> None:
    if _LOGGER:
        _LOGGER.log(msg, level, emoji)


# ------------------------------- Config -------------------------------

def _load_config() -> Dict:
    """Lê config da raiz (config.json) ou fallback em system/config.json."""
    for p in (Path("config.json"), Path("system/config.json")):
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


# ------------------------------- Entrada ------------------------------

def _iter_items_from_json(path: Path) -> Iterable[Dict]:
    """Retorna itens do JSON com pelo menos album_url e (se houver) album_folder_name."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        _log(f"Erro ao ler JSON {path.name}: {e}", "ERROR", "❌")
        return []

    items: List[Dict] = []
    if isinstance(data, list):
        items = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict):
        for k in ("produtos", "produtos_extraidos", "items", "data"):
            v = data.get(k)
            if isinstance(v, list):
                items = [x for x in v if isinstance(x, dict)]
                break

    for it in items:
        url = it.get("album_url")
        if url:
            yield {
                "album_url": url,
                "album_folder_name": it.get("album_folder_name"),
            }


def _classify(url: str) -> str:
    return "yupoo" if ".yupoo.com" in url else "wordpress"


# ------------------------------ Execução ------------------------------

def main_integrated(system_logger=None, selected_files: Optional[List[Path]] = None) -> Dict[str, object]:
    """Entrada padrão chamada pelo bora.py.
    selected_files: lista de Path (provocado) ou None (autônomo → usa último JSON por timestamp no nome)
    """
    global _CANCEL
    _CANCEL = False
    if system_logger:
        set_system_logger(system_logger)

    cfg = _load_config()
    id_cfg = cfg.get("image_downloader", {})
    ua = id_cfg.get("user_agent")
    timeout = float(id_cfg.get("timeout", 12.0))
    delay = float(id_cfg.get("delay_between_images", 0.8))
    referer_all = bool(id_cfg.get("referer_all_images", False))
    headless = bool(id_cfg.get("headless", True))
    min_kb = int(cfg.get("tamanho_minimo_imagem", 50))

    out_root = Path("./imagens"); out_root.mkdir(exist_ok=True)

    # modo autônomo → pega JSON mais recente pelo timestamp no nome
    if not selected_files:
        meta = Path("Metadados")
        files = sorted(meta.glob("*.json"), key=lambda p: p.name, reverse=True)
        selected_files = files[:1]
        if selected_files:
            _log(f"Modo autônomo: {selected_files[0].name}", "INFO", "🧭")
        else:
            _log("Modo autônomo: nenhum JSON encontrado em Metadados", "WARNING", "📁")
            return {"success": False, "total_albums": 0, "cancelled": False}
    else:
        _log(f"Modo provocado: {len(selected_files)} arquivo(s)", "INFO", "📁")

    # instanciar provedores
    from system.imgdownloader.yupoo import YupooDownloader
    from system.imgdownloader.wordpress import WordPressDownloader

    yup = YupooDownloader(logger=_LOGGER, user_agent=ua, timeout=timeout, delay=delay,
                          referer_all=referer_all, headless=headless, min_kb=min_kb, out_root=out_root)
    wp = WordPressDownloader(logger=_LOGGER, user_agent=ua, timeout=timeout, delay=delay,
                             referer_all=referer_all, min_kb=min_kb, out_root=out_root)

    total = 0
    ok = True

    for jf in selected_files or []:
        if _CANCEL:
            break
        _log(f"📁 Arquivo: {jf.name}", "INFO", "📁")
        for it in _iter_items_from_json(jf):
            if _CANCEL:
                break
            url = it["album_url"]; folder = it.get("album_folder_name")
            prov = _classify(url)
            _log(f"📁 Álbum: {folder} ", "INFO", "📁")
            _log(f"🔍 URL: {url}  [{prov}]", "INFO", "🔍")
            try:
                if prov == "yupoo":
                    yup.process_album(url, album_folder_name=folder)
                else:
                    wp.process_page(url, album_folder_name=folder)
                total += 1
            except Exception as e:
                ok = False
                _log(f"Falha no álbum: {url} → {e}", "ERROR", "❌")

    if _CANCEL:
        _log("Download cancelado pelo usuário", "WARNING", "⏹️")
    else:
        _log("Processo de download finalizado", "SUCCESS", "✅")

    return {"success": ok and not _CANCEL, "total_albums": total, "cancelled": _CANCEL}


# --------------------------- Compatibilidade UI ---------------------------

def run_from_ui(mode: str, selected: Optional[List[Union[str, Path]]], system_logger=None) -> Dict[str, object]:
    """Wrapper compatível com callbacks da UI.
    mode: "provocado" | "autonomo" (ignoramos o valor internamente)
    selected: lista de caminhos (str/Path) ou None
    """
    paths: Optional[List[Path]] = None
    if selected:
        paths = [Path(s) for s in selected]
    return main_integrated(system_logger=system_logger, selected_files=paths)
