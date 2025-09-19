import streamlit as st
import os
import subprocess

# Configuração inicial
st.set_page_config(page_title="Sistema Bora - Yp Webscraping", layout="centered")

# Estado inicial da fila de URLs
if "urls" not in st.session_state:
    st.session_state.urls = []

if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# Função para adicionar URL
def add_url():
    url = st.session_state.url_input.strip()
    if url and len(st.session_state.urls) < 2:  # Limite de 2 URLs
        st.session_state.urls.append(url)
    st.session_state.url_input = ""  # Limpa o campo depois de adicionar

# Função para remover URL da fila
def remove_url(idx):
    if 0 <= idx < len(st.session_state.urls):
        st.session_state.urls.pop(idx)

# Cabeçalho
st.title("Sistema Bora - Yp Webscraping")

# Entrada de URL
st.text_input("Digite a URL:", key="url_input", on_change=add_url)

# Exibir fila de URLs com botão de lixeira
st.subheader("Fila de URLs (máximo 2)")
for i, url in enumerate(st.session_state.urls):
    col1, col2 = st.columns([8, 1])
    col1.write(url)
    if col2.button("🗑️", key=f"del_{i}"):
        remove_url(i)

# Botões de processamento
st.subheader("Ações")
if st.button("Processar Imagens"):
    if not st.session_state.urls:
        st.warning("Adicione pelo menos 1 URL antes de processar.")
    else:
        for url in st.session_state.urls:
            st.write(f"🔍 Processando: {url}")
            try:
                # Chamada ao script existente
                result = subprocess.run(
                    ["python3", "bora.py", "--url", url],
                    capture_output=True, text=True
                )
                st.text(result.stdout)
                if result.stderr:
                    st.error(result.stderr)
            except Exception as e:
                st.error(f"Erro ao processar {url}: {e}")

# 🔒 Ocultado temporariamente
# if st.button("Coletar Metadados + Gerar CSV"):
#     st.info("Função desativada temporariamente.")
