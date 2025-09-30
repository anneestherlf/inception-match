#!/usr/bin/env python3
"""
Script para testar a API em uma nova sessão
"""

import time
import requests
import json

def test_api_direct():
    print("Aguardando servidor inicializar...")
    time.sleep(3)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/startups', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando! Total: {len(data)} startups")
            
            if data:
                first = data[0]
                print(f"Nome: {first.get('nome')}")
                print(f"Status: '{first.get('status')}'")
                print(f"Investidor: {first.get('investidor')}")
                
                # Conta quantos têm N/A
                na_count = sum(1 for s in data if s.get('status') == 'N/A')
                valid_count = len(data) - na_count
                
                print(f"\n📊 Status dos dados:")
                print(f"Startups com status N/A: {na_count}")
                print(f"Startups com status válido: {valid_count}")
                
                if na_count == 0:
                    print("🎉 Problema resolvido! Todos os status estão corretos!")
                else:
                    print("⚠️  Ainda existem status N/A")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    test_api_direct()