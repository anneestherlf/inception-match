#!/usr/bin/env python3
"""
Script de inicialização do Dashboard Inception-match
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    try:
        import flask
        import gspread
        print("✅ Dependências principais encontradas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install -r requirements.txt")
        return False

def check_credentials():
    """Verifica se o arquivo de credenciais existe"""
    if not Path("credentials.json").exists():
        print("❌ Arquivo credentials.json não encontrado")
        print("Configure as credenciais do Google Sheets API")
        return False
    print("✅ Arquivo credentials.json encontrado")
    return True

def check_sheets_connection():
    """Testa a conexão com o Google Sheets"""
    try:
        import gspread
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open("Base de Startups NVIDIA")
        worksheet = spreadsheet.sheet1
        print("✅ Conexão com Google Sheets estabelecida")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com Google Sheets: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando Dashboard Inception-match...")
    print("=" * 50)
    
    # Verificações
    if not check_requirements():
        sys.exit(1)
    
    if not check_credentials():
        sys.exit(1)
    
    if not check_sheets_connection():
        print("⚠️  Continuando sem conexão com Sheets (modo demo)")
    
    print("=" * 50)
    print("🌐 Iniciando servidor web...")
    print("📱 Acesse: http://localhost:5000")
    print("⏹️  Para parar: Ctrl+C")
    print("=" * 50)
    
    # Inicia o servidor Flask
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Dashboard encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
