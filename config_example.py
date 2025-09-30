"""
Arquivo de configuração de exemplo para o Dashboard Inception-match
Copie este arquivo para config.py e ajuste as configurações conforme necessário
"""

# Configurações do Google Sheets
GOOGLE_SHEETS_CONFIG = {
    'spreadsheet_name': 'Base de Startups NVIDIA',
    'worksheet_name': 'Sheet1',  # ou o nome da aba específica
    'credentials_file': 'credentials.json'
}

# Configurações do Flask
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Configurações do Dashboard
DASHBOARD_CONFIG = {
    'title': 'Inception-match',
    'refresh_interval': 300000,  # 5 minutos em millisegundos
    'max_startups_display': 100,  # Máximo de startups na tabela
    'default_language': 'pt-BR'
}

# Configurações de API
API_CONFIG = {
    'timeout': 30,  # Timeout para requisições em segundos
    'retry_attempts': 3,  # Tentativas de retry
    'cache_duration': 300  # Cache em segundos
}

# Configurações de UI
UI_CONFIG = {
    'theme': 'dark',
    'primary_color': '#00FF88',
    'background_color': '#0a0a0a',
    'card_background': '#1a1a1a',
    'text_color': '#ffffff',
    'secondary_text_color': '#888888'
}

# Configurações de notificações
NOTIFICATION_CONFIG = {
    'enabled': True,
    'sound_enabled': False,
    'desktop_notifications': False
}

# Configurações de logs
LOG_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'file': 'dashboard.log',
    'max_size': '10MB',
    'backup_count': 5
}
