#!/usr/bin/env python3
"""
Script para limpar startups inválidas do Google Sheets
Remove startups dos EUA e do setor Venture Capital
"""

import gspread
from dotenv import load_dotenv

load_dotenv()

# Lista de setores rejeitados (empresas de investimento, não startups)
setores_rejeitados = [
    'venture capital', 'vc', 'venture builder', 'investment', 'investor', 'fund', 'capital', 
    'private equity', 'asset management', 'investment management', 'investment fund',
    'venture fund', 'growth capital', 'seed fund', 'accelerator fund', 'incubator fund',
    'investment company', 'investment firm', 'capital management', 'wealth management',
    'investment banking', 'merchant banking', 'development finance', 'investment vehicle'
]

paises_rejeitados = ['estados unidos', 'eua', 'usa', 'us', 'united states', 'silicon valley']

def main():
    """Executa a limpeza da planilha"""
    print("🧹 Iniciando limpeza de startups inválidas...")
    
    try:
        # Conecta com a planilha
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open("Base de Startups NVIDIA")
        worksheet = spreadsheet.sheet1
        print("✅ Conexão com a planilha estabelecida.")
        
        # Busca todos os registros da planilha
        all_records = worksheet.get_all_records()
        rows_to_delete = []
        
        print(f"📊 Analisando {len(all_records)} registros...")
        
        for i, record in enumerate(all_records, start=2):  # start=2 porque linha 1 é cabeçalho
            startup_name = record.get('Nome da Startup', '').strip()
            pais = record.get('País', '').lower().strip()
            setor = record.get('Setor de Atuação', '').lower().strip()
            
            # Verifica se é dos EUA
            is_usa = any(termo in pais for termo in paises_rejeitados)
            
            # Verifica se é do setor venture capital
            is_vc = any(termo in setor for termo in setores_rejeitados)
            
            if is_usa or is_vc:
                reason = "EUA" if is_usa else "Venture Capital"
                print(f"❌ Marcando para remoção: {startup_name} - Motivo: {reason}")
                print(f"   País: {pais}")
                print(f"   Setor: {setor}")
                rows_to_delete.append(i)
        
        # Remove as linhas (de trás para frente para não alterar os índices)
        if rows_to_delete:
            print(f"\n🗑️  Removendo {len(rows_to_delete)} startups inválidas...")
            
            # Confirma com o usuário
            confirm = input(f"Confirma a remoção de {len(rows_to_delete)} startups? (s/N): ").lower()
            if confirm == 's':
                for row_index in sorted(rows_to_delete, reverse=True):
                    worksheet.delete_rows(row_index)
                print(f"✅ Limpeza concluída! {len(rows_to_delete)} startups removidas.")
            else:
                print("❌ Operação cancelada pelo usuário.")
        else:
            print("✅ Nenhuma startup inválida encontrada na planilha.")
            
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")

if __name__ == '__main__':
    main()