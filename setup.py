#!/usr/bin/env python3
"""
Script para criar todos os arquivos necessários do Trading Bot
"""
import os

def create_directories():
    """Cria as pastas necessárias"""
    dirs = ['templates', 'static', 'data']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ Pasta '{d}' criada/verificada")

def create_html():
    """Cria o arquivo HTML"""
    html_content = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot - BTC Scalping</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div class="container">
        <!-- Linha 1: Portfolio e P&L -->
        <div class="row">
            <div class="block" id="portfolio-block">
                <div class="block-label">Portfolio</div>
                <div class="block-value" id="portfolio-value" onclick="editPortfolio()">$35.00</div>
            </div>
            <div class="block" id="session-pnl-block">
                <div class="block-label">P&L Sessão</div>
                <div class="block-value" id="session-pnl">0.00%</div>
            </div>
            <div class="block" id="historical-pnl-block">
                <div class="block-label">P&L Histórico</div>
                <div class="block-value" id="historical-pnl">0.00%</div>
            </div>
            <div class="block" id="real-gain-block">
                <div class="block-label">Ganho/Perda Real</div>
                <div class="block-value" id="real-gain">$0.00</div>
            </div>
        </div>

        <!-- Linha 2: Estatísticas de Trades -->
        <div class="row">
            <div class="block">
                <div class="block-label">Trades da Sessão</div>
                <div class="block-value" id="session-trades">0</div>
            </div>
            <div class="block" id="trades-won-block">
                <div class="block-label">Trades Ganhos</div>
                <div class="block-value" id="trades-won">0</div>
            </div>
            <div class="block" id="trades-lost-block">
                <div class="block-label">Trades Perdidos</div>
                <div class="block-value" id="trades-lost">0</div>
            </div>
            <div class="block" id="biggest-win-block">
                <div class="block-label">Maior Win</div>
                <div class="block-value" id="biggest-win">$0.00</div>
            </div>
        </div>

        <!-- Linha 3: Informações do Bitcoin -->
        <div class="row">
            <div class="block">
                <div class="block-label">BTC Atual</div>
                <div class="block-value" id="btc-price">$0.00</div>
            </div>
            <div class="block" id="btc-today-block">
                <div class="block-label">Variação Hoje</div>
                <div class="block-value" id="btc-today">0.00%</div>
            </div>
            <div class="block" id="btc-15min-block">
                <div class="block-label">Variação 15min</div>
                <div class="block-value" id="btc-15min">0.00%</div>
            </div>
            <div class="block" id="btc-5min-block">
                <div class="block-label">Variação 5min</div>
                <div class="block-value" id="btc-5min">0.00%</div>
            </div>
        </div>

        <!-- Linha 4: Status e Controles -->
        <div class="row">
            <div class="block" style="flex: 2;">
                <div class="block-label">Status do Bot</div>
                <div class="block-value status-text" id="bot-status">Aguardando Sinal</div>
            </div>
            <div class="block" style="flex: 2;">
                <div class="block-label">Último Sinal</div>
                <div class="block-value" id="last-signal">-</div>
            </div>
            <div class="block">
                <div class="block-label">Próxima Vela</div>
                <div class="block-value" id="next-candle">5:00</div>
            </div>
        </div>

        <!-- Controles Manuais -->
        <div class="row controls-row">
            <button class="control-btn pause-btn" id="pause-btn" onclick="togglePause()">
                <span id="pause-icon">⏸</span> Pausar Bot
            </button>
            <button class="control-btn close-btn" onclick="closeAllPositions()">
                ✕ Fechar Todas Posições
            </button>
            <button class="control-btn adjust-btn" onclick="editPortfolio()">
                ⚙ Ajustar Capital
            </button>
        </div>

        <!-- Posições Abertas -->
        <div class="positions-section">
            <h3>Posições Abertas</h3>
            <div id="open-positions"></div>
        </div>

        <!-- Histórico de Trades -->
        <div class="trades-section">
            <h3>Histórico de Trades</h3>
            <div id="trades-history"></div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("✅ Arquivo 'templates/index.html' criado")

