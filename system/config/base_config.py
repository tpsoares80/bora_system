#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Base de Configurações
Classe base para módulos de configuração
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import customtkinter as ctk

class BaseConfig:
    """Classe base para módulos de configuração"""
    
    def __init__(self, parent_configurator):
        self.parent = parent_configurator
        self.logger = parent_configurator.logger
        self.config_manager = parent_configurator.config_manager
        self.main_app = parent_configurator.main_app
        
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria a aba no notebook - deve ser implementado pelos módulos"""
        raise NotImplementedError("Módulo deve implementar create_tab()")
    
    def save_config(self) -> bool:
        """Salva configurações específicas do módulo"""
        return True
    
    def load_config(self) -> bool:
        """Carrega configurações específicas do módulo"""
        return True
    
    def get_config_value(self, key: str, default=None):
        """Obtém valor de configuração"""
        return self.config_manager.get(key, default)
    
    def set_config_value(self, key: str, value: Any):
        """Define valor de configuração"""
        keys = key.split('.')
        config = self.config_manager.config
        
        # Navega até o penúltimo nível
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Define o valor final
        config[keys[-1]] = value
    
    def create_frame_with_title(self, parent, title: str, emoji: str = "") -> ctk.CTkFrame:
        """Cria frame com título padronizado"""
        frame = ctk.CTkFrame(parent)
        
        title_text = f"{emoji} {title}" if emoji else title
        ctk.CTkLabel(
            frame, 
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        return frame
    
    def create_entry_row(self, parent, label: str, variable, width: int = 100) -> ctk.CTkFrame:
        """Cria linha com label e entry"""
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(row_frame, text=label).pack(side="left", padx=5)
        entry = ctk.CTkEntry(row_frame, textvariable=variable, width=width)
        entry.pack(side="right", padx=5)
        
        return row_frame
    
    def log_action(self, message: str, level: str = "INFO", emoji: str = "ℹ️"):
        """Log padronizado para ações do módulo"""
        self.logger.log(message, level, emoji)