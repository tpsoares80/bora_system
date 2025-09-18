# Módulo: size_rules.py
# Função: normaliza/expande tamanhos conforme TXT. Corrige S-2XL (inclui XXL) e S-4XL (inclui XXXXL).

import re

ADULTO_DEFAULT = "S, M, L, XL, XXL"
KIDS_DEFAULT = "16, 18, 20, 22, 24, 26, 28"

_order = ["S","M","L","XL","XXL","XXXL","XXXXL"]

def _expand_interval(token: str) -> str:
    token = token.upper().replace("XG", "XL")
    if not token.startswith("S-"):
        return ""
    end = token.split("S-")[-1]
    # 2XL / 3XL / 4XL
    m = re.fullmatch(r"(\d)XL", end)
    if m:
        n = int(m.group(1))
        idx = 2 + n  # S,M,L = 3 itens base -> +n para XLs
        return ", ".join(_order[:idx])
    # XXL / XXXL / XXXXL
    if end in _order:
        idx = _order.index(end) + 1
        return ", ".join(_order[:idx])
    return ""

def normalize_sizes(album_title: str, raw: str|None) -> str:
    title = (album_title or "").lower()
    if "kid" in title or "kids" in title:
        return KIDS_DEFAULT

    txt = (raw or "").strip()
    # Sanitização de resíduos (S-XXL9 -> S-XXL, S-2XL2 -> S-2XL)
    txt = re.sub(r"(S-\s*X{1,4}L)\d+", r"\1", txt, flags=re.I)
    txt = re.sub(r"(S-\s*\dXL)\d*", r"\1", txt, flags=re.I)

    m = re.search(r"S\s*-\s*(\dXL|X{1,4}L)", txt, flags=re.I)
    if m:
        expanded = _expand_interval("S-" + m.group(1).upper())
        if expanded:
            return expanded

    tokens = re.findall(r"\b(XXXXL|XXXL|XXL|XL|L|M|S)\b", txt.upper())
    if tokens:
        seen, out = set(), []
        for t in tokens:
            if t not in seen:
                seen.add(t); out.append(t)
        out.sort(key=lambda x: _order.index(x))
        return ", ".join(out)

    return ADULTO_DEFAULT
