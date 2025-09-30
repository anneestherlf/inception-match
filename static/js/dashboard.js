// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Atualizar data e hora
    updateDateTime();
    setInterval(updateDateTime, 60000); // Atualiza a cada minuto

    // Carregar dados do dashboard
    loadDashboardData();
    
    // Configurar eventos dos botões
    setupEventListeners();
});

function updateDateTime() {
    const now = new Date();
    const options = { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    const dateTimeString = now.toLocaleDateString('pt-BR', options);
    document.getElementById('current-datetime').textContent = dateTimeString;
}

async function loadDashboardData() {
    try {
        // Carregar estatísticas (com cache-busting)
        const statsResponse = await fetch(`/api/statistics?t=${Date.now()}`);
        const stats = await statsResponse.json();
        updateStatistics(stats);

        // Carregar dados das startups (com cache-busting)
        const startupsResponse = await fetch(`/api/startups?t=${Date.now()}`);
        const startups = await startupsResponse.json();
        updateStartupsTable(startups);

    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        showError('Erro ao carregar dados do dashboard');
    }
}

function updateStatistics(stats) {
    // Atualizar total de startups
    document.getElementById('total-startups').textContent = stats.total_startups;
    document.getElementById('last-update').textContent = `Última atualização ${stats.last_update}`;

    // Atualizar top setores
    const sectorsContainer = document.getElementById('top-sectors');
    sectorsContainer.innerHTML = '';
    
    stats.top_sectors.forEach((sector, index) => {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.innerHTML = `
            <span class="rank">${index + 1}°</span>
            <span class="name">${sector.name}</span>
            <span class="count">${sector.count}</span>
        `;
        sectorsContainer.appendChild(item);
    });

    // Atualizar top países
    const countriesContainer = document.getElementById('top-countries');
    countriesContainer.innerHTML = '';
    
    stats.top_countries.forEach((country, index) => {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.innerHTML = `
            <span class="rank">${index + 1}°</span>
            <span class="name">${country.name}</span>
            <span class="count">${country.count}</span>
        `;
        countriesContainer.appendChild(item);
    });
}

function updateStartupsTable(startups) {
    const tbody = document.getElementById('startups-table-body');
    tbody.innerHTML = '';

    startups.forEach(startup => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${startup.nome || 'Não informado'}</strong></td>
            <td>${startup.investidor || 'Não informado'}</td>
            <td>${startup.status || 'Não disponível'}</td>
            <td>${startup.pais || 'Não informado'}</td>
            <td>€ ${startup.tam || '0.00'}</td>
            <td>${startup.setor || 'Não informado'}</td>
        `;
        tbody.appendChild(row);
    });
}

function setupEventListeners() {
    // Botão GitHub
    const githubBtn = document.querySelector('.action-btn:nth-child(1)');
    githubBtn.addEventListener('click', () => {
        window.open('https://github.com/anneestherlf/inception-agents', '_blank');
    });

    // Botão Base de Dados
    const databaseBtn = document.querySelector('.action-btn:nth-child(2)');
    databaseBtn.addEventListener('click', () => {
        window.open('https://docs.google.com/spreadsheets/d/1vTNdvg3JAxKxu7td8HnuVDwdiIcBnYN0YPrfQc6m5gg/edit?usp=sharing', '_blank');
    });

    // Botão Chat Insights
    const chatBtn = document.querySelector('.action-btn:nth-child(3)');
    chatBtn.addEventListener('click', () => {
        alert('Chat Insights será implementado em breve');
    });

    // Toggle Filtro Inception
    const inceptionToggle = document.querySelector('.toggle-switch input');
    inceptionToggle.addEventListener('change', (e) => {
        const isEnabled = e.target.checked;
        console.log('Filtro Inception:', isEnabled ? 'Ativado' : 'Desativado');
        
        // Aqui você pode implementar a lógica de filtro
        if (isEnabled) {
            // Aplicar filtro
            applyInceptionFilter();
        } else {
            // Remover filtro
            removeInceptionFilter();
        }
    });

    // Notificação
    const notificationIcon = document.querySelector('.notification-icon');
    notificationIcon.addEventListener('click', () => {
        alert('Você tem novas notificações');
    });

    // Perfil do usuário
    const userProfile = document.querySelector('.user-profile');
    userProfile.addEventListener('click', () => {
        alert('Menu do usuário será implementado');
    });
}

function applyInceptionFilter() {
    // Implementar lógica de filtro Inception
    console.log('Aplicando filtro Inception...');
    // Aqui você pode filtrar os dados da tabela ou recarregar com filtro
}

function removeInceptionFilter() {
    // Implementar remoção do filtro Inception
    console.log('Removendo filtro Inception...');
    // Recarregar dados sem filtro
    loadDashboardData();
}

function showError(message) {
    // Criar elemento de erro temporário
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #ff4444;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 1000;
        font-size: 14px;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);

    // Remover após 5 segundos
    setTimeout(() => {
        document.body.removeChild(errorDiv);
    }, 5000);
}

// Função para atualizar dados periodicamente
setInterval(() => {
    loadDashboardData();
}, 300000); // Atualiza a cada 5 minutos