def create_css():
    """Cria o arquivo CSS"""
    css_content = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    padding: 20px;
    min-height: 100vh;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

.row {
    display: flex;
    gap: 15px;
    margin-bottom: 15px;
}

.block {
    flex: 1;
    background: rgba(30, 30, 50, 0.6);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(100, 100, 150, 0.3);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.block:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
}

.block-label {
    font-size: 12px;
    color: #a0a0c0;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.block-value {
    font-size: 24px;
    font-weight: 600;
    color: #ffffff;
}

#portfolio-value {
    cursor: pointer;
}

#portfolio-value:hover {
    color: #6dd5ed;
}

.status-text {
    font-size: 18px;
}

.border-green {
    border-color: rgba(0, 255, 100, 0.6);
    box-shadow: 0 0 15px rgba(0, 255, 100, 0.2);
}

.border-red {
    border-color: rgba(255, 50, 50, 0.6);
    box-shadow: 0 0 15px rgba(255, 50, 50, 0.2);
}

.border-neutral {
    border-color: rgba(100, 150, 255, 0.4);
}

.controls-row {
    justify-content: center;
    margin-top: 20px;
}

.control-btn {
    padding: 12px 30px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.pause-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.pause-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.close-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
}

.close-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
}

.adjust-btn {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
}

.adjust-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba79, 172, 254, 0.4);
}

.positions-section, .trades-section {
    margin-top: 30px;
}

h3 {
    color: #a0a0c0;
    font-size: 18px;
    margin-bottom: 15px;
    text-transform: uppercase;
    letter-spacing: 2px;
}

#open-positions, #trades-history {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.trade-block {
    background: rgba(30, 30, 50, 0.6);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(100, 100, 150, 0.3);
    border-radius: 12px;
    padding: 15px;
    display: flex;
    align-items: center;
    gap: 20px;
    transition: all 0.3s ease;
}

.trade-block:hover {
    transform: translateX(5px);
}

.trade-type {
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 14px;
    text-align: center;
    min-width: 70px;
}

.trade-type.long {
    background: rgba(0, 255, 100, 0.2);
    color: #00ff64;
    border: 2px solid #00ff64;
}

.trade-type.short {
    background: rgba(255, 50, 50, 0.2);
    color: #ff3232;
    border: 2px solid #ff3232;
}

.trade-info {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.trade-detail {
    display: flex;
    flex-direction: column;
}

.trade-detail-label {
    font-size: 11px;
    color: #808090;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.trade-detail-value {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}

.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: #6dd5ed;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.day-group {
    margin-bottom: 20px;
}

.day-header {
    color: #6dd5ed;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    padding: 8px 15px;
    background: rgba(109, 213, 237, 0.1);
    border-radius: 6px;
    border-left: 4px solid #6dd5ed;
}

@media (max-width: 1200px) {
    .row {
        flex-wrap: wrap;
    }
    
    .block {
        min-width: calc(50% - 10px);
    }
}

@media (max-width: 768px) {
    .block {
        min-width: 100%;
    }
    
    .controls-row {
        flex-direction: column;
    }
    
    .trade-info {
        grid-template-columns: 1fr;
    }
}'''
    
    with open('static/style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)
    print("✅ Arquivo 'static/style.css' criado")

def create_js():
    """Cria o arquivo JavaScript"""
    js_content = '''const socket = io();

let botState = {};
let openPositions = [];
let historicalTrades = [];

socket.on('connect', () => {
    console.log('Conectado ao servidor');
    loadInitialState();
});

socket.on('state_update', (data) => {
    if (data.bot_state) botState = data.bot_state;
    if (data.open_positions) openPositions = data.open_positions;
    if (data.historical_trades) historicalTrades = data.historical_trades;
    updateUI();
});

async function loadInitialState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        botState = data.bot_state;
        openPositions = data.open_positions;
        historicalTrades = data.historical_trades;
        updateUI();
    } catch (error) {
        console.error('Erro ao carregar estado:', error);
    }
}

