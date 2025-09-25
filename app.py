# Importações necessárias
import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import google.generativeai as genai
import os
from datetime import datetime, date
import json
import base64
from io import BytesIO
import numpy as np

# Carrega as chaves do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NVIDIA Inception LatAm Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        border-left: 5px solid #76B900;
        margin: 0.5rem 0;
    }
    .startup-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .similar-btn {
        background-color: #76B900;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
    }
    .report-section {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BACKEND ---

# Conecta com o Google Sheets e busca os dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados():
    try:
        # Para rodar localmente
        gc = gspread.service_account(filename='credentials.json')
    except FileNotFoundError:
        # Para deploy no Streamlit Cloud, usando os Secrets
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        
    planilha = gc.open("Base de Startups NVIDIA")
    aba = planilha.sheet1
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)
    
    # Limpeza e processamento dos dados
    df = df.replace('', pd.NA).replace('Não encontrado', pd.NA)
    df['Ano de Fundação'] = pd.to_numeric(df['Ano de Fundação'], errors='coerce')
    
    # Adicionar coluna de idade da startup
    current_year = datetime.now().year
    df['Idade'] = current_year - df['Ano de Fundação']
    
    return df

# Função para calcular KPIs dinâmicos
def calcular_kpis(df):
    total_startups = len(df)
    
    # País com mais startups
    if not df['País'].isna().all():
        pais_top = df['País'].value_counts().index[0]
        count_pais_top = df['País'].value_counts().iloc[0]
    else:
        pais_top = "N/A"
        count_pais_top = 0
    
    # Setor mais comum
    if not df['Setor de Atuação'].isna().all():
        setor_top = df['Setor de Atuação'].value_counts().index[0]
        count_setor_top = df['Setor de Atuação'].value_counts().iloc[0]
    else:
        setor_top = "N/A"
        count_setor_top = 0
    
    # Startups "jovens" (últimos 3 anos)
    current_year = datetime.now().year
    startups_recentes = len(df[df['Ano de Fundação'] >= current_year - 3])
    
    return total_startups, pais_top, count_pais_top, setor_top, count_setor_top, startups_recentes

