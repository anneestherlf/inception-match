# Carrega as chaves secretas do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Importações padrão e de bibliotecas
import os
import json
import gspread
from datetime import datetime

# Importações do CrewAI e ferramentas
from crewai import Agent, Task, Crew, Process, tool
from crewai_tools import SerperDevTool, WebsiteSearchTool

# --- CONFIGURAÇÃO DAS FERRAMENTAS ---
search_tool = SerperDevTool()
website_tool = WebsiteSearchTool()

# --- CONEXÃO COM A PLANILHA (Google Sheets) ---
try:
    gc = gspread.service_account(filename='credentials.json')
    spreadsheet = gc.open("Base de Startups NVIDIA")
    worksheet = spreadsheet.sheet1
    print("Conexão com a planilha bem-sucedida.")
except Exception as e:
    print(f"Erro ao conectar com a planilha: {e}")
    exit()

# --- FERRAMENTA PERSONALIZADA PARA O GOOGLE SHEETS ---
@tool("Spreadsheet Update Tool")
def spreadsheet_tool(data_json: str) -> str:
    """
    Recebe um JSON com os dados completos de uma startup e o utiliza para adicionar ou
    atualizar uma linha na planilha do Google Sheets.
    """
    try:
        data = json.loads(data_json)
        cell = worksheet.find(data.get('Nome da Startup', ''))
        row_data = [
            data.get('Nome da Startup', 'Não encontrado'), data.get('Site', 'Não encontrado'),
            data.get('Setor de Atuação', 'Não encontrado'), data.get('País', 'Não encontrado'),
            data.get('Legalmente Instituída', 'Não encontrado'), data.get('Ano de Fundação', 'Não encontrado'),
            data.get('Tecnologias Utilizadas', 'Não encontrado'), data.get('Nome do Investidor (VC)', 'Não encontrado'),
            data.get('Valor da Última Rodada', 'Não encontrado'), data.get('Status do Financiamento', 'Não encontrado'),
            data.get('Liderança Técnica (Nome)', 'Não encontrado'), data.get('Liderança Técnica (LinkedIn)', 'Não encontrado'),
            data.get('Integrantes do Time', 'Não encontrado'), data.get('Tamanho da Startup', 'Não encontrado'),
            data.get('Base de Clientes', 'Não encontrado'), data.get('TAM', 'Não encontrado'),
            data.get('SAM', 'Não encontrado'), data.get('SOM', 'Não encontrado'),
            data.get('Dinâmica do Setor', 'Não encontrado'), data.get('Principais Concorrentes', 'Não encontrado'),
            data.get('Previsões de Mercado', 'Não encontrado'), data.get('Análise de Riscos Ambientais', 'Não encontrado'),
            data.get('CAC', 'Não encontrado'), data.get('Churn Rate', 'Não encontrado'),
            data.get('Fontes da Análise de Mercado', 'Não encontrado'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        if cell:
            worksheet.update(f'A{cell.row}', [row_data])
            return f"Dados da startup '{data['Nome da Startup']}' atualizados com sucesso."
        else:
            worksheet.append_row(row_data)
            return f"Nova startup '{data['Nome da Startup']}' adicionada com sucesso."
    except Exception as e:
        return f"Ocorreu um erro ao interagir com a planilha: {str(e)}"

# --- EQUIPE DE AGENTES ESPECIALISTAS ---
prospector_agent = Agent(role='Prospector de Startups de IA', goal='Gerar uma lista massiva de nomes de startups de IA', backstory='Especialista em prospecção digital, encontra o máximo de nomes de startups possível.', verbose=True, allow_delegation=False, tools=[search_tool, website_tool])
qualifier_agent = Agent(role='Qualificador de Leads de Startups', goal='Filtrar uma lista, mantendo apenas startups de tecnologia da América Latina.', backstory='Analista rápido e preciso, verifica a localização e o setor de cada empresa.', verbose=True, allow_delegation=False, tools=[search_tool])
data_analyst_agent = Agent(role='Analista de Dados de Startups', goal='Coletar informações detalhadas sobre uma única startup.', backstory='Pesquisador persistente que mergulha fundo para encontrar dados essenciais.', verbose=True, allow_delegation=True, tools=[search_tool])
market_strategist_agent = Agent(role='Estrategista de Mercado de Tecnologia', goal='Realizar uma análise de mercado aprofundada para uma startup.', backstory='Especialista em interpretar dados para avaliar o potencial de mercado, sempre citando fontes.', verbose=True, allow_delegation=True, tools=[search_tool])
database_manager_agent = Agent(role='Gerente de Banco de Dados', goal='Garantir a integridade da base de dados no Google Sheets.', backstory='Guardião da nossa fonte da verdade, prevenindo duplicatas e garantindo dados precisos.', verbose=True, allow_delegation=False, tools=[spreadsheet_tool])

# --- LISTAS DE FONTES PARA PROSPECÇÃO ---
lista_vcs = ["Sequoia Capital", "Andreessen Horowitz", "SoftBank", "Kaszek", "Valor Capital Group", "Tiger Global", "Canary", "Bossa Invest", "Monashees", "Latitud"]
lista_plataformas = ["crunchbase.com", "pitchbook.com", "latamlist.com", "slinghub.com.br", "distrito.me"]
lista_paises_latam = ["Brasil", "México", "Argentina", "Colômbia", "Chile", "Peru"]

# --- TAREFAS ---
task_prospect = Task(
    description=(
        "Sua missão é gerar a maior lista possível de nomes de startups. Combine as fontes abaixo em múltiplas buscas no Google.\n"
        f"**VCs para pesquisar (busque por 'nome do VC portfolio'):** {', '.join(lista_vcs)}\n"
        f"**Plataformas para pesquisar (use 'site:'):** {', '.join(lista_plataformas)}\n"
        f"**Países para focar:** {', '.join(lista_paises_latam)}\n"
        "**ESTRATÉGIA:** Não busque por 'IA', apenas liste os nomes das empresas nos portfólios. A qualificação virá depois. Execute pelo menos 15 buscas diferentes."
    ),
    expected_output="Uma única string contendo uma longa lista de nomes de startups, separados por vírgula.",
    agent=prospector_agent
)

task_qualify = Task(
    description="Para cada nome na lista de entrada, faça uma busca rápida e determine se a empresa atende a DOIS critérios: 1. É uma empresa de TECNOLOGIA. 2. Está sediada na AMÉRICA LATINA.",
    expected_output="Uma string contendo uma lista filtrada apenas com os nomes das startups qualificadas, separados por vírgula.",
    agent=qualifier_agent
)

task_analyze_data_template = Task(description='Para a startup "{startup_name}", encontre: site, setor, país, status legal, ano de fundação, tecnologias, VCs, funding, e o nome e LinkedIn da liderança técnica.', expected_output='Um relatório em texto com os dados fundamentais da startup "{startup_name}".', agent=data_analyst_agent)
task_analyze_market_template = Task(description='Para a startup "{startup_name}", realize uma análise de mercado: TAM, SAM, SOM, concorrentes, dinâmica do setor, previsões, e riscos. CRÍTICO: Liste todas as URLs das fontes.', expected_output='Um relatório de análise de mercado para "{startup_name}", incluindo as fontes.', agent=market_strategist_agent)
task_manage_database_template = Task(description='Consolide os relatórios de dados e mercado da startup "{startup_name}" em um único JSON e use a ferramenta "Spreadsheet Update Tool" para salvá-lo.', expected_output='Mensagem de confirmação de que a startup "{startup_name}" foi salva ou atualizada.', agent=database_manager_agent)

# --- FLUXO DE TRABALHO PRINCIPAL ---
if __name__ == '__main__':
    print("Iniciando fluxo de trabalho completo...")

    # ETAPA 1: Prospecção e Qualificação
    prospecting_crew = Crew(
        agents=[prospector_agent, qualifier_agent],
        tasks=[task_prospect, task_qualify],
        process=Process.sequential,
        verbose=True
    )
    print("Executando Crew de Prospecção...")
    prospecting_result = prospecting_crew.kickoff()
    
    # **CORREÇÃO APLICADA AQUI**
    # Acessa o resultado da ÚLTIMA tarefa (qualificação), que contém a lista final
    qualified_names_str = prospecting_result.tasks_output[-1].raw if (prospecting_result and prospecting_result.tasks_output) else ""
    startup_names_to_analyze = [name.strip() for name in qualified_names_str.split(',') if name.strip()]
    
    print("\n--------------------------------------------------")
    print(f"Total de {len(startup_names_to_analyze)} startups qualificadas encontradas: {startup_names_to_analyze}")
    print("--------------------------------------------------\n")

    # ETAPA 2: Análise Profunda em Loop
    if startup_names_to_analyze:
        existing_startups = set(worksheet.col_values(1))
        
        for name in startup_names_to_analyze:
            if name in existing_startups:
                print(f"Startup '{name}' já existe na base. Pulando.")
                continue

            print(f"\n>>> Iniciando análise profunda para: {name} <<<")
            
            # Cria tarefas dinâmicas
            task_analyze_data = task_analyze_data_template
            task_analyze_data.description = task_analyze_data.description.format(startup_name=name)
            
            task_analyze_market = task_analyze_market_template
            task_analyze_market.description = task_analyze_market.description.format(startup_name=name)

            task_manage_database = task_manage_database_template
            task_manage_database.description = task_manage_database.description.format(startup_name=name)
            task_manage_database.context = [task_analyze_data, task_analyze_market]

            # Cria Crew de Análise para esta startup
            analysis_crew = Crew(
                agents=[data_analyst_agent, market_strategist_agent, database_manager_agent],
                tasks=[task_analyze_data, task_analyze_market, task_manage_database],
                process=Process.sequential,
                verbose=True
            )
            
            analysis_result = analysis_crew.kickoff()
            print(f"Resultado da análise para '{name}': {analysis_result.raw if analysis_result else 'Sem resultado.'}")
            
    print("\n\n########################")
    print("## Processo finalizado!")
    print("########################")