function updateUI() {
    updateLine1();
    updateLine2();
    updateLine3();
    updateLine4();
    updateOpenPositions();
    updateTradesHistory();
}

function updateLine1() {
    document.getElementById('portfolio-value').textContent = `$${botState.portfolio?.toFixed(2) || '35.00'}`;
    
    const sessionPnl = botState.session_pnl || 0;
    const sessionPnlEl = document.getElementById('session-pnl');
    sessionPnlEl.textContent = `${sessionPnl >= 0 ? '+' : ''}${sessionPnl.toFixed(2)}%`;
    updateBorder('session-pnl-block', sessionPnl);
    
    const historicalPnl = botState.historical_pnl || 0;
    const historicalPnlEl = document.getElementById('historical-pnl');
    historicalPnlEl.textContent = `${historicalPnl >= 0 ? '+' : ''}${historicalPnl.toFixed(2)}%`;
    updateBorder('historical-pnl-block', historicalPnl);
    
    const realGain = botState.real_gain_loss || 0;
    const realGainEl = document.getElementById('real-gain');
    realGainEl.textContent = `${realGain >= 0 ? '+' : ''}$${Math.abs(realGain).toFixed(2)}`;
    updateBorder('real-gain-block', realGain);
}

function updateLine2() {
    document.getElementById('session-trades').textContent = botState.session_trades || 0;
    
    const won = botState.trades_won || 0;
    document.getElementById('trades-won').textContent = won;
    updateBorder('trades-won-block', won > 0 ? 1 : 0);
    
    const lost = botState.trades_lost || 0;
    document.getElementById('trades-lost').textContent = lost;
    updateBorder('trades-lost-block', lost > 0 ? -1 : 0);
    
    const biggestWin = botState.biggest_win || 0;
    document.getElementById('biggest-win').textContent = `$${biggestWin.toFixed(2)}`;
    updateBorder('biggest-win-block', biggestWin);
}

function updateLine3() {
    document.getElementById('btc-price').textContent = `$${(botState.btc_price || 0).toFixed(2)}`;
    
    const today = botState.btc_change_today || 0;
    document.getElementById('btc-today').textContent = `${today >= 0 ? '+' : ''}${today.toFixed(2)}%`;
    updateBorder('btc-today-block', today);
    
    const min15 = botState.btc_change_15min || 0;
    document.getElementById('btc-15min').textContent = `${min15 >= 0 ? '+' : ''}${min15.toFixed(2)}%`;
    updateBorder('btc-15min-block', min15);
    
    const min5 = botState.btc_change_5min || 0;
    document.getElementById('btc-5min').textContent = `${min5 >= 0 ? '+' : ''}${min5.toFixed(2)}%`;
    updateBorder('btc-5min-block', min5);
}

