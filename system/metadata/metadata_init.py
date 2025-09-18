#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema BORA - Módulo de Metadados
Pipeline completo para coleta e processamento de metadados
"""

from .url_analyzer import URLAnalyzer
from .data_processor import DataProcessor
from .metadata_generator import MetadataGenerator

__all__ = [
    'URLAnalyzer',
    'DataProcessor', 
    'MetadataGenerator'
]