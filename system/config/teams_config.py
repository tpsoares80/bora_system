#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações de Equipes
Módulo para visualização da base de dados das equipes
"""

import json
from pathlib import Path
import customtkinter as ctk
from .base_config import BaseConfig

class TeamsConfig(BaseConfig):
    """Configurações e visualização de equipes"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.stats_frame = None
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de visualização das equipes"""
        tab = notebook.add("⚽ Equipes")
        
        # Frame principal
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_frame = self.create_frame_with_title(main_frame, "Base de Dados das Equipes", "📊")
        title_frame.pack(fill="x", pady=10)
        
        # Estatísticas
        self._create_stats_section(main_frame)
        
        # Controles
        self._create_controls(main_frame)
        
        # Informações
        self._create_info_section(main_frame)
        
        return tab
    
    def _create_stats_section(self, parent):
        """Cria seção de estatísticas"""
        self.stats_frame = ctk.CTkFrame(parent)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        self._load_team_stats()
    
    def _create_controls(self, parent):
        """Cria controles de gerenciamento"""
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            controls_frame,
            text="🔄 Recarregar Base",
            command=self._reload_teams,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="📊 Mostrar Detalhes",
            command=self._show_details,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="📂 Abrir Arquivo",
            command=self._open_teams_file,
            width=150
        ).pack(side="right", padx=5)
    
    def _create_info_section(self, parent):
        """Cria seção informativa"""
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="📋 Informações sobre a Base de Equipes",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        info_text = """A base de equipes é carregada do arquivo 'system/equipes.json' e contém:

• Times Brasileiros: Clubes nacionais organizados por estado
• Times Internacionais: Principais clubes mundiais por país
• Seleções: Times nacionais de futebol

Esta base é usada para:
- Categorização automática de produtos
- Sanitização e padronização de nomes
- Identificação de uniformes por equipe

