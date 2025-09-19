import streamlit as st
import io
import zipfile
import csv
import json
import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from system import image_downloader

# ---------------- Logger Fake ---------------- #
class LoggerFake:
    def log(self, msg, level="INFO", emoji="ℹ️"):
        print(f"{emoji} [{level}] {msg}")

# ---------------- Sanitizador Inline ---------------- #
@dataclass
class InfoProduto:
    nome_original: str
    nome_limpo: str

class SanitizadorNomes:
    def __init__(self):
        self.caracteres_proibidos = ["<", ">", ":", "\"", "|", "?", "*", "\\", "/"]
        self.palavras_remover = [
            'new', 'novo', 'original', 'authentic', 'replica', 'copia',
            'quality', 'high', 'premium', 'top', 'best', 'melhor',
            'football', 'soccer', 'futebol', 'sport', 'team', 'club',
            'fc', 'cf', 'ac', 'sc', 'ec', 'clube'
        ]

    def _remover_acentos(self, texto: str) -> str:
        return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')

    def _limpar_caracteres_especiais(self, texto: str) -> str:
        for char in self.caracteres_proibidos:
            texto = texto.replace(char, '')
        texto = re.sub(r'[^\w\s\-]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def _remover_palavras_desnecessarias(self, nome: str) -> str:
        palavras = nome.split()
        return ' '.join([p for p in palavras if p not in self.palavras_remover and len(p) > 1])

    def _nome_fallback(self, nome_original: str) -> str:
        nome_limpo = self._remover_acentos(nome_original.lower())
        nome_limpo = self._limpar_caracteres_especiais(nome_limpo)
        palavras = nome_limpo.split()
        palavras_filtradas = [p.title() for p in palavras if p not in self.palavras_remover and len(p) > 2]
        return ' '.join(palavras_filtradas[:4]) if palavras_filtradas else "Produto Esportivo"

    def sanitizar_nome(self, nome: str) -> InfoProduto:
        try:
            nome_trabalho = nome.lower().strip()
            nome_trabalho = self._remover_acentos(nome_trabalho)
            nome_trabalho = self._limpar_caracteres_especiais(nome_trabalho)
            nome_trabalho = self._remover_palavras_desnecessarias(nome_trabalho)
            if not nome_trabalho:
                nome_trabalho = self._nome_fallback(nome)
            return InfoProduto(nome_original=nome, nome_limpo=nome_trabalho.title())
        except Exception:
            return InfoProduto(nome_original=nome, nome_limpo=self._nome_fallback(nome))

    def validar_nome_arquivo(self, nome: str) -> str:
        nome_limpo = nome
        for char in self.caracteres_proibidos:
            nome_limpo = nome_limpo.replace(char, '_')
        if len(nome_limpo) > 200:
            nome_limpo = nome_limpo[:200].rsplit(' ', 1)[0]
        nome_limpo = nome_limpo.strip()
        if nome_limpo.endswith('.'):
            nome_limpo = nome_limpo[:-1]
        return nome_limpo

# ---------------- Funções Auxiliares ---------------- #
def extrair_album_name(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        titulo = None
        if soup.title and soup.title.string:
            titulo = soup.title.string.strip()
        elif soup.find("h1"):
            titulo = soup.find("h1").get_text(strip=True)
        elif soup.find("h2"):
            titulo = soup.find("h2").get_text(strip=True)
        if not titulo:
            titulo = url
        sanitizador = SanitizadorNomes()
        info = sanitizador.sanitizar_nome(titulo)
        return sanitizador.validar_nome_arquivo(info.nome_limpo)
    except Exception:
        return f"album_sem_nome_{abs(hash(url)) % 10000}"

def gerar_csv_stub(metadados):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["URL", "Album"])
    for dado in metadados:
        writer.writerow([dado["album_url"], dado["album_folder_name"]])
    return output.getvalue().encode("utf-8")

# ---------------- Interface Web ---------------- #
st.set_page_config(page_title="Sistema Bora - Yp Webscraping", layout="centered")
st.title("Sistema Bora - Yp Webscraping")

# Estado
if "urls" not in st.session_state:
    st.session_state.urls = []
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

st.subheader("Adicionar URLs (máx. 2)")
st.text_input(
    "Informe a URL (Yupoo ou WordPress)",
    key="url_input",
    placeholder="https://exemplo.com/...",
)
add_disabled = len(st.session_state.urls) >= 2
if st.button("➕ Adicionar URL", type="primary", disabled=add_disabled):
    nova_url = (st.session_state.url_input or "").strip()
    if nova_url:
        if nova_url in st.session_state.urls:
            st.warning("⚠️ Esta URL já foi adicionada.")
        elif len(st.session_state.urls) >= 2:
            st.error("❌ Máximo de 2 URLs permitido!")
        else:
            st.session_state.urls.append(nova_url)
            st.session_state.url_input = ""   # limpa o campo após adicionar
    else:
        st.warning("Informe uma URL antes de adicionar.")

# Lista com botão de lixeira
if st.session_state.urls:
    st.subheader("📋 Fila de URLs")
    for i, url in enumerate(st.session_state.urls):
        c1, c2 = st.columns([10, 1])
        with c1:
            st.write(url)
        with c2:
            if st.button("🗑️", key=f"del_{i}", help="Remover esta URL"):
                st.session_state.urls.pop(i)
                st.experimental_rerun()
else:
    st.info("Nenhuma URL na fila ainda. Adicione até 2.")

# Botão principal renomeado
process_disabled = len(st.session_state.urls) == 0
if st.button("📷 Processar Imagens", type="primary", disabled=process_disabled):
    if st.session_state.urls:
        metadados = [{"album_url": u, "album_folder_name": extrair_album_name(u)} for u in st.session_state.urls]
        temp_file = Path("temp_metadata.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(metadados, f, indent=4, ensure_ascii=False)
        try:
            logger = LoggerFake()
            image_downloader.main_integrated(logger, [temp_file])
            # ZIP da pasta "imagens"
            output_dir = Path("imagens")
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, mode="w") as zf:
                for path in output_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(output_dir))
            mem_zip.seek(0)
            st.success("✅ Imagens baixadas com sucesso!")
            st.download_button("⬇️ Baixar Imagens (ZIP)", mem_zip, file_name="imagens.zip")
        except Exception as e:
            st.error(f"Erro ao baixar imagens: {e}")
    else:
        st.warning("Nenhuma URL adicionada.")

# Ocultar (por enquanto) o botão de CSV
if False:
    if st.button("📊 Coletar Metadados + Gerar CSV"):
        if st.session_state.urls:
            metadados = [{"album_url": u, "album_folder_name": extrair_album_name(u)} for u in st.session_state.urls]
            csv_file = gerar_csv_stub(metadados)
            st.success("✅ CSV gerado com sucesso!")
            st.download_button("⬇️ Baixar CSV", csv_file, file_name="dados.csv")
        else:
            st.warning("Nenhuma URL adicionada.")
