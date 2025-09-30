# Carrega as chaves secretas do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Importações padrão e de bibliotecas
import os
import json
import re
import gspread
from datetime import datetime

# Importações do CrewAI e ferramentas
from crewai import Agent, Task, Crew, Process

# Compatibilidade: algumas versões do crewai não expõem 'tool'.
try:
    from crewai import tool  # type: ignore
except ImportError:  # Fallback simples para não quebrar execução
    def tool(name: str):
        def decorator(fn):
            fn.tool_name = name
            return fn
        return decorator
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
    """Atualiza ou insere uma linha da startup. Exige pelo menos 'Nome da Startup'."""
    REQUIRED_ORDER = [
        'Nome da Startup','Site','Setor de Atuação','País','Legalmente Instituída','Ano de Fundação',
        'Tecnologias Utilizadas','Nome do Investidor (VC)','Valor da Última Rodada','Status de financiamento',
        'Liderança Técnica (Nome)','Liderança Técnica (LinkedIn)','Integrantes do Time','Tamanho da Startup',
        'Base de Clientes','TAM','SAM','SOM','Dinâmica do Setor','Principais Concorrentes',
        'Previsões de Mercado','Análise de Riscos Ambientais','CAC','Churn Rate','Fontes da Análise de Mercado'
    ]
    try:
        data = json.loads(data_json)
        if not data.get('Nome da Startup'):
            return "Erro: campo 'Nome da Startup' ausente no JSON enviado ao spreadsheet_tool." 
        # Normaliza valores
        normalized = {k: (v if v not in (None, 'N/A', 'n/a', 'NA') else 'Não disponível') for k, v in data.items()}
        cell = worksheet.find(normalized['Nome da Startup'])
        row_data = [normalized.get(k, '') or 'Não encontrado' for k in REQUIRED_ORDER]
        row_data.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if cell:
            worksheet.update(f'A{cell.row}', [row_data])
            return f"Dados da startup '{normalized['Nome da Startup']}' atualizados com sucesso."
        worksheet.append_row(row_data)
        return f"Nova startup '{normalized['Nome da Startup']}' adicionada com sucesso."
    except Exception as e:
        return f"Ocorreu um erro ao interagir com a planilha: {str(e)}"

# --- EQUIPE DE AGENTES ESPECIALISTAS ---
prospector_agent = Agent(role='Prospector de Startups de IA', goal='Gerar uma lista massiva de nomes de startups de IA', backstory='Especialista em prospecção digital, encontra o máximo de nomes de startups possível.', verbose=True, allow_delegation=False, tools=[search_tool, website_tool])
qualifier_agent = Agent(role='Qualificador de Leads de Startups', goal='Filtrar uma lista, mantendo EXCLUSIVAMENTE startups de tecnologia da América Latina. REJEITAR TOTALMENTE qualquer startup dos Estados Unidos, EUA, USA, US ou United States. REJEITAR empresas dos setores: Venture Capital, VC, Venture Builder, Investment, Investor, Fund, Capital, Private Equity. ACEITAR APENAS startups de tecnologia/produto da América Latina.', backstory='Analista extremamente rigoroso que verifica meticulosamente a localização geográfica e o setor de cada empresa, rejeitando qualquer startup fora da América Latina ou que seja empresa de investimento.', verbose=True, allow_delegation=False, tools=[search_tool])
data_analyst_agent = Agent(role='Analista de Dados de Startups', goal='Coletar informações detalhadas sobre uma única startup.', backstory='Pesquisador persistente que mergulha fundo para encontrar dados essenciais.', verbose=True, allow_delegation=True, tools=[search_tool])
market_strategist_agent = Agent(role='Estrategista de Mercado de Tecnologia', goal='Realizar uma análise de mercado aprofundada para uma startup.', backstory='Especialista em interpretar dados para avaliar o potencial de mercado, sempre citando fontes.', verbose=True, allow_delegation=True, tools=[search_tool])
# Removido database_manager_agent porque o decorator @tool desta versão não converte a função em BaseTool automaticamente.

