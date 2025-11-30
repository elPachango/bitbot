from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime

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
    'status': 'Aguardando Sinal',
    'last_signal': '',
    'next_candle_countdown': 300,
    'is_paused': False
}

open_positions = []

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
    bot_state['status'] = 'Pausado' if bot_state['is_paused'] else 'Aguardando Sinal'
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
    emit('state_update', {
        'bot_state': bot_state,
        'open_positions': open_positions,
        'historical_trades': load_trades()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Trading Bot iniciado!")
    print("📊 Acesse: http://localhost:5000")
    print("=" * 50)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
