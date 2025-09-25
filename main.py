# Carrega as chaves secretas do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Importações padrão
import os
import json
import gspread
from datetime import datetime

# Importações do CrewAI (usando a estrutura de importação que funcionou para você)
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Importações das ferramentas prontas
from crewai_tools import SerperDevTool, WebsiteSearchTool

# --- PAÍSES DA AMÉRICA LATINA (LISTA OFICIAL) ---
LATIN_AMERICA_COUNTRIES = [
    'Argentina', 'Bolívia', 'Brasil', 'Chile', 'Colômbia', 'Costa Rica', 
    'Cuba', 'Equador', 'El Salvador', 'Guatemala', 'Haiti', 'Honduras', 
    'México', 'Nicarágua', 'Panamá', 'Paraguai', 'Peru', 
    'República Dominicana', 'Uruguai', 'Venezuela'
]

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
def spreadsheet_tool(startup_data_json: str) -> str:
    """
    Salva dados de startups DA AMÉRICA LATINA na planilha, verificando duplicatas e país.
    O input DEVE ser uma string JSON válida.
    """
    try:
        data = json.loads(startup_data_json)
        startup_name = data.get('Nome da Startup', '')
        country = data.get('País', '')
        
        # VERIFICAÇÃO 1: País deve ser da América Latina
        if country not in LATIN_AMERICA_COUNTRIES:
            return f"REJEITADO: '{startup_name}' não é da América Latina (país: {country}). Apenas países válidos: {', '.join(LATIN_AMERICA_COUNTRIES)}"
        
        # VERIFICAÇÃO 2: Verificar se a startup já existe (evitar duplicatas)
        try:
            existing_cell = worksheet.find(startup_name)
            if existing_cell:
                return f"DUPLICATA EVITADA: '{startup_name}' já existe na planilha (linha {existing_cell.row}). Não foi adicionada novamente."
        except:
            # Se não encontrou, significa que não é duplicata
            pass
        
        # VERIFICAÇÃO 3: Dados mínimos obrigatórios
        if not startup_name or startup_name == 'Não encontrado':
            return f"REJEITADO: Nome da startup é obrigatório"
        
        # VERIFICAÇÃO 4: Idade da startup (máximo 10 anos)
        founding_year_str = data.get('Ano de Fundação', '')
        if founding_year_str and founding_year_str != 'Não encontrado':
            try:
                # Extrair apenas o ano numérico (caso tenha texto adicional)
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', str(founding_year_str))
                if year_match:
                    founding_year = int(year_match.group())
                    current_year = datetime.now().year
                    startup_age = current_year - founding_year
                    
                    if startup_age > 10:
                        return f"REJEITADO: '{startup_name}' tem {startup_age} anos (fundada em {founding_year}). Limite máximo: 10 anos."
                else:
                    # Se não conseguiu extrair um ano válido, continua sem rejeitar
                    pass
            except (ValueError, TypeError):
                # Se houve erro na conversão, continua sem rejeitar
                pass
            
        # Preparar dados para salvar
        row_data = [
            startup_name,
            data.get('Site', 'Não encontrado'),
            data.get('Setor de Atuação', 'Não encontrado'),
            country,
            data.get('Ano de Fundação', 'Não encontrado'),
            data.get('Tecnologias de IA Utilizadas', 'Não encontrado'),
            data.get('Nome do Investidor (VC)', 'Não encontrado'),
            data.get('Valor da Última Rodada', 'Não encontrado'),
            data.get('Nome do Líder Técnico', 'Não encontrado'),
            data.get('Linkedin do Líder Técnico', 'Não encontrado'),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        # Salvar na planilha
        worksheet.append_row(row_data)
        return f"✅ SUCESSO: Startup '{startup_name}' da {country} adicionada à planilha!"
            
    except json.JSONDecodeError:
        return f"ERRO: JSON inválido fornecido para a ferramenta de planilha"
    except Exception as e:
        return f"ERRO ao salvar na planilha: {str(e)}"

# --- DEFINIÇÃO DOS AGENTES ---

vc_scout = Agent(
    role='Venture Capital Portfolio Scraper',
    goal='Extrair nomes de startups de IA diretamente de páginas de portfólio de VCs.',
    backstory='Você é um robô focado em visitar páginas de portfólio de fundos de investimento e extrair os nomes das empresas listadas.',
    verbose=True,
    allow_delegation=False,
    tools=[website_tool]
)

database_researcher = Agent(
    role='Latin America AI Startup Researcher',
    goal='Encontrar o máximo possível de startups de IA da América Latina usando buscas direcionadas e verificando a origem geográfica.',
    backstory='Você é um especialista em startups latino-americanas. Conhece bem os países da região e sempre verifica se uma startup é realmente da América Latina antes de incluí-la nos resultados. Usa termos em português, espanhol e inglês nas buscas.',
    verbose=True,
    allow_delegation=False,
    tools=[search_tool]
)

startup_analyst = Agent(
    role='Startup Analyst',
    goal='Pesquisar ativamente e extrair o máximo de informações sobre uma startup da América Latina, usando múltiplas buscas e diferentes termos quando necessário.',
    backstory='Você é um pesquisador experiente que nunca desiste. Usa diferentes estratégias de busca: nome da startup + "sobre", "about", "website", "funding", "series", "investment". Sempre tenta pelo menos 3-4 buscas diferentes antes de desistir.',
    verbose=True,
    tools=[search_tool]
)

people_investigator = Agent(
    role='Tech Leadership Investigator',
    goal='Encontrar informações sobre líderes técnicos de startups usando várias estratégias de busca.',
    backstory='Você é um investigador de pessoas expert que usa múltiplas abordagens: busca por "CTO", "Head of Engineering", "Tech Lead", "Founder", "CEO", além do LinkedIn da empresa, equipe, sobre nós, etc.',
    verbose=True,
    tools=[search_tool]
)

data_organizer = Agent(
    role='Data Organizer',
    goal='Consolidar todas as informações coletadas em um JSON estruturado e salvá-lo na planilha.',
    backstory='Você é um organizador de dados que recebe informações dos outros agentes e as consolida em um formato JSON. Você sempre verifica se recebeu dados antes de marcar algo como "Não encontrado".',
    verbose=True,
    tools=[spreadsheet_tool]
)

# --- DEFINIÇÃO DAS TAREFAS ---

# Listas de fontes para a busca
portfolio_websites = [
    "www.sequoiacap.com/companies", 
    "www.monashees.com/portfolio", 
    "www.perception.com/portfolio"
]

database_platforms = [
    "pitchbook.com",
    "crunchbase.com",
    "cbinsights.com",
    "slinghub.com.br",
    "distrito.me",
    "ligaventures.com.br"
]

# Tarefa 1: Busca em Portfólios (mais focada)
prospect_from_portfolios_task = Task(
    description=f"Acesse cada um destes sites: {', '.join(portfolio_websites)}. Para cada site, leia os nomes das empresas e identifique até 2 que pareçam ser do setor de Inteligência Artificial.",
    expected_output='Uma string com uma lista de nomes de startups, separados por vírgula. Ex: "NotCo, Cortex"',
    agent=vc_scout
)

# Tarefa 2: Busca Focada APENAS na América Latina
prospect_from_databases_task = Task(
    description=(
        f"MISSÃO: Encontrar startups de IA EXCLUSIVAMENTE dos países da América Latina.\n\n"
        f"**PAÍSES VÁLIDOS (OBRIGATÓRIO VERIFICAR):**\n"
        f"{', '.join(LATIN_AMERICA_COUNTRIES)}\n\n"
        f"**BUSCAS OBRIGATÓRIAS A EXECUTAR:**\n"
        f"1. 'startup inteligência artificial brasil site:crunchbase.com'\n"
        f"2. 'AI startup Mexico artificial intelligence site:crunchbase.com'\n"
        f"3. 'startup IA Argentina Colombia Chile site:crunchbase.com'\n"
        f"4. 'machine learning startups Peru Uruguai site:pitchbook.com'\n"
        f"5. 'artificial intelligence startup Costa Rica Panama site:cbinsights.com'\n"
        f"6. 'AI startups Latin America Brasil México site:slinghub.com.br'\n"
        f"7. 'startup artificial intelligence Venezuela Ecuador site:distrito.me'\n"
        f"8. 'inteligencia artificial startup Guatemala Honduras site:ligaventures.com.br'\n\n"
        f"**REGRAS CRÍTICAS:**\n"
        f"- Para CADA startup encontrada, VERIFIQUE se o país é da lista acima\n"
        f"- Se a startup não for da América Latina, NÃO inclua na lista\n"
        f"- Use termos em português, espanhol e inglês\n"
        f"- Procure variações: 'IA', 'AI', 'artificial intelligence', 'inteligência artificial', 'machine learning'\n\n"
        f"**PLATAFORMAS PARA BUSCAR:**\n"
        f"- {', '.join(database_platforms)}"
    ),
    expected_output='Lista de nomes de startups CONFIRMADAMENTE da América Latina, separados por vírgula.',
    agent=database_researcher
)

# --- CRIAÇÃO E EXECUÇÃO DO PROCESSO ---

if __name__ == "__main__":
    print("Iniciando o processo de busca massiva de startups...")

    # ETAPA 1: PROSPECÇÃO
    prospecting_crew = Crew(
        agents=[vc_scout, database_researcher],
        tasks=[prospect_from_portfolios_task, prospect_from_databases_task],
        process=Process.sequential
    )
    
    print("Buscando nomes de startups em portfólios e bases de dados...")
    prospecting_results = prospecting_crew.kickoff()

    # Consolida os resultados, corrigindo o acesso ao output
    found_names = set()
    # O resultado agora é um objeto CrewOutput, pegamos o output de cada tarefa
    if prospecting_results and prospecting_results.tasks_output:
        for task_output in prospecting_results.tasks_output:
            # Acessamos o texto bruto do resultado da tarefa
            names_string = task_output.raw
            names = names_string.split(',')
            for name in names:
                clean_name = name.strip()
                if clean_name:
                    found_names.add(clean_name)
    
    startup_names = list(found_names)
    
    print("\n--------------------------------------------------")
    print(f"Total de {len(startup_names)} startups únicas encontradas para análise: {startup_names}")
    print("--------------------------------------------------\n")

    # ETAPA 2: ANÁLISE INDIVIDUAL
    if startup_names:
        for name in startup_names:
            print(f"\n>>> Analisando startup: {name}")
            
            # Tarefa de análise da startup com instruções MUITO detalhadas
            startup_task = Task(
                description=f'''
ANÁLISE RIGOROSA da startup "{name}" - APENAS AMÉRICA LATINA:

**PAÍSES VÁLIDOS DA AMÉRICA LATINA:**
{', '.join(LATIN_AMERICA_COUNTRIES)}

**BUSCAS OBRIGATÓRIAS:**
1. "{name} startup empresa"
2. "{name} site oficial about company"
3. "{name} sede headquarters location país"
4. "{name} crunchbase pitchbook funding"
5. "{name} artificial intelligence IA machine learning"

**VERIFICAÇÃO CRÍTICA DO PAÍS:**
- PROCURE ESPECIFICAMENTE por: "sediada em", "baseada em", "headquarters", "based in", "located in"
- CONFIRME se o país está na lista da América Latina
- Se a startup for de QUALQUER país fora da América Latina, reporte: "REJEITAR - País fora da América Latina"

**INFORMAÇÕES A EXTRAIR:**
- Site oficial (URL própria)
- Setor (fintech, healthtech, edtech, etc.)  
- País sede (DEVE estar na lista acima)
- Ano de fundação
- Tecnologias de IA específicas
- Investidores/VCs
- Valor de investimento

**FORMATO OBRIGATÓRIO:**
Se país válido:
Site: [URL]
Setor: [setor]
País: [país da América Latina]
Fundação: [ano]
IA: [tecnologias]
Investidor: [VC]
Rodada: [valor]

Se país inválido:
REJEITAR - País fora da América Latina: [nome do país encontrado]
                ''',
                expected_output=f'Relatório completo com informações específicas da startup {name} no formato solicitado',
                agent=startup_analyst
            )
            
            # Tarefa de liderança com estratégias múltiplas
            leadership_task = Task(
                description=f'''
ENCONTRAR LIDERANÇA TÉCNICA da startup "{name}":

BUSCAS OBRIGATÓRIAS:
1. "{name} CTO chief technology officer"
2. "{name} founder co-founder technical"
3. "{name} team equipe leadership"
4. "{name} about us sobre nós"
5. "{name} linkedin company"

PROCURAR POR:
- CTO, VP Engineering, Head of Tech
- Co-founder técnico
- CEO com background técnico
- Engineering Director/Manager

ESTRATÉGIAS:
- Verificar site oficial da empresa (seção Team/About)
- LinkedIn da empresa
- Notícias sobre a startup
- Perfis dos fundadores

FORMATO OBRIGATÓRIO:
Nome: [nome completo da pessoa]
Cargo: [posição técnica]
LinkedIn: [URL do perfil]
                ''',
                expected_output=f'Informações do líder técnico da startup {name} no formato especificado',
                agent=people_investigator
            )

            # Tarefa de consolidação melhorada
            consolidation_task = Task(
                description=f'''
VERIFICAR E CONSOLIDAR dados da startup "{name}":

**PAÍSES VÁLIDOS DA AMÉRICA LATINA:**
{', '.join(LATIN_AMERICA_COUNTRIES)}

**VERIFICAÇÃO OBRIGATÓRIA:**
1. LEIA o relatório do startup_analyst
2. Se contém "REJEITAR - País fora da América Latina", NÃO SALVE e reporte: "Startup {name} rejeitada - não é da América Latina"
3. Se o país relatado NÃO está na lista acima, NÃO SALVE e reporte: "Startup {name} rejeitada - país inválido"

**SE A STARTUP FOR VÁLIDA (da América Latina):**
4. EXTRAIA as informações dos relatórios
5. MONTE o JSON exatamente assim:

{{
  "Nome da Startup": "{name}",
  "Site": "[do relatório: Site: ...]",
  "Setor de Atuação": "[do relatório: Setor: ...]", 
  "País": "[do relatório: País: ... - DEVE ser da América Latina]",
  "Ano de Fundação": "[do relatório: Fundação: ...]",
  "Tecnologias de IA Utilizadas": "[do relatório: IA: ...]",
  "Nome do Investidor (VC)": "[do relatório: Investidor: ...]",
  "Valor da Última Rodada": "[do relatório: Rodada: ...]",
  "Nome do Líder Técnico": "[do relatório: Nome: ...]",
  "Linkedin do Líder Técnico": "[do relatório: LinkedIn: ...]"
}}

6. USE A FERRAMENTA spreadsheet_tool para salvar
7. A ferramenta já verifica duplicatas automaticamente
                ''',
                expected_output=f'Confirmação de salvamento na planilha para {name}',
                agent=data_organizer,
                context=[startup_task, leadership_task]
            )
            
            # Cria um Crew de análise SÓ para esta startup
            analysis_crew = Crew(
                agents=[startup_analyst, people_investigator, data_organizer],
                tasks=[startup_task, leadership_task, consolidation_task],
                process=Process.sequential
            )

            startup_result = analysis_crew.kickoff()
            print(f"Resultado para {name}: {startup_result.raw if startup_result else 'Sem resultado.'}")
        
        print("\n\n########################")
        print("## Processo finalizado!")
        print("## Todas as startups foram analisadas e salvas na planilha.")
        print("########################")
    else:
        print("Nenhuma startup foi encontrada para analisar.")