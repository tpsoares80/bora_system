from __future__ import annotations

# --- Hotfix: normalização de URLs de imagens (Yupoo) ---
def _normalize_image_url(url: str) -> str | None:
    """
    Retorna URL normalizada para a melhor qualidade disponível.
    Regras:
      - aceitar somente host *.photo.yupoo.com
      - sempre HTTPS
      - promover tamanhos: thumb/small/medium -> large
      - remover querystring/fragment
      - descartar URLs inválidas/ícones (hosts como s.yupoo.com)
    """
    if not url:
        return None
    try:
        # tratar protocolo relativo
        if url.startswith("//"):
            url = "https:" + url
        parts = urlparse(url)
        host = parts.netloc.lower()
        if not host.endswith("photo.yupoo.com"):
            return None  # descarta ícones e domínios que não são de fotos
        scheme = "https"
        path = parts.path

        # heurísticas comuns de tamanhos
        # exemplos: /.../thumb.jpg, /.../small.jpg, /.../medium.jpg
        #           /.../small.png, /.../medium.jpeg
        basename = Path(path).name
        promoted = basename
        promoted = re.sub(r"(?i)\bthumb\.(jpg|jpeg|png|webp)$", r"large.\1", promoted)
        promoted = re.sub(r"(?i)\bsmall\.(jpg|jpeg|png|webp)$", r"large.\1", promoted)
        promoted = re.sub(r"(?i)\bmedium\.(jpg|jpeg|png|webp)$", r"large.\1", promoted)
        # alguns path patterns usam .../small/arquivo.jpg
        path = re.sub(r"(?i)/thumb/", "/large/", path)
        path = re.sub(r"(?i)/small/", "/large/", path)
        path = re.sub(r"(?i)/medium/", "/large/", path)

        if promoted != Path(path).name:
            # substitui somente o nome do arquivo, preservando diretórios
            path = str(Path(path).parent / promoted)

        # monta sem query/fragment
        cleaned = urlunparse((scheme, parts.netloc, path, "", "", ""))
        return cleaned
    except Exception:
        return None
# --- Fim Hotfix ---

# -*- coding: utf-8 -*-
"""
MÓDULO: metadata_generator.py
Funções/Classes:
- class MetadataGenerator: gera arquivo JSON de metadados padronizado.
Entradas esperadas:
- lista de produtos (dicts) com, preferencialmente, as chaves: album_url, album_id, album_title, page_title, sizes, image_urls
Interage com:
- data_processor_main.DataProcessor (chama este gerador ao final do pipeline)
Contrato:
- Não altera interface da aplicação (bora.py)
"""

import os
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

WINDOWS_FORBIDDEN = set('<>:"/\\|?*')

def _sanitize_folder_name(name: str) -> str:
    # normaliza 25/26 → 25-26
    name = name.replace('25/26', '25-26').replace('24/25', '24-25').replace('23/24', '23-24')
    # remove sufixos de site comuns
    for suf in (' | Yupoo', ' | 又拍图片管家', '| Yupoo', '| 又拍图片管家'):
        name = name.replace(suf, '').strip()
    # remove dígitos-resíduo logo após variação de tamanho (ex.: S-XXL9 → S-XXL)
    name = re.sub(r'(S-X{0,4}XL|S-\dXL)\d+\b', r'\1', name, flags=re.IGNORECASE)
    # sanitiza para Windows
    name = ''.join('_' if ch in WINDOWS_FORBIDDEN else ch for ch in name)
    # remove pontos/espaços finais
    return name.rstrip(' .')

def _clean_title(s: str) -> str:
    if not s:
        return ''
    s = s.strip()
    # remove parte do site após pipe
    s = s.split('|', 1)[0].strip()
    # normalizações simples
    s = s.replace('25/26', '25-26').replace('24/25', '24-25').replace('23/24', '23-24')
    return s

def _longest_common_substring(a: str, b: str) -> str:
    if not a or not b:
        return ''
    a, b = a.strip(), b.strip()
    # DP simples para LCS (substring contígua)
    m, n = len(a), len(b)
    dp = [0] * (n + 1)
    longest_len = 0
    end_pos = 0
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i-1] == b[j-1]:
                dp[j] = prev + 1
                if dp[j] > longest_len:
                    longest_len = dp[j]
                    end_pos = i
            else:
                dp[j] = 0
            prev = temp
    return a[end_pos - longest_len:end_pos] if longest_len else ''

