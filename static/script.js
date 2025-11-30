const socket = io();

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

loadInitialState();