# Inception-match Dashboard

Dashboard web para visualização de dados de startups coletados pela NVIDIA.

## 🚀 Funcionalidades

- **Dashboard Dark Theme**: Interface idêntica ao design fornecido
- **Integração com Google Sheets**: Conecta diretamente com a planilha "Base de Startups NVIDIA"
- **Estatísticas em Tempo Real**: Total de startups, setores e países principais
- **Tabela Interativa**: Lista completa de startups com dados detalhados
- **Filtros**: Sistema de filtros para análise de dados

## 📋 Pré-requisitos

1. **Python 3.8+**
2. **Google Sheets API**: Arquivo `credentials.json` configurado
3. **Planilha**: "Base de Startups NVIDIA" no Google Sheets

## 🛠️ Instalação

1. **Clone o repositório**:
```bash
git clone <seu-repositorio>
cd inception-agent
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure o Google Sheets**:
   - Certifique-se de que o arquivo `credentials.json` está na raiz do projeto
   - A planilha "Base de Startups NVIDIA" deve estar compartilhada com a conta de serviço

4. **Execute o dashboard**:
```bash
python app.py
```

5. **Acesse no navegador**:
```
http://localhost:5000
```

## 📊 Estrutura dos Dados

O dashboard consome dados da planilha Google Sheets com as seguintes colunas:

- Nome da Startup
- Site
- Setor de Atuação
- País
- Legalmente Instituída
- Ano de Fundação
- Tecnologias Utilizadas
- Nome do Investidor (VC)
- Valor da Última Rodada
- Status do Financiamento
- Liderança Técnica (Nome)
- Liderança Técnica (LinkedIn)
- Integrantes do Time
- Tamanho da Startup
- Base de Clientes
- TAM
- SAM
- SOM
- Dinâmica do Setor
- Principais Concorrentes
- Previsões de Mercado
- Análise de Riscos Ambientais
- CAC
- Churn Rate
- Fontes da Análise de Mercado

## 🔧 Arquitetura

```
inception-agent/
├── app.py                 # Servidor Flask principal
├── main.py               # Script de coleta de dados (CrewAI)
├── templates/
│   └── dashboard.html    # Template HTML principal
├── static/
│   ├── css/
│   │   └── style.css     # Estilos CSS
│   └── js/
│       └── dashboard.js  # JavaScript do dashboard
├── requirements.txt       # Dependências Python
└── credentials.json      # Credenciais Google Sheets
```

## 📡 APIs

### GET `/api/startups`
Retorna lista de startups formatada para a tabela.

### GET `/api/statistics`
Retorna estatísticas gerais (total, setores, países).

## 🚀 Executando o Coletor de Dados

Para coletar novos dados de startups:

```bash
python main.py
```

Este script usa CrewAI para:
1. Prospecção de startups
2. Qualificação de leads
3. Análise de dados
4. Atualização da planilha

## 🔒 Segurança

- Credenciais do Google Sheets em arquivo separado
- Variáveis de ambiente para chaves API
- Validação de dados de entrada

## 📱 Responsividade

O dashboard é totalmente responsivo e funciona em:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🐛 Troubleshooting

### Erro de conexão com Google Sheets
- Verifique se `credentials.json` está presente
- Confirme se a planilha está compartilhada com a conta de serviço

### Dados não carregam
- Verifique a conexão com a internet
- Confirme se a planilha tem dados nas colunas esperadas

### Estilos não aplicam
- Limpe o cache do navegador
- Verifique se os arquivos CSS estão sendo servidos

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.