# --- LISTAS DE FONTES PARA PROSPECÇÃO ---
lista_vcs = ["Sequoia Capital", "Andreessen Horowitz", "SoftBank", "Kaszek", "Valor Capital Group", "Tiger Global", "Canary", "Bossa Invest", "Monashees", "Latitud", "New Enterprise Associates", "Accel", "Lightspeed Venture Partners", "Bessemer Venture Partners", "Canary", "Igah Ventures", "Bossanova Investimentos"]
lista_plataformas = ["crunchbase.com", "pitchbook.com", "latamlist.com", "slinghub.com.br", "distrito.me"]
lista_paises_latam = ["Brasil", "Brazil", "México", "Mexico", "Argentina", "Colômbia", "Colombia", "Chile", "Peru", "Perú", "Bolívia", "Bolivia", "Equador", "Ecuador", "Guiana", "Guyana", "Paraguai", "Paraguay", "Suriname", "Uruguai", "Uruguay", "Venezuela", "Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Nicarágua", "Nicaragua", "Panamá", "Panama", "Cuba", "Haiti", "República Dominicana", "Dominican Republic"]

# Lista de setores rejeitados (empresas de investimento, não startups)
setores_rejeitados_global = [
    'venture capital', 'vc', 'venture builder', 'investment', 'investor', 'fund', 'capital', 
    'private equity', 'asset management', 'investment management', 'investment fund',
    'venture fund', 'growth capital', 'seed fund', 'accelerator fund', 'incubator fund',
    'investment company', 'investment firm', 'capital management', 'wealth management',
    'investment banking', 'merchant banking', 'development finance', 'investment vehicle'
]

# --- CONFIG PROSPECÇÃO DINÂMICA ---
MAX_PROSPECTION_ATTEMPTS = 8
MIN_NEW_STARTUPS_REQUIRED = 3  # parar cedo se já conseguimos pelo menos isso de novos nomes

def build_prospect_task(existing_names: set, attempt: int):
    avoid_clause = ''
    if existing_names:
        # Limita a lista a 50 primeiros para não poluir prompt
        sample = list(existing_names)[:50]
        avoid_clause = ("Evite listar novamente estas startups já conhecidas (NÃO repita nenhuma delas; busque outras): "
                        + ", ".join(sample) + ".")
    return Task(
        description=(
            f"[TENTATIVA {attempt}] Sua missão é gerar a maior lista possível de NOMES NOVOS de startups de tecnologia (não repetir as já conhecidas). "
            "Combine as fontes abaixo em múltiplas buscas no Google. "
            f"Use portfólios de VCs: {', '.join(lista_vcs)}. "
            f"Use sites especializados com 'site:': {', '.join(lista_plataformas)}. "
            f"Foque em países: {', '.join(lista_paises_latam)}. "
            "NÃO adicione explicações, apenas nomes separados por vírgula. "
            "Varie buscas (mínimo 10). " + avoid_clause
        ),
        expected_output="Uma única string contendo apenas nomes de startups separados por vírgula.",
        agent=prospector_agent
    )