# Função para o chat interagir com o modelo de IA
def perguntar_ao_modelo(pergunta, contexto_dados):
    try:
        # Configurar API do Gemini
        try:
            # Para deploy no Streamlit Cloud
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        except KeyError:
            # Para rodar localmente
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Você é um assistente especialista em análise de startups para a NVIDIA Inception.
        
        Responda à pergunta do usuário usando APENAS os dados fornecidos abaixo.
        Seja claro, direto e formate listas como tabelas em Markdown quando apropriado.
        
        Se a pergunta for sobre gráficos ou visualizações, responda com sugestões de análise,
        mas não tente criar código.
        
        Dados das startups:
        {contexto_dados}
        
        Pergunta: {pergunta}
        """
        
        resposta = model.generate_content(prompt)
        return resposta.text
        
    except Exception as e:
        return f"Erro ao processar pergunta: {str(e)}"

# Função para encontrar startups similares
def encontrar_similares(startup_selecionada, df, modelo):
    try:
        startup_data = df[df['Nome da Startup'] == startup_selecionada].iloc[0]
        
        prompt = f"""
        Com base nas startups listadas abaixo, encontre as 3 mais similares à startup "{startup_selecionada}".
        
        Características da startup de referência:
        - Setor: {startup_data.get('Setor de Atuação', 'N/A')}
        - País: {startup_data.get('País', 'N/A')}
        - Tecnologias: {startup_data.get('Tecnologias Usadas', 'N/A')}
        
        Lista de todas as startups:
        {df[['Nome da Startup', 'Setor de Atuação', 'País', 'Tecnologias Usadas']].to_string(index=False)}
        
        Responda APENAS com os nomes das 3 startups mais similares, separados por vírgula.
        Não inclua a startup de referência na resposta.
        """
        
        resposta = modelo.generate_content(prompt)
        similares = [nome.strip() for nome in resposta.text.split(',')]
        return similares[:3]  # Garantir máximo 3
        
    except Exception as e:
        return [f"Erro: {str(e)}"]

# Função para criar card de startup
def criar_card_startup(startup_row, show_similar_btn=False):
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="startup-card">
                <h4>🚀 {startup_row.get('Nome da Startup', 'N/A')}</h4>
                <p><strong>País:</strong> {startup_row.get('País', 'N/A')}</p>
                <p><strong>Setor:</strong> {startup_row.get('Setor de Atuação', 'N/A')}</p>
                <p><strong>Fundação:</strong> {startup_row.get('Ano de Fundação', 'N/A')} 
                   ({startup_row.get('Idade', 'N/A')} anos)</p>
                <p><strong>Tecnologias:</strong> {startup_row.get('Tecnologias Usadas', 'N/A')}</p>
                <p><strong>Website:</strong> 
                   <a href="{startup_row.get('Website', '#')}" target="_blank">
                   {startup_row.get('Website', 'N/A')}</a></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            col_add, col_similar = st.columns(2)
            
            with col_add:
                if st.button("⭐ Adicionar", key=f"add_{startup_row.get('Nome da Startup', 'unknown')}"):
                    if 'relatorio_startups' not in st.session_state:
                        st.session_state.relatorio_startups = []
                    
                    if startup_row.get('Nome da Startup') not in [s.get('Nome da Startup') for s in st.session_state.relatorio_startups]:
                        st.session_state.relatorio_startups.append(dict(startup_row))
                        st.success("Adicionada ao relatório!")
                    else:
                        st.warning("Já está no relatório!")
            
            if show_similar_btn:
                with col_similar:
                    if st.button("🔍 Similares", key=f"similar_{startup_row.get('Nome da Startup', 'unknown')}"):
                        st.session_state.show_similar = startup_row.get('Nome da Startup')

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'relatorio_startups' not in st.session_state:
    st.session_state.relatorio_startups = []

if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- INÍCIO DA INTERFACE GRÁFICA ---
st.title("🤖 NVIDIA Inception: Dashboard Proativo de Startups LatAm")

# Carrega os dados
try:
    df = carregar_dados()
    total_startups, pais_top, count_pais_top, setor_top, count_setor_top, startups_recentes = calcular_kpis(df)
    
    # --- SIDEBAR COM FILTROS ---
    with st.sidebar:
        st.header("🔍 Filtros de Exploração")
        
        # Filtro por países
        paises_disponiveis = df['País'].dropna().unique().tolist()
        paises_selecionados = st.multiselect(
            "Filtre por País:", 
            paises_disponiveis,
            default=paises_disponiveis[:5]  # Primeiros 5 por padrão
        )
        
        # Filtro por ano de fundação
        ano_min = int(df['Ano de Fundação'].min()) if not df['Ano de Fundação'].isna().all() else 2010
        ano_max = int(df['Ano de Fundação'].max()) if not df['Ano de Fundação'].isna().all() else 2025
        
        anos_selecionados = st.slider(
            "Ano de Fundação:", 
            min_value=ano_min, 
            max_value=ano_max, 
            value=(ano_min, ano_max)
        )
        
        # Filtro por setor
        setores_disponiveis = ['Todos'] + df['Setor de Atuação'].dropna().unique().tolist()
        setor_selecionado = st.selectbox("Selecione o Setor:", setores_disponiveis)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if paises_selecionados:
            df_filtrado = df_filtrado[df_filtrado['País'].isin(paises_selecionados)]
        
        df_filtrado = df_filtrado[
            (df_filtrado['Ano de Fundação'] >= anos_selecionados[0]) & 
            (df_filtrado['Ano de Fundação'] <= anos_selecionados[1])
        ]
        
        if setor_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Setor de Atuação'] == setor_selecionado]
        
        st.markdown("---")
        
        # --- SEÇÃO DO RELATÓRIO ---
        st.header("📋 Relatório Personalizado")
        
        if st.session_state.relatorio_startups:
            st.write(f"**{len(st.session_state.relatorio_startups)} startups selecionadas**")
            
            for startup in st.session_state.relatorio_startups:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {startup.get('Nome da Startup', 'N/A')}")
                with col2:
                    if st.button("❌", key=f"remove_{startup.get('Nome da Startup', 'unknown')}"):
                        st.session_state.relatorio_startups.remove(startup)
                        st.rerun()
            
            if st.button("📄 Exportar CSV"):
                df_relatorio = pd.DataFrame(st.session_state.relatorio_startups)
                csv = df_relatorio.to_csv(index=False)
                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=csv,
                    file_name=f"relatorio_startups_{date.today()}.csv",
                    mime="text/csv"
                )
            
            if st.button("🗑️ Limpar Relatório"):
                st.session_state.relatorio_startups = []
                st.rerun()
        else:
            st.write("Nenhuma startup selecionada")
            st.write("Use o botão ⭐ para adicionar startups ao seu relatório personalizado.")
    
    # --- DASHBOARD PRINCIPAL ---
    
    # KPIs no topo
    st.subheader("📊 KPIs em Tempo Real")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Startups Mapeadas",
            value=f"{len(df_filtrado)}",
            delta=f"{len(df_filtrado) - total_startups}" if len(df_filtrado) != total_startups else None
        )
    
    with col2:
        st.metric(
            label=f"País: {pais_top}",
            value=f"{count_pais_top} startups"
        )
    
    with col3:
        st.metric(
            label=f"Setor: {setor_top}",
            value=f"{count_setor_top} startups"
        )
    
    with col4:
        st.metric(
            label="Startups Jovens (≤3 anos)",
            value=f"{startups_recentes}"
        )
    
    st.markdown("---")
    
    # Criar abas principais
    tab1, tab2, tab3 = st.tabs(["📈 Visualizações", "🤖 Chat Inteligente", "🔍 Explorar Startups"])
    
    # --- TAB 1: VISUALIZAÇÕES ---
    with tab1:
        if len(df_filtrado) > 0:
            col1, col2 = st.columns(2)
            
            # Gráfico de barras por país
            with col1:
                st.subheader("🌎 Startups por País")
                pais_counts = df_filtrado['País'].value_counts().reset_index()
                pais_counts.columns = ['País', 'Quantidade']
                
                fig_pais = px.bar(
                    pais_counts, 
                    x='País', 
                    y='Quantidade',
                    color='Quantidade',
                    color_continuous_scale='Viridis'
                )
                fig_pais.update_layout(height=400)
                st.plotly_chart(fig_pais, use_container_width=True)
            
            # Gráfico de pizza por setor
            with col2:
                st.subheader("🏢 Distribuição por Setor")
                setor_counts = df_filtrado['Setor de Atuação'].value_counts().reset_index()
                
                fig_setor = px.pie(
                    setor_counts, 
                    names='Setor de Atuação', 
                    values='count',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_setor.update_layout(height=400)
                st.plotly_chart(fig_setor, use_container_width=True)
            
            # Gráfico de linha temporal
            st.subheader("📅 Evolução Temporal das Fundações")
            if not df_filtrado['Ano de Fundação'].isna().all():
                timeline_data = df_filtrado['Ano de Fundação'].value_counts().reset_index().sort_values('Ano de Fundação')
                
                fig_timeline = px.line(
                    timeline_data, 
                    x='Ano de Fundação', 
                    y='count',
                    title="Número de Startups Fundadas por Ano",
                    markers=True
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Mapa de calor (simulado com gráfico de barras horizontal)
            st.subheader("🗺️ Mapa de Calor - Concentração por Região")
            if len(pais_counts) > 0:
                fig_map = px.bar(
                    pais_counts.head(10), 
                    x='Quantidade', 
                    y='País',
                    orientation='h',
                    color='Quantidade',
                    color_continuous_scale='Reds',
                    title="Top 10 Países por Concentração de Startups"
                )
                fig_map.update_layout(height=500)
                st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Nenhum dado corresponde aos filtros selecionados.")
    
    # --- TAB 2: CHAT INTELIGENTE ---
    with tab2:
        st.subheader("💬 Converse com os Dados")
        st.write("Faça perguntas em linguagem natural e receba insights personalizados!")
        
        # Sugestões de perguntas
        st.write("**💡 Perguntas sugeridas:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Quais startups do Brasil usam IA?"):
                pergunta_sugerida = "Quais startups do Brasil usam IA?"
        
        with col2:
            if st.button("Top 5 setores mais ativos"):
                pergunta_sugerida = "Quais são os top 5 setores mais ativos?"
        
        with col3:
            if st.button("Startups fundadas em 2023"):
                pergunta_sugerida = "Quais startups foram fundadas em 2023?"
        
        # Exibir mensagens do chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Se a mensagem contém dados de startup, mostrar gráficos
                if message["role"] == "assistant" and "startups" in message["content"].lower():
                    # Aqui poderia adicionar lógica para gerar gráficos baseados na resposta
                    pass
        
        # Input do chat
        if prompt := st.chat_input("Ex: Quais startups de fintech temos no México?"):
            # Adicionar pergunta ao histórico
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Gerar resposta
            with st.chat_message("assistant"):
                with st.spinner("🤖 Analisando dados..."):
                    contexto_dados = df_filtrado.to_string(index=False)
                    resposta = perguntar_ao_modelo(prompt, contexto_dados)
                    st.markdown(resposta)
                    
                    # Adicionar funcionalidade de gráficos baseados na pergunta
                    if any(word in prompt.lower() for word in ['gráfico', 'visualizar', 'mostrar']):
                        if 'país' in prompt.lower():
                            fig = px.bar(df_filtrado['País'].value_counts().head(10))
                            st.plotly_chart(fig, use_container_width=True)
                        elif 'setor' in prompt.lower():
                            fig = px.pie(df_filtrado['Setor de Atuação'].value_counts())
                            st.plotly_chart(fig, use_container_width=True)
            
            # Adicionar resposta ao histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta})
    
    # --- TAB 3: EXPLORAR STARTUPS ---
    with tab3:
        st.subheader("🔍 Explorar Startups Individualmente")
        
        if len(df_filtrado) > 0:
            # Mostrar startups como cards
            for idx, (_, startup) in enumerate(df_filtrado.iterrows()):
                criar_card_startup(startup, show_similar_btn=True)
                
                # Mostrar startups similares se solicitado
                if 'show_similar' in st.session_state and st.session_state.show_similar == startup.get('Nome da Startup'):
                    st.markdown("### 🔍 Startups Similares")
                    
                    try:
                        # Configurar modelo para busca de similares
                        try:
                            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        except KeyError:
                            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                        
                        modelo = genai.GenerativeModel('gemini-pro')
                        similares = encontrar_similares(startup.get('Nome da Startup'), df, modelo)
                        
                        for similar_name in similares:
                            similar_startup = df[df['Nome da Startup'] == similar_name.strip()]
                            if not similar_startup.empty:
                                criar_card_startup(similar_startup.iloc[0], show_similar_btn=False)
                        
                        if st.button("❌ Fechar Similares", key=f"close_similar_{idx}"):
                            if 'show_similar' in st.session_state:
                                del st.session_state.show_similar
                    
                    except Exception as e:
                        st.error(f"Erro ao buscar similares: {str(e)}")
                
                st.markdown("---")
        else:
            st.warning("Nenhuma startup encontrada com os filtros atuais.")

except Exception as e:
    st.error(f"""
    ❌ **Erro ao carregar os dados**
    
    Verifique se:
    - O arquivo `credentials.json` está no diretório correto
    - A planilha "Base de Startups NVIDIA" existe e está acessível
    - As credenciais têm permissão para acessar a planilha
    
    **Detalhes técnicos:** {str(e)}
    """)
    
    # Mostrar dados de exemplo para demonstração
    st.info("📋 **Modo Demonstração**: Usando dados simulados para preview das funcionalidades")
    
    # Dados de exemplo para demonstração
    dados_exemplo = {
        'Nome da Startup': ['TechAI Brasil', 'FinLat Mexico', 'HealthTech Argentina'],
        'País': ['Brasil', 'México', 'Argentina'],
        'Setor de Atuação': ['IA Generativa', 'Fintech', 'Healthtech'],
        'Ano de Fundação': [2020, 2021, 2019],
        'Website': ['techbrasil.com', 'finlat.mx', 'healtharg.com'],
        'Tecnologias Usadas': ['Machine Learning, NLP', 'Blockchain, API', 'IoT, Data Analytics']
    }
    
    df_exemplo = pd.DataFrame(dados_exemplo)
    df_exemplo['Idade'] = 2025 - df_exemplo['Ano de Fundação']
    
    st.subheader("🎯 Preview das Funcionalidades")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Simulado", "3")
    with col2:
        st.metric("País Top", "Brasil")
    with col3:
        st.metric("Setor Top", "IA Generativa")
    with col4:
        st.metric("Startups Jovens", "3")
    
    st.dataframe(df_exemplo)