#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurador Principal (Versão Tkinter)
Interface principal que coordena configurações especializadas
"""

import json
import tkinter as tk
from tkinter import ttk, colorchooser, font, messagebox
from pathlib import Path
from typing import Dict, Any, Optional

class LoggerConfig:
    """Configurador de cores e fontes do logger"""
    
    def __init__(self, configurador):
        self.configurador = configurador
        self.logger = configurador.logger
        self.config_manager = configurador.config_manager
        
        # Configurações padrão de cores
        self.default_colors = {
            "INFO": "#4A90E2",      # Azul
            "SUCCESS": "#7ED321",   # Verde
            "ERROR": "#D0021B",     # Vermelho
            "WARNING": "#F5A623",   # Laranja
            "DEBUG": "#9013FE",     # Roxo
            "TIMESTAMP": "#666666"  # Cinza
        }
        
        # Configurações padrão de fonte
        self.default_font_config = {
            "family": "Consolas",
            "size": 12,
            "weight": "normal"  # normal ou bold
        }
        
        self.color_vars = {}
        self.font_vars = {}
        self.preview_text = None
        
    def create_tab(self, notebook):
        """Cria a aba de configuração do logger"""
        # Cria aba
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="🎨 Logger")
        
        # Container principal SEM scroll - tudo na tela visível
        main_container = ttk.Frame(self.tab)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Configurar grid principal: 2 linhas
        main_container.grid_rowconfigure(0, weight=1)  # Área superior (cores + fonte)
        main_container.grid_rowconfigure(1, weight=1)  # Área inferior (preview)
        main_container.grid_columnconfigure(0, weight=1)
        
        # LINHA SUPERIOR: Cores e Fonte lado a lado
        top_frame = ttk.Frame(main_container)
        top_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Configurar colunas da linha superior
        top_frame.grid_columnconfigure(0, weight=3)  # Cores - 75%
        top_frame.grid_columnconfigure(1, weight=1)  # Fonte - 25%
        top_frame.grid_rowconfigure(0, weight=1)
        
        # Seção de cores (esquerda superior)
        self._create_colors_section(top_frame)
        
        # Seção de fonte (direita superior)
        self._create_font_section(top_frame)
        
        # LINHA INFERIOR: Preview ocupando toda largura
        self._create_preview_section(main_container)
        
        # Carregar configurações atuais
        self.load_config()
        
    def _create_colors_section(self, parent):
        """Cria seção de configuração de cores"""
        colors_frame = ttk.LabelFrame(parent, text="🎨 Cores das Mensagens", padding=12)
        colors_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Título compacto
        title_label = ttk.Label(
            colors_frame,
            text="Personalize as cores para cada tipo de mensagem do logger",
            font=("Arial", 9, "italic"),
            wraplength=300
        )
        title_label.pack(pady=(0, 10))
        
        # Grid para as cores (3 colunas x 2 linhas) - mais compacto
        colors_grid = ttk.Frame(colors_frame)
        colors_grid.pack(fill="both", expand=True)
        
        # Configurar grid para 3 colunas
        for i in range(3):
            colors_grid.grid_columnconfigure(i, weight=1)
        
        # Labels descritivos para cada tipo
        color_descriptions = {
            "INFO": "Informações gerais",
            "SUCCESS": "Operações bem-sucedidas", 
            "ERROR": "Mensagens de erro",
            "WARNING": "Avisos importantes",
            "DEBUG": "Modo debug",
            "TIMESTAMP": "Horário das mensagens"
        }
        
        # Organizar em 2 linhas x 3 colunas
        positions = [
            ("INFO", 0, 0), ("SUCCESS", 0, 1), ("ERROR", 0, 2),
            ("WARNING", 1, 0), ("DEBUG", 1, 1), ("TIMESTAMP", 1, 2)
        ]
        
        for level, row, col in positions:
            description = color_descriptions[level]
            
            # Frame para cada cor - mais compacto
            color_frame = ttk.Frame(colors_grid)
            color_frame.grid(row=row, column=col, padx=8, pady=5, sticky="ew")
            
            # Label do tipo - fonte menor
            type_label = ttk.Label(
                color_frame,
                text=f"{level}:",
                font=("Arial", 8, "bold")
            )
            type_label.pack(anchor="w")
            
            # Descrição - fonte menor
            desc_label = ttk.Label(
                color_frame,
                text=description,
                font=("Arial", 7),
                foreground="gray"
            )
            desc_label.pack(anchor="w")
            
            # Variável para cor
            color_var = tk.StringVar(value=self.default_colors[level])
            self.color_vars[level] = color_var
            
            # Botão de cor - altura reduzida
            color_button = tk.Button(
                color_frame,
                text="   ",
                bg=self.default_colors[level],
                relief="solid",
                borderwidth=2,
                command=lambda l=level: self._choose_color(l),
                cursor="hand2",
                height=1
            )
            color_button.pack(pady=3, fill="x")
            
            # Salvar referência do botão
            setattr(self, f"color_button_{level.lower()}", color_button)
        
        # Botão para restaurar cores padrão - compacto
        restore_button = ttk.Button(
            colors_frame,
            text="🔄 Restaurar Cores Padrão",
            command=self._restore_default_colors
        )
        restore_button.pack(pady=8)
        
    def _create_font_section(self, parent):
        """Cria seção de configuração de fonte"""
        font_frame = ttk.LabelFrame(parent, text="🔤 Configuração da Fonte", padding=12)
        font_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        # Título compacto
        desc_label = ttk.Label(
            font_frame,
            text="Configure a fonte do logger",
            font=("Arial", 9, "italic")
        )
        desc_label.pack(pady=(0, 10))
        
        # Família da fonte
        family_frame = ttk.Frame(font_frame)
        family_frame.pack(fill="x", pady=3)
        
        ttk.Label(family_frame, text="Família:", font=("Arial", 8, "bold")).pack(anchor="w")
        
        # Lista de fontes monospace disponíveis
        monospace_fonts = [
            "Consolas", "Courier New", "Monaco", "Menlo", 
            "DejaVu Sans Mono", "Liberation Mono", "Lucida Console"
        ]
        
        self.font_vars["family"] = tk.StringVar(value=self.default_font_config["family"])
        font_combo = ttk.Combobox(
            family_frame,
            textvariable=self.font_vars["family"],
            values=monospace_fonts,
            state="readonly",
            height=5  # Reduz altura do dropdown
        )
        font_combo.pack(fill="x", pady=2)
        font_combo.bind("<<ComboboxSelected>>", self._update_preview)
        
        # Tamanho da fonte
        size_frame = ttk.Frame(font_frame)
        size_frame.pack(fill="x", pady=3)
        
        ttk.Label(size_frame, text="Tamanho:", font=("Arial", 8, "bold")).pack(anchor="w")
        
        self.font_vars["size"] = tk.StringVar(value=str(self.default_font_config["size"]))
        size_spin = tk.Spinbox(
            size_frame,
            from_=8,
            to=24,
            textvariable=self.font_vars["size"],
            command=self._update_preview,
            width=15
        )
        size_spin.pack(fill="x", pady=2)
        size_spin.bind("<KeyRelease>", self._update_preview)
        
        # Peso da fonte (negrito)
        weight_frame = ttk.Frame(font_frame)
        weight_frame.pack(fill="x", pady=3)
        
        ttk.Label(weight_frame, text="Estilo:", font=("Arial", 8, "bold")).pack(anchor="w")
        
        self.font_vars["weight"] = tk.StringVar(value=self.default_font_config["weight"])
        
        style_frame = ttk.Frame(weight_frame)
        style_frame.pack(fill="x", pady=2)
        
        ttk.Radiobutton(
            style_frame,
            text="Normal",
            variable=self.font_vars["weight"],
            value="normal",
            command=self._update_preview
        ).pack(anchor="w")
        
        ttk.Radiobutton(
            style_frame,
            text="Negrito",
            variable=self.font_vars["weight"],
            value="bold",
            command=self._update_preview
        ).pack(anchor="w")
        
    def _create_preview_section(self, parent):
        """Cria seção de preview das configurações"""
        preview_frame = ttk.LabelFrame(parent, text="👁️ Visualização", padding=12)
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        # Configurar para que o preview se expanda
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)
        
        # Descrição compacta
        desc_label = ttk.Label(
            preview_frame,
            text="Veja como ficarão as mensagens do logger com suas configurações:",
            font=("Arial", 9, "italic")
        )
        desc_label.grid(row=0, column=0, pady=(0, 8), sticky="w")
        
        # Widget de preview - altura otimizada
        self.preview_text = tk.Text(
            preview_frame,
            height=6,  # Altura reduzida para caber na tela
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief="solid",
            borderwidth=1
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew")
        
        # Scrollbar para o preview
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        preview_scrollbar.grid(row=1, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        # Atualizar preview inicial
        self.root_after_idle = parent.after_idle(self._update_preview)
    
    def _choose_color(self, level):
        """Abre seletor de cores"""
        current_color = self.color_vars[level].get()
        
        color = colorchooser.askcolor(
            color=current_color,
            title=f"Escolha a cor para {level}"
        )
        
        if color[1]:  # Se uma cor foi selecionada
            new_color = color[1]
            self.color_vars[level].set(new_color)
            
            # Atualiza botão
            button = getattr(self, f"color_button_{level.lower()}")
            button.configure(bg=new_color)
            
            # Atualiza preview
            self._update_preview()
    
    def _restore_default_colors(self):
        """Restaura cores padrão"""
        for level, default_color in self.default_colors.items():
            self.color_vars[level].set(default_color)
            button = getattr(self, f"color_button_{level.lower()}")
            button.configure(bg=default_color)
        
        self._update_preview()
        
    def _update_preview(self, event=None):
        """Atualiza preview das configurações"""
        if not self.preview_text:
            return
            
        # Limpa preview
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        # Configurações de fonte atuais
        font_family = self.font_vars["family"].get()
        font_size = int(self.font_vars["size"].get() or 12)
        font_weight = self.font_vars["weight"].get()
        
        # Configura tags de cores
        for level in self.color_vars.keys():
            color = self.color_vars[level].get()
            if level == "TIMESTAMP":
                self.preview_text.tag_config(
                    level.lower(),
                    foreground=color,
                    font=(font_family, font_size, font_weight)
                )
            else:
                self.preview_text.tag_config(
                    level.lower(),
                    foreground=color,
                    font=(font_family, font_size, font_weight)
                )
        
        # Exemplos de mensagens
        examples = [
            ("TIMESTAMP", "[14:30:25] "),
            ("INFO", "ℹ️ Sistema iniciado com sucesso\n"),
            ("TIMESTAMP", "[14:30:26] "),
            ("SUCCESS", "✅ Configurações carregadas\n"),
            ("TIMESTAMP", "[14:30:27] "),
            ("WARNING", "⚠️ Aviso: Memória em 85%\n"),
            ("TIMESTAMP", "[14:30:28] "),
            ("ERROR", "❌ Erro ao conectar com servidor\n"),
            ("TIMESTAMP", "[14:30:29] "),
            ("DEBUG", "🛠 Modo debug ativado\n")
        ]
        
        # Adiciona exemplos com as cores configuradas
        for level, text in examples:
            self.preview_text.insert(tk.END, text, level.lower())
        
        self.preview_text.configure(state=tk.DISABLED)
    
    def load_config(self):
        """Carrega configurações atuais"""
        try:
            # Carrega cores
            logger_colors = self.config_manager.get("logger_colors", {})
            for level in self.color_vars.keys():
                saved_color = logger_colors.get(level, self.default_colors[level])
                self.color_vars[level].set(saved_color)
                
                # Atualiza botão
                button = getattr(self, f"color_button_{level.lower()}")
                button.configure(bg=saved_color)
            
            # Carrega configurações de fonte
            logger_font = self.config_manager.get("logger_font", {})
            for key, default in self.default_font_config.items():
                saved_value = logger_font.get(key, default)
                self.font_vars[key].set(str(saved_value))
            
            # Atualiza preview
            self._update_preview()
            
        except Exception as e:
            self.logger.log(f"Erro ao carregar config do logger: {str(e)}", "ERROR", "❌")
    
    def save_config(self):
        """Salva configurações do logger"""
        try:
            # Salva cores
            colors_config = {}
            for level, var in self.color_vars.items():
                colors_config[level] = var.get()
            
            # Salva configurações de fonte
            font_config = {}
            for key, var in self.font_vars.items():
                value = var.get()
                if key == "size":
                    value = int(value)
                font_config[key] = value
            
            # Atualiza config_manager
            self.config_manager.config["logger_colors"] = colors_config
            self.config_manager.config["logger_font"] = font_config
            
            # Aplica configurações no logger principal se disponível
            if hasattr(self.configurador, 'main_app') and self.configurador.main_app:
                main_logger = self.configurador.main_app.logger
                if main_logger and hasattr(main_logger, 'update_config'):
                    main_logger.update_config()
            
            return True
            
        except Exception as e:
            self.logger.log(f"Erro ao salvar config do logger: {str(e)}", "ERROR", "❌")
            return False

class ConfiguradorSistema:
    """Interface principal de configuração - Versão Tkinter"""
    
    def __init__(self, parent_window, logger, config_manager, main_app=None):
        self.parent = parent_window
        self.logger = logger
        self.config_manager = config_manager
        self.main_app = main_app
        self.config_window: Optional[tk.Toplevel] = None
        
        # Inicializa módulos especializados - INCLUINDO ImageDownloadConfig
        self.modules = {
            'logger': LoggerConfig(self),
            'download': ImageDownloadConfig(self),  # NOVA ABA ADICIONADA
            'general': GeneralConfig(self),
            'sizes': SizesConfig(self),
            'teams': TeamsConfig(self)  # REMOVIDAS: apis, categories, interface
        }
        
    def abrir_configuracoes(self):
        """Abre a janela principal de configurações"""
        if self.config_window is not None:
            self.config_window.focus()
            return
        
        self.logger.log("Abrindo configurações do sistema...", "INFO", "⚙️")
        
        # Carrega geometria salva
        saved_geometry = self.config_manager.get("config_window_geometry", "950x750")
        
        # Cria janela principal
        self.config_window = tk.Toplevel(self.parent)
        self.config_window.title("Configurações - Sistema BORA")
        self.config_window.geometry(saved_geometry)
        self.config_window.transient(self.parent)
        
        # Centraliza
        self.config_window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 100,
            self.parent.winfo_rooty() + 50
        ))
        
        # Evento de fechamento
        self.config_window.protocol("WM_DELETE_WINDOW", self._fechar_configuracoes)
        
        # Bind para salvar geometria quando redimensionar
        self.config_window.bind('<Configure>', self._on_window_configure)
        
        self._criar_interface_principal()
        
    def _on_window_configure(self, event):
        """Salva geometria da janela quando redimensionada"""
        # Só salva se o evento é da janela principal (não de widgets filhos)
        if event.widget == self.config_window:
            try:
                geometry = self.config_window.geometry()
                self.config_manager.config["config_window_geometry"] = geometry
                
                # Salva imediatamente no arquivo
                config_file = Path("system") / "config.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config_manager.config, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                self.logger.log(f"Erro ao salvar geometria: {str(e)}", "ERROR", "❌")
        
    def _criar_interface_principal(self):
        """Cria a interface principal com abas modulares"""
        # Header
        header_frame = ttk.Frame(self.config_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Título principal
        title_label = ttk.Label(
            header_frame,
            text="🔧 Configurações do Sistema BORA",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Configure todos os aspectos do sistema através das abas abaixo",
            font=("Arial", 11)
        )
        subtitle_label.pack(pady=5)
        
        # Notebook principal com abas modulares
        self.notebook = ttk.Notebook(self.config_window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cria todas as abas usando os módulos
        self._criar_abas_modulares()
        
        # Footer com botões principais
        self._criar_footer()
        
    def _criar_abas_modulares(self):
        """Cria abas usando módulos especializados"""
        try:
            # Ordem das abas - Logger primeiro, Download segundo, depois outros
            module_order = ['logger', 'download', 'general', 'sizes', 'teams']
            
            self.logger.log(f"Tentando criar {len(module_order)} abas", "INFO", "📋")
            self.logger.log(f"Módulos disponíveis: {list(self.modules.keys())}", "INFO", "📋")
            
            for module_name in module_order:
                self.logger.log(f"Processando módulo '{module_name}'...", "INFO", "🔧")
                
                if module_name in self.modules:
                    module = self.modules[module_name]
                    try:
                        self.logger.log(f"Criando aba '{module_name}'...", "INFO", "🔧")
                        module.create_tab(self.notebook)
                        self.logger.log(f"Aba '{module_name}' criada com sucesso", "SUCCESS", "✅")
                    except Exception as e:
                        self.logger.log(f"Erro ao criar aba '{module_name}': {str(e)}", "ERROR", "❌")
                        import traceback
                        self.logger.log(f"Traceback: {traceback.format_exc()}", "ERROR", "🔍")
                else:
                    self.logger.log(f"Módulo '{module_name}' não encontrado nos módulos disponíveis", "WARNING", "⚠️")
            
            # Log final
            tabs_count = self.notebook.index("end")
            self.logger.log(f"Total de abas criadas: {tabs_count}", "INFO", "📊")
                        
        except Exception as e:
            self.logger.log(f"Erro geral ao criar abas: {str(e)}", "ERROR", "❌")
            import traceback
            self.logger.log(f"Traceback geral: {traceback.format_exc()}", "ERROR", "🔍")
    
    def _criar_footer(self):
        """Cria footer com botões de ação"""
        footer_frame = ttk.Frame(self.config_window)
        footer_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(
            footer_frame,
            text="🛠 Pronto para configurar",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left", padx=10, pady=10)
        
        # Botões principais
        ttk.Button(
            footer_frame,
            text="💾 Salvar Todas",
            command=self._salvar_todas_configuracoes
        ).pack(side="right", padx=5, pady=10)
        
        ttk.Button(
            footer_frame,
            text="🔄 Recarregar",
            command=self._recarregar_configuracoes
        ).pack(side="right", padx=5, pady=10)
        
        ttk.Button(
            footer_frame,
            text="❌ Fechar",
            command=self._fechar_configuracoes
        ).pack(side="right", padx=5, pady=10)
        
    def _salvar_todas_configuracoes(self):
        """Salva configurações de todos os módulos"""
        try:
            self._update_status("💾 Salvando configurações...")
            
            # Salva cada módulo
            success_count = 0
            total_modules = len(self.modules)
            
            for module_name, module in self.modules.items():
                try:
                    if module.save_config():
                        success_count += 1
                        self.logger.log(f"Módulo '{module_name}' salvo", "SUCCESS", "✅")
                    else:
                        self.logger.log(f"Falha ao salvar módulo '{module_name}'", "ERROR", "❌")
                except Exception as e:
                    self.logger.log(f"Erro no módulo '{module_name}': {str(e)}", "ERROR", "❌")
            
            # Salva arquivo principal de configuração
            self._salvar_arquivo_config()
            
            if success_count == total_modules:
                self._update_status("✅ Todas as configurações salvas com sucesso!")
                self.logger.log("💾 Configurações salvas com sucesso!", "SUCCESS", "✅")
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            else:
                self._update_status(f"⚠️ {success_count}/{total_modules} módulos salvos")
                self.logger.log(f"Apenas {success_count}/{total_modules} módulos salvos", "WARNING", "⚠️")
                
        except Exception as e:
            self._update_status("❌ Erro ao salvar configurações")
            self.logger.log(f"Erro ao salvar configurações: {str(e)}", "ERROR", "❌")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {str(e)}")
    
    def _salvar_arquivo_config(self):
        """Salva o arquivo principal config.json"""
        try:
            config_file = Path("system") / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_manager.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Falha ao salvar config.json: {str(e)}")
    
    def _recarregar_configuracoes(self):
        """Recarrega todas as configurações"""
        try:
            self._update_status("🔄 Recarregando configurações...")
            
            if self.config_manager.load_config():
                self.logger.log("Configurações recarregadas do arquivo", "INFO", "🔄")
                self._fechar_configuracoes()
                self.abrir_configuracoes()
            else:
                self._update_status("❌ Erro ao recarregar")
                self.logger.log("Erro ao recarregar configurações", "ERROR", "❌")
                
        except Exception as e:
            self._update_status("❌ Erro no recarregamento")
            self.logger.log(f"Erro ao recarregar: {str(e)}", "ERROR", "❌")
    
    def _update_status(self, message: str):
        """Atualiza mensagem de status"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            self.config_window.update_idletasks()
    
    def _fechar_configuracoes(self):
        """Fecha a janela de configurações"""
        if self.config_window:
            self.logger.log("Fechando configurações", "INFO", "🔧")
            self.config_window.destroy()
            self.config_window = None
    
    # Métodos auxiliares para módulos
    def get_main_window(self):
        """Retorna referência à janela principal"""
        return self.parent
        
    def get_config_window(self):
        """Retorna referência à janela de configurações"""
        return self.config_window
        
    def refresh_module(self, module_name: str):
        """Recarrega um módulo específico"""
        if module_name in self.modules:
            try:
                self.modules[module_name].load_config()
                self.logger.log(f"Módulo '{module_name}' recarregado", "INFO", "🔄")
            except Exception as e:
                self.logger.log(f"Erro ao recarregar módulo '{module_name}': {str(e)}", "ERROR", "❌")
    
    def _apply_config_to_logger(self, logger):
        """Aplica configurações ao logger principal"""
        try:
            # Atualiza cores
            for level, color in self.color_vars.items():
                logger.color_map[level] = color.get()
                logger.log_widget.tag_config(level.lower(), foreground=color.get())
            
            # Atualiza fonte
            font_family = self.font_vars["family"].get()
            font_size = int(self.font_vars["size"].get())
            font_weight = self.font_vars["weight"].get()
            
            logger.log_widget.configure(font=(font_family, font_size, font_weight))
            
        except Exception as e:
            self.logger.log(f"Erro ao aplicar config no logger: {str(e)}", "ERROR", "❌")