def build_qualify_task(raw_names: str):
    return Task(
        description=(
            "INSTRUÇÕES CRÍTICAS DE FILTRAGEM:\n"
            "1. REJEITAR TOTALMENTE qualquer startup dos Estados Unidos, EUA, USA, US, United States ou Silicon Valley\n"
            "2. ACEITAR APENAS startups com sede confirmada nos países da América Latina: Brasil, México, Argentina, Colômbia, Chile, Peru, Bolívia, Equador, Guiana, Paraguai, Suriname, Uruguai, Venezuela, Belize, Costa Rica, El Salvador, Guatemala, Honduras, Nicarágua, Panamá, Cuba, Haiti, República Dominicana\n"
            "3. VERIFICAR se é empresa de tecnologia/produto (não empresa de investimento)\n"
            "4. REJEITAR TOTALMENTE setores de investimento: Venture Capital, VC, Venture Builder, Investment, Investor, Fund, Capital, Private Equity, Asset Management, Financial Services (se for fundo)\n"
            "5. ACEITAR APENAS startups que desenvolvem produtos ou serviços tecnológicos\n\n"
            "Para cada nome da lista, pesquise e verifique rigorosamente a localização da sede e o setor de atuação. "
            "Responda APENAS com os nomes que atendem TODOS os critérios, separados por vírgula, sem texto adicional.\n\n"
            "Lista para verificar: " + raw_names[:6000]
        ),
        expected_output="Nomes de startups de tecnologia da América Latina aprovados, separados por vírgula.",
        agent=qualifier_agent
    )

JSON_SCHEMA_GUIDE = (
    "Responda APENAS em JSON puro (sem texto antes/depois) com as chaves exatas: "
    "['Nome da Startup','Site','Setor de Atuação','País','Legalmente Instituída','Ano de Fundação',"
    "'Tecnologias Utilizadas','Nome do Investidor (VC)','Valor da Última Rodada','Status de financiamento',"
    "'Liderança Técnica (Nome)','Liderança Técnica (LinkedIn)','Integrantes do Time','Tamanho da Startup',"
    "'Base de Clientes'] . Use string vazia se não encontrar."
)
MARKET_SCHEMA_GUIDE = (
    "Responda APENAS em JSON puro com as chaves: ['Nome da Startup','TAM','SAM','SOM','Dinâmica do Setor',"
    "'Principais Concorrentes','Previsões de Mercado','Análise de Riscos Ambientais','CAC','Churn Rate',"
    "'Fontes da Análise de Mercado'] . 'Fontes da Análise de Mercado' deve ser uma lista de URLs ou uma string com URLs separadas por ponto e vírgula."
)

def build_data_task(startup_name: str):
    return Task(
        description=(f"Para a startup '{startup_name}', encontre os dados fundamentais. IMPORTANTE: Verifique se a startup está realmente localizada na América Latina. Se descobrir que está nos EUA ou fora da América Latina, inclua essa informação no campo 'País'. {JSON_SCHEMA_GUIDE}"),
        expected_output=f"JSON válido com dados fundamentais da startup '{startup_name}', incluindo verificação de localização",
        agent=data_analyst_agent
    )

def build_market_task(startup_name: str):
    return Task(
        description=(f"Para a startup '{startup_name}', faça análise de mercado. {MARKET_SCHEMA_GUIDE}"),
        expected_output=f"JSON válido com análise de mercado da startup '{startup_name}'",
        agent=market_strategist_agent
    )

