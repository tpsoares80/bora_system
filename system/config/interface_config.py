#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações de Interface
Módulo para configurações visuais e de interface
"""

import customtkinter as ctk
from .base_config import BaseConfig

class InterfaceConfig(BaseConfig):
    """Configurações de interface do sistema"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.font_size_var = None
        self.font_size_label = None
        self.preview_log = None
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de configurações de interface"""
        tab = notebook.add("🎨 Interface")
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurações do Log
        log_frame = self.create_frame_with_title(scroll_frame, "Configurações do Log", "📜")
        log_frame.pack(fill="x", pady=10)
        
        self._create_font_controls(log_frame)
        self._create_test_buttons(log_frame)
        self._create_preview(log_frame)
        
        return tab
    
    def _create_font_controls(self, parent):
        """Cria controles de fonte"""
        font_frame = ctk.CTkFrame(parent)
        font_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(font_frame, text="Tamanho da Fonte do Log:").pack(side="left", padx=5)
        
        # Inicializa variável
        current_font_size = self.get_config_value("log_font_size", 12)
        self.font_size_var = ctk.IntVar(value=current_font_size)
        
        # Slider
        font_slider = ctk.CTkSlider(
            font_frame, 
            from_=8, 
            to=20, 
            number_of_steps=12,
            variable=self.font_size_var,
            command=self._on_font_size_change
        )
        font_slider.pack(side="right", padx=10)
        
        # Label do valor
        self.font_size_label = ctk.CTkLabel(font_frame, text=f"{current_font_size}px")
        self.font_size_label.pack(side="right", padx=5)
    
    def _create_test_buttons(self, parent):
        """Cria botões de teste"""
        test_frame = ctk.CTkFrame(parent)
        test_frame.pack(fill="x", padx=10, pady=10)
        
        buttons = [
            ("🔤 Pequena", 10),
            ("🔤 Média", 12), 
            ("🔤 Grande", 16)
        ]
        
        for text, size in buttons:
            ctk.CTkButton(
                test_frame,
                text=text,
                command=lambda s=size: self._test_font(s),
                width=120
            ).pack(side="left", padx=5)
    
    def _create_preview(self, parent):
        """Cria preview do log"""
        preview_frame = ctk.CTkFrame(parent)
        preview_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            preview_frame, 
            text="📋 Preview do Log:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=5)
        
        self.preview_log = ctk.CTkTextbox(preview_frame, height=100, width=400)
        self.preview_log.pack(padx=10, pady=5)
        
        self._update_preview()
    
    def _on_font_size_change(self, value):
        """Callback do slider"""
        font_size = int(value)
        self.font_size_label.configure(text=f"{font_size}px")
        self._update_preview()
    
    def _update_preview(self):
        """Atualiza preview"""
        try:
            font_size = self.font_size_var.get()
            
            # Usa a mesma lógica de fonte do logger principal
            import platform
            system = platform.system()
            
            if system == "Windows":
                font_family = "Segoe UI"
            elif system == "Darwin":  # macOS
                font_family = "SF Mono"
            else:  # Linux
                font_family = "DejaVu Sans Mono"
            
            try:
                self.preview_log.configure(font=ctk.CTkFont(family=font_family, size=font_size))
            except:
                # Fallback para fonte padrão
                self.preview_log.configure(font=ctk.CTkFont(size=font_size))
            
            # Texto de exemplo
            self.preview_log.delete("1.0", "end")
            sample_text = """[12:34:56] 🚀 Sistema BORA iniciado
[12:34:57] ✅ Configurações carregadas
[12:34:58] 📊 Processando URLs...
[12:34:59] ⚠️ Aviso de exemplo
[12:35:00] ❌ Erro simulado"""
            self.preview_log.insert("1.0", sample_text)
        except:
            pass
    
    def _test_font(self, size):
        """Testa tamanho específico"""
        self.font_size_var.set(size)
        self._update_preview()
        
        # Aplica imediatamente se possível
        if self.main_app and hasattr(self.main_app, 'logger'):
            self.set_config_value("log_font_size", size)
            self.main_app.logger.update_font_size()
            self.log_action(f"Fonte alterada para {size}px", "INFO", "🔤")
    
    def save_config(self) -> bool:
        """Salva configurações de interface"""
        try:
            self.set_config_value("log_font_size", self.font_size_var.get())
            
            # Aplica nova fonte se disponível
            if self.main_app and hasattr(self.main_app, 'logger'):
                self.main_app.logger.update_font_size()
            
            return True
        except Exception as e:
            self.log_action(f"Erro ao salvar interface: {str(e)}", "ERROR", "❌")
            return False