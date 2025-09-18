# Módulo: price_mark.py
# Função: persistir e validar prices.json (preço padrão + palavras-chave com desconto_percentual).

import json
from pathlib import Path

PRICES_PATHS = [
    Path(__file__).resolve().parent / 'prices.json',
    Path(__file__).resolve().parent.parent / 'prices.json'
]

def _load_json():
    for p in PRICES_PATHS:
        try:
            if p.exists():
                return json.loads(p.read_text(encoding='utf-8')), p
        except Exception:
            continue
    # default vazio
    data = {"preco_padrao": {"preco": 0.0, "preco_promocional": 0.0}, "palavras_chave": {}}
    path = PRICES_PATHS[0]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data, path

def _save_json(data, path=None):
    if path is None:
        _, path = _load_json()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def get_all():
    data, path = _load_json()
    return data

def set_defaults(preco: str, promo: str):
    data, path = _load_json()
    def _num(x):
        if isinstance(x, str): x = x.replace(',', '.')
        try: return round(float(x), 2)
        except: return 0.0
    p = max(0.0, _num(preco))
    pp = max(0.0, _num(promo))
    if pp > p: pp = 0.0  # regra: promo não pode ser > preço
    data["preco_padrao"] = {"preco": p, "preco_promocional": pp}
    _save_json(data, path)

def upsert_keyword(name: str, preco: str, promo: str = '', desconto_percentual: str = ''):
    data, path = _load_json()
    key = (name or '').strip()
    if not key: raise ValueError("nome_identificador obrigatório")
    def _num(x):
        if isinstance(x, str): x = x.replace(',', '.')
        try: return round(float(x), 2)
        except: return 0.0
    p = max(0.0, _num(preco))
    pp = _num(promo)
    dp = _num(desconto_percentual)
    if dp and p:  # calc promo a partir do percentual
        if dp <= 0 or dp >= 100: dp = 0.0
        if dp: pp = round(p * (1 - dp/100.0), 2)
    if pp > p:  # regra de bloqueio
        raise ValueError("Não Permitido! Preço promocional superior ao preço normal. Corrija.")
    data.setdefault("palavras_chave", {})[key] = {
        "preco": p,
        "preco_promocional": pp if pp>0 else 0.0,
        "desconto_percentual": dp if dp>0 else 0.0
    }
    _save_json(data, path)

def delete_keyword(name: str):
    data, path = _load_json()
    key = (name or '').strip()
    if key in data.get("palavras_chave", {}):
        del data["palavras_chave"][key]
        _save_json(data, path)