def merge_and_write(startup_name: str, outputs: list):
    """Tenta extrair JSON de cada saída, mesclar e enviar à planilha. Retorna mensagem."""
    merged = {'Nome da Startup': startup_name}
    json_blocks = []
    for raw in outputs:
        if not raw:
            continue
        candidate = None
        # Primeiro tentativa direta
        try:
            if isinstance(raw, str):
                candidate = json.loads(raw)
        except Exception:
            candidate = None
        if candidate is None:
            # Procura primeiro bloco JSON com regex
            try:
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    candidate = json.loads(match.group(0))
            except Exception:
                candidate = None
        if isinstance(candidate, dict):
            json_blocks.append(candidate)
    for block in json_blocks:
        for k,v in block.items():
            if v not in (None, '', 'Não encontrado'):
                merged[k] = v
    
    # VALIDAÇÃO FINAL: Rejeitar startups dos EUA
    pais = merged.get('País', '').lower()
    if any(termo in pais for termo in ['estados unidos', 'eua', 'usa', 'us', 'united states', 'silicon valley']):
        print(f"[MERGE] {startup_name}: REJEITADA - Startup dos EUA detectada: {merged.get('País', 'N/A')}")
        return f"Startup '{startup_name}' rejeitada - localizada nos EUA."
    
    # Validar se está na América Latina
    paises_latam_lower = [p.lower() for p in lista_paises_latam]
    if pais and not any(pais_latam in pais for pais_latam in paises_latam_lower):
        print(f"[MERGE] {startup_name}: REJEITADA - País fora da América Latina: {merged.get('País', 'N/A')}")
        return f"Startup '{startup_name}' rejeitada - não está na América Latina."
    
    # VALIDAÇÃO FINAL: Rejeitar setores de investimento
    setor = merged.get('Setor de Atuação', '').lower()
    if any(termo in setor for termo in setores_rejeitados_global):
        print(f"[MERGE] {startup_name}: REJEITADA - Setor de investimento detectado: {merged.get('Setor de Atuação', 'N/A')}")
        return f"Startup '{startup_name}' rejeitada - setor de investimento: {merged.get('Setor de Atuação', 'N/A')}."
    
    # Normaliza fontes: pode vir lista
    fontes = merged.get('Fontes da Análise de Mercado')
    if isinstance(fontes, list):
        merged['Fontes da Análise de Mercado'] = '; '.join(str(x) for x in fontes)
    # Envia para sheet
    result = spreadsheet_tool(json.dumps(merged))
    print(f"[MERGE] {startup_name}: {result} | Keys: {list(merged.keys())}")
    return result

def clean_invalid_startups():
    """Remove startups dos EUA e do setor Venture Capital da planilha."""
    print("🧹 Iniciando limpeza de startups inválidas...")
    
    try:
        # Busca todos os registros da planilha
        all_records = worksheet.get_all_records()
        rows_to_delete = []
        
        paises_rejeitados = ['estados unidos', 'eua', 'usa', 'us', 'united states', 'silicon valley']
        
        for i, record in enumerate(all_records, start=2):  # start=2 porque linha 1 é cabeçalho
            startup_name = record.get('Nome da Startup', '').strip()
            pais = record.get('País', '').lower().strip()
            setor = record.get('Setor de Atuação', '').lower().strip()
            
            # Verifica se é dos EUA
            is_usa = any(termo in pais for termo in paises_rejeitados)
            
            # Verifica se é do setor venture capital
            is_vc = any(termo in setor for termo in setores_rejeitados_global)
            
            if is_usa or is_vc:
                reason = "EUA" if is_usa else "Venture Capital"
                print(f"❌ Marcando para remoção: {startup_name} - Motivo: {reason} (País: {pais}, Setor: {setor})")
                rows_to_delete.append(i)
        
        # Remove as linhas (de trás para frente para não alterar os índices)
        if rows_to_delete:
            print(f"🗑️  Removendo {len(rows_to_delete)} startups inválidas...")
            for row_index in sorted(rows_to_delete, reverse=True):
                worksheet.delete_rows(row_index)
            print(f"✅ Limpeza concluída! {len(rows_to_delete)} startups removidas.")
        else:
            print("✅ Nenhuma startup inválida encontrada na planilha.")
            
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")

def safe_kickoff(crew: Crew, label: str, retries: int = 2):
    """Executa crew.kickoff com retentativas se não houver outputs válidos."""
    for attempt in range(1, retries+2):  # primeira + retries
        try:
            result = crew.kickoff()
            if result and getattr(result, 'tasks_output', None):
                # Verifica se algum task_output tem raw não vazio
                raws = [getattr(t, 'raw', '') for t in result.tasks_output]
                if any(r.strip() for r in raws):
                    return result
            if result and getattr(result, 'raw', None) and result.raw.strip():
                return result
            print(f"[safe_kickoff] '{label}' tentativa {attempt} sem outputs válidos.")
        except Exception as e:
            print(f"[safe_kickoff] Erro em '{label}' tentativa {attempt}: {e}")
        if attempt <= retries:
            print(f"[safe_kickoff] Retentando '{label}'...")
    print(f"[safe_kickoff] Falha definitiva em '{label}' após {retries+1} tentativas.")
    return None

