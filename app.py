from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime
import threading
import time

# Importar data provider
try:
    from data_provider import data_provider
    DATA_PROVIDER_AVAILABLE = True
except ImportError:
    print("⚠️  data_provider.py não encontrado. Dados reais desabilitados.")
    DATA_PROVIDER_AVAILABLE = False

# Garantir que estamos no diretório correto
if hasattr(sys, 'frozen'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# Verificar se as pastas existem
required_dirs = ['templates', 'static', 'data']
for dir_name in required_dirs:
    dir_path = os.path.join(BASE_DIR, dir_name)
    if not os.path.exists(dir_path):
        print(f"❌ ERRO: Pasta '{dir_name}' não encontrada em {BASE_DIR}")
        print(f"Execute 'python setup_files.py' primeiro!")
        sys.exit(1)

# Verificar se index.html existe
index_path = os.path.join(BASE_DIR, 'templates', 'index.html')
if not os.path.exists(index_path):
    print(f"❌ ERRO: Arquivo 'templates/index.html' não encontrado!")
    print(f"Caminho esperado: {index_path}")
    print(f"Execute 'python setup_files.py' primeiro!")
    sys.exit(1)

print(f"✅ Diretório base: {BASE_DIR}")
print(f"✅ Templates encontrados em: {os.path.join(BASE_DIR, 'templates')}")

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = 'trading_bot_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Arquivo de dados
TRADES_FILE = os.path.join(BASE_DIR, 'data', 'trades.json')
SESSION_FILE = os.path.join(BASE_DIR, 'data', 'session.json')

# Estado global
bot_state = {
    'portfolio': 35.0,
    'session_pnl': 0.0,
    'historical_pnl': 0.0,
    'real_gain_loss': 0.0,
    'session_trades': 0,
    'trades_won': 0,
    'trades_lost': 0,
    'biggest_win': 0.0,
    'btc_price': 0.0,
    'btc_change_today': 0.0,
    'btc_change_15min': 0.0,
    'btc_change_5min': 0.0,
    'status': 'Bot Pausado - Clique em Iniciar',
    'last_signal': '',
    'next_candle_countdown': 300,
    'is_paused': True  # Inicia pausado
}

open_positions = []

# Thread para atualizar dados em tempo real
update_thread = None
update_running = False

def update_market_data():
    """Thread que atualiza dados de mercado continuamente"""
    global bot_state, update_running
    
    while update_running:
        try:
            if DATA_PROVIDER_AVAILABLE:
                # Obter dados atualizados
                market_data = data_provider.get_market_data()
                
                # Atualizar estado
                bot_state['btc_price'] = market_data['price']
                bot_state['btc_change_today'] = market_data['change_24h']
                bot_state['btc_change_15min'] = market_data['change_15min']
                bot_state['btc_change_5min'] = market_data['change_5min']
                
                # Emitir atualização via WebSocket
                socketio.emit('state_update', {'bot_state': bot_state})
            
            # Aguardar 5 segundos antes da próxima atualização
            time.sleep(5)
            
        except Exception as e:
            print(f"Erro ao atualizar dados: {e}")
            time.sleep(10)

def start_market_updates():
    """Inicia thread de atualização de dados"""
    global update_thread, update_running
    
    if not update_running and DATA_PROVIDER_AVAILABLE:
        update_running = True
        update_thread = threading.Thread(target=update_market_data, daemon=True)
        update_thread.start()
        print("✅ Atualização de dados em tempo real iniciada")

def load_trades():
    """Carrega histórico de trades"""
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trade(trade):
    """Salva um trade no histórico"""
    trades = load_trades()
    trades.append(trade)
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    """Retorna estado atual do bot"""
    return jsonify({
        'bot_state': bot_state,
        'open_positions': open_positions,
        'historical_trades': load_trades()
    })

@app.route('/api/update_portfolio', methods=['POST'])
def update_portfolio():
    """Atualiza valor do portfolio"""
    data = request.json
    bot_state['portfolio'] = float(data['value'])
    socketio.emit('state_update', {'bot_state': bot_state})
    return jsonify({'success': True})

@app.route('/api/pause', methods=['POST'])
def pause_bot():
    """Pausa/Resume o bot"""
    bot_state['is_paused'] = not bot_state['is_paused']
    
    if bot_state['is_paused']:
        bot_state['status'] = 'Bot Pausado - Clique em Iniciar'
    else:
        bot_state['status'] = 'Bot Ativo - Aguardando Sinal'
    
    socketio.emit('state_update', {'bot_state': bot_state})
    return jsonify({'success': True, 'is_paused': bot_state['is_paused']})

@app.route('/api/close_all', methods=['POST'])
def close_all_positions():
    """Fecha todas as posições abertas"""
    global open_positions
    
    for position in open_positions:
        position['status'] = 'closed'
        position['close_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        position['close_type'] = 'manual'
        save_trade(position)
    
    open_positions = []
    bot_state['status'] = 'Todas posições fechadas'
    socketio.emit('state_update', {'bot_state': bot_state, 'open_positions': open_positions})
    return jsonify({'success': True})

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    # Iniciar atualizações se ainda não iniciou
    start_market_updates()
    
    emit('state_update', {
        'bot_state': bot_state,
        'open_positions': open_positions,
        'historical_trades': load_trades()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Trading Bot iniciado!")
    print("📊 Acesse: http://localhost:5000")
    
    if DATA_PROVIDER_AVAILABLE:
        print("✅ Binance API conectada")
        # Carregar dados históricos
        print("⏳ Carregando dados históricos...")
        data_provider.get_historical_klines(days=30)
    else:
        print("⚠️  Binance API não disponível (instale 'requests')")
    
    print("=" * 50)
    socketio.run(app, debug=True, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
