#!/usr/bin/env python3
"""
Script para debugar exatamente o que está sendo retornado pela API
"""

from app import get_startups_data

def debug_data():
    print("🔍 Debugando dados retornados...")
    
    # Testa a função diretamente
    startups = get_startups_data()
    print(f"Total de startups: {len(startups)}")
    
    if startups:
        first = startups[0]
        print("\n--- Dados brutos da primeira startup ---")
        for key, value in first.items():
            if 'status' in key.lower() or 'financiamento' in key.lower():
                print(f"  '{key}': '{value}'")
        
        print("\n--- Testando mapeamento ---")
        formatted = {
            'nome': first.get('Nome da Startup', 'N/A'),
            'investidor': first.get('Nome do Investidor (VC)', 'N/A'),
            'status': first.get('Status de financiamento', 'N/A'),
            'pais': first.get('País', 'N/A'),
            'tam': first.get('TAM', 'N/A'),
            'setor': first.get('Setor de Atuação', 'N/A')
        }
        
        for key, value in formatted.items():
            print(f"  {key}: {value}")
            
        print("\n--- Todas as chaves disponíveis ---")
        for key in sorted(first.keys()):
            print(f"  '{key}'")

if __name__ == '__main__':
    debug_data()