function updateLine4() {
    document.getElementById('bot-status').textContent = botState.status || 'Aguardando Sinal';
    document.getElementById('last-signal').textContent = botState.last_signal || '-';
    
    const countdown = botState.next_candle_countdown || 300;
    const minutes = Math.floor(countdown / 60);
    const seconds = countdown % 60;
    document.getElementById('next-candle').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function updateBorder(blockId, value) {
    const block = document.getElementById(blockId);
    if (!block) return;
    
    block.classList.remove('border-green', 'border-red', 'border-neutral');
    
    if (value > 0) {
        block.classList.add('border-green');
    } else if (value < 0) {
        block.classList.add('border-red');
    } else {
        block.classList.add('border-neutral');
    }
}

function updateOpenPositions() {
    const container = document.getElementById('open-positions');
    
    if (!openPositions || openPositions.length === 0) {
        container.innerHTML = '<p style="color: #808090; text-align: center; padding: 20px;">Nenhuma posição aberta</p>';
        return;
    }
    
    container.innerHTML = openPositions.map(pos => createTradeBlock(pos, true)).join('');
}

function updateTradesHistory() {
    const container = document.getElementById('trades-history');
    
    if (!historicalTrades || historicalTrades.length === 0) {
        container.innerHTML = '<p style="color: #808090; text-align: center; padding: 20px;">Nenhum trade no histórico</p>';
        return;
    }
    
    const groupedByDay = {};
    historicalTrades.forEach(trade => {
        const date = trade.open_time?.split(' ')[0] || 'Sem data';
        if (!groupedByDay[date]) groupedByDay[date] = [];
        groupedByDay[date].push(trade);
    });
    
    const days = Object.keys(groupedByDay).sort().reverse();
    container.innerHTML = days.map(day => `
        <div class="day-group">
            <div class="day-header">${formatDate(day)}</div>
            ${groupedByDay[day].map(trade => createTradeBlock(trade, false)).join('')}
        </div>
    `).join('');
}

function createTradeBlock(trade, isOpen) {
    const type = trade.type || 'long';
    const pnlPercent = trade.pnl_percent || 0;
    const pnlDollar = trade.pnl_dollar || 0;
    const borderClass = pnlPercent >= 0 ? 'border-green' : 'border-red';
    
    return `
        <div class="trade-block ${borderClass}">
            <div class="trade-type ${type}">${type.toUpperCase()}</div>
            <div class="trade-info">
                <div class="trade-detail">
                    <div class="trade-detail-label">Investido</div>
                    <div class="trade-detail-value">$${(trade.amount || 0).toFixed(2)}</div>
                </div>
                <div class="trade-detail">
                    <div class="trade-detail-label">P&L</div>
                    <div class="trade-detail-value" style="color: ${pnlPercent >= 0 ? '#00ff64' : '#ff3232'}">
                        ${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}% 
                        (${pnlDollar >= 0 ? '+' : ''}$${pnlDollar.toFixed(2)})
                    </div>
                </div>
                <div class="trade-detail">
                    <div class="trade-detail-label">Abertura</div>
                    <div class="trade-detail-value">${trade.open_time || '-'}</div>
                </div>
                <div class="trade-detail">
                    <div class="trade-detail-label">Fechamento</div>
                    <div class="trade-detail-value">
                        ${isOpen ? '<span class="spinner"></span>' : (trade.close_time || '-')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

function editPortfolio() {
    const newValue = prompt('Digite o novo valor do portfolio:', botState.portfolio || 35);
    if (newValue && !isNaN(newValue)) {
        fetch('/api/update_portfolio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: parseFloat(newValue) })
        });
    }
}

function togglePause() {
    fetch('/api/pause', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            const btn = document.getElementById('pause-btn');
            if (data.is_paused) {
                btn.innerHTML = '<span id="pause-icon">▶</span> Resumir Bot';
            } else {
                btn.innerHTML = '<span id="pause-icon">⏸</span> Pausar Bot';
            }
        });
}

function closeAllPositions() {
    if (confirm('Tem certeza que deseja fechar todas as posições abertas?')) {
        fetch('/api/close_all', { method: 'POST' });
    }
}

loadInitialState();'''
    
    with open('static/script.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("✅ Arquivo 'static/script.js' criado")

def main():
    print("\n" + "="*60)
    print("🤖 CRIANDO ARQUIVOS DO TRADING BOT")
    print("="*60 + "\n")
    
    create_directories()
    create_html()
    create_css()
    create_js()
    
    print("\n" + "="*60)
    print("✅ TODOS OS ARQUIVOS FORAM CRIADOS!")
    print("="*60)
    print("\n🚀 Próximos passos:")
    print("1. Execute: python app.py")
    print("2. Abra o navegador em: http://localhost:5000")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
