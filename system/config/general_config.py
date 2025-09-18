#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações Gerais
Módulo para delays, imagens e configurações básicas
"""

import customtkinter as ctk
from .base_config import BaseConfig

class GeneralConfig(BaseConfig):
    """Configurações gerais do sistema"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.delay_padrao_var = None
        self.delay_erro_var = None
        self.tamanho_img_var = None
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de configurações gerais"""
        tab = notebook.add("⚙️ Geral")
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Seção de Delays
        self._create_delay_section(scroll_frame)
        
        # Seção de Imagens
        self._create_image_section(scroll_frame)
        
        return tab
    
    def _create_delay_section(self, parent):
        """Cria seção de configurações de tempo"""
        delay_frame = self.create_frame_with_title(parent, "Configurações de Tempo", "⏱️")
        delay_frame.pack(fill="x", pady=5)
        
        # Delay padrão
        self.delay_padrao_var = ctk.DoubleVar(value=self.get_config_value("delay_padrao", 2.0))
        self.create_entry_row(delay_frame, "Delay Padrão (segundos):", self.delay_padrao_var)
        
        # Delay após erro
        self.delay_erro_var = ctk.DoubleVar(value=self.get_config_value("delay_apos_erro", 5.0))
        self.create_entry_row(delay_frame, "Delay Após Erro (segundos):", self.delay_erro_var)
        
        # Descrições
        desc_frame = ctk.CTkFrame(delay_frame)
        desc_frame.pack(fill="x", padx=10, pady=5)
        
        desc_text = """Delays controlam a velocidade do scraping:
• Delay Padrão: Tempo entre requisições normais
• Delay Após Erro: Tempo extra após falhas de conexão"""
        
        ctk.CTkLabel(
            desc_frame,
            text=desc_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(padx=10, pady=5)
    
    def _create_image_section(self, parent):
        """Cria seção de configurações de imagem"""
        img_frame = self.create_frame_with_title(parent, "Configurações de Imagem", "🖼️")
        img_frame.pack(fill="x", pady=15)
        
        # Tamanho mínimo
        self.tamanho_img_var = ctk.IntVar(value=self.get_config_value("tamanho_minimo_imagem", 1024))
        self.create_entry_row(img_frame, "Tamanho Mínimo (pixels):", self.tamanho_img_var)
        
        # Informações adicionais
        info_frame = ctk.CTkFrame(img_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """Configuração de qualidade de imagem:
• Tamanho Mínimo: Imagens menores são ignoradas
• Recomendado: 1024px para boa qualidade"""
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(padx=10, pady=5)
        
        # Botões de preset
        preset_frame = ctk.CTkFrame(img_frame)
        preset_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(preset_frame, text="Presets Rápidos:").pack(side="left", padx=5)
        
        presets = [
            ("Baixa (512px)", 512),
            ("Média (1024px)", 1024),
            ("Alta (2048px)", 2048)
        ]
        
        for text, size in presets:
            ctk.CTkButton(
                preset_frame,
                text=text,
                command=lambda s=size: self._set_image_preset(s),
                width=100
            ).pack(side="right", padx=2)
    
    def _set_image_preset(self, size):
        """Define preset de tamanho de imagem"""
        self.tamanho_img_var.set(size)
        self.log_action(f"Preset de imagem definido: {size}px", "INFO", "🖼️")
    
    def save_config(self) -> bool:
        """Salva configurações gerais"""
        try:
            self.set_config_value("delay_padrao", self.delay_padrao_var.get())
            self.set_config_value("delay_apos_erro", self.delay_erro_var.get())
            self.set_config_value("tamanho_minimo_imagem", self.tamanho_img_var.get())
            return True
        except Exception as e:
            self.log_action(f"Erro ao salvar configurações gerais: {str(e)}", "ERROR", "❌")
            return False