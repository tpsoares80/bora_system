#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações de Categorias
Módulo para identificadores de URL de categoria
"""

import customtkinter as ctk
from .base_config import BaseConfig

class CategoriesConfig(BaseConfig):
    """Configurações de identificadores de categoria"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.novo_identificador_entry = None
        self.identificadores_frame = None
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de configurações de categorias"""
        tab = notebook.add("📁 Categorias")
        
        # Frame principal
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título e descrição
        title_frame = self.create_frame_with_title(main_frame, "Identificadores de URL de Categoria", "📁")
        title_frame.pack(fill="x", pady=10)
        
        desc_label = ctk.CTkLabel(
            main_frame, 
            text="Palavras que identificam URLs como páginas de categoria/coleção.\nUsadas para detectar se uma URL aponta para lista de produtos ou produto individual.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        desc_label.pack(pady=5)
        
        # Controles de adição
        self._create_add_controls(main_frame)
        
        # Lista de identificadores
        self._create_identifier_list(main_frame)
        
        # Carregar identificadores
        self._load_identifiers()
        
        return tab
    
    def _create_add_controls(self, parent):
        """Cria controles para adicionar identificadores"""
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(controls_frame, text="Novo identificador:").pack(side="left", padx=5)
        
        self.novo_identificador_entry = ctk.CTkEntry(
            controls_frame, 
            width=200,
            placeholder_text="Ex: search, collection, gallery..."
        )
        self.novo_identificador_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="➕ Adicionar",
            command=self._add_identifier,
            width=100
        ).pack(side="left", padx=5)
        
        # Enter para adicionar
        self.novo_identificador_entry.bind("<Return>", lambda e: self._add_identifier())
        
        # Botão para restaurar padrões
        ctk.CTkButton(
            controls_frame,
            text="🔄 Restaurar Padrões",
            command=self._restore_defaults,
            width=130,
            fg_color="orange"
        ).pack(side="right", padx=5)
    
    def _create_identifier_list(self, parent):
        """Cria lista scrollável de identificadores"""
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            list_frame,
            text="📋 Identificadores Ativos:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.identificadores_frame = ctk.CTkScrollableFrame(list_frame)
        self.identificadores_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _load_identifiers(self):
        """Carrega identificadores existentes"""
        # Limpa lista
        for widget in self.identificadores_frame.winfo_children():
            widget.destroy()
        
        identificadores = self.get_config_value("identificadores_categoria", [])
        
        if not identificadores:
            ctk.CTkLabel(
                self.identificadores_frame,
                text="Nenhum identificador cadastrado\n\nAdicione palavras que aparecem em URLs de categoria",
                font=ctk.CTkFont(size=12),
                justify="center"
            ).pack(pady=20)
            return
        
        # Exibe cada identificador
        for i, identificador in enumerate(identificadores):
            frame = ctk.CTkFrame(self.identificadores_frame)
            frame.pack(fill="x", pady=2)
            
            # Número e texto
            ctk.CTkLabel(
                frame, 
                text=f"{i+1:2d}. {identificador}",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10, pady=5)
            
            # Botão remover
            ctk.CTkButton(
                frame,
                text="🗑️",
                command=lambda id=identificador: self._remove_identifier(id),
                width=30,
                height=25,
                fg_color="red"
            ).pack(side="right", padx=5)
            
            # Info sobre uso
            if identificador in ["search", "collection", "categories", "gallery"]:
                status_label = ctk.CTkLabel(
                    frame,
                    text="📌 Padrão",
                    font=ctk.CTkFont(size=10),
                    text_color="blue"
                )
                status_label.pack(side="right", padx=5)
    
    def _add_identifier(self):
        """Adiciona novo identificador"""
        identificador = self.novo_identificador_entry.get().strip().lower()
        if not identificador:
            return
        
        # Validações
        if len(identificador) < 2:
            self.log_action("Identificador muito curto (mín. 2 caracteres)", "WARNING", "⚠️")
            return
        
        identificadores = self.get_config_value("identificadores_categoria", [])
        
        if identificador in identificadores:
            self.log_action(f"Identificador '{identificador}' já existe", "WARNING", "⚠️")
            return
        
        # Adiciona
        identificadores.append(identificador)
        self.set_config_value("identificadores_categoria", identificadores)
        self.novo_identificador_entry.delete(0, "end")
        
        self.log_action(f"Identificador '{identificador}' adicionado", "SUCCESS", "➕")
        self._load_identifiers()
    
    def _remove_identifier(self, identificador: str):
        """Remove identificador"""
        identificadores = self.get_config_value("identificadores_categoria", [])
        
        if identificador in identificadores:
            identificadores.remove(identificador)
            self.set_config_value("identificadores_categoria", identificadores)
            self.log_action(f"Identificador '{identificador}' removido", "INFO", "🗑️")
            self._load_identifiers()
    
    def _restore_defaults(self):
        """Restaura identificadores padrão"""
        default_identifiers = ["search", "collection", "categories", "gallery", "shop", "products"]
        self.set_config_value("identificadores_categoria", default_identifiers)
        self.log_action("Identificadores restaurados para padrão", "INFO", "🔄")
        self._load_identifiers()
    
    def save_config(self) -> bool:
        """Salva configurações de categorias"""
        # Identificadores são salvos em tempo real
        return True