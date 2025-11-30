#!/usr/bin/env python3
"""
Script de inicialização do Trading Bot
"""
import os
import sys
import shutil

# Limpar cache
cache_dir = '__pycache__'
if os.path.exists(cache_dir):
    print(f"🧹 Limpando cache...")
    shutil.rmtree(cache_dir)
    print(f"✅ Cache limpo")

# Verificar estrutura
print("\n🔍 Verificando estrutura de arquivos...")
required_files = {
    'templates/index.html': 'Template HTML',
    'static/style.css': 'CSS',
    'static/script.js': 'JavaScript',
    'app.py': 'Backend Flask',
    'data_provider.py': 'Data Provider',
    'analyzer.py': 'Analyzer',
    'trader.py': 'Trader'
}

all_ok = True
for file_path, description in required_files.items():
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"  ✅ {description}: {file_path} ({size} bytes)")
    else:
        print(f"  ❌ {description}: {file_path} NÃO ENCONTRADO")
        all_ok = False

if not all_ok:
    print("\n❌ Arquivos faltando!")
    print("Certifique-se de ter todos os arquivos na pasta do projeto.")
    sys.exit(1)

print("\n" + "="*60)
print("🚀 Iniciando Trading Bot...")
print("="*60 + "\n")

# Executar app.py diretamente
os.system('python app.py')
