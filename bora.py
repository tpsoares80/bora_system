import logging

logger = logging.getLogger("bora")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Yupoo Webscraping
Módulo Principal - Interface Gráfica e Coordenação (Versão Tkinter)

Desenvolvido para automatizar catalogação de produtos esportivos
Foco inicial: Uniformes de futebol (expansível para tênis, chuteiras, etc.)
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from typing import Optional

# Importa classes auxiliares do sistema
from system.interface_manager import InterfaceManager
from system.data_processor_main import DataProcessor
from system.csv_generator import CSVGenerator

class BoraLogger:
    """Sistema de Log em Tempo Real com fonte e cores configuráveis"""
    
    def __init__(self, log_widget: scrolledtext.ScrolledText, config_manager=None):
        self.log_widget = log_widget
        self.log_history = []
        self.config_manager = config_manager
        
        # Configurações padrão (fallback)
        self.default_colors = {
            "INFO": "#000000",      # Azul
            "SUCCESS": "#008040",   # Verde
            "ERROR": "#D0021B",     # Vermelho
            "WARNING": "#F5A623",   # Laranja
            "DEBUG": "#9013FE",     # Roxo
            "TIMESTAMP": "#666666"  # Cinza
        }
        
        self.default_font = {
            "family": "Consolas",
            "size": 12,
            "weight": "normal"
        }
        
        # Inicializa configurações
        self.color_map = {}
        self.font_config = {}
        self._load_logger_config()
        self._setup_colors()
        self._update_font()
        
    def _load_logger_config(self):
        """Carrega configurações do logger do config.json"""
        if self.config_manager:
            # Carrega cores
            logger_colors = self.config_manager.get("logger_colors", {})
            self.color_map = {**self.default_colors, **logger_colors}
            
            # Carrega configurações de fonte
            logger_font = self.config_manager.get("logger_font", {})
            self.font_config = {**self.default_font, **logger_font}
        else:
            # Usa padrões se não há config_manager
            self.color_map = self.default_colors.copy()
            self.font_config = self.default_font.copy()
        
    def _setup_colors(self):
        """Configura as cores para diferentes níveis de log"""
        # Configura tags de cor no widget
        for level, color in self.color_map.items():
            self.log_widget.tag_config(level.lower(), foreground=color)
        
    def _update_font(self):
        """Atualiza a fonte do log baseada na configuração"""
        try:
            font_family = self.font_config.get("family", "Consolas")
            font_size = self.font_config.get("size", 12)
            font_weight = self.font_config.get("weight", "normal")
            
            self.log_widget.configure(font=(font_family, font_size, font_weight))
        except:
            pass  # Widget pode nao estar pronto ainda
    
    def update_config(self):
        """Atualiza configurações do logger (chamado após salvar configurações)"""
        self._load_logger_config()
        self._setup_colors()
        self._update_font()
    
    def update_font_size(self):
        """Atualiza o tamanho da fonte (mantido para compatibilidade)"""
        self._update_font()
        
    def log(self, message: str, level: str = "INFO", emoji: str = "ℹ️"):
        """Adiciona mensagem ao log com timestamp e cores"""
        formatted_msg = f"{emoji} {message}"
        
        self.log_history.append(f"[{level}] {formatted_msg}")
        self.log_widget.after(0, self._add_to_widget, formatted_msg, level)
    
    def _add_to_widget(self, message: str, level: str = "INFO"):
        """Adiciona mensagem ao widget de forma thread-safe com cores"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Divide a mensagem em partes para aplicar cores diferentes
        timestamp_part = f"[{timestamp}]"
        message_part = message
        
        # Posição inicial
        start_pos = self.log_widget.index(tk.END)
        
        # Adiciona timestamp com cor específica
        self.log_widget.insert(tk.END, timestamp_part, "timestamp")
        self.log_widget.insert(tk.END, " ")
        
        # Adiciona mensagem com cor baseada no nível
        color_tag = level.lower() if level in self.color_map else "info"
        self.log_widget.insert(tk.END, message_part, color_tag)
        self.log_widget.insert(tk.END, "\n")
        
        # Rola para o final
        self.log_widget.see(tk.END)


    def _log_with_background(self, message: str, level: str = "INFO", emoji: str = "ℹ️", bg_color: str = "#FFFFE0"):
        """Adiciona mensagem ao log com fundo colorido"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"{emoji} {message}"
        
        self.log_history.append(f"[{level}] {formatted_msg}")
        
        # Adiciona ao widget com fundo colorido
        self.log_widget.after(0, self._add_to_widget_with_bg, formatted_msg, level, bg_color)
    
    def _add_to_widget_with_bg(self, message: str, level: str = "INFO", bg_color: str = "#FFFFE0"):
        """Adiciona mensagem ao widget com fundo colorido"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Cria tag com fundo colorido
        tag_name = f"{level.lower()}_bg"
        color = self.color_map.get(level, "#000000")
        
        self.log_widget.tag_config(tag_name, 
                                  foreground=color, 
                                  background=bg_color,
                                  relief="solid",
                                  borderwidth=1)
    
        # Adiciona timestamp
        self.log_widget.insert(tk.END, f"[{timestamp}] ", "timestamp")
    
        # Adiciona mensagem com fundo
        self.log_widget.insert(tk.END, message, tag_name)
        self.log_widget.insert(tk.END, "\n")
        
        # Rola para o final
        self.log_widget.see(tk.END)



    
    def clear(self):
        """Limpa o log"""
        self.log_history.clear()
        self.log_widget.delete(1.0, tk.END)
    
    def save_to_file(self) -> str:
        """Salva log em arquivo e retorna o caminho"""
        if not self.log_history:
            return ""
            
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        filename = f"log-{timestamp}.txt"
        filepath = Path("Logs") / filename
        
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Sistema BORA Webscraping\n")
            f.write(f"Log gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            for line in self.log_history:
                f.write(line + "\n")
        
        return str(filepath)

class RequirementChecker:
    """Verificador e Instalador de Requisitos"""
    
    def __init__(self, logger: BoraLogger):
        self.logger = logger
        self.requirements_file = Path("system") / "requisitos.json"
    
    def check_and_install(self) -> bool:
        """Verifica e instala requisitos necessários"""
        self.logger.log("Iniciando verificação de requisitos...", "INFO", "🔍")
        
        if not self.requirements_file.exists():
            self.logger.log("Arquivo requisitos.json não encontrado. Criando...", "WARNING", "⚠️")
            self._create_default_requirements()
        
        try:
            import json
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                requirements = json.load(f)
            
            packages = requirements.get("required_packages", [])
            self.logger.log(f"Verificando {len(packages)} pacotes...", "INFO", "📦")
            
            failed_installs = []
            
            for package in packages:
                if not self._check_package(package):
                    self.logger.log(f"Instalando {package}...", "INFO", "⬇️")
                    if not self._install_package(package):
                        failed_installs.append(package)
            
            if failed_installs:
                self.logger.log(f"Falha ao instalar: {', '.join(failed_installs)}", "ERROR", "❌")
                return False
            
            self.logger.log("Todos os requisitos verificados com sucesso!", "SUCCESS", "✅")
            return True
            
        except Exception as e:
            self.logger.log(f"Erro ao verificar requisitos: {str(e)}", "ERROR", "❌")
            return False
    
    def _create_default_requirements(self):
        """Cria arquivo de requisitos padrão"""
        import json
        default_requirements = {
            "required_packages": [
                "requests>=2.31.0", 
                "beautifulsoup4>=4.12.0",
                "pandas>=2.0.0",
                "Pillow>=10.0.0",
                "cryptography>=41.0.0",
                "lxml>=4.9.0",
                "selenium>=4.15.0",
                "urllib3>=2.0.0",
                "openpyxl>=3.1.0",
                "python-dateutil>=2.8.0",
                "chardet>=5.2.0",
                "fake-useragent>=1.4.0",
                "tqdm>=4.66.0",
                "webdriver-manager>=4.0.0",
                "unidecode>=1.3.0",
                "httpx>=0.24.0",
                "selectolax>=0.3.0"
            ]
        }
        
        self.requirements_file.parent.mkdir(exist_ok=True)
        
        with open(self.requirements_file, 'w', encoding='utf-8') as f:
            json.dump(default_requirements, f, indent=2, ensure_ascii=False)
    
    def _check_package(self, package: str) -> bool:
        """Verifica se um pacote está instalado"""
        import importlib
        package_name = package.split('>=')[0].split('==')[0]
        try:
            importlib.import_module(package_name.replace('-', '_'))
            return True
        except ImportError:
            return False
    
    def _install_package(self, package: str) -> bool:
        """Instala um pacote via pip"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.returncode == 0
        except Exception:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except subprocess.CalledProcessError:
                return False

