#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações de Tamanhos
Módulo para tamanhos adulto e infantil
"""

import customtkinter as ctk
from .base_config import BaseConfig

class SizesConfig(BaseConfig):
    """Configurações de tamanhos de produtos"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.tamanhos_adulto = []
        self.tamanhos_infantil = {}
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de configurações de tamanhos"""
        tab = notebook.add("👕 Tamanhos")
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Seção adulto
        self._create_adult_section(scroll_frame)
        
        # Seção infantil
        self._create_child_section(scroll_frame)
        
        return tab
    
    def _create_adult_section(self, parent):
        """Cria seção de tamanhos adulto"""
        adulto_frame = self.create_frame_with_title(parent, "Tamanhos Adulto", "👨")
        adulto_frame.pack(fill="x", pady=10)
        
        # Lista atual de tamanhos
        tamanhos_atuais = self.get_config_value("tamanhos_adulto", ["P", "M", "G", "XG", "XXG", "XXXG"])
        
        # Cria entradas para cada tamanho
        self.tamanhos_adulto = []
        for i, tamanho in enumerate(tamanhos_atuais):
            frame = ctk.CTkFrame(adulto_frame)
            frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(frame, text=f"Tamanho {i+1}:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame, width=100)
            entry.insert(0, tamanho)
            entry.pack(side="right", padx=5)
            self.tamanhos_adulto.append(entry)
        
        # Botões de gerenciamento
        btn_frame = ctk.CTkFrame(adulto_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Adicionar",
            command=self._add_adult_size,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Resetar",
            command=self._reset_adult_sizes,
            width=100
        ).pack(side="left", padx=5)
    
    def _create_child_section(self, parent):
        """Cria seção de tamanhos infantil"""
        infantil_frame = self.create_frame_with_title(parent, "Tamanhos Infantil", "👶")
        infantil_frame.pack(fill="x", pady=10)
        
        # Tamanhos infantis atuais
        tamanhos_inf_atuais = self.get_config_value("tamanhos_infantil", {
            "16": "2 a 3 anos",
            "18": "3 a 4 anos", 
            "20": "4 a 5 anos",
            "22": "6 a 7 anos",
            "24": "8 a 9 anos",
            "26": "10 a 11 anos",
            "28": "12 a 13 anos"
        })
        
        self.tamanhos_infantil = {}
        for numero, idade in tamanhos_inf_atuais.items():
            frame = ctk.CTkFrame(infantil_frame)
            frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(frame, text=f"Tamanho {numero}:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame, width=200)
            entry.insert(0, idade)
            entry.pack(side="right", padx=5)
            self.tamanhos_infantil[numero] = entry
        
        # Info sobre tamanhos infantis
        info_frame = ctk.CTkFrame(infantil_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """Tamanhos infantis seguem padrão brasileiro:
16-28 = Números do tamanho
Descrição = Faixa etária aproximada"""
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(padx=10, pady=5)
    
    def _add_adult_size(self):
        """Adiciona novo tamanho adulto"""
        if len(self.tamanhos_adulto) >= 10:
            self.log_action("Máximo de 10 tamanhos atingido", "WARNING", "⚠️")
            return
        
        # Encontra o frame pai
        parent_frame = self.tamanhos_adulto[0].master.master if self.tamanhos_adulto else None
        if not parent_frame:
            return
        
        # Cria nova entrada
        frame = ctk.CTkFrame(parent_frame)
        frame.pack(fill="x", padx=10, pady=2, before=parent_frame.winfo_children()[-1])
        
        index = len(self.tamanhos_adulto) + 1
        ctk.CTkLabel(frame, text=f"Tamanho {index}:").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, width=100)
        entry.pack(side="right", padx=5)
        
        self.tamanhos_adulto.append(entry)
        self.log_action(f"Novo campo de tamanho adicionado", "INFO", "➕")
    
    def _reset_adult_sizes(self):
        """Reseta tamanhos adulto para padrão"""
        default_sizes = ["P", "M", "G", "XG", "XXG", "XXXG"]
        
        # Limita ao número de campos disponíveis
        for i, entry in enumerate(self.tamanhos_adulto):
            if i < len(default_sizes):
                entry.delete(0, "end")
                entry.insert(0, default_sizes[i])
            else:
                entry.delete(0, "end")
        
        self.log_action("Tamanhos adulto resetados para padrão", "INFO", "🔄")
    
    def save_config(self) -> bool:
        """Salva configurações de tamanhos"""
        try:
            # Salva tamanhos adulto
            tamanhos_adulto = []
            for entry in self.tamanhos_adulto:
                tamanho = entry.get().strip().upper()
                if tamanho:
                    tamanhos_adulto.append(tamanho)
            self.set_config_value("tamanhos_adulto", tamanhos_adulto)
            
            # Salva tamanhos infantil
            tamanhos_infantil = {}
            for numero, entry in self.tamanhos_infantil.items():
                idade = entry.get().strip()
                if idade:
                    tamanhos_infantil[numero] = idade
            self.set_config_value("tamanhos_infantil", tamanhos_infantil)
            
            return True
        except Exception as e:
            self.log_action(f"Erro ao salvar tamanhos: {str(e)}", "ERROR", "❌")
            return False