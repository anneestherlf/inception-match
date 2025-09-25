# Importações necessárias (incluindo a do Gemini)
import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega as chaves do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NVIDIA Inception LatAm Dashboard",
    page_icon="🤖",
    layout="wide"
)

# --- FUNÇÕES DE BACKEND ---

# Conecta com o Google Sheets e busca os dados
@st.cache_data(ttl=600)
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
    df['Ano de Fundação'] = pd.to_numeric(df['Ano de Fundação'], errors='coerce')
    return df

# Função para o chat interagir com o modelo de IA
def perguntar_ao_modelo(pergunta, contexto_dados):
    # Configura o modelo de IA (Gemini do Google) usando os Secrets
    try:
        # Para deploy no Streamlit Cloud
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except KeyError:
        # Para rodar localmente, busca do arquivo .env
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Você é um assistente especialista em análise de startups para a NVIDIA.
    Responda à pergunta do usuário usando apenas os dados fornecidos abaixo.
    Seja claro, direto e, se a resposta contiver uma lista, formate-a como uma tabela em Markdown. Não mostre código.
    Dados:
    {contexto_dados}
    Pergunta:
    {pergunta}
    """
    resposta = model.generate_content(prompt)
    return resposta.text

# --- INÍCIO DA INTERFACE GRÁFICA ---

st.title("🤖 NVIDIA Inception: Análise de Startups na América Latina")

# Carrega os dados uma vez
try:
    df = carregar_dados()

    # Cria a estrutura de Abas
    tab1, tab2 = st.tabs(["📊 Dashboard de Análise", "💬 Chat Interativo"])

    # --- Conteúdo da Aba 1: DASHBOARD ---
    with tab1:
        st.header("Visão Geral do Ecossistema")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Startups Mapeadas", f"{len(df)}")
        col2.metric("País com Mais Startups", df['País'].mode()[0] if not df['País'].empty else "N/A")
        col3.metric("Setor Mais Comum", df['Setor de Atuação'].mode()[0] if not df['Setor de Atuação'].empty else "N/A")
        col4.metric("Fundada Mais Recentemente", f"{int(df['Ano de Fundação'].max())}" if not df['Ano de Fundação'].dropna().empty else "N/A")

        # Gráficos...
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.write("##### Startups por País")
            fig_pais = px.bar(df['País'].value_counts().reset_index(), x='País', y='count', labels={'count':'Número de Startups'})
            st.plotly_chart(fig_pais, use_container_width=True)
        with col_graf2:
            st.write("##### Startups por Setor")
            fig_setor = px.pie(df['Setor de Atuação'].value_counts().reset_index(), names='Setor de Atuação', values='count')
            st.plotly_chart(fig_setor, use_container_width=True)

        st.header("Explore os Dados")
        st.dataframe(df) # Exibe a tabela completa

    # --- Conteúdo da Aba 2: CHAT ---
    with tab2:
        st.header("Converse com os Dados")
        st.write("Faça perguntas em linguagem natural sobre o ecossistema de startups.")

        # Inicializa o histórico do chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Exibe as mensagens do histórico
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input do usuário
        if prompt := st.chat_input("Ex: Quais startups do Brasil usam IA Generativa?"):
            # Adiciona a mensagem do usuário ao histórico e exibe
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Gera e exibe a resposta do assistente
            with st.chat_message("assistant"):
                with st.spinner("Analisando..."):
                    contexto_dados_string = df.to_string(index=False)
                    resposta = perguntar_ao_modelo(prompt, contexto_dados_string)
                    st.markdown(resposta)
            
            # Adiciona a resposta do assistente ao histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta})

except Exception as e:
    st.error(f"Erro ao carregar os dados. Verifique a conexão com a planilha e suas credenciais. Detalhes: {e}")