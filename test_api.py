#!/usr/bin/env python3
"""
Script para testar a API diretamente
"""

import requests
import json

def test_api():
    try:
        # Testa a API de startups
        response = requests.get('http://127.0.0.1:5000/api/startups', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API respondeu com {len(data)} startups")
            
            if data:
                first = data[0]
                print("\n--- Primeira startup da API ---")
                print(f"Nome: {first.get('nome', 'N/A')}")
                print(f"Status: {first.get('status', 'N/A')}")
                print(f"Investidor: {first.get('investidor', 'N/A')}")
                print(f"País: {first.get('pais', 'N/A')}")
                print(f"Setor: {first.get('setor', 'N/A')}")
                
                # Verifica quantos têm status N/A
                na_count = sum(1 for s in data if s.get('status') == 'N/A')
                print(f"\n📊 Estatísticas:")
                print(f"Total de startups: {len(data)}")
                print(f"Com status 'N/A': {na_count}")
                print(f"Com status válido: {len(data) - na_count}")
        else:
            print(f"❌ Erro na API: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    test_api()