#!/usr/bin/env python3
"""
Script de teste para verificar se tudo está configurado corretamente
"""
import os
import sys

def test_structure():
    """Verifica estrutura de pastas"""
    print("🔍 Verificando estrutura de pastas...")
    
    required_dirs = ['templates', 'static', 'data']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ Pasta '{dir_name}' encontrada")
        else:
            print(f"  ❌ Pasta '{dir_name}' NÃO encontrada - Criando...")
            os.makedirs(dir_name, exist_ok=True)
    
    required_files = {
        'templates/index.html': 'template HTML',
        'static/style.css': 'arquivo CSS',
        'static/script.js': 'arquivo JavaScript'
    }
    
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"  ✅ {description} encontrado")
        else:
            print(f"  ❌ {description} NÃO encontrado em {file_path}")
    
    print()

def test_imports():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências Python...")
    
    dependencies = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('socketio', 'python-socketio')
    ]
    
    all_ok = True
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} instalado")
        except ImportError:
            print(f"  ❌ {display_name} NÃO instalado")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Instale as dependências com: pip install -r requirements.txt")
    
    print()

def test_app():
    """Testa se o app.py pode ser importado"""
    print("🔍 Verificando app.py...")
    
    try:
        from app import app, socketio
        print("  ✅ app.py carregado com sucesso")
        print(f"  ✅ Flask app criado: {app.name}")
        print(f"  ✅ SocketIO configurado")
    except Exception as e:
        print(f"  ❌ Erro ao carregar app.py: {e}")
        return False
    
    print()
    return True

def main():
    print("\n" + "="*60)
    print("🤖 TESTE DE CONFIGURAÇÃO - TRADING BOT")
    print("="*60 + "\n")
    
    test_structure()
    test_imports()
    
    if test_app():
        print("="*60)
        print("✅ Tudo configurado corretamente!")
        print("🚀 Execute: python app.py")
        print("📊 Depois acesse: http://localhost:5000")
        print("="*60 + "\n")
        return True
    else:
        print("="*60)
        print("❌ Há problemas na configuração")
        print("="*60 + "\n")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
