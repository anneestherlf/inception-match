from flask import Flask, render_template, jsonify
import gspread
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
import requests
from flask import request
import re

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
                'Status de financiamento': 'Seed',
                'País': 'Brasil',
                'TAM': '521.30',
                'Setor de Atuação': 'Edtech'
            },
            {
                'Nome da Startup': 'CaizStable',
                'Nome do Investidor (VC)': 'Antler',
                'Status de financiamento': 'Pré-seed',
                'País': 'México',
                'TAM': '201.12',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'CaizGold',
                'Nome do Investidor (VC)': 'VC',
                'Status de financiamento': 'Seed',
                'País': 'México',
                'TAM': '680.22',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'BitCoin',
                'Nome do Investidor (VC)': 'VC',
                'Status de financiamento': 'Seed',
                'País': 'México',
                'TAM': '730.44',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'Ethereum',
                'Nome do Investidor (VC)': 'VC',
                'Status de financiamento': 'Seed',
                'País': 'México',
                'TAM': '2,843.18',
                'Setor de Atuação': 'Fintech'
            },
            {
                'Nome da Startup': 'BitCoin Cash',
                'Nome do Investidor (VC)': 'VC',
                'Status de financiamento': 'Seed',
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

@app.route('/favicon.ico')
def favicon():
    """Serve o favicon"""
    return app.send_static_file('images/favicon.png')

@app.route('/')
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/insights')
def insights():
    """Página de insights com chatbot"""
    return render_template('insights.html')

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
            'status': startup.get('Status de financiamento', 'N/A'),
            'pais': startup.get('País', 'N/A'),
            'tam': startup.get('TAM', 'N/A'),
            'setor': startup.get('Setor de Atuação', 'N/A')
        }
        formatted_startups.append(formatted_startup)
    
    return jsonify(formatted_startups)

@app.route('/api/debug')
def api_debug():
    """API de debug para verificar dados brutos"""
    startups = get_startups_data()
    if startups:
        first = startups[0]
        return jsonify({
            'total': len(startups),
            'first_startup_raw': first,
            'status_field_exists': 'Status de financiamento' in first,
            'status_value': first.get('Status de financiamento', 'CAMPO_NAO_ENCONTRADO')
        })
    return jsonify({'error': 'No data'})

@app.route('/api/statistics')
def api_statistics():
    """API para buscar estatísticas"""
    return jsonify(get_statistics())


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Recebe uma mensagem do frontend, consulta a Serper API e retorna uma resposta"""
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    serper_key = os.getenv('SERPER_API_KEY')
    if not serper_key:
        return jsonify({'error': 'SERPER_API_KEY not configured on server'}), 500

    # Chamada à API Serper
    try:
        url = 'https://google.serper.dev/search'
        headers = {
            'X-API-KEY': serper_key,
            'Content-Type': 'application/json'
        }
        payload = {'q': message}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        result = resp.json()


        # Tentar extrair uma resposta direta (campo 'answer') ou montar um texto a partir dos resultados orgânicos
        answer = None
        if isinstance(result, dict):
            # Primeiro, campo 'answer' (pode conter resposta direta ou snippet)
            if 'answer' in result and result.get('answer'):
                a = result.get('answer')
                if isinstance(a, dict):
                    answer = a.get('answer') or a.get('snippet') or a.get('text')
                else:
                    answer = str(a)

            # Se não houver resposta direta, tente compor uma resposta mais completa a partir dos snippets orgânicos
            if not answer:
                organic = result.get('organic', [])
                snippets = []
                if organic and isinstance(organic, list):
                    # colete até 3 snippets/titles para compor uma resposta maior
                    for item in organic[:3]:
                        s = item.get('snippet') or item.get('title') or ''
                        if s:
                            snippets.append(s)

                # também verifique se existe algum 'knowledge' ou 'rich_snippet'
                if not snippets and result.get('knowledge'):
                    k = result.get('knowledge')
                    if isinstance(k, dict):
                        ks = k.get('snippets') or k.get('answers') or []
                        for it in ks[:3]:
                            if isinstance(it, dict):
                                s = it.get('text') or it.get('snippet') or ''
                            else:
                                s = str(it)
                            if s:
                                snippets.append(s)

                # junte e limpe as reticências artificiais
                if snippets:
                    def normalize_snippets(parts):
                        cleaned = []
                        seen = set()
                        for p in parts:
                            # remove reticências e múltiplos espaços
                            s = re.sub(r'\.{2,}', ' ', p)
                            s = s.replace('\n', ' ').strip()
                            # remove leading/trailing ellipses or dashes
                            s = re.sub(r'^[\s\-\u2026]+|[\s\-\u2026]+$', '', s)
                            if not s:
                                continue
                            # simple dedupe: skip if substring already present
                            key = s.lower()
                            if key in seen:
                                continue
                            if any(key in prev for prev in seen):
                                continue
                            seen.add(key)
                            # ensure ends with punctuation for nicer joining
                            if not re.search(r'[\.\!\?]$', s):
                                s = s.rstrip(' ,;:')
                                s = s + '.'
                            cleaned.append(s)

                        # join with space to form continuous prose
                        text = ' '.join(cleaned)
                        # normalize spaces
                        text = re.sub(r'\s{2,}', ' ', text).strip()
                        return text

                    answer = normalize_snippets(snippets)

        if not answer:
            answer = 'Desculpe, não consegui encontrar uma resposta precisa para isso.'

        # Extrair fontes (links) dos resultados orgânicos
        sources = []
        if isinstance(result, dict):
            organic = result.get('organic', [])
            if organic and isinstance(organic, list):
                for item in organic[:5]:
                    title = item.get('title') or item.get('serpapi_title') or ''
                    link = item.get('link') or item.get('url') or item.get('source') or ''
                    if link:
                        sources.append({'title': title, 'link': link})

        return jsonify({'answer': answer, 'raw': result, 'sources': sources})

    except requests.RequestException as e:
        return jsonify({'error': 'Failed to contact Serper API', 'details': str(e)}), 502

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
