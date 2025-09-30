#!/usr/bin/env python3
"""
Script para verificar os cabeçalhos da planilha Google Sheets
"""

import gspread

def main():
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open('Base de Startups NVIDIA')
        worksheet = spreadsheet.sheet1
        
        headers = worksheet.row_values(1)
        print('Cabeçalhos da planilha:')
        for i, header in enumerate(headers, 1):
            print(f'{i:2d}: "{header}"')
            
        # Vamos pegar uma amostra de dados também
        print('\n--- Amostra de dados da primeira startup ---')
        if len(worksheet.get_all_records()) > 0:
            sample = worksheet.get_all_records()[0]
            for key, value in sample.items():
                if 'status' in key.lower() or 'financiamento' in key.lower():
                    print(f'Campo relacionado ao status: "{key}" = "{value}"')
                    
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()