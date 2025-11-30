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
    'app.py': 'Backend Flask'
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
    print("\n❌ Arquivos faltando! Execute: python setup_files.py")
    sys.exit(1)

print("\n" + "="*60)
print("🚀 Iniciando Trading Bot...")
print("="*60 + "\n")

# Importar e executar o app
try:
    from app import app, socketio
    socketio.run(app, debug=True, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
except Exception as e:
    print(f"\n❌ ERRO ao iniciar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