class ImageDownloadConfig:
    """Configurações de download de imagens"""
    
    def __init__(self, configurador):
        self.configurador = configurador
        self.logger = configurador.logger
        self.config_manager = configurador.config_manager
        
        # Configurações padrão
        self.default_config = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "timeout": 10.0,
            "delay_between_images": 1.0
        }
        
        self.vars = {}
        
    def create_tab(self, notebook):
        """Cria a aba de configuração de download de imagens"""
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="🖼️ Download")
        
        # Container principal
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="🖼️ Configurações de Download de Imagens",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para configurações de rede
        network_frame = ttk.LabelFrame(main_frame, text="Configurações de Rede", padding=15)
        network_frame.pack(fill="x", pady=10)
        
        # User-Agent
        ua_frame = ttk.Frame(network_frame)
        ua_frame.pack(fill="x", pady=5)
        
        ttk.Label(ua_frame, text="User-Agent:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.vars["user_agent"] = tk.StringVar(value=self.default_config["user_agent"])
        ua_entry = ttk.Entry(ua_frame, textvariable=self.vars["user_agent"], width=70)
        ua_entry.pack(fill="x", pady=2)
        
        ttk.Label(
            ua_frame,
            text="Identifica o navegador nas requisições. Use o padrão ou um User-Agent específico.",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor="w", pady=(2, 0))
        
        # Timeout
        timeout_frame = ttk.Frame(network_frame)
        timeout_frame.pack(fill="x", pady=5)
        
        ttk.Label(timeout_frame, text="Timeout (segundos):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        timeout_container = ttk.Frame(timeout_frame)
        timeout_container.pack(fill="x", pady=2)
        
        self.vars["timeout"] = tk.DoubleVar(value=self.default_config["timeout"])
        timeout_spin = ttk.Spinbox(
            timeout_container,
            from_=1.0,
            to=60.0,
            increment=1.0,
            textvariable=self.vars["timeout"],
            width=10
        )
        timeout_spin.pack(side="left")
        
        ttk.Label(
            timeout_container,
            text="Tempo limite para cada requisição de imagem",
            font=("Arial", 8),
            foreground="gray"
        ).pack(side="left", padx=(10, 0))
        
        # Delay entre imagens
        delay_frame = ttk.Frame(network_frame)
        delay_frame.pack(fill="x", pady=5)
        
        ttk.Label(delay_frame, text="Delay entre imagens (segundos):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        delay_container = ttk.Frame(delay_frame)
        delay_container.pack(fill="x", pady=2)
        
        self.vars["delay_between_images"] = tk.DoubleVar(value=self.default_config["delay_between_images"])
        delay_spin = ttk.Spinbox(
            delay_container,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.vars["delay_between_images"],
            width=10
        )
        delay_spin.pack(side="left")
        
        ttk.Label(
            delay_container,
            text="Pausa entre downloads para evitar sobrecarga do servidor",
            font=("Arial", 8),
            foreground="gray"
        ).pack(side="left", padx=(10, 0))
        
        # Frame para configurações de imagem (movido da aba Geral)
        images_frame = ttk.LabelFrame(main_frame, text="Configurações de Imagem", padding=15)
        images_frame.pack(fill="x", pady=10)
        
        # Tamanho mínimo da imagem
        image_size_frame = ttk.Frame(images_frame)
        image_size_frame.pack(fill="x", pady=5)
        
        ttk.Label(image_size_frame, text="Tamanho mínimo da imagem (Kb):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        size_container = ttk.Frame(image_size_frame)
        size_container.pack(fill="x", pady=2)
        
        self.vars["tamanho_minimo_imagem"] = tk.IntVar(value=self.config_manager.get("tamanho_minimo_imagem", 1024))
        image_size_spin = ttk.Spinbox(
            size_container,
            from_=10,
            to=1024,
            increment=5,
            textvariable=self.vars["tamanho_minimo_imagem"],
            width=10
        )
        image_size_spin.pack(side="left")
        
        ttk.Label(
            size_container,
            text="Tamanho mínimo em Kb que uma imagem deve ter para ser considerada válida",
            font=("Arial", 8),
            foreground="gray"
        ).pack(side="left", padx=(10, 0))
        
        # Frame para botões de ação
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill="x", pady=20)
        
        # Botão para restaurar padrões
        restore_btn = ttk.Button(
            actions_frame,
            text="🔄 Restaurar Padrões",
            command=self._restore_defaults
        )
        restore_btn.pack(side="left")
        
        # Carrega configurações
        self.load_config()
    
    def _restore_defaults(self):
        """Restaura configurações padrão"""
        for key, value in self.default_config.items():
            if key in self.vars:
                self.vars[key].set(value)
        
        # Restaura também o tamanho mínimo da imagem
        self.vars["tamanho_minimo_imagem"].set(10)
        
        self.logger.log("Configurações de download restauradas para padrão", "INFO", "🔄")
    
    def load_config(self):
        """Carrega configurações atuais"""
        try:
            download_config = self.config_manager.get("image_downloader", {})
            
            for key, default_value in self.default_config.items():
                saved_value = download_config.get(key, default_value)
                if key in self.vars:
                    self.vars[key].set(saved_value)
            
            # Carrega tamanho mínimo da imagem
            if "tamanho_minimo_imagem" in self.vars:
                tamanho = self.config_manager.get("tamanho_minimo_imagem", 1024)
                self.vars["tamanho_minimo_imagem"].set(tamanho)
            
        except Exception as e:
            self.logger.log(f"Erro ao carregar config de download: {str(e)}", "ERROR", "❌")
    
    def save_config(self):
        """Salva configurações de download"""
        try:
            download_config = {}
            
            for key, var in self.vars.items():
                if key == "tamanho_minimo_imagem":
                    # Salva tamanho mínimo da imagem no nível raiz do config
                    self.config_manager.config["tamanho_minimo_imagem"] = var.get()
                else:
                    download_config[key] = var.get()
            
            self.config_manager.config["image_downloader"] = download_config
            
            return True
            
        except Exception as e:
            self.logger.log(f"Erro ao salvar config de download: {str(e)}", "ERROR", "❌")
            return False

class GeneralConfig:
    """Configurações gerais do sistema"""
    
    def __init__(self, configurador):
        self.configurador = configurador
        self.logger = configurador.logger
        self.config_manager = configurador.config_manager
        
    def create_tab(self, notebook):
        """Cria a aba de configurações gerais"""
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="⚙️ Geral")
        
        # Container principal
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="⚙️ Configurações Gerais",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para delays
        delays_frame = ttk.LabelFrame(main_frame, text="Configurações de Tempo", padding=15)
        delays_frame.pack(fill="x", pady=10)
        
        # Delay padrão
        delay_frame = ttk.Frame(delays_frame)
        delay_frame.pack(fill="x", pady=5)
        
        ttk.Label(delay_frame, text="Delay padrão (segundos):").pack(side="left")
        
        self.delay_var = tk.StringVar(value=str(self.config_manager.get("delay_padrao", 2.0)))
        delay_spin = tk.Spinbox(
            delay_frame,
            from_=0.5,
            to=10.0,
            increment=0.5,
            textvariable=self.delay_var,
            width=10
        )
        delay_spin.pack(side="right")
        
        # Delay após erro
        error_delay_frame = ttk.Frame(delays_frame)
        error_delay_frame.pack(fill="x", pady=5)
        
        ttk.Label(error_delay_frame, text="Delay após erro (segundos):").pack(side="left")
        
        self.error_delay_var = tk.StringVar(value=str(self.config_manager.get("delay_apos_erro", 5.0)))
        error_delay_spin = tk.Spinbox(
            error_delay_frame,
            from_=1.0,
            to=30.0,
            increment=1.0,
            textvariable=self.error_delay_var,
            width=10
        )
        error_delay_spin.pack(side="right")
    
    def save_config(self):
        """Salva configurações gerais"""
        try:
            self.config_manager.config["delay_padrao"] = float(self.delay_var.get())
            self.config_manager.config["delay_apos_erro"] = float(self.error_delay_var.get())
            return True
        except Exception as e:
            self.logger.log(f"Erro ao salvar config geral: {str(e)}", "ERROR", "❌")
            return False

class SizesConfig:
    """Configurações de tamanhos"""
    
    def __init__(self, configurador):
        self.configurador = configurador
        self.logger = configurador.logger
        self.config_manager = configurador.config_manager
        
    def create_tab(self, notebook):
        """Cria a aba de configurações de tamanhos"""
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="📏 Tamanhos")
        
        # Container principal
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="📏 Configurações de Tamanhos",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame horizontal para adulto e infantil
        sizes_container = ttk.Frame(main_frame)
        sizes_container.pack(fill="both", expand=True)
        
        # Tamanhos adulto
        adult_frame = ttk.LabelFrame(sizes_container, text="Tamanhos Adulto", padding=15)
        adult_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.adult_sizes = self.config_manager.get("tamanhos_adulto", ["P", "M", "G", "XG", "XXG", "XXXG"])
        self.adult_listbox = tk.Listbox(adult_frame, height=8)
        self.adult_listbox.pack(fill="both", expand=True, pady=5)
        
        for size in self.adult_sizes:
            self.adult_listbox.insert(tk.END, size)
        
        # Botões para tamanhos adulto
        adult_btn_frame = ttk.Frame(adult_frame)
        adult_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(adult_btn_frame, text="Adicionar", command=self._add_adult_size).pack(side="left", padx=2)
        ttk.Button(adult_btn_frame, text="Remover", command=self._remove_adult_size).pack(side="left", padx=2)
        
        # Tamanhos infantil
        child_frame = ttk.LabelFrame(sizes_container, text="Tamanhos Infantil", padding=15)
        child_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.child_sizes = self.config_manager.get("tamanhos_infantil", {})
        self.child_listbox = tk.Listbox(child_frame, height=8)
        self.child_listbox.pack(fill="both", expand=True, pady=5)
        
        for size, desc in self.child_sizes.items():
            self.child_listbox.insert(tk.END, f"{size} - {desc}")
        
        # Botões para tamanhos infantil
        child_btn_frame = ttk.Frame(child_frame)
        child_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(child_btn_frame, text="Adicionar", command=self._add_child_size).pack(side="left", padx=2)
        ttk.Button(child_btn_frame, text="Remover", command=self._remove_child_size).pack(side="left", padx=2)
    
    def _add_adult_size(self):
        """Adiciona tamanho adulto"""
        import tkinter.simpledialog
        size = tkinter.simpledialog.askstring("Novo Tamanho", "Digite o tamanho:")
        if size:
            self.adult_listbox.insert(tk.END, size)
    
    def _remove_adult_size(self):
        """Remove tamanho adulto selecionado"""
        selection = self.adult_listbox.curselection()
        if selection:
            self.adult_listbox.delete(selection[0])
    
    def _add_child_size(self):
        """Adiciona tamanho infantil"""
        import tkinter.simpledialog
        size = tkinter.simpledialog.askstring("Novo Tamanho", "Digite o tamanho (ex: 30):")
        if size:
            desc = tkinter.simpledialog.askstring("Descrição", "Digite a descrição (ex: 14 a 15 anos):")
            if desc:
                self.child_listbox.insert(tk.END, f"{size} - {desc}")
    
    def _remove_child_size(self):
        """Remove tamanho infantil selecionado"""
        selection = self.child_listbox.curselection()
        if selection:
            self.child_listbox.delete(selection[0])
    
    def save_config(self):
        """Salva configurações de tamanhos"""
        try:
            # Salva tamanhos adulto
            adult_sizes = []
            for i in range(self.adult_listbox.size()):
                adult_sizes.append(self.adult_listbox.get(i))
            self.config_manager.config["tamanhos_adulto"] = adult_sizes
            
            # Salva tamanhos infantil
            child_sizes = {}
            for i in range(self.child_listbox.size()):
                item = self.child_listbox.get(i)
                if " - " in item:
                    size, desc = item.split(" - ", 1)
                    child_sizes[size] = desc
            self.config_manager.config["tamanhos_infantil"] = child_sizes
            
            return True
        except Exception as e:
            self.logger.log(f"Erro ao salvar config de tamanhos: {str(e)}", "ERROR", "❌")
            return False

class TeamsConfig:
    """Configurações de Times/Equipes"""
    
    def __init__(self, configurador):
        self.configurador = configurador
        self.logger = configurador.logger
        self.config_manager = configurador.config_manager
        self.equipes_data = {}
        self.selected_item = None
        
        # Variáveis dos campos
        self.vars = {
            'categoria_principal': tk.StringVar(),
            'equipe': tk.StringVar(),
            'tipo': tk.StringVar(),
            'continente': tk.StringVar(),
            'pais': tk.StringVar(),
            'regiao': tk.StringVar(),
            'estado': tk.StringVar(),
            'is_national_team': tk.BooleanVar(),
            'is_brazilian': tk.BooleanVar()
        }
        
    def create_tab(self, notebook):
        """Cria a aba de configuração de times"""
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="⚽ Times")
        
        # Container principal
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="⚽ Configuração de Times e Equipes",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Frame para busca
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar equipe:", font=("Arial", 10, "bold")).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(10, 0))
        
        # Container principal dividido em duas partes
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_columnconfigure(0, weight=2)  # Tabela - 60%
        content_frame.grid_columnconfigure(1, weight=1)  # Formulário - 40%
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Frame da tabela (esquerda)
        table_frame = ttk.LabelFrame(content_frame, text="Lista de Equipes", padding=10)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview para a tabela
        columns = ("categoria", "tipo", "continente", "pais", "regiao", "estado", "nacional", "brasileiro")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", height=15)
        
        # Configurar cabeçalhos
        self.tree.heading("#0", text="Equipe")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("continente", text="Continente")
        self.tree.heading("pais", text="País")
        self.tree.heading("regiao", text="Região")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("nacional", text="Seleção")
        self.tree.heading("brasileiro", text="Brasileiro")
        
        # Configurar larguras
        self.tree.column("#0", width=120)
        self.tree.column("categoria", width=120)
        self.tree.column("tipo", width=80)
        self.tree.column("continente", width=100)
        self.tree.column("pais", width=100)
        self.tree.column("regiao", width=100)
        self.tree.column("estado", width=100)
        self.tree.column("nacional", width=70)
        self.tree.column("brasileiro", width=70)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars para a tabela
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Bind de seleção
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Frame do formulário (direita)
        form_frame = ttk.LabelFrame(content_frame, text="Edição de Equipe", padding=10)
        form_frame.grid(row=0, column=1, sticky="nsew")
        
        # Campos do formulário
        row = 0
        
        # Categoria Principal
        ttk.Label(form_frame, text="Categoria Principal:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        categoria_combo = ttk.Combobox(form_frame, textvariable=self.vars['categoria_principal'], 
                                     values=["times_brasileiros", "times_internacionais", "selecoes"], 
                                     state="readonly", width=25)
        categoria_combo.grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        categoria_combo.bind("<<ComboboxSelected>>", self._on_categoria_change)
        row += 1
        
        # Equipe
        ttk.Label(form_frame, text="Equipe:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Entry(form_frame, textvariable=self.vars['equipe'], width=25).grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        row += 1
        
        # Tipo
        ttk.Label(form_frame, text="Tipo:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        tipo_combo = ttk.Combobox(form_frame, textvariable=self.vars['tipo'], 
                                values=["Equipes", "Seleção"], state="readonly", width=25)
        tipo_combo.grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        tipo_combo.bind("<<ComboboxSelected>>", self._on_tipo_change)
        row += 1
        
        # Continente
        ttk.Label(form_frame, text="Continente:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        continente_combo = ttk.Combobox(form_frame, textvariable=self.vars['continente'], 
                                      values=["América do Sul", "América do Norte", "América Central", "Europa", 
                                             "África", "Ásia", "Oceania"], state="readonly", width=25)
        continente_combo.grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        row += 1
        
        # País
        ttk.Label(form_frame, text="País:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Entry(form_frame, textvariable=self.vars['pais'], width=25).grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        row += 1
        
        # Região (só para brasileiros)
        ttk.Label(form_frame, text="Região:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        self.regiao_combo = ttk.Combobox(form_frame, textvariable=self.vars['regiao'], 
                                       values=["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"], 
                                       state="readonly", width=25)
        self.regiao_combo.grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        row += 1
        
        # Estado (só para brasileiros)
        ttk.Label(form_frame, text="Estado:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        self.estado_combo = ttk.Combobox(form_frame, textvariable=self.vars['estado'], 
                                       values=["Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", 
                                              "Distrito Federal", "Espírito Santo", "Goiás", "Maranhão", 
                                              "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", 
                                              "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", 
                                              "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", 
                                              "Roraima", "Santa Catarina", "São Paulo", "Sergipe", "Tocantins"], 
                                       state="readonly", width=25)
        self.estado_combo.grid(row=row, column=1, sticky="ew", pady=2, padx=(5, 0))
        row += 1
        
        # É uma seleção nacional?
        ttk.Label(form_frame, text="É uma seleção nacional?", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 2))
        row += 1
        
        radio_frame1 = ttk.Frame(form_frame)
        radio_frame1.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Radiobutton(radio_frame1, text="Sim", variable=self.vars['is_national_team'], value=True).pack(side="left")
        ttk.Radiobutton(radio_frame1, text="Não", variable=self.vars['is_national_team'], value=False).pack(side="left", padx=(20, 0))
        row += 1
        
        # É brasileiro?
        ttk.Label(form_frame, text="É brasileiro?", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 2))
        row += 1
        
        radio_frame2 = ttk.Frame(form_frame)
        radio_frame2.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Radiobutton(radio_frame2, text="Sim", variable=self.vars['is_brazilian'], value=True, command=self._on_brasileiro_change).pack(side="left")
        ttk.Radiobutton(radio_frame2, text="Não", variable=self.vars['is_brazilian'], value=False, command=self._on_brasileiro_change).pack(side="left", padx=(20, 0))
        row += 1
        
        # Configurar expansão da coluna do formulário
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Botões de ação
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Button(buttons_frame, text="Inserir Novo", command=self._inserir_novo).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Alterar", command=self._alterar).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Excluir", command=self._excluir).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Salvar", command=self._salvar).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Limpar", command=self._limpar_campos).pack(side="left", padx=5)
        
        # Carrega dados iniciais
        self._load_equipes_data()
        self._populate_tree()
        self._on_brasileiro_change()  # Configura estado inicial dos campos
        
    def _load_equipes_data(self):
        """Carrega dados do arquivo equipes.json"""
        try:
            equipes_file = Path("system") / "equipes.json"
            if equipes_file.exists():
                with open(equipes_file, 'r', encoding='utf-8') as f:
                    self.equipes_data = json.load(f)
            else:
                self.equipes_data = {}
                self.logger.log("Arquivo equipes.json não encontrado", "WARNING", "⚠️")
        except Exception as e:
            self.logger.log(f"Erro ao carregar equipes.json: {str(e)}", "ERROR", "❌")
            self.equipes_data = {}
    
    def _populate_tree(self, filter_text=""):
        """Popula a árvore com dados das equipes"""
        # Limpa árvore atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Popula com dados filtrados
        for categoria, equipes in self.equipes_data.items():
            for nome_equipe, dados in equipes.items():
                # Aplica filtro se especificado
                if filter_text and filter_text.lower() not in nome_equipe.lower():
                    continue
                
                # Insere item na árvore
                self.tree.insert("", "end", text=nome_equipe, values=(
                    categoria,
                    dados.get("tipo", ""),
                    dados.get("continente", ""),
                    dados.get("pais", ""),
                    dados.get("regiao", ""),
                    dados.get("estado", ""),
                    "Sim" if dados.get("is_national_team", False) else "Não",
                    "Sim" if dados.get("is_brazilian", False) else "Não"
                ))
    
    def _on_search_change(self, *args):
        """Evento de mudança na busca"""
        filter_text = self.search_var.get()
        self._populate_tree(filter_text)
    
    def _on_tree_select(self, event):
        """Evento de seleção na árvore"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            self.selected_item = item
            
            # Pega dados do item selecionado
            nome_equipe = self.tree.item(item, "text")
            values = self.tree.item(item, "values")
            
            if values:
                categoria = values[0]
                
                # Preenche campos com dados da equipe selecionada
                if categoria in self.equipes_data and nome_equipe in self.equipes_data[categoria]:
                    dados = self.equipes_data[categoria][nome_equipe]
                    
                    self.vars['categoria_principal'].set(categoria)
                    self.vars['equipe'].set(nome_equipe)
                    self.vars['tipo'].set(dados.get("tipo", ""))
                    self.vars['continente'].set(dados.get("continente", ""))
                    self.vars['pais'].set(dados.get("pais", ""))
                    self.vars['regiao'].set(dados.get("regiao", ""))
                    self.vars['estado'].set(dados.get("estado", ""))
                    self.vars['is_national_team'].set(dados.get("is_national_team", False))
                    self.vars['is_brazilian'].set(dados.get("is_brazilian", False))
                    
                    # Atualiza estado dos campos baseado nas configurações
                    self._on_brasileiro_change()
    
    def _on_categoria_change(self, event=None):
        """Evento de mudança na categoria principal"""
        categoria = self.vars['categoria_principal'].get()
        
        # Configurações automáticas baseadas na categoria
        if categoria == "times_brasileiros":
            self.vars['is_brazilian'].set(True)
            self.vars['pais'].set("Brasil")
            self.vars['continente'].set("América do Sul")
        elif categoria == "selecoes":
            self.vars['is_national_team'].set(True)
            self.vars['tipo'].set("Seleção")
        
        self._on_brasileiro_change()
    
    def _on_tipo_change(self, event=None):
        """Evento de mudança no tipo"""
        tipo = self.vars['tipo'].get()
        if tipo == "Seleção":
            self.vars['is_national_team'].set(True)
        elif tipo == "Equipes":
            self.vars['is_national_team'].set(False)
    
    def _on_brasileiro_change(self):
        """Habilita/desabilita campos baseado se é brasileiro"""
        is_brazilian = self.vars['is_brazilian'].get()
        
        if is_brazilian:
            self.regiao_combo.configure(state="readonly")
            self.estado_combo.configure(state="readonly")
        else:
            self.regiao_combo.configure(state="disabled")
            self.estado_combo.configure(state="disabled")
            self.vars['regiao'].set("")
            self.vars['estado'].set("")
    
    def _inserir_novo(self):
        """Prepara formulário para inserção de nova equipe"""
        self._limpar_campos()
        self.selected_item = None
        self.logger.log("Modo inserção ativado", "INFO", "➕")
    
    def _alterar(self):
        """Prepara formulário para alteração"""
        if not self.selected_item:
            messagebox.showwarning("Atenção", "Selecione uma equipe na tabela para alterar")
            return
        self.logger.log("Modo alteração ativado", "INFO", "✏️")
    
    def _excluir(self):
        """Exclui equipe selecionada"""
        if not self.selected_item:
            messagebox.showwarning("Atenção", "Selecione uma equipe na tabela para excluir")
            return
        
        nome_equipe = self.tree.item(self.selected_item, "text")
        
        if messagebox.askyesno("Confirmação", f"Deseja realmente excluir a equipe '{nome_equipe}'?"):
            # Remove da estrutura de dados
            for categoria, equipes in self.equipes_data.items():
                if nome_equipe in equipes:
                    del equipes[nome_equipe]
                    break
            
            # Atualiza árvore
            self._populate_tree()
            self._limpar_campos()
            self.selected_item = None
            
            self.logger.log(f"Equipe '{nome_equipe}' excluída", "SUCCESS", "🗑️")
    
    def _salvar(self):
        """Salva equipe (nova ou alterada)"""
        # Validações
        if not self.vars['equipe'].get().strip():
            messagebox.showerror("Erro", "Nome da equipe é obrigatório")
            return
        
        if not self.vars['categoria_principal'].get():
            messagebox.showerror("Erro", "Categoria Principal é obrigatória")
            return
        
        nome_equipe = self.vars['equipe'].get().strip().lower()
        categoria = self.vars['categoria_principal'].get()
        
        # Cria estrutura de dados da equipe
        dados_equipe = {
            "tipo": self.vars['tipo'].get(),
            "continente": self.vars['continente'].get(),
            "pais": self.vars['pais'].get(),
            "regiao": self.vars['regiao'].get(),
            "estado": self.vars['estado'].get(),
            "is_national_team": self.vars['is_national_team'].get(),
            "is_brazilian": self.vars['is_brazilian'].get()
        }
        
        # Se é alteração, remove item anterior
        if self.selected_item:
            nome_anterior = self.tree.item(self.selected_item, "text")
            for cat, equipes in self.equipes_data.items():
                if nome_anterior in equipes:
                    del equipes[nome_anterior]
                    break
        
        # Adiciona/atualiza na categoria correta
        if categoria not in self.equipes_data:
            self.equipes_data[categoria] = {}
        
        self.equipes_data[categoria][nome_equipe] = dados_equipe
        
        # Atualiza árvore
        self._populate_tree()
        self._limpar_campos()
        self.selected_item = None
        
        self.logger.log(f"Equipe '{nome_equipe}' salva com sucesso", "SUCCESS", "💾")
    
    def _limpar_campos(self):
        """Limpa todos os campos do formulário"""
        for var in self.vars.values():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            else:
                var.set("")
        
        self.selected_item = None
        self._on_brasileiro_change()  # Redefine estado dos campos
    
    def save_config(self):
        """Salva configurações de times no arquivo equipes.json"""
        try:
            equipes_file = Path("system") / "equipes.json"
            with open(equipes_file, 'w', encoding='utf-8') as f:
                json.dump(self.equipes_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.log(f"Erro ao salvar equipes.json: {str(e)}", "ERROR", "❌")
            return False