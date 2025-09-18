#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Configurações de APIs
Módulo para gerenciamento de chaves de API
"""

import base64
import customtkinter as ctk
from .base_config import BaseConfig

class APIsConfig(BaseConfig):
    """Configurações de APIs de IA"""
    
    def __init__(self, parent_configurator):
        super().__init__(parent_configurator)
        self.apis_listbox = None
    
    def create_tab(self, notebook: ctk.CTkTabview) -> ctk.CTkFrame:
        """Cria aba de configurações de APIs"""
        tab = notebook.add("🤖 APIs IA")
        
        # Frame principal
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_frame = self.create_frame_with_title(main_frame, "Gerenciamento de Chaves de API", "🔑")
        title_frame.pack(fill="x", pady=10)
        
        # Controles
        self._create_controls(main_frame)
        
        # Lista de APIs
        self._create_api_list(main_frame)
        
        # Carregar APIs existentes
        self._load_apis()
        
        return tab
    
    def _create_controls(self, parent):
        """Cria controles de gerenciamento"""
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            controls_frame,
            text="➕ Adicionar API",
            command=self._adicionar_api,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="🗑️ Remover Selecionada",
            command=self._remover_api,
            width=150,
            fg_color="red"
        ).pack(side="left", padx=5)
        
        # Info sobre limite
        info_label = ctk.CTkLabel(
            controls_frame,
            text="Máximo: 15 APIs",
            font=ctk.CTkFont(size=11)
        )
        info_label.pack(side="right", padx=10)
    
    def _create_api_list(self, parent):
        """Cria lista scrollável de APIs"""
        self.apis_listbox = ctk.CTkScrollableFrame(parent)
        self.apis_listbox.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _load_apis(self):
        """Carrega APIs cadastradas"""
        # Limpa lista atual
        for widget in self.apis_listbox.winfo_children():
            widget.destroy()
        
        apis = self.get_config_value("ia_apis", [])
        
        if not apis:
            ctk.CTkLabel(
                self.apis_listbox,
                text="Nenhuma API cadastrada\n\nClique em 'Adicionar API' para começar",
                font=ctk.CTkFont(size=12),
                justify="center"
            ).pack(pady=20)
            return
        
        # Exibe cada API
        for i, api_encrypted in enumerate(apis):
            try:
                api_key = self._decrypt_api(api_encrypted)
                display_key = self._format_api_display(api_key)
                
                frame = ctk.CTkFrame(self.apis_listbox)
                frame.pack(fill="x", pady=2)
                
                # Checkbox para seleção
                var = ctk.BooleanVar()
                checkbox = ctk.CTkCheckBox(frame, text="", variable=var, width=20)
                checkbox.pack(side="left", padx=5)
                
                # Info da API
                api_label = ctk.CTkLabel(frame, text=f"API {i+1}: {display_key}")
                api_label.pack(side="left", padx=10)
                
                # Status
                status_label = ctk.CTkLabel(
                    frame, 
                    text="✅ Ativa", 
                    font=ctk.CTkFont(size=10),
                    text_color="green"
                )
                status_label.pack(side="right", padx=5)
                
                # Armazena referências
                checkbox.api_var = var
                checkbox.api_index = i
                
            except Exception as e:
                self.log_action(f"Erro ao carregar API {i+1}: {str(e)}", "ERROR", "❌")
    
    def _format_api_display(self, api_key: str) -> str:
        """Formata chave para exibição"""
        if len(api_key) > 10:
            return f"{api_key[:5]}...{api_key[-5:]}"
        return api_key
    
    def _encrypt_api(self, api_key: str) -> str:
        """Criptografia simples da API"""
        try:
            encrypted = base64.b64encode(api_key.encode('utf-8')).decode('utf-8')
            return encrypted
        except Exception:
            return api_key
    
    def _decrypt_api(self, encrypted_key: str) -> str:
        """Descriptografia simples da API"""
        try:
            decrypted = base64.b64decode(encrypted_key.encode('utf-8')).decode('utf-8')
            return decrypted
        except Exception:
            return encrypted_key
    
    def _adicionar_api(self):
        """Adiciona nova chave de API"""
        # Verifica limite
        apis = self.get_config_value("ia_apis", [])
        if len(apis) >= 15:
            self.log_action("Limite de 15 APIs atingido", "ERROR", "❌")
            return
        
        # Cria dialog
        dialog = ctk.CTkToplevel(self.parent.config_window)
        dialog.title("Adicionar API Key")
        dialog.geometry("450x250")
        dialog.transient(self.parent.config_window)
        dialog.grab_set()
        
        # Centraliza
        dialog.geometry("+%d+%d" % (
            self.parent.config_window.winfo_rootx() + 50,
            self.parent.config_window.winfo_rooty() + 50
        ))
        
        # Interface
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame, 
            text="🔑 Adicionar Nova API Key",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text="Digite a chave da API:",
            font=ctk.CTkFont(size=12)
        ).pack(pady=5)
        
        api_entry = ctk.CTkEntry(main_frame, width=350, show="*", placeholder_text="sk-...")
        api_entry.pack(pady=10)
        api_entry.focus()
        
        # Info sobre segurança
        info_label = ctk.CTkLabel(
            main_frame,
            text="🔒 A chave será criptografada antes de ser salva",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        info_label.pack(pady=5)
        
        def save_api():
            api_key = api_entry.get().strip()
            if not api_key:
                return
            
            # Validação básica
            if len(api_key) < 10:
                self.log_action("Chave muito curta", "WARNING", "⚠️")
                return
            
            # Criptografa e adiciona
            encrypted_key = self._encrypt_api(api_key)
            apis = self.get_config_value("ia_apis", [])
            apis.append(encrypted_key)
            self.set_config_value("ia_apis", apis)
            
            self.log_action("API adicionada com sucesso", "SUCCESS", "✅")
            dialog.destroy()
            self._load_apis()
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame, 
            text="💾 Salvar", 
            command=save_api,
            width=100
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="❌ Cancelar", 
            command=dialog.destroy,
            width=100,
            fg_color="gray30"
        ).pack(side="left", padx=10)
        
        # Enter para salvar
        api_entry.bind("<Return>", lambda e: save_api())
    
    def _remover_api(self):
        """Remove APIs selecionadas"""
        apis = self.get_config_value("ia_apis", [])
        indices_to_remove = []
        
        # Encontra APIs selecionadas
        for widget in self.apis_listbox.winfo_children():
            for child in widget.winfo_children():
                if hasattr(child, 'api_var') and child.api_var.get():
                    indices_to_remove.append(child.api_index)
        
        if not indices_to_remove:
            self.log_action("Nenhuma API selecionada", "WARNING", "⚠️")
            return
        
        # Remove em ordem reversa
        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(apis):
                apis.pop(index)
        
        self.set_config_value("ia_apis", apis)
        self.log_action(f"{len(indices_to_remove)} API(s) removida(s)", "INFO", "🗑️")
        self._load_apis()
    
    def save_config(self) -> bool:
        """Salva configurações de APIs"""
        # APIs são salvas em tempo real, nada a fazer aqui
        return True