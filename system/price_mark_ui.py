# -*- coding: utf-8 -*-
# Módulo: price_mark_ui.py
# Função: UI de preços com campos responsivos e validação automática

import tkinter as tk
from tkinter import ttk, messagebox
import re
from .price_mark import get_all, set_defaults, upsert_keyword, delete_keyword

class PriceMarkUI:
    def __init__(self, parent, logger):
        self.parent = parent
        self.logger = logger
        self.win = None
        self._selected_index = None
        self._rows = []
        self._updating = False  # Flag para evitar loops de atualização

    def open(self):
        if self.win and tk.Toplevel.winfo_exists(self.win):
            self.win.focus_set()
            return
        self.win = tk.Toplevel(self.parent)
        self.win.title("Marcação de Preços")
        self.win.geometry("900x560")
        self.win.transient(self.parent)
        self._build()

    def _build(self):
        data = get_all()
        # Defaults
        frm_top = ttk.LabelFrame(self.win, text="Preço Padrão")
        frm_top.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(frm_top, text="Preço:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(frm_top, text="Promocional:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.ent_preco_padrao = ttk.Entry(frm_top, width=12)
        self.ent_preco_promo = ttk.Entry(frm_top, width=12)
        self.ent_preco_padrao.grid(row=0, column=1, padx=5, pady=5)
        self.ent_preco_promo.grid(row=0, column=3, padx=5, pady=5)
        self.ent_preco_padrao.insert(0, str(data.get("preco_padrao", {}).get("preco", 0.0)))
        self.ent_preco_promo.insert(0, str(data.get("preco_padrao", {}).get("preco_promocional", 0.0)))
        ttk.Button(frm_top, text="Salvar Padrão", command=self._save_defaults).grid(row=0, column=4, padx=8, pady=5)

        # Tabela palavras-chave
        frm_tbl = ttk.LabelFrame(self.win, text="Palavras-chave")
        frm_tbl.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cols = ("identificador", "preco", "promocional", "percentual")
        self.tree = ttk.Treeview(frm_tbl, columns=cols, show="headings", height=10)
        self.tree.heading("identificador", text="Identificador")
        self.tree.heading("preco", text="Preço") 
        self.tree.heading("promocional", text="Promocional")
        self.tree.heading("percentual", text="%")
        
        for c, w in zip(cols, (35, 12, 15, 10)):
            self.tree.column(c, width=w*10, stretch=True)
        
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_row)

        scrollbar = ttk.Scrollbar(frm_tbl, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # carregar linhas
        self._rows = []
        for k, v in (data.get("palavras_chave") or {}).items():
            self._rows.append((k, str(v.get("preco",0.0)), str(v.get("preco_promocional",0.0)), str(v.get("desconto_percentual",0.0))))
        for r in self._rows:
            self.tree.insert("", tk.END, values=r)

        # Editor com campos responsivos
        frm_ed = ttk.LabelFrame(self.win, text="Editar/Adicionar")
        frm_ed.pack(fill=tk.X, padx=10, pady=6)
        
        ttk.Label(frm_ed, text="Identificador:").grid(row=0, column=0, padx=5, pady=4, sticky="e")
        ttk.Label(frm_ed, text="Preço:").grid(row=0, column=2, padx=5, pady=4, sticky="e")
        ttk.Label(frm_ed, text="Preço Promocional:").grid(row=0, column=4, padx=5, pady=4, sticky="e")
        ttk.Label(frm_ed, text="% de Desconto:").grid(row=0, column=6, padx=5, pady=4, sticky="e")

        # Campos com validação responsiva
        self.ent_nome = ttk.Entry(frm_ed, width=24)
        self.ent_preco = ttk.Entry(frm_ed, width=10, state="disabled")
        self.ent_promo = ttk.Entry(frm_ed, width=12, state="disabled")
        self.ent_pct = ttk.Entry(frm_ed, width=12, state="disabled")

        self.ent_nome.grid(row=0, column=1, padx=5, pady=4)
        self.ent_preco.grid(row=0, column=3, padx=5, pady=4)
        self.ent_promo.grid(row=0, column=5, padx=5, pady=4)
        self.ent_pct.grid(row=0, column=7, padx=5, pady=4)

        # Binds para responsividade
        self.ent_nome.bind('<KeyRelease>', self._on_identificador_change)
        self.ent_preco.bind('<KeyRelease>', self._on_preco_change)
        self.ent_promo.bind('<KeyRelease>', self._on_promo_change)
        self.ent_pct.bind('<KeyRelease>', self._on_pct_change)

        btns = ttk.Frame(frm_ed)
        btns.grid(row=1, column=0, columnspan=8, pady=6)
        
        ttk.Button(btns, text="Novo", command=self._clear_fields).pack(side=tk.LEFT, padx=4)
        self.btn_save = ttk.Button(btns, text="Adicionar/Salvar", command=self._save_row, state="disabled")
        self.btn_save.pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Excluir", command=self._delete_row).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Fechar", command=self.win.destroy).pack(side=tk.RIGHT, padx=4)

    def _on_identificador_change(self, event=None):
        """Controla habilitação dos outros campos baseado no identificador"""
        nome = self.ent_nome.get().strip()
        
        if nome:
            # Habilita campo preço
            self.ent_preco.configure(state="normal")
            self.btn_save.configure(state="normal")
        else:
            # Desabilita todos os outros campos
            self.ent_preco.configure(state="disabled")
            self.ent_promo.configure(state="disabled")
            self.ent_pct.configure(state="disabled")
            self.btn_save.configure(state="disabled")
            
            # Limpa campos desabilitados
            self.ent_preco.delete(0, tk.END)
            self.ent_promo.delete(0, tk.END)
            self.ent_pct.delete(0, tk.END)

    def _on_preco_change(self, event=None):
        """Controla habilitação dos campos promocional e percentual baseado no preço"""
        if self._updating:
            return
            
        preco_text = self.ent_preco.get().strip()
        
        if preco_text and self._is_valid_number(preco_text):
            # Habilita campos promocional e percentual
            self.ent_promo.configure(state="normal")
            self.ent_pct.configure(state="normal")
            
            # Recalcula percentual se promocional estiver preenchido
            promo_text = self.ent_promo.get().strip()
            if promo_text and self._is_valid_number(promo_text):
                self._calculate_percentage()
        else:
            # Desabilita campos promocional e percentual
            self.ent_promo.configure(state="disabled")
            self.ent_pct.configure(state="disabled")
            
            # Limpa campos desabilitados
            self.ent_promo.delete(0, tk.END)
            self.ent_pct.delete(0, tk.END)

    def _on_promo_change(self, event=None):
        """Calcula percentual automaticamente quando promocional muda"""
        if self._updating:
            return
        self._calculate_percentage()

    def _on_pct_change(self, event=None):
        """Calcula promocional automaticamente quando percentual muda"""
        if self._updating:
            return
        self._calculate_promotional()

    def _calculate_percentage(self):
        """Calcula e atualiza o campo de percentual"""
        try:
            self._updating = True
            
            preco_text = self.ent_preco.get().strip()
            promo_text = self.ent_promo.get().strip()
            
            if not (preco_text and promo_text and 
                    self._is_valid_number(preco_text) and 
                    self._is_valid_number(promo_text)):
                return
            
            preco = float(preco_text.replace(',', '.'))
            promo = float(promo_text.replace(',', '.'))
            
            if preco > 0:
                percentual = ((preco - promo) / preco) * 100
                if percentual >= 0:
                    self.ent_pct.delete(0, tk.END)
                    self.ent_pct.insert(0, f"{percentual:.2f}")
                    
        except (ValueError, ZeroDivisionError):
            pass
        finally:
            self._updating = False

    def _calculate_promotional(self):
        """Calcula e atualiza o campo promocional"""
        try:
            self._updating = True
            
            preco_text = self.ent_preco.get().strip()
            pct_text = self.ent_pct.get().strip().replace('%', '')
            
            if not (preco_text and pct_text and 
                    self._is_valid_number(preco_text) and 
                    self._is_valid_number(pct_text)):
                return
            
            preco = float(preco_text.replace(',', '.'))
            percentual = float(pct_text.replace(',', '.'))
            
            if 0 <= percentual < 100:
                promocional = preco * (1 - percentual/100)
                self.ent_promo.delete(0, tk.END)
                self.ent_promo.insert(0, f"{promocional:.2f}")
                
        except (ValueError, ZeroDivisionError):
            pass
        finally:
            self._updating = False

    def _is_valid_number(self, text):
        """Valida se o texto é um número válido"""
        if not text:
            return False
        # Aceita números com vírgula ou ponto como separador decimal
        pattern = r'^\d+([.,]\d+)?$'
        return bool(re.match(pattern, text))

    def _format_percentage_display(self):
        """Formata campo de percentual com símbolo %"""
        pct_text = self.ent_pct.get().strip()
        if pct_text and not pct_text.endswith('%'):
            # Remove % se existe e reaplica formatação
            clean_text = pct_text.replace('%', '')
            if self._is_valid_number(clean_text):
                # Não adiciona % fisicamente no campo, apenas visual
                pass

    def _clear_fields(self):
        """Limpa os campos para nova entrada"""
        self.ent_nome.delete(0, tk.END)
        self.ent_preco.delete(0, tk.END)
        self.ent_promo.delete(0, tk.END)
        self.ent_pct.delete(0, tk.END)
        
        # Reseta estados dos campos
        self.ent_preco.configure(state="disabled")
        self.ent_promo.configure(state="disabled")
        self.ent_pct.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        
        self.ent_nome.focus()

    def _save_defaults(self):
        try:
            set_defaults(self.ent_preco_padrao.get(), self.ent_preco_promo.get())
            self.logger.log("Preço padrão salvo", "SUCCESS", "💾")
        except Exception as e:
            self.logger.log(f"Erro ao salvar padrão: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", str(e))

    def _on_select_row(self, event):
        """Carrega dados da linha selecionada nos campos"""
        sel = self.tree.selection()
        if not sel: 
            return
        item = self.tree.item(sel[0])["values"]
        if not item: 
            return
        
        nome, preco, promo, pct = item
        
        # Limpa e preenche campos
        self.ent_nome.delete(0, tk.END)
        self.ent_nome.insert(0, nome)
        
        # Trigger da validação do identificador
        self._on_identificador_change()
        
        # Preenche outros campos se habilitados
        if self.ent_preco['state'] == 'normal':
            self.ent_preco.delete(0, tk.END)
            self.ent_preco.insert(0, preco)
            self._on_preco_change()
            
        if self.ent_promo['state'] == 'normal':
            self.ent_promo.delete(0, tk.END)
            self.ent_promo.insert(0, promo)
            
        if self.ent_pct['state'] == 'normal':
            self.ent_pct.delete(0, tk.END)
            self.ent_pct.insert(0, pct)

    def _save_row(self):
        nome = self.ent_nome.get().strip()
        preco = self.ent_preco.get().strip()
        promo = self.ent_promo.get().strip()
        pct = self.ent_pct.get().strip().replace('%', '')
        
        if not nome:
            messagebox.showwarning("Aviso", "Informe o Identificador.")
            return
        if not preco:
            messagebox.showwarning("Aviso", "Informe o Preço (obrigatório).")
            return
        
        # vírgula -> ponto
        preco = preco.replace(',', '.') if preco else ''
        promo = promo.replace(',', '.') if promo else ''
        pct = pct.replace(',', '.') if pct else ''
        
        try:
            upsert_keyword(nome, preco, promo, pct)
            # atualizar linha na tabela
            found = None
            for iid in self.tree.get_children():
                vals = self.tree.item(iid)["values"]
                if vals and vals[0] == nome:
                    found = iid
                    break
            
            display = (nome, str(preco), str(promo or '0.0'), str(pct or '0.0'))
            if found:
                self.tree.item(found, values=display)
            else:
                self.tree.insert("", tk.END, values=display)
            
            self.logger.log("Entrada salva", "SUCCESS", "💾")
        except Exception as e:
            self.logger.log(f"Erro ao salvar entrada: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", str(e))

    def _delete_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma linha para excluir.")
            return
        item = self.tree.item(sel[0])["values"]
        nome = item[0] if item else ""
        if not nome:
            return
        if not messagebox.askyesno("Confirmar", f"Excluir '{nome}'?"):
            return
        try:
            delete_keyword(nome)
            self.tree.delete(sel[0])
            self.logger.log(f"'{nome}' excluído", "SUCCESS", "🗑️")
        except Exception as e:
            self.logger.log(f"Erro ao excluir: {e}", "ERROR", "❌")
            messagebox.showerror("Erro", str(e))