# --- FLUXO DE TRABALHO PRINCIPAL ---
if __name__ == '__main__':
    print("Iniciando fluxo de trabalho completo...")
    
    # ETAPA 1: Limpeza de dados inválidos
    clean_invalid_startups()
    
    # Atualiza a lista após limpeza
    existing_startups = set(worksheet.col_values(1))
    print(f"Startups na planilha após limpeza: {len(existing_startups)}")

    all_new_qualified = []
    attempted_names = set()

    for attempt in range(1, MAX_PROSPECTION_ATTEMPTS + 1):
        prospect_task = build_prospect_task(existing_startups.union(attempted_names), attempt)
        prospect_crew = Crew(
            agents=[prospector_agent],
            tasks=[prospect_task],
            process=Process.sequential,
            verbose=False
        )
        print(f"\n[Prospecção] Executando tentativa {attempt}...")
        prospect_result = safe_kickoff(prospect_crew, f"Prospecção {attempt}")
        raw_names = prospect_result.raw if (prospect_result and getattr(prospect_result,'raw', None)) else ''
        # Normaliza splits
        raw_candidates = [n.strip() for n in raw_names.split(',') if n.strip()]
        # Remove já existentes e já tentados
        new_candidates = [n for n in raw_candidates if n not in existing_startups and n not in attempted_names]
        attempted_names.update(raw_candidates)
        if not new_candidates:
            print("Nenhum nome novo bruto nesta tentativa.")
            continue
        qualify_task = build_qualify_task(', '.join(new_candidates))
        qualify_crew = Crew(
            agents=[qualifier_agent],
            tasks=[qualify_task],
            process=Process.sequential,
            verbose=False
        )
        print(f"[Qualificação] Verificando {len(new_candidates)} candidatos novos...")
        qualify_result = safe_kickoff(qualify_crew, f"Qualificação {attempt}")
        qualified_str = qualify_result.raw if (qualify_result and getattr(qualify_result,'raw', None)) else ''
        qualified_list = [n.strip() for n in qualified_str.split(',') if n.strip()]
        qualified_new_unique = [n for n in qualified_list if n not in existing_startups and n not in all_new_qualified]
        print(f"[Qualificação] Novos aprovados nesta tentativa: {qualified_new_unique}")
        all_new_qualified.extend(qualified_new_unique)
        if len(all_new_qualified) >= MIN_NEW_STARTUPS_REQUIRED:
            print("Critério mínimo de novas startups atingido. Encerrando prospecção.")
            break

    print(f"Total final de novas startups qualificadas: {all_new_qualified}")

    # ETAPA 2: Análise Apenas das Novas
    for name in all_new_qualified:
        print(f"\n>>> Iniciando análise profunda para: {name} <<<")
        task_analyze_data = build_data_task(name)
        task_analyze_market = build_market_task(name)
        analysis_crew = Crew(
            agents=[data_analyst_agent, market_strategist_agent],
            tasks=[task_analyze_data, task_analyze_market],
            process=Process.sequential,
            verbose=True
        )
        analysis_result = analysis_crew.kickoff()
        outputs = []
        try:
            if analysis_result and getattr(analysis_result, 'tasks_output', None):
                outputs = [t.raw for t in analysis_result.tasks_output if getattr(t,'raw', None)]
            else:
                if getattr(analysis_result, 'raw', None):
                    outputs = [analysis_result.raw]
        except Exception as e:
            print(f"Falha ao coletar outputs: {e}")
        merge_and_write(name, outputs)
        print(f"Conclusão para '{name}'.")

    print("\n\n########################")
    print("## Processo finalizado!")
    print("########################")