def _compute_album_folder_name(album_title: str, page_title: str) -> str:
    a = _clean_title(album_title or '')
    p = _clean_title(page_title or '')
    if not a and p:
        name = p
    elif not p and a:
        name = a
    else:
        common = _longest_common_substring(a, p)
        # se a interseção for muito curta, prefira o menor título não vazio
        name = common if len(common) >= 6 else (a if a and len(a) <= len(p) else p)
    return _sanitize_folder_name(name)

def _expand_sizes_from_range(range_str: str) -> Optional[str]:
    if not range_str:
        return None
    s = range_str.upper()
    s = re.sub(r'\d+\b$', '', s)  # remove dígito-resíduo no fim (S-4XL9 → S-4XL)
    # padrões S-2XL, S-3XL, S-4XL etc
    m = re.match(r'^S-(\d)XL$', s)
    if m:
        upto = int(m.group(1))
        base = ['S','M','L','XL']
        plus = ['XXL','XXXL','XXXXL','XXXXXL']
        return ' '.join(base + plus[:max(0, upto-1)])
    # padrões S-XXL, S-XXXL, S-XXXXL...
    m2 = re.match(r'^S-(X{2,5})L$', s)
    if m2:
        x_count = len(m2.group(1))
        base = ['S','M','L','XL']
        plus = ['XXL','XXXL','XXXXL','XXXXXL','XXXXXXL']
        return ' '.join(base + plus[:max(0, x_count-1)])
    return None

def _parse_sizes(album_title: str, current_sizes: Optional[str]) -> Optional[str]:
    t = (album_title or '').lower()
    if 'kids' in t:
        return '16 18 20 22 24 26 28'
    # já é uma lista explícita?
    if current_sizes and re.search(r'\bS\b.*\bM\b.*\bL\b', current_sizes.upper()):
        return ' '.join(re.findall(r'S|M|L|XL|XXL|XXXL|XXXXL|XXXXXL', current_sizes.upper()))
    # tenta capturar intervalo no título
    m = re.search(r'(S-[0-9]XL|S-XX{1,5}L)', album_title.upper())
    if m:
        expanded = _expand_sizes_from_range(m.group(1))
        if expanded:
            return expanded
    # fallback adulto padrão
    return current_sizes or 'S M L XL XXL'

class MetadataGenerator:
    def __init__(self, logger=None, config_manager=None):
        self.logger = logger
        self.config_manager = config_manager

    def gerar_arquivo(self, produtos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera o JSON de metadados simplificado no padrão exigido.
        Retorna dict com caminho do arquivo e estatísticas.
        """
        if self.logger:
            try:
                self.logger.info('📄 Iniciando geração do arquivo de metadados simplificado')
            except Exception:
                pass

        out_dir = 'Metadados'
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        out_path = os.path.join(out_dir, f'metadados_simples_{ts}.json')

        saida: List[Dict[str, Any]] = []
        for p in produtos or []:
            album_url = p.get('album_url') or p.get('url') or ''
            album_id = p.get('album_id') or ''
            album_title = p.get('album_title') or ''
            page_title = p.get('page_title') or p.get('title') or ''
            sizes_in = p.get('sizes') or ''
            sizes_out = _parse_sizes(album_title, sizes_in)
            folder = _compute_album_folder_name(album_title, page_title)

            image_urls = []
            for key in ('image_urls', 'images', 'image_links', 'photos'):
                vals = p.get(key)
                if isinstance(vals, list):
                    image_urls.extend([v for v in vals if isinstance(v, str)])
            # dedupe preservando ordem
            seen = set()
            ordered = []
            for u in image_urls:
                if u not in seen:
                    seen.add(u)
                    ordered.append(u)

            item = {
                'album_url': album_url,
                'album_id': album_id if album_id else self._derive_album_id(album_url),
                'album_title': album_title,
                'page_title': page_title,
                'album_folder_name': folder,
                'sizes': sizes_out,
                'image_urls': ordered,
            }
            saida.append(item)

        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(saida, f, ensure_ascii=False, indent=2)

        if self.logger:
            try:
                self.logger.info(f'✅ Arquivo gerado: {os.path.basename(out_path)}')
            except Exception:
                pass

        return {'arquivo': out_path, 'qtd': len(saida), 'sucesso': True}

    @staticmethod
    def _derive_album_id(url: str) -> str:
        if not url:
            return ''
        # tenta extrair id numérico do caminho /albums/<id>
        m = re.search(r'/albums/(\d+)', url)
        if m:
            return m.group(1)
        # caso WordPress, usa o slug
        m2 = re.search(r'/product/([^/?#]+)/?', url)
        if m2:
            return m2.group(1)
        return url