#!/usr/bin/env python3
"""
Teste direto da API sem depender do terminal
"""

import subprocess
import time
import requests
import json
import sys

def quick_test():
    print("🔍 Testando API diretamente...")
    
    try:
        # Teste a API de debug primeiro
        print("\n1. Testando /api/debug...")
        r = requests.get('http://127.0.0.1:5000/api/debug', timeout=5)
        if r.status_code == 200:
            debug_data = r.json()
            print(f"   Total startups: {debug_data.get('total')}")
            print(f"   Campo existe: {debug_data.get('status_field_exists')}")
            print(f"   Valor do status: '{debug_data.get('status_value')}'")
        else:
            print(f"   Erro: {r.status_code}")
            
        # Teste a API principal
        print("\n2. Testando /api/startups...")
        r = requests.get('http://127.0.0.1:5000/api/startups', timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   Total startups: {len(data)}")
            if data:
                first = data[0]
                print(f"   Primeira startup status: '{first.get('status')}'")
                
                # Conta N/A
                na_count = sum(1 for s in data if s.get('status') == 'N/A')
                print(f"   Startups com N/A: {na_count}/{len(data)}")
                
                if na_count == 0:
                    print("   ✅ SUCESSO! Todos os status estão corretos!")
                elif na_count < len(data):
                    print("   ⚠️  Alguns status estão corretos, mas outros ainda são N/A")
                else:
                    print("   ❌ Todos os status ainda são N/A")
        else:
            print(f"   Erro: {r.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

if __name__ == '__main__':
    quick_test()