Para editar a base:
1. Clique em 'Abrir Arquivo' para editar o JSON
2. Adicione novos times seguindo a estrutura existente
3. Clique em 'Recarregar Base' para aplicar mudanças"""
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=700
        )
        info_label.pack(padx=20, pady=10)
    
    def _load_team_stats(self):
        """Carrega estatísticas das equipes"""
        # Limpa estatísticas atuais
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        try:
            equipes_file = Path("system") / "equipes.json"
            if not equipes_file.exists():
                self._show_no_file_error()
                return
            
            with open(equipes_file, 'r', encoding='utf-8') as f:
                equipes_data = json.load(f)
            
            # Calcula estatísticas
            times_br = len(equipes_data.get("times_brasileiros", {}))
            times_int = len(equipes_data.get("times_internacionais", {}))
            selecoes = len(equipes_data.get("selecoes", {}))
            total = times_br + times_int + selecoes
            
            # Grid de estatísticas
            stats_grid = ctk.CTkFrame(self.stats_frame)
            stats_grid.pack(fill="x", padx=10, pady=10)
            
            # Cards de estatísticas
            stats = [
                ("🇧🇷 Times Brasileiros", times_br, "blue"),
                ("🌍 Times Internacionais", times_int, "green"),
                ("🏆 Seleções", selecoes, "orange"),
                ("📈 Total Geral", total, "purple")
            ]
            
            for i, (label, value, color) in enumerate(stats):
                card = ctk.CTkFrame(stats_grid)
                card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
                stats_grid.grid_columnconfigure(i, weight=1)
                
                ctk.CTkLabel(
                    card,
                    text=str(value),
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=color
                ).pack(pady=5)
                
                ctk.CTkLabel(
                    card,
                    text=label,
                    font=ctk.CTkFont(size=12)
                ).pack(pady=(0, 10))
            
            # Status
            status_label = ctk.CTkLabel(
                self.stats_frame,
                text=f"✅ Base carregada com sucesso - {total} equipes disponíveis",
                font=ctk.CTkFont(size=12),
                text_color="green"
            )
            status_label.pack(pady=5)
            
        except Exception as e:
            self._show_load_error(str(e))
    
    def _show_no_file_error(self):
        """Mostra erro de arquivo não encontrado"""
        error_label = ctk.CTkLabel(
            self.stats_frame,
            text="❌ Arquivo equipes.json não encontrado",
            font=ctk.CTkFont(size=14),
            text_color="red"
        )
        error_label.pack(pady=20)
        
        self.log_action("Arquivo equipes.json não encontrado", "ERROR", "❌")
    
    def _show_load_error(self, error_msg):
        """Mostra erro de carregamento"""
        error_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"❌ Erro ao carregar equipes:\n{error_msg}",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        error_label.pack(pady=20)
        
        self.log_action(f"Erro ao carregar equipes: {error_msg}", "ERROR", "❌")
    
    def _reload_teams(self):
        """Recarrega a base de equipes"""
        self.log_action("Recarregando base de equipes...", "INFO", "🔄")
        self._load_team_stats()
        self.log_action("Base de equipes recarregada", "SUCCESS", "✅")
    
    def _show_details(self):
        """Mostra detalhes da base de equipes"""
        try:
            equipes_file = Path("system") / "equipes.json"
            if not equipes_file.exists():
                self.log_action("Arquivo não encontrado", "ERROR", "❌")
                return
            
            with open(equipes_file, 'r', encoding='utf-8') as f:
                equipes_data = json.load(f)
            
            # Cria janela de detalhes
            details_window = ctk.CTkToplevel(self.parent.config_window)
            details_window.title("Detalhes da Base de Equipes")
            details_window.geometry("800x600")
            details_window.transient(self.parent.config_window)
            
            # Notebook para categorias
            details_notebook = ctk.CTkTabview(details_window)
            details_notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Aba para cada categoria
            for categoria, equipes in equipes_data.items():
                if isinstance(equipes, dict):
                    self._create_details_tab(details_notebook, categoria, equipes)
            
        except Exception as e:
            self.log_action(f"Erro ao mostrar detalhes: {str(e)}", "ERROR", "❌")
    
    def _create_details_tab(self, notebook, categoria, equipes):
        """Cria aba de detalhes para uma categoria"""
        tab_name = {
            "times_brasileiros": "🇧🇷 Brasileiros",
            "times_internacionais": "🌍 Internacionais", 
            "selecoes": "🏆 Seleções"
        }.get(categoria, categoria)
        
        tab = notebook.add(tab_name)
        
        # Frame scrollável
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Lista as equipes
        for grupo, times in equipes.items():
            if isinstance(times, dict):
                # Cabeçalho do grupo
                header_frame = ctk.CTkFrame(scroll_frame)
                header_frame.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    header_frame,
                    text=f"📍 {grupo.title()} ({len(times)} times)",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).pack(pady=5)
                
                # Lista os times
                for time_id, time_nome in times.items():
                    time_frame = ctk.CTkFrame(scroll_frame)
                    time_frame.pack(fill="x", pady=1, padx=20)
                    
                    ctk.CTkLabel(
                        time_frame,
                        text=f"• {time_nome}",
                        font=ctk.CTkFont(size=11)
                    ).pack(side="left", padx=10, pady=2)
    
    def _open_teams_file(self):
        """Abre o arquivo de equipes no editor padrão"""
        try:
            import platform
            import subprocess
            import os
            
            equipes_file = Path("system") / "equipes.json"
            if not equipes_file.exists():
                self.log_action("Arquivo equipes.json não encontrado", "ERROR", "❌")
                return
            
            # Abre no editor padrão do sistema
            if platform.system() == "Windows":
                os.startfile(str(equipes_file))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(equipes_file)])
            else:  # Linux
                subprocess.run(["xdg-open", str(equipes_file)])
            
            self.log_action("Arquivo equipes.json aberto no editor", "INFO", "📂")
            
        except Exception as e:
            self.log_action(f"Erro ao abrir arquivo: {str(e)}", "ERROR", "❌")
    
    def save_config(self) -> bool:
        """Salva configurações de equipes"""
        # Equipes são gerenciadas via arquivo JSON externo
        return True