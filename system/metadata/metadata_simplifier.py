#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Gerador Simplificado de Metadados
Retorna apenas campos essenciais
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class SimpleMetadataGenerator:
    """Gerador simplificado que retorna apenas campos essenciais"""
    
    def __init__(self, logger, config_manager):
        self.logger = logger
        self.config_manager = config_manager
        self.output_dir = Path("Metadados")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_simple_metadata(self, processed_data: Dict[str, Any]) -> str:
        """Gera arquivo JSON simplificado"""
        
        self.logger.log("Gerando metadados simplificados", "INFO", ">")
        
        simplified_products = []
        
        for produto in processed_data['produtos_extraidos']:
            if produto['status'] == 'success' and (produto.get('title') or produto.get('images')):
                
                # Extrai informações básicas
                simplified = {
                    "album_url": produto['url'],
                    "album_id": produto.get('album_id', ''),
                    "album_title": produto.get('title', ''),
                    "album_folder_name": self._generate_folder_name(produto.get('title', '')),
                    "image_count": len(produto.get('images', [])),
                    "image_urls": produto.get('images', [])
                }
                
                simplified_products.append(simplified)
        
        # Estrutura final simplificada
        final_data = {
            "extraction_info": {
                "date": datetime.now().isoformat(),
                "total_products": len(simplified_products),
                "successful_extractions": len(simplified_products)
            },
            "products": simplified_products
        }
        
        # Gera arquivo
        filename = f"metadados_simples_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        self.logger.log(f"Arquivo simplificado gerado: {filename}", "SUCCESS", "OK")
        self.logger.log(f"Produtos válidos: {len(simplified_products)}", "INFO", "#")
        
        return str(filepath)
    
    def _generate_folder_name(self, title: str) -> str:
        """Gera nome de pasta limpo baseado no título"""
        if not title:
            return ""
        
        # Remove caracteres inválidos para nomes de pasta
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        # Remove números no final (como jersey8 -> jersey)
        clean_title = re.sub(r'\d+$', '', clean_title).strip()
        
        # Limita tamanho
        if len(clean_title) > 50:
            clean_title = clean_title[:50].strip()
        
        return clean_title