
<img src="static\images\Slide 16_9 - 17.png">

# Inception-match

Plataforma para explorar, prospectar e avaliar startups — com dashboard, integração a Google Sheets e um chatbot de insights que usa a API Serper.

<div align="center">

<img src="static\images\img.png" width="300px">

</div>

**Case proposto pela NVIDIA + Inteli Academy:** como a NVIDIA pode transformar o desafio da fragmentação de informações em uma oportunidade estratégica, utilizando da inteligência artificial para mapear tendências, identificar as startups de maior potencial na América Latina e fortalecer ainda mais a posição do Inception como referência global no apoio à inovação?

Badges
------

| Build | License | Version |
|---|---|---|
| ✅ local | MIT | v0.1.0 |

Índice
------

- [Contexto / Motivação](#contexto--motivação)
- [Funcionalidades](#funcionalidades)
- [Demonstração](#demonstração)
- [Como rodar localmente (Setup)](#como-rodar-localmente-setup)
- [Uso / Endpoints Principais](#uso--endpoints-principais)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Segurança e Secrets](#segurança-e-secrets)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Autores / Créditos](#autores--créditos)

Contexto / Motivação
---------------------

Este projeto foi criado para facilitar a prospecção, qualificação e análise de startups (com foco em América Latina), combinando:

- Automação de prospecção via agentes (CrewAI) e ferramentas de busca
- Consolidação e armazenamento em Google Sheets
- Painel de controle (dashboard) com estatísticas e tabela de startups
- Chat interativo que usa a API Serper para responder perguntas e citar fontes

Problema que resolve:

- Centraliza dados de startups coletadas automaticamente
- Fornece interface simples para analisar e consultar (por humanos ou agentes)

Funcionalidades
---------------

- Dashboard com estatísticas e tabela de startups
- Integração com Google Sheets para leitura/escrita
- Pipeline de prospecção/qualificação via CrewAI (scripts em `main.py`)
- Chat de insights (`/insights`) que consulta a Serper e exibe fontes
- Botões de sugestão e mensagens com feedback visual

<img src="static\images\img.gif">

Demonstração
-----------

Abra a rota `/insights` no servidor local para ver o chat e `/` para o dashboard.

Como rodar localmente (Setup)
-----------------------------

Pré-requisitos

- Python 3.8+
- Virtualenv (recomendado)
- Conta e credenciais do Google (para uso do Google Sheets)

Passos

1. Clone o repositório:

```bash
git clone https://github.com/anneestherlf/inception-match.git
cd inception-match
```

2. Crie um ambiente virtual e instale dependências:

```bash
python -m venv .venv
source .venv/bin/activate    # macOS / Linux
.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

3. Configurar variáveis de ambiente (arquivo `.env` local ou variáveis de ambiente do sistema)

Exemplo mínimo `.env` (NÃO COMMITAR este arquivo no git):

```properties
SERPER_API_KEY="<sua_serper_key>"
GOOGLE_API_KEY="<sua_google_key>"
# outras chaves opcionais: OPENAI_API_KEY, GEMINI_API_KEY
```

4. Coloque `credentials.json` do Google Service Account na raiz (apenas localmente) para `gspread` acessar a planilha.

5. Inicie o servidor Flask (desenvolvimento):

```powershell
python app.py
```

Uso / Endpoints Principais
--------------------------

- `GET /` — Dashboard principal (templates/dashboard.html)
- `GET /insights` — Interface do chatbot (templates/insights.html)
- `GET /api/startups` — Retorna startups formatadas (JSON)
- `GET /api/statistics` — Retorna estatísticas calculadas (JSON)
- `POST /api/chat` — Recebe JSON { message } e retorna JSON { answer, raw, sources }

Exemplo de uso do `/api/chat` (fetch):

```js
fetch('/api/chat', {
	method: 'POST',
	headers: { 'Content-Type': 'application/json' },
	body: JSON.stringify({ message: 'Quais startups de IA no Brasil?' })
}).then(r => r.json()).then(console.log)
```

Tecnologias Utilizadas
----------------------

- Python + Flask — servidor HTTP e endpoints
- CrewAI / crewai-tools — automação de agentes para prospecção/qualificação (em `main.py`)
- gspread — integração com Google Sheets
- requests — chamadas HTTP para Serper
- HTML/CSS/JS (templates + static) — UI
- Dependências listadas em `requirements.txt`

Estrutura de Pastas
-------------------

```
.
├── app.py                  # Servidor Flask principal e APIs
├── main.py                 # Pipelines com CrewAI para prospecção/qualificação
├── templates/
│   ├── dashboard.html
│   └── insights.html       # Chat UI
├── static/
│   ├── css/
│   │   └── style-insights.css
│   └── js/
│       └── dashboard.js
├── credentials.json        # (não versionar) Google Service Account
├── .env                    # (não versionar) arquivo de chaves
├── requirements.txt
└── README.md
```

Segurança e Secrets
-------------------

ATENÇÃO: o repositório contém exemplos de variáveis de ambiente. NÃO commite chaves sensíveis.

Recomendações imediatas de segurança:

1. Remover `.env` do repositório e adicioná-lo ao `.gitignore`.
2. Rotacionar chaves que já foram expostas.
3. Armazenar secrets em um secret manager (Azure Key Vault, AWS Secrets Manager, GitHub Secrets para CI).
4. Nunca incluir `credentials.json` em commits.

Licença
-------

Este projeto está licenciado sob a Licença MIT — veja o arquivo `LICENSE` para detalhes.

Autores / Créditos
------------------

- Repositório original: anneestherlf/inception-match
- Ferramentas: CrewAI, Serper, gspread
- Autora: Anne Esther Lins Figueirôa (<https://www.linkedin.com/in/anneestherlf/>)


Contato
-------

Se precisar de ajuda, descreva o problema no GitHub issues ou envie uma mensagem ao mantenedor.

Obrigada!

