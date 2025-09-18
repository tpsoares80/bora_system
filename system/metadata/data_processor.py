#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Data Processor de Metadados
Processador específico do pipeline de metadados
"""

import time
from typing import List, Dict, Any
from datetime import datetime

class DataProcessor:
    """Processador de metadados do pipeline"""
    
    def __init__(self, logger, config_manager):
        self.logger = logger
        self.config_manager = config_manager
    
    def process_product_urls(self, product_urls: List[str]) -> Dict[str, Any]:
        """Processa URLs de produtos e extrai metadados"""
        self.logger.log(f"Iniciando processamento de {len(product_urls)} produtos", "INFO", "⚙️")
        
        tempo_inicio = datetime.now()
        produtos_extraidos = []
        sucessos = 0
        falhas = 0
        
        try:
            # Importa scraper engine
            import sys
            sys.path.append('system')
            from system.scraper_engine import ScraperEngine
            
            scraper = ScraperEngine(self.logger, self.config_manager)
            
            for i, url in enumerate(product_urls):
                try:
                    self.logger.log(f"Processando produto {i+1}/{len(product_urls)}", "INFO", "📦")
                    
                    # Extrai metadados
                    metadata = scraper.extract_product_metadata(url)
                    
                    if metadata.get('status') == 'success':
                        produtos_extraidos.append(metadata)
                        sucessos += 1
                    else:
                        falhas += 1
                        
                except Exception as e:
                    falhas += 1
                    self.logger.log(f"Erro no produto {url}: {str(e)}", "ERROR", "❌")
            
            # Fecha scrapers
            scraper.close_specialized_scrapers()
            
        except Exception as e:
            self.logger.log(f"Erro crítico no processamento: {str(e)}", "ERROR", "❌")
        
        tempo_fim = datetime.now()
        tempo_total = (tempo_fim - tempo_inicio).total_seconds()
        
        # Estatísticas
        estatisticas = {
            'total_urls': len(product_urls),
            'sucessos': sucessos,
            'falhas': falhas,
            'produtos_validos': len(produtos_extraidos),
            'produtos_invalidos': sucessos - len(produtos_extraidos),
            'tempo_inicio': tempo_inicio.isoformat(),
            'tempo_fim': tempo_fim.isoformat(),
            'tempo_total': tempo_total
        }
        
        return {
            'produtos_extraidos': produtos_extraidos,
            'urls_processadas': product_urls,
            'estatisticas': estatisticas
        }