# -*- coding: utf-8 -*-
# interface_manager.py – UI auxiliar do Sistema BORA
# Mantém compatibilidade com bora.py e adiciona integração com image_downloader (Cancelar)

from __future__ import annotations

import json
import platform
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox
from typing import List, Optional
import time

class MetadataInterface:
    def __init__(self, parent, config_manager, process_callback):
        self.parent = parent
        self.config_manager = config_manager
        self.process_callback = process_callback
        self.urls = []
        self.counter = 1

        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        # Campo de inserção + botão adicionar
        entry_frame = ttk.Frame(self.frame)
        entry_frame.pack(fill="x", pady=5)

        self.url_entry = ttk.Entry(entry_frame)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        add_btn = ttk.Button(entry_frame, text="Adicionar", command=self.add_url)
        add_btn.pack(side="left", padx=5)

        # Container principal para tabela + botões
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, pady=5)

        # Área da tabela (70%)
        self.table_frame = ttk.Frame(main_frame)
        self.table_frame.pack(side="left", fill="both", expand=True)

        header = ttk.Frame(self.table_frame)
        header.pack(fill="x")
        ttk.Label(header, text="#", width=5).pack(side="left")
        ttk.Label(header, text="URL", width=70).pack(side="left", padx=5)
        ttk.Label(header, text="Ação", width=10).pack(side="left")

        self.rows_container = ttk.Frame(self.table_frame)
        self.rows_container.pack(fill="both", expand=True)

        # Botões laterais (30%)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side="left", fill="y", padx=10)

        clear_btn = ttk.Button(btn_frame, text="Limpar Fila", command=self.clear_urls)
        clear_btn.pack(fill="x", pady=2)

        process_btn = ttk.Button(btn_frame, text="Processar URLs", command=self.start_processing)
        process_btn.pack(fill="x", pady=2)

    def add_url(self):
        url = self.url_entry.get().strip()
        if url:
            self.urls.append(url)

            row = ttk.Frame(self.rows_container)
            row.pack(fill="x", pady=1)

            ttk.Label(row, text=str(self.counter), width=5).pack(side="left")
            ttk.Label(row, text=url, width=70, anchor="w").pack(side="left", padx=5)
            del_btn = ttk.Button(row, text="Excluir", width=10, command=lambda r=row, u=url: self.remove_url(r, u))
            del_btn.pack(side="left")

            self.url_entry.delete(0, tk.END)
            self.counter += 1

    def remove_url(self, row, url):
        if url in self.urls:
            self.urls.remove(url)
        row.destroy()

    def clear_urls(self):
        self.urls.clear()
        for child in self.rows_container.winfo_children():
            child.destroy()
        self.counter = 1

    def start_processing(self):
        if not self.urls:
            messagebox.showwarning("Atenção", "Nenhuma URL na fila.")
            return

        start_time = time.time()

        def run():
            try:
                resultado = self.process_callback(self.urls)
                elapsed = time.time() - start_time
                
                # CORREÇÃO: Verifica se resultado é válido
                if resultado is None:
                    # Cria resultado padrão em caso de falha
                    resultado = {
                        "ok": False,
                        "erro": "Processamento retornou resultado vazio",
                        "total_urls": len(self.urls),
                        "sucessos": 0,
                        "falhas": len(self.urls),
                        "arquivo": ""
                    }
                elif not isinstance(resultado, dict):
                    # Se não é dict, converte para formato esperado
                    resultado = {
                        "ok": False,
                        "erro": f"Resultado inválido: {type(resultado).__name__}",
                        "total_urls": len(self.urls),
                        "sucessos": 0,
                        "falhas": len(self.urls),
                        "arquivo": ""
                    }
                
                self.show_summary(resultado, elapsed)
                
            except Exception as e:
                # Em caso de erro no processamento
                elapsed = time.time() - start_time
                resultado = {
                    "ok": False,
                    "erro": f"Erro durante processamento: {str(e)}",
                    "total_urls": len(self.urls),
                    "sucessos": 0,
                    "falhas": len(self.urls),
                    "arquivo": ""
                }
                self.show_summary(resultado, elapsed)

        threading.Thread(target=run, daemon=True).start()

    def show_summary(self, resultado, elapsed):
        for widget in self.frame.winfo_children():
            widget.destroy()

        resumo = ttk.Frame(self.frame)
        resumo.pack(fill="both", expand=True, pady=20, padx=20)

        # CORREÇÃO: Valores padrão seguros para evitar KeyError
        total = resultado.get("total_urls", 0)
        sucessos = resultado.get("sucessos", 0)
        falhas = resultado.get("falhas", 0)
        arquivo = resultado.get("arquivo", "-")
        # erro = resultado.get("erro", "")                                                                 --- removido devido a bug
        
        # Exibe erro se houver
        # if erro:                                                                                         --- removido devido a bug
        #    ttk.Label(resumo, text=f"❌ Erro: {erro}", foreground="red").pack(anchor="w", pady=2)         --- removido devido a bug

        ttk.Label(resumo, text=f"URLs processadas: {total}").pack(anchor="w", pady=2)
        ttk.Label(resumo, text=f"Sucessos: {sucessos} | Falhas: {falhas}").pack(anchor="w", pady=2)
        ttk.Label(resumo, text=f"Tempo decorrido: {elapsed:.1f}s").pack(anchor="w", pady=2)
        
        if arquivo and arquivo != "-":
            ttk.Label(resumo, text=f"Metadados salvos em: {arquivo}").pack(anchor="w", pady=2)

        btns = ttk.Frame(resumo)
        btns.pack(fill="x", pady=10)

        concluir_btn = ttk.Button(btns, text="Concluir", command=self.clear_all)
        concluir_btn.pack(side="left", padx=5)

        # Só mostra botão "Abrir pasta" se há arquivo válido
        if arquivo and arquivo != "-":
            abrir_btn = ttk.Button(btns, text="Abrir pasta", command=lambda: self.open_folder(arquivo))
            abrir_btn.pack(side="left", padx=5)

    def clear_all(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def open_folder(self, arquivo):
        if not arquivo:
            return
        pasta = Path(arquivo).parent
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", str(pasta.resolve())], check=True)
            elif system == "Darwin":
                subprocess.run(["open", str(pasta.resolve())], check=True)
            else:
                subprocess.run(["xdg-open", str(pasta.resolve())], check=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")


class InterfaceManager:
    def __init__(self, parent_window, logger):
        self.parent = parent_window
        self.logger = logger
        self.work_content: Optional[tk.Widget] = None
        self.config_manager = None
        self.download_callback = None
        self.files_tree: Optional[ttk.Treeview] = None
        self.download_status: Optional[ttk.Label] = None

    def _clear(self, container: tk.Widget) -> None:
        for w in container.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _set_buttons_state(self, frame: tk.Widget, state: str) -> None:
        try:
            for child in frame.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state=state)
        except Exception:
            pass

    def create_image_download_interface(self, work_content, config_manager, callback):
        self.work_content = work_content
        self.config_manager = config_manager
        self.download_callback = callback
        self.logger.log("🖼️ Iniciando interface de download de imagens...", "INFO", "🖼️")
        self._clear(work_content)

        main = ttk.Frame(work_content)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        ttk.Label(main, text="Download de Imagens", font=("Arial", 16, "bold")).grid(
            row=0, column=0, pady=(0, 10)
        )

        files_frame = ttk.LabelFrame(main, text="Arquivos de metadados (pasta: Metadados)", padding=10)
        files_frame.grid(row=1, column=0, sticky="nsew")
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(0, weight=1)

        self.files_tree = ttk.Treeview(
            files_frame,
            columns=("itens", "mod"),
            show="tree headings",
            selectmode="extended",
            height=12,
        )
        self.files_tree.heading("#0", text="Arquivo")
        self.files_tree.heading("itens", text="Itens")
        self.files_tree.heading("mod", text="Modificado em")
        self.files_tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.files_tree.configure(yscrollcommand=vsb.set)

        actions = ttk.Frame(main)
        actions.grid(row=2, column=0, pady=(12, 0))

        start_btn = ttk.Button(actions, text="🚀 Iniciar Download", width=20,
                               command=self._on_start_download)
        start_btn.pack(side=tk.LEFT, padx=(0, 10))

        open_btn = ttk.Button(actions, text="📂 Abrir Pasta Imagens", width=20,
                              command=self._abrir_pasta_imagens)
        open_btn.pack(side=tk.LEFT)

        cancel_btn = ttk.Button(actions, text="⏹️ Cancelar", width=14,
                                command=self._on_cancel_download)
        cancel_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.download_status = ttk.Label(main, text="Selecione um ou mais JSONs e clique em Iniciar.",
                                         foreground="gray")
        self.download_status.grid(row=3, column=0, sticky="w", pady=(10, 0))

        self._carregar_lista_arquivos()

    def _carregar_lista_arquivos(self) -> None:
        if not self.files_tree:
            return
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        pasta = Path("Metadados")
        if not pasta.exists():
            self.logger.log("Pasta 'Metadados' não encontrada", "WARNING", "📁")
            return

        arquivos = sorted(pasta.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for arq in arquivos:
            try:
                tamanho = len(self._load_metadata_file(arq))
            except Exception as e:
                tamanho = 0
                self.logger.log(f"Erro ao ler {arq.name}: {e}", "ERROR", "❌")
            mod = datetime.fromtimestamp(arq.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.files_tree.insert("", "end", text=arq.name, values=(tamanho, mod))

    def _load_metadata_file(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return (
                data.get("produtos")
                or data.get("produtos_extraidos")
                or data.get("items")
                or data.get("data")
                or []
            )
        return []

    def _get_selected_metadata_files(self) -> List[Path]:
        if not self.files_tree:
            return []
        sel = self.files_tree.selection()
        names = [self.files_tree.item(i, "text") for i in sel]
        return [Path("Metadados") / n for n in names]

    def _on_start_download(self) -> None:
        if not callable(self.download_callback):
            messagebox.showerror("Erro", "Callback de download não configurado.")
            return

        arquivos = self._get_selected_metadata_files()
        if not arquivos:
            if not messagebox.askyesno(
                "Baixar Imagens",
                "Nenhum arquivo selecionado.\nDeseja usar o JSON mais recente automaticamente?",
            ):
                return
            arquivos = []

        self.download_status.configure(text="⏳ Iniciando...", foreground="orange")
        self.logger.log(f"Iniciando download para {len(arquivos)} arquivo(s)", "INFO", "🖼️")

        try:
            self.download_callback("provocado", arquivos)
        except Exception as e:
            self.logger.log(f"Erro ao iniciar download: {e}", "ERROR", "❌")
            self.download_status.configure(text=f"❌ Erro: {e}", foreground="red")

    def _on_cancel_download(self) -> None:
        try:
            import sys
            sys.path.append(str(Path("system").resolve()))
            import image_downloader
            image_downloader.request_cancel()
            if self.download_status:
                self.download_status.configure(text="⏹️ Cancelamento solicitado...", foreground="red")
            self.logger.log("Cancelamento solicitado pelo usuário", "WARNING", "⏹️")
        except Exception as e:
            self.logger.log(f"Falha ao solicitar cancelamento: {e}", "ERROR", "❌")

    def _abrir_pasta_imagens(self) -> None:
        pasta = Path("imagens")
        pasta.mkdir(exist_ok=True)
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", str(pasta.resolve())], check=True)
            elif system == "Darwin":
                subprocess.run(["open", str(pasta.resolve())], check=True)
            else:
                subprocess.run(["xdg-open", str(pasta.resolve())], check=True)
            self.logger.log("Pasta de imagens aberta", "INFO", "📂")
        except Exception as e:
            self.logger.log(f"Erro ao abrir pasta: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")

    def create_metadata_interface(self, work_content, config_manager, callback):
        self.work_content = work_content
        self.config_manager = config_manager
        self._clear(self.work_content or self.parent)
        MetadataInterface(self.work_content or self.parent, config_manager, callback)

    def create_csv_interface(self, *args, **kwargs):
        self._clear(self.work_content or self.parent)
        ttk.Label(self.work_content or self.parent, text="Geração de CSV (interface não utilizada aqui).").pack(
            pady=10
        )

    def abrir_marcacao_precos(self):
        try:
            from system.price_mark_ui import PriceMarkUI  # type: ignore
            ui = PriceMarkUI(self.parent, self.logger)
            ui.open()
            self.logger.log("Interface de marcação de preços aberta", "SUCCESS", "💰")
        except Exception as e:
            self.logger.log(f"Erro ao abrir marcação de preços: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", f"Erro ao abrir interface: {e}")

    def mostrar_seletor_arquivos_metadados(self, callback):
        """Método para compatibilidade com bora.py"""
        try:
            from tkinter import filedialog
            pasta_metadados = Path("Metadados")
            if not pasta_metadados.exists():
                messagebox.showerror("Erro", "Pasta 'Metadados' não encontrada")
                return
            
            arquivos = filedialog.askopenfilenames(
                title="Selecione arquivos de metadados",
                initialdir=str(pasta_metadados),
                filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
            )
            
            if arquivos:
                arquivos_path = [Path(arq) for arq in arquivos]
                callback(arquivos_path)
            
        except Exception as e:
            self.logger.log(f"Erro ao abrir seletor de arquivos: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", f"Erro ao abrir seletor: {e}")