class ConfigManager:
    """Gerenciador de Configurações"""
    
    def __init__(self, logger: BoraLogger):
        self.logger = logger
        self.config_file = Path("system") / "config.json"
        self.config = {}
        
    def load_config(self) -> bool:
        """Carrega configurações do arquivo"""
        if not self.config_file.exists():
            self.logger.log("Arquivo config.json não encontrado. Criando...", "WARNING", "⚠️")
            self._create_default_config()
        
        try:
            import json
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.logger.log("Configurações carregadas com sucesso", "SUCCESS", "⚙️")
            return True
        except Exception as e:
            self.logger.log(f"Erro ao carregar config: {str(e)}", "ERROR", "❌")
            return False
    
    def get(self, key: str, default=None):
        """Obtém valor de configuração com fallback"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _create_default_config(self):
        """Cria arquivo de configurações padrão"""
        import json
        default_config = {
            "tamanhos_adulto": ["P", "M", "G", "XG", "XXG", "XXXG"],
            "tamanhos_infantil": {
                "16": "2 a 3 anos",
                "18": "3 a 4 anos", 
                "20": "4 a 5 anos",
                "22": "6 a 7 anos",
                "24": "8 a 9 anos",
                "26": "10 a 11 anos",
                "28": "12 a 13 anos"
            },
            "delay_padrao": 2.0,
            "delay_apos_erro": 5.0,
            "tamanho_minimo_imagem": 1024,
            "identificadores_categoria": ["search", "collection", "categories"],
            "caracteres_proibidos": ["<", ">", ":", "\"", "|", "?", "*", "\\", "/"],
            "ia_apis": [],
            "log_font_size": 12,
            "csv": {
                "preco_padrao": 199.90,
                "preco_promocional": 179.90
            },
            "debug": {
                "log_detalhado": False
            },
            "image_downloader": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "timeout": 10.0,
                "delay_between_images": 1.0
            }
        }
        
        self.config_file.parent.mkdir(exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.config = default_config

class SistemaBORA:
    """Interface Principal do Sistema BORA - Versão Tkinter"""
    
    def __init__(self):
        # Janela principal
        self.root = tk.Tk()
        self.root.title("Sistema BORA Webscraping - Desenvolvido por Thiago P Soares")
        
        # Maximiza a janela - FUNCIONA PERFEITAMENTE no Tkinter!
        self.root.state('zoomed')
        
        # Configura estilo ttk
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Tema mais moderno
        
        # Variáveis de controle
        self.debug_mode = tk.BooleanVar()
        self.processing = False
        
        # Componentes do sistema
        self.logger: Optional[BoraLogger] = None
        self.config_manager: Optional[ConfigManager] = None
        self.interface_manager: Optional[InterfaceManager] = None
        self.data_processor: Optional[DataProcessor] = None
        self.csv_generator: Optional[CSVGenerator] = None
        
        # Interface
        self._setup_ui()
        self._create_directories()
        
        # Inicialização
        self.root.after(100, self._initialize_system)
    



    def _setup_ui(self):
        """Configura a interface do usuário com painel redimensionável"""

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Painel esquerdo - Botões
        self.left_frame = ttk.LabelFrame(main_frame, text="SISTEMA BORA WEBSCRAPING", padding=10)
        self.left_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.left_frame.grid_propagate(False)
        self.left_frame.configure(width=250)

        title_label = ttk.Label(
            self.left_frame,
            text="SISTEMA BORA WEBSCRAPING",
            font=("Arial", 14, "bold"),
            anchor="center",
            justify="center"
        )
        title_label.pack(pady=(20, 10))
        
        # Adiciona logomarca
#        try:
#            from PIL import Image, ImageTk
#            logo_path = Path("system") / "logo.png"  # ou logo.jpg
#            if logo_path.exists():
#                # Carrega e redimensiona a imagem
#                logo_image = Image.open(logo_path)
#                logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)  # Ajuste o tamanho conforme necessário
#                logo_photo = ImageTk.PhotoImage(logo_image)
#                
#                logo_label = ttk.Label(self.left_frame, image=logo_photo)
#                logo_label.image = logo_photo  # Mantém referência
#                logo_label.pack(pady=(0, 20))
#        except Exception as e:
#            # Se não conseguir carregar a logo, apenas registra no log
#            print(f"Logo não carregada: {e}")
        
        



        self.buttons = {}
        button_configs = [
            ("📊 COLETAR METADADOS", self._coletar_metadados),
            ("📄 GERAR CSV", self._gerar_csv),
            ("🖼️ BAIXAR IMAGENS", self._baixar_imagens),
            ("📦 PROCESSAR PRODUTOS", self._processar_produtos),
            ("💰 MARCAÇÃO DE PREÇOS", self._marcacao_precos),
            ("⚙️ CONFIGURAÇÕES", self._abrir_configuracoes),
            ("📄 GERAR LOG", self._gerar_log),
            ("🚪 SAIR", self._sair)
        ]
        for text, command in button_configs:
            btn = ttk.Button(self.left_frame, text=text, command=command, width=25)
            btn.pack(pady=5, fill=tk.X)
            self.buttons[text] = btn

#        ttk.Checkbutton(self.left_frame, text="🛠 Modo DEBUG", variable=self.debug_mode).pack(pady=20)


        # Mensagem de incentivo
        incentivo_frame = ttk.Frame(self.left_frame)
        incentivo_frame.pack(pady=(10, 20))
        
        ttk.Label(incentivo_frame, text="ESSE SISTEMA É GRATUITO", 
                 font=("Arial", 11, "bold"), anchor="center", foreground="RED").pack()
        ttk.Label(incentivo_frame, text="APOIE O DESENVOLVEDOR", 
                 font=("Arial", 10), anchor="center").pack()
        ttk.Label(incentivo_frame, text="PIX: TPSOARES@GMAIL.COM", 
                 font=("Arial", 10, "bold"), anchor="center", foreground="blue").pack()
        ttk.Label(incentivo_frame, text="MUITO OBRIGADO!!!", 
                 font=("Arial", 10), anchor="center").pack()
        ttk.Label(incentivo_frame, text="© 2025 por Thiago P Soares", 
                 font=("Arial", 10), anchor="center").pack()


        ttk.Button(self.left_frame, text="🧹 Limpar Log", command=self._limpar_log).pack(side=tk.BOTTOM, pady=10, fill=tk.X)

        # Painel direito - PanedWindow para divisor móvel
        self.paned_window = ttk.PanedWindow(main_frame, orient='vertical')
        self.paned_window.grid(row=0, column=1, sticky="nsew")

        # Área de trabalho
        self.work_frame = ttk.LabelFrame(self.paned_window, text="💼 ÁREA DE TRABALHO", padding=10)
        self.work_frame.grid_columnconfigure(0, weight=1)
        self.work_frame.grid_rowconfigure(0, weight=1)

        self.work_content = ttk.Frame(self.work_frame)
        self.work_content.grid(row=0, column=0, sticky="nsew")

        self.work_status = ttk.Label(self.work_content, text="Selecione uma função no menu lateral para começar", font=("Arial", 12), anchor="center")
        self.work_status.pack(expand=True)

        # Logger
        self.log_frame = ttk.LabelFrame(self.paned_window, text="📜 LOG EM TEMPO REAL", padding=10)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)

        self.log_widget = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.NORMAL)
        self.log_widget.grid(row=0, column=0, sticky="nsew")

        # Adiciona painéis ao PanedWindow
        self.paned_window.add(self.work_frame, weight=3)
        self.paned_window.add(self.log_frame, weight=1)

        # Posição inicial do divisor na posição do config.json
        # ===== SALVAR/CARREGAR POSIÇÃO DO DIVISOR =====
        import json
        
        # Carrega posição salva do config.json
        # Carrega posição salva do config.json
        try:
            with open('system/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}
        
        initial_pos = int(config.get('paned_divider_position', 400))
        
        # CORRETO: usar sashpos com 2 argumentos
        self.root.after(100, lambda: self.paned_window.sashpos(0, initial_pos))
        
        # Função para salvar posição quando soltar o mouse
        def on_drag_end(event):
            try:
                # ✅ USAR sashpos ao invés de sash_coord
                val = self.paned_window.sashpos(0)
                
                if isinstance(val, int):
                    y_pos = val
                else:
                    try:
                        y_pos = int(round(float(str(val))))
                    except (ValueError, TypeError):
                        return
                
                config['paned_divider_position'] = y_pos
                with open('system/config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.log(f"Posição do divisor salva: {y_pos}", "INFO", "💾")
                
            except Exception as e:
                if "coord" not in str(e):
                    self.logger.log(f"Erro ao salvar posição: {str(e)}", "ERROR", "❌")
        
        self.paned_window.bind('<ButtonRelease-1>', on_drag_end)




        # Inicializa logger
        self.logger = BoraLogger(self.log_widget)




    
    def _create_directories(self):
        """Cria diretórios necessários"""
        directories = ["system", "Imagens", "csv_gerados", "Metadados", "Logs", "system/downloader"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def _clear_work_area(self):
        """Limpa a área de trabalho"""
        for widget in self.work_content.winfo_children():
            widget.destroy()
        
        self.work_status = ttk.Label(
            self.work_content,
            text="Operação concluída",
            font=("Arial", 12),
            foreground="green",
            anchor="center"
        )
        self.work_status.pack(expand=True)
    
    def _initialize_system(self):
        """Inicializa o sistema em thread separada"""
        def init_thread():
            self.logger.log("🚀 Iniciando Sistema BORA...", "INFO", "🚀")
            
            # Verifica requisitos
            req_checker = RequirementChecker(self.logger)
            if not req_checker.check_and_install():
                self.logger.log("❌ Falha na inicialização", "ERROR", "❌")
                return
            
            # Carrega configurações
            self.config_manager = ConfigManager(self.logger)
            if not self.config_manager.load_config():
                self.logger.log("❌ Falha ao carregar configurações", "ERROR", "❌")
                return
            
            # Atualiza logger com config_manager e recarrega cores/fontes
            self.logger.config_manager = self.config_manager
            self.logger.update_config()  # ESTA É A LINHA CHAVE
            
            # Inicializa módulos
            self.interface_manager = InterfaceManager(self.root, self.logger)
            self.data_processor = DataProcessor(self.logger, self.config_manager)
            self.csv_generator = CSVGenerator(self.logger, self.config_manager)
            
            self.logger.log("✅ Sistema BORA pronto para uso!", "SUCCESS", "✅")

            self.logger._log_with_background("ESTE SISTEMA É GRATUITO E NÃO DEVE SER COMERCIALIZADO", "INFO", "")
            self.logger._log_with_background("SE ELE É ÚTIL E ESTÁ TE AJUDANDO, INCENTIVE O DESENVOLVEDOR:", "INFO", "")
            self.logger._log_with_background("🔑CHAVE PIX E-MAIL: TPSOARES@GMAIL.COM --- MUITO OBRIGADO", "INFO", "")
            self.logger._log_with_background("© 2025 por Thiago P Soares", "INFO", "")

            self.logger.log("👈 Selecione uma função no menu lateral", "INFO", "👈")
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def _set_buttons_state(self, state: str):
        """Ativa/desativa botões durante processamento"""
        for button in self.buttons.values():
            button.configure(state=state)
    
    def _coletar_metadados(self):
        """Abre tela para coletar metadados"""
      
        self.logger.log("🎯 Iniciando coleta de metadados...", "INFO", "📊")
        
        if not self.config_manager or not self.interface_manager:
            self.logger.log("Sistema não inicializado", "ERROR", "❌")
            return
        
        # Confirma se modo DEBUG
        if self.debug_mode.get():
            result = messagebox.askyesno("Modo DEBUG", "Executar coleta de metadados em modo DEBUG?")
            if not result:
                return
        
        # Usa interface_manager para criar interface na área de trabalho
        self.interface_manager.create_metadata_interface(
            self.work_content,
            self.config_manager,
            self._processar_metadados
        )
    
    def _processar_metadados(self, urls):
        """Processa URLs usando DataProcessor"""
        if not self.data_processor:
            self.logger.log("DataProcessor não inicializado", "ERROR", "❌")
            return
        
        self._set_buttons_state("disabled")
        
        def processar_thread():
            try:
                resultado = self.data_processor.processar_metadados(urls)
                
                if "erro" in resultado:
                    self.logger.log(f"❌ {resultado['erro']}", "ERROR", "❌")
                else:
                    self.logger.log("✅ Processamento concluído com sucesso!", "SUCCESS", "✅")
                    self._clear_work_area()
                    
            finally:
                self._set_buttons_state("normal")
        
        threading.Thread(target=processar_thread, daemon=True).start()
    
    def _gerar_csv(self):
        """Abre interface de seleção de arquivos de metadados"""
        if not self.interface_manager:
            self.logger.log("InterfaceManager não inicializado", "ERROR", "❌")
            return
        
        # Abre seletor de arquivos
        self.interface_manager.mostrar_seletor_arquivos_metadados(self._processar_gerar_csv)
    

    def _processar_gerar_csv(self, arquivos_selecionados):
        """Processa geração de CSV com arquivos selecionados - CORRIGIDO"""
        if not self.csv_generator:
            self.logger.log("CSVGenerator não inicializado", "ERROR", "❌")
            return
        
        self._set_buttons_state("disabled")
        
        def gerar_thread():
            try:
                # Carrega e combina dados de múltiplos arquivos
                produtos_combinados = []
                
                self.logger.log(f"📊 Carregando dados de {len(arquivos_selecionados)} arquivo(s)...", "INFO", "📊")
                
                for arquivo in arquivos_selecionados:
                    try:
                        import json
                        with open(arquivo, 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        
                        # CORREÇÃO: Trata corretamente diferentes estruturas de JSON
                        if isinstance(dados, list):
                            # Se dados é uma lista direta (como no exemplo)
                            produtos = dados
                        elif isinstance(dados, dict):
                            # Se dados é um dict, procura por chaves conhecidas
                            produtos = (dados.get('produtos_extraidos') or 
                                      dados.get('produtos') or 
                                      dados.get('items') or 
                                      dados.get('data') or [])
                        else:
                            produtos = []
                        
                        produtos_combinados.extend(produtos)
                        
                        self.logger.log(f"✅ Carregado: {len(produtos)} produtos de {arquivo.name}", "SUCCESS", "✅")
                        
                    except Exception as e:
                        self.logger.log(f"❌ Erro ao carregar {arquivo.name}: {str(e)}", "ERROR", "❌")
                
                if not produtos_combinados:
                    self.logger.log("❌ Nenhum produto encontrado nos arquivos selecionados", "ERROR", "❌")
                    return
                
                self.logger.log(f"📊 Total de produtos combinados: {len(produtos_combinados)}", "INFO", "📊")
                
                # Gera CSV com dados combinados
                sucesso = self.csv_generator.gerar_csv_ecommerce(produtos_combinados)
                
                if sucesso:
                    self.logger.log("✅ CSV gerado com sucesso!", "SUCCESS", "✅")
                    self._clear_work_area()
                else:
                    self.logger.log("❌ Falha na geração do CSV", "ERROR", "❌")
                    
            except Exception as e:
                self.logger.log(f"❌ Erro na geração de CSV: {str(e)}", "ERROR", "❌")
            finally:
                self._set_buttons_state("normal")
        
        threading.Thread(target=gerar_thread, daemon=True).start()

    
    def _baixar_imagens(self):
        """Abre interface para baixar imagens"""
        if not self.interface_manager:
            self.logger.log("InterfaceManager não inicializado", "ERROR", "❌")
            return
        
        self.logger.log("🖼️ Iniciando interface de download de imagens...", "INFO", "🖼️")
        
        # Usa interface_manager para criar interface de download de imagens
        self.interface_manager.create_image_download_interface(
            self.work_content,
            self.config_manager,
            self._processar_download_imagens
        )
    
    def _processar_download_imagens(self, modo, arquivos_selecionados=None):
        """Processa download de imagens usando image_downloader INTEGRADO"""
        self._set_buttons_state("disabled")
        
        def download_thread():
            try:
                # Import do image_downloader integrado
                sys.path.append(str(Path("system")))
                import image_downloader
                
                # Configura logger do sistema no image_downloader
                image_downloader.set_system_logger(self.logger)
                
                self.logger.log("🖼️ Iniciando sistema de download integrado", "INFO", "🖼️")
                
                # Determina arquivos baseado no modo
                selected_files = None
                if modo == "provocado" and arquivos_selecionados:
                    selected_files = arquivos_selecionados
                    self.logger.log(f"📁 Modo provocado: {len(arquivos_selecionados)} arquivo(s)", "INFO", "📁")
                else:
                    self.logger.log("🤖 Modo autônomo: arquivo mais recente", "INFO", "🤖")
                
                # Chama função integrada do image_downloader
                resultado = image_downloader.main_integrated(
                    system_logger=self.logger,
                    selected_files=selected_files
                )
                
                if resultado.get("success"):
                    total_albums = resultado.get("total_albums", 0)
                    self.logger.log(f"✅ Download concluído com sucesso! {total_albums} álbuns processados", "SUCCESS", "✅")
                    self._clear_work_area()
                else:
                    error = resultado.get("error", "Erro desconhecido")
                    self.logger.log(f"❌ Falha no download: {error}", "ERROR", "❌")
                
            except ImportError as e:
                self.logger.log(f"❌ Erro ao importar image_downloader: {e}", "ERROR", "❌")
            except Exception as e:
                self.logger.log(f"❌ Erro crítico no download: {e}", "ERROR", "❌")
                import traceback
                traceback.print_exc()
            finally:
                self._set_buttons_state("normal")
        
        threading.Thread(target=download_thread, daemon=True).start()    
    def _processar_categorias(self):
        self.logger.log("🔧 Função 'Processar Categorias' será implementada", "INFO", "🔧")
    


    def _processar_produtos(self):
        """Pipeline AUTÔNOMO: Coletar Metadados -> Gerar CSV -> Baixar Imagens (último JSON)."""
        if not self.interface_manager:
            self.logger.log("InterfaceManager não inicializado", "ERROR", "❌")
            return
        self.interface_manager.create_metadata_interface(
            self.work_content,
            self.config_manager,
            self._pipeline_produtos
        )
    
    def _pipeline_produtos(self, urls):
        """Executa coleta de metadados, gera CSV do JSON recém-criado e baixa imagens desse JSON."""
        if not self.data_processor or not self.csv_generator:
            self.logger.log("Módulos DataProcessor/CSVGenerator não inicializados", "ERROR", "❌")
            return
    
        self._set_buttons_state("disabled")
    
        def run_pipeline():
            try:
                self.logger.log("🧩 Coletando metadados…", "INFO", "🧩")
                resultado = self.data_processor.processar_metadados(urls)
    
                from pathlib import Path
                json_path = None
                if isinstance(resultado, dict) and resultado.get("arquivo"):
                    json_path = Path(str(resultado["arquivo"]))
                if not json_path or not json_path.exists():
                    json_path = self._find_latest_metadata_file()
    
                if not json_path:
                    self.logger.log("❌ Nenhum arquivo de metadados encontrado", "ERROR", "❌")
                    return
    
                self.logger.log(f"🗂️ Metadados: {json_path.name}", "INFO", "🗂️")
    
                produtos = self._load_products_from_json(json_path)
                if not produtos:
                    self.logger.log("❌ Nenhum produto encontrado", "ERROR", "❌")
                    return
    
                self.logger.log(f"📊 Gerando CSV para {len(produtos)} produtos…", "INFO", "📊")
                if not self.csv_generator.gerar_csv_ecommerce(produtos):
                    self.logger.log("❌ Falha na geração do CSV", "ERROR", "❌")
                    return
                self.logger.log("✅ CSV gerado com sucesso", "SUCCESS", "✅")
    
                import sys
                sys.path.append(str(Path("system")))
                import image_downloader
                image_downloader.set_system_logger(self.logger)
                self.logger.log("🖼️ Baixando imagens (modo autônomo)…", "INFO", "🖼️")
                res = image_downloader.main_integrated(system_logger=self.logger, selected_files=[json_path])
                if res.get("success"):
                    self.logger.log("✅ Download de imagens concluído", "SUCCESS", "✅")
                    self._clear_work_area()
                else:
                    self.logger.log(f"❌ Falha no download: {res.get('error')}", "ERROR", "❌")
            finally:
                self._set_buttons_state("normal")
    
        import threading
        threading.Thread(target=run_pipeline, daemon=True).start()
    
    def _find_latest_metadata_file(self):
        """Retorna o JSON mais recente em ./Metadados/."""
        from pathlib import Path
        import re, datetime
        metadir = Path("Metadados")
        files = list(metadir.glob("*.json"))
        if not files:
            return None
        def parse_ts(p: Path):
            m = re.search(r"(20\\d{6})[-_](\\d{6})", p.name)
            if m:
                try:
                    return datetime.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S")
                except Exception:
                    return None
            return None
        files_scored = [(parse_ts(f) or 0, f.stat().st_mtime, f) for f in files]
        return max(files_scored, key=lambda x: (x[0], x[1]))[2]
    
    def _load_products_from_json(self, json_path):
        """Carrega lista de produtos a partir de um JSON de metadados."""
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("produtos_extraidos") or data.get("produtos") or data.get("items") or data.get("data") or []
        return []
    







    def _marcacao_precos(self):
        if not self.interface_manager:
            self.logger.log("InterfaceManager não inicializado", "ERROR", "❌")
            return
        try:
            self.interface_manager.abrir_marcacao_precos()
        except Exception as e:
            self.logger.log("Erro ao abrir marcação de preços: " + str(e), "ERROR", "❌")
    def _abrir_configuracoes(self):
        """Abre a tela de configurações"""
        if not self.config_manager:
            self.logger.log("Sistema de configurações não inicializado", "ERROR", "❌")
            return
            
        try:
            config_file = Path("system") / "configuracao.py"
            if not config_file.exists():
                self.logger.log("Módulo de configuração não encontrado", "ERROR", "❌")
                return
            
            sys.path.append("system")
            from configuracao import ConfiguradorSistema
            
            configurador = ConfiguradorSistema(self.root, self.logger, self.config_manager, self)
            configurador.abrir_configuracoes()
            
        except ImportError as e:
            self.logger.log(f"Erro ao importar configuração: {str(e)}", "ERROR", "❌")
        except Exception as e:
            self.logger.log(f"Erro ao abrir configurações: {str(e)}", "ERROR", "❌")
    
    def _gerar_log(self):
        """Gera arquivo de log"""
        if not self.logger.log_history:
            self.logger.log("⚠️ Nenhum log para salvar", "WARNING", "⚠️")
            return
        
        filepath = self.logger.save_to_file()
        if filepath:
            self.logger.log(f"📄 Log salvo em: {filepath}", "SUCCESS", "✅")
        else:
            self.logger.log("❌ Erro ao salvar log", "ERROR", "❌")
    
    def _limpar_log(self):
        """Limpa o log em tempo real"""
        self.logger.clear()
        self.logger.log("🧹 Log limpo", "INFO", "🧹")
    
    def _sair(self):
        """Encerra o sistema"""
        if self.processing:
            self.logger.log("⚠️ Aguarde o processamento terminar", "WARNING", "⚠️")
            return
        
        result = messagebox.askyesno("Sair", "Deseja realmente sair do Sistema BORA?")
        if result:
            self.logger.log("👋 Encerrando Sistema BORA...", "INFO", "👋")
            self.root.after(1000, self.root.destroy)
    
    def run(self):
        """Inicia o sistema"""
        self.root.mainloop()

def main():
    """Função principal"""
    try:
        logger.info("🚀 Iniciando Sistema BORA...")
        
        # Cria e executa a aplicação
        app = SistemaBORA()
        logger.info("✅ Interface criada com sucesso")
        app.run()
        
    except Exception as e:
        logger.info(f"❌ Erro crítico: {str(e)}")
        logger.info(f"🔍 Detalhes do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()