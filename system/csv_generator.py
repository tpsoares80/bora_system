#!/usr/bin/env python3
# MÃ³dulo: csv_generator.py
# FunÃ§Ã£o: gerar CSV (30 colunas) a partir de metadados JSON.
# Regras: cabeÃ§alho csv_modelo.csv; UTF-8 BOM; ';'; 1 linha por tamanho;
# Identificador URL (slug de album_folder_name); Categorias (tipo,continente,pais,regiao-se-br,especial,genero);
# PreÃ§os: aplica preÃ§o padrÃ£o; se palavra-chave bater (palavra inteira), substitui; loga fonte do preÃ§o.
import os, re, json, unicodedata
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

class CSVGenerator:
    def __init__(self, logger=None, config_manager=None):
        self.log = logger
        self.config = config_manager
        if self.log: 
            try: self.log.log("CSVGenerator inicializado", "DEBUG", "🧩")
            except Exception: pass

    # Helpers
    @staticmethod
    def _strip_accents(text: str) -> str:
        if not text: return ''
        return unicodedata.normalize('NFKD', text).encode('ASCII','ignore').decode('ASCII')

    @staticmethod
    def _slug_from_name(name: str) -> str:
        s = CSVGenerator._strip_accents((name or '').lower())
        s = s.replace('/', '-').replace('\\', '-')
        s = re.sub(r'\s+', '-', s)
        s = re.sub(r'[^a-z0-9_-]+', '', s)
        s = re.sub(r'-{2,}', '-', s).strip('-')
        if len(s) > 120: s = s[:120].rstrip('-')
        return s

    @staticmethod
    def _norm(s: str) -> str:
        return CSVGenerator._strip_accents((s or '').lower())

    @staticmethod
    def _tokenize_words(s: str):
        return re.findall(r'[a-z0-9]+', CSVGenerator._norm(s))

    # Load tables
    def _load_equipes(self) -> Dict[str, Any]:
        candidates = [
            Path(__file__).resolve().parent / 'equipes.json',
            Path(__file__).resolve().parent.parent / 'equipes.json',
            Path(os.getcwd()) / 'equipes.json'
        ]
        for p in candidates:
            try:
                if p.exists():
                    return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                continue
        return {"times_brasileiros": {}, "times_internacionais": {}, "selecoes": {}}

    def _load_prices(self) -> Dict[str, Any]:
        candidates = [
            Path(__file__).resolve().parent / 'prices.json',
            Path(__file__).resolve().parent.parent / 'prices.json',
            Path(os.getcwd()) / 'prices.json'
        ]
        for p in candidates:
            try:
                if p.exists():
                    data = json.loads(p.read_text(encoding='utf-8'))
                    if isinstance(data, dict):
                        # sane defaults
                        data.setdefault("preco_padrao", {"preco": 0.0, "preco_promocional": 0.0})
                        data.setdefault("palavras_chave", {})
                        return data
            except Exception:
                continue
        return {"preco_padrao": {"preco":0.0, "preco_promocional":0.0}, "palavras_chave": {}}

    # Categorias
    def _scan_bucket(self, text: str, bucket: Dict[str, Any]):
        if not text: return None, 0
        key_norm = self._norm(text)
        best = None; best_len = 0
        for team_key, info in bucket.items():
            tk = self._norm(team_key)
            if tk and tk in key_norm and len(tk) > best_len:
                best = info; best_len = len(tk)
        return best, best_len

    def _team_info_for_product(self, product: Dict[str, Any]):
        buckets = self._equipes
        candidates = [
            product.get('category',''),
            product.get('team_brand',''),
            product.get('album_folder_name',''),
            product.get('album_title',''),
            product.get('page_title',''),
        ]
        for text in candidates:
            info,_ = self._scan_bucket(text, buckets.get('times_brasileiros',{}))
            if info: return info
            info,_ = self._scan_bucket(text, buckets.get('times_internacionais',{}))
            if info: return info
            info,_ = self._scan_bucket(text, buckets.get('selecoes',{}))
            if info: return info
        return {"tipo":"Outros","continente":"","pais":"","regiao":"","estado":"","is_national_team":False,"is_brazilian":False}

    def _especial_modelo(self, nome: str) -> str:
        n = self._norm(nome)
        if re.search(r'\bkids?\b', n): return "Infantil"
        if re.search(r'\bretro\b', n): return "Retrô"
        if re.search(r'\b(player|jogador|players)\b', n): return "Jogador"
        if re.search(r'\blong\s+sleeve\b', n): return "Manga Longa"
        return "Jovens e Adultos"

    def _genero(self, nome: str) -> str:
        n = self._norm(nome)
        return "Feminino" if re.search(r'\b(woman|women|female|feminino|feminina)\b', n) else "Unissex"

    def _categorias_str(self, product: Dict[str, Any], nome: str) -> str:
        info = self._team_info_for_product(product)
        tipo = info.get('tipo','Outros') or 'Outros'
        cont = info.get('continente','') or ''
        pais = info.get('pais','') or ''
        reg = info.get('regiao','') if info.get('is_brazilian') else ''
        esp = self._especial_modelo(nome)
        gen = self._genero(nome)
        return ','.join([tipo, cont, pais, reg or '', esp, gen])

    # Sizes
    SIZE_MAP = {
        "16": "16 - 2 a 3 anos",
        "18": "18 - 3 a 4 anos",
        "20": "20 - 4 a 5 anos",
        "22": "22 - 6 a 7 anos",
        "24": "24 - 8 a 9 anos",
        "26": "26 - 10 a 11 anos",
        "28": "28 - 12 a 13 anos",
        "S": "P", "M": "M", "L": "G", "XL": "XG",
        "XXL": "2XG", "XXXL": "3XG", "XXXXL": "4XG",
        "P":"P","G":"G","XG":"XG","2XG":"2XG","3XG":"3XG","4XG":"4XG"
    }

    def _sizes_from_json(self, product: Dict[str, Any]):
        sizes = (product.get('sizes') or '').strip()
        if not sizes: return []
        tokens = [t.strip() for t in sizes.replace(';',',').split(',') if t.strip()]
        out = []
        for t in tokens:
            key = t.strip().upper().replace(' ', '')
            key = key.replace('2XL','XXL').replace('3XL','XXXL').replace('4XL','XXXXL')
            out.append(self.SIZE_MAP.get(key, t.strip()))
        seen=set(); uniq=[]
        for x in out:
            if x not in seen:
                seen.add(x); uniq.append(x)
        return uniq

    # Prices
    def _price_for_name(self, nome: str) -> Tuple[str,str,str]:
        prices = self._prices or {}
        padrao = prices.get("preco_padrao", {"preco":0.0,"preco_promocional":0.0})
        preco = float(padrao.get("preco",0) or 0)
        promo = float(padrao.get("preco_promocional",0) or 0)

        source = "preço padrão"
        n_tokens = set(self._tokenize_words(nome))

        # match palabra inteira
        best = None
        for key, val in (prices.get("palavras_chave") or {}).items():
            if not isinstance(val, dict): continue
            k_tokens = set(self._tokenize_words(key))
            if not k_tokens: continue
            # palavra inteira: todos tokens da chave precisam estar em nome
            if not k_tokens.issubset(n_tokens): 
                continue
            ppromo = float(val.get('preco_promocional', 0) or 0)
            pfull  = float(val.get('preco', 0) or 0)
            if best is None or ppromo > best[0] or (ppromo == best[0] and pfull > best[1]):
                best = (ppromo, pfull, val, key)

        if best:
            promo = float(best[2].get('preco_promocional',0) or 0)
            preco = float(best[2].get('preco',0) or 0)
            source = f"palavra-chave: {best[3]}"

        preco_s = f"{preco:.2f}" if preco>0 else ""
        promo_s = f"{promo:.2f}" if promo>0 else ""
        return preco_s, promo_s, source

    @staticmethod
    def _headers() -> List[str]:
        return [
            'Identificador URL', 'Nome', 'Categorias',
            'Nome da variação 1', 'Valor da variação 1',
            'Nome da variação 2', 'Valor da variação 2',
            'Nome da variação 3', 'Valor da variação 3',
            'Preço', 'Preço promocional', 'Peso (kg)', 'Altura (cm)', 'Largura (cm)', 'Comprimento (cm)',
            'Estoque', 'SKU', 'Código de barras', 'Exibir na loja', 'Frete gratis',
            'Descrição', 'Tags', 'Título para SEO', 'Descrição para SEO', 'Marca', 'Produto Físico',
            'MPN (Cód. Exclusivo Modelo Fabricante)', 'Sexo', 'Faixa etária', 'Custo'
        ]

    def gerar_csv_ecommerce(self, produtos_combinados: List[Dict[str, Any]]) -> bool:
        """Gera CSV para e-commerce a partir de produtos combinados - CORRIGIDO"""
        try:
            self._equipes = self._load_equipes()
            self._prices = self._load_prices()
            if self.log:
                try: 
                    self.log.log("📚 Tabelas carregadas (equipes, prices)", "INFO", "📚")
                except Exception: 
                    pass

            if not produtos_combinados:
                if self.log:
                    try:
                        self.log.log("Nenhum produto para processar", "WARNING", "⚠️")
                    except Exception:
                        pass
                return False

            # Gera nome do arquivo
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"csv_gerados/catalogo_{ts}.csv"
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)

            rows: List[List[str]] = [self._headers()]

            for product in produtos_combinados:
                nome = product.get('album_folder_name') or product.get('album_title') or product.get('page_title') or 'Produto'
                identificador = self._slug_from_name(nome)
                categorias = self._categorias_str(product, nome)
                sexo = 'Feminino' if re.search(r'\b(woman|women|female|feminino|feminina)\b', self._norm(nome)) else 'Unissex'
                faixa = 'Infantil' if re.search(r'\bkids?\b', self._norm(nome)) else 'Jovens e Adultos'
                preco, promo, fonte = self._price_for_name(nome)

                if self.log:
                    try: 
                        self.log.log(f"Preço aplicado ({fonte}) → {preco}/{promo or '—'}", "DEBUG", "💲")
                    except Exception: 
                        pass

                sizes = self._sizes_from_json(product) or ['']

                for sz in sizes:
                    row = [
                        identificador, nome, categorias,
                        'Tamanho', sz,
                        '', '', '', '',
                        preco, promo, '0.250', '', '', '',
                        '', '', '', 'NÃO', '',
                        '', '', '', '', '', 'SIM',
                        '', sexo, faixa, ''
                    ]
                    rows.append([str(x) if x is not None else '' for x in row])

            with open(output_filename, 'w', encoding='utf-8-sig', newline='') as f:
                for row in rows:
                    f.write(';'.join(row) + '\n')

            if self.log:
                try: 
                    self.log.log(f"✅ CSV gerado: {output_filename}", "SUCCESS", "✅")
                except Exception: 
                    pass
            return True
            
        except Exception as e:
            if self.log:
                try:
                    self.log.log(f"Erro ao gerar CSV: {str(e)}", "ERROR", "❌")
                except Exception:
                    pass
            return False

    def generate_csv(self, json_files: List, output_filename: str|None=None):
        """Método de compatibilidade - aceita lista de strings ou Paths"""
        self._equipes = self._load_equipes()
        self._prices = self._load_prices()
        if self.log:
            try: self.log.log("📚 Tabelas carregadas (equipes, prices)", "INFO", "📚")
            except Exception: pass

        products: List[Dict[str, Any]] = []
        for f in json_files:
            try:
                # Converte para Path se for string
                file_path = Path(f) if isinstance(f, str) else f
                data = json.loads(file_path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    items = data.get('items') or data.get('produtos') or data.get('produtos_extraidos') or []
                else:
                    items = data
                if isinstance(items, list):
                    products.extend(items)
            except Exception as e:
                file_name = f.name if hasattr(f, 'name') else str(f)
                if self.log: 
                    try: self.log.log(f"Erro lendo {file_name}: {e}", "ERROR", "❌")
                    except Exception: pass

        if not products:
            return None

        if not output_filename:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"csv_gerados/catalogo_{ts}.csv"
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)

        rows: List[List[str]] = [self._headers()]

        for product in products:
            nome = product.get('album_folder_name') or product.get('page_title') or 'Produto'
            identificador = self._slug_from_name(nome)
            categorias = self._categorias_str(product, nome)
            sexo = 'Feminino' if re.search(r'\b(woman|women|female|feminino|feminina)\b', self._norm(nome)) else 'Unissex'
            faixa = 'Infantil' if re.search(r'\bkids?\b', self._norm(nome)) else 'Jovens e Adultos'
            preco, promo, fonte = self._price_for_name(nome)

            if self.log:
                try: self.log.log(f"Preço aplicado ({fonte}) → {preco}/{promo or '—'}", "DEBUG", "💲")
                except Exception: pass

            sizes = self._sizes_from_json(product) or ['']

            for sz in sizes:
                row = [
                    identificador, nome, categorias,
                    'Tamanho', sz,
                    '', '', '', '',
                    preco, promo, '0.250', '', '', '',
                    '', '', '', 'NÃO', '',
                    '', '', '', '', '', 'SIM',
                    '', sexo, faixa, ''
                ]
                rows.append([str(x) if x is not None else '' for x in row])

        with open(output_filename, 'w', encoding='utf-8-sig', newline='') as f:
            for row in rows:
                f.write(';'.join(row) + '\n')

        if self.log:
            try: self.log.log(f"✅ CSV gerado: {output_filename}", "SUCCESS", "✅")
            except Exception: pass
        return output_filename