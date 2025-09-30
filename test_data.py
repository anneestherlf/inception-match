#!/usr/bin/env python3
"""
Script de teste para verificar se os dados do Google Sheets aparecem corretamente
"""

from app import get_startups_data

def main():
    print('Testando a função get_startups_data...')
    startups = get_startups_data()
    print(f'Total de startups: {len(startups)}')
    
    if startups:
        print('\n--- Primeira startup ---')
        first = startups[0]
        print(f'Nome: {first.get("Nome da Startup", "N/A")}')
        print(f'Status: {first.get("Status de financiamento", "N/A")}')
        print(f'Investidor: {first.get("Nome do Investidor (VC)", "N/A")}')
        print(f'País: {first.get("País", "N/A")}')
        print(f'Setor: {first.get("Setor de Atuação", "N/A")}')
        
        print('\n--- Verificando se campo existe ---')
        print('Campos disponíveis na primeira startup:')
        for key in sorted(first.keys()):
            if 'status' in key.lower() or 'financiamento' in key.lower():
                print(f'  >> {key}: {first[key]}')

if __name__ == '__main__':
    main()