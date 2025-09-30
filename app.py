from flask import Flask, render_template, jsonify
import gspread
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração do Google Sheets
print("Tentando conectar ao Google Sheets...")
try:
    gc = gspread.service_account(filename='credentials.json')
    spreadsheet = gc.open("Base de Startups NVIDIA")
    worksheet = spreadsheet.sheet1
    print("Conexão com a planilha bem-sucedida.")
except FileNotFoundError:
    print("Erro: O arquivo 'credentials.json' não foi encontrado. Certifique-se de que ele está no diretório correto.")
    worksheet = None
except gspread.exceptions.APIError as api_error:
    print(f"Erro na API do Google Sheets: {api_error}")
    worksheet = None
except Exception as e:
    print(f"Erro inesperado ao conectar com a planilha: {e}")
    worksheet = None

def get_startups_data():
    """Busca todos os dados das startups da planilha"""
    if not worksheet:
        print("⚠️  Conexão com o Google Sheets não estabelecida. Usando dados de exemplo.")
        return [
            {
                'Nome da Startup': 'CaizCoin',
                'Nome do Investidor (VC)': 'Monashees',
                'Status do Financiamento': 'Seed',
                'País': 'Brasil',
                'TAM': '521.30',
                'Setor de Atuação': 'Edtech'
            },
            {
                'Nome da Startup': 'CaizStable',
                'Nome do Investidor (VC)': 'Antler',
                'Status do Financiamento': 'Pré-seed',
                'País': 'México',
                'TAM': '201.12',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'CaizGold',
                'Nome do Investidor (VC)': 'VC',
                'Status do Financiamento': 'Seed',
                'País': 'México',
                'TAM': '680.22',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'BitCoin',
                'Nome do Investidor (VC)': 'VC',
                'Status do Financiamento': 'Seed',
                'País': 'México',
                'TAM': '730.44',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'Ethereum',
                'Nome do Investidor (VC)': 'VC',
                'Status do Financiamento': 'Seed',
                'País': 'México',
                'TAM': '2,843.18',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'BitCoin Cash',
                'Nome do Investidor (VC)': 'VC',
                'Status do Financiamento': 'Seed',
                'País': 'México',
                'TAM': '730.44',
                'Setor de Atuação': 'Fintech'
            }
        ]

    try:
        print("🔄 Lendo dados reais da planilha...")
        all_records = worksheet.get_all_records()
        print(f"✅ {len(all_records)} registros carregados da planilha.")
        return all_records
    except Exception as e:
        print(f"❌ Erro ao ler dados da planilha: {e}")
        return []

def get_statistics():
    """Calcula estatísticas dos dados"""
    startups = get_startups_data()
    
    if not startups:
        return {
            'total_startups': 0,
            'last_update': 'N/A',
            'top_sectors': [],
            'top_countries': []
        }
    
    # Conta setores
    sectors = {}
    countries = {}
    
    for startup in startups:
        sector = startup.get('Setor de Atuação', 'N/A')
        country = startup.get('País', 'N/A')
        
        if sector and sector != 'N/A':
            sectors[sector] = sectors.get(sector, 0) + 1
        
        if country and country != 'N/A':
            countries[country] = countries.get(country, 0) + 1
    
    # Top 5 setores
    top_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5]
    top_sectors = [{'name': name, 'count': count} for name, count in top_sectors]
    
    # Top 5 países
    top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
    top_countries = [{'name': name, 'count': count} for name, count in top_countries]
    
    return {
        'total_startups': len(startups),
        'last_update': 'há 30 min',  # Simulado baseado na imagem
        'top_sectors': top_sectors,
        'top_countries': top_countries
    }

@app.route('/')
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/startups')
def api_startups():
    """API para buscar dados das startups"""
    startups = get_startups_data()
    
    # Formata os dados para a tabela
    formatted_startups = []
    for startup in startups:
        formatted_startup = {
            'nome': startup.get('Nome da Startup', 'N/A'),
            'investidor': startup.get('Nome do Investidor (VC)', 'N/A'),
            'status': startup.get('Status do Financiamento', 'N/A'),
            'pais': startup.get('País', 'N/A'),
            'tam': startup.get('TAM', 'N/A'),
            'setor': startup.get('Setor de Atuação', 'N/A')
        }
        formatted_startups.append(formatted_startup)
    
    return jsonify(formatted_startups)

@app.route('/api/statistics')
def api_statistics():
    """API para buscar estatísticas"""
    return jsonify(get_statistics())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
