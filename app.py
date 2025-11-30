from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime
import threading
import time

# Importar módulos do bot
try:
    from data_provider import data_provider
    DATA_PROVIDER_AVAILABLE = True
except ImportError:
    print("⚠️  data_provider.py não encontrado. Dados reais desabilitados.")
    DATA_PROVIDER_AVAILABLE = False

try:
    from analyzer import analyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    print("⚠️  analyzer.py não encontrado. Análise desabilitada.")
    ANALYZER_AVAILABLE = False

try:
    from trader import trader
    TRADER_AVAILABLE = True
except ImportError:
    print("⚠️  trader.py não encontrado. Trading desabilitado.")
    TRADER_AVAILABLE = False

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

# Controle de velas e sinais
last_candle_time = None
waiting_for_confirmation = None  # Guarda sinal esperando confirmação

# Thread para atualizar dados em tempo real
update_thread = None
update_running = False
trading_thread = None
trading_running = False

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
                
                # Calcular tempo até próxima vela de 5min
                import datetime
                now = datetime.datetime.now()
                seconds_in_5min = now.minute % 5 * 60 + now.second
                seconds_until_next = 300 - seconds_in_5min
                bot_state['next_candle_countdown'] = seconds_until_next
                
                # Emitir atualização via WebSocket
                socketio.emit('state_update', {'bot_state': bot_state})
            
            # Aguardar 1 segundo antes da próxima atualização
            time.sleep(1)
            
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

def trading_loop():
    """Loop principal de trading"""
    global bot_state, last_candle_time, waiting_for_confirmation, trading_running
    
    candle_check_interval = 60  # Verificar a cada 1 minuto
    last_check = 0
    
    while trading_running:
        try:
            current_time = time.time()
            
            # Verificar a cada minuto se uma vela de 5min fechou
            if current_time - last_check >= candle_check_interval:
                last_check = current_time
                
                # Se o bot estiver pausado, não fazer nada
                if bot_state['is_paused']:
                    time.sleep(5)
                    continue
                
                if not (DATA_PROVIDER_AVAILABLE and ANALYZER_AVAILABLE and TRADER_AVAILABLE):
                    time.sleep(5)
                    continue
                
                # Obter últimas velas
                klines = data_provider.get_latest_klines(limit=100)
                
                if not klines or len(klines) < 50:
                    bot_state['status'] = 'Carregando dados...'
                    time.sleep(5)
                    continue
                
                # Verificar se uma nova vela de 5min fechou
                current_candle_time = klines[-1]['timestamp']
                candle_closed = (last_candle_time != current_candle_time)
                
                if candle_closed:
                    last_candle_time = current_candle_time
                    
                    # Atualizar posições abertas
                    update_open_positions(klines[-1]['close'], candle_closed=True)
                    
                    # Analisar indicadores
                    analysis = analyzer.analyze_klines(klines)
                    
                    # Atualizar status
                    bot_state['last_signal'] = f"{analysis['signal'] or 'Nenhum'} - {analysis['reason']}"
                    
                    # Log da análise
                    print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Análise:")
                    print(f"   Stoch RSI K: {analysis['stoch_rsi_k']}")
                    print(f"   Sinal: {analysis['signal']}")
                    print(f"   Razão: {analysis['reason']}")
                    
                    # Processar sinais
                    if analysis['signal'] in ['LONG', 'SHORT']:
                        # Verificar condições de entrada
                        can_enter, entry_reason = analyzer.check_entry_conditions(klines, analysis['signal'])
                        
                        if can_enter:
                            # Tentar abrir posição
                            position, msg = trader.open_position(analysis['signal'], analysis['price'])
                            
                            if position:
                                open_positions.append(position)
                                bot_state['status'] = f"✅ {msg}"
                                bot_state['session_trades'] += 1
                                print(f"   ✅ {msg}")
                                
                                # Salvar trade
                                save_trade(position)
                            else:
                                bot_state['status'] = f"⚠️ {msg}"
                                print(f"   ⚠️ {msg}")
                        else:
                            bot_state['status'] = entry_reason
                            print(f"   ⏳ {entry_reason}")
                    
                    elif analysis['signal'] == 'EXIT_LONG':
                        # Fechar posições LONG
                        close_positions_by_type('LONG', analysis['price'], 'Stoch RSI Overbought')
                    
                    elif analysis['signal'] == 'EXIT_SHORT':
                        # Fechar posições SHORT
                        close_positions_by_type('SHORT', analysis['price'], 'Stoch RSI Oversold')
                    
                    else:
                        bot_state['status'] = 'Bot Ativo - Aguardando Sinal'
                    
                    # Atualizar estatísticas
                    update_statistics()
                    
                    # Emitir atualização
                    socketio.emit('state_update', {
                        'bot_state': bot_state,
                        'open_positions': open_positions
                    })
                
                else:
                    # Vela ainda aberta, apenas atualizar P&L das posições
                    if klines:
                        update_open_positions(klines[-1]['close'], candle_closed=False)
            
            time.sleep(5)  # Verificar a cada 5 segundos
            
        except Exception as e:
            print(f"❌ Erro no trading loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)

def update_open_positions(current_price, candle_closed=False):
    """Atualiza todas as posições abertas"""
    global open_positions
    
    positions_to_close = []
    
    for position in open_positions:
        # Atualizar P&L e verificar stop loss
        hit_stop, stop_type = trader.update_position(position, current_price, candle_closed)
        
        if hit_stop:
            positions_to_close.append((position, stop_type))
    
    # Fechar posições que bateram no stop
    for position, reason in positions_to_close:
        close_position(position, current_price, reason)

def close_positions_by_type(position_type, current_price, reason):
    """Fecha todas as posições de um tipo específico"""
    global open_positions
    
    positions_to_close = [p for p in open_positions if p['type'] == position_type]
    
    for position in positions_to_close:
        close_position(position, current_price, reason)

def close_position(position, current_price, reason):
    """Fecha uma posição individual"""
    global open_positions
    
    closed = trader.close_position(position, current_price, reason)
    
    if closed in open_positions:
        open_positions.remove(closed)
    
    # Atualizar estatísticas
    if closed['pnl_dollar'] > 0:
        bot_state['trades_won'] += 1
    else:
        bot_state['trades_lost'] += 1
    
    # Salvar trade fechado
    save_trade(closed)
    
    print(f"   🔒 Posição {closed['type']} fechada: {reason}")
    print(f"   💰 P&L: {closed['pnl_percent']:.2f}% (${closed['pnl_dollar']:.2f})")

def update_statistics():
    """Atualiza estatísticas do bot"""
    stats = trader.get_statistics()
    
    bot_state['session_pnl'] = stats['total_pnl_percent']
    bot_state['real_gain_loss'] = stats['total_pnl']
    bot_state['biggest_win'] = stats['biggest_win']
    bot_state['portfolio'] = stats['current_capital']
    
    # Calcular P&L histórico (incluindo trades anteriores)
    all_trades = load_trades()
    if all_trades:
        historical_pnl = sum(t.get('pnl_dollar', 0) for t in all_trades)
        bot_state['historical_pnl'] = (historical_pnl / 35.0) * 100

def start_trading():
    """Inicia thread de trading"""
    global trading_thread, trading_running
    
    if not trading_running and TRADER_AVAILABLE and ANALYZER_AVAILABLE:
        trading_running = True
        trading_thread = threading.Thread(target=trading_loop, daemon=True)
        trading_thread.start()
        print("✅ Trading loop iniciado")

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

@app.route('/api/debug/stochrsi')
def debug_stochrsi():
    """Endpoint de debug para verificar Stoch RSI"""
    if not (DATA_PROVIDER_AVAILABLE and ANALYZER_AVAILABLE):
        return jsonify({'error': 'Módulos não disponíveis'})
    
    try:
        # Obter últimas 100 velas
        klines = data_provider.get_latest_klines(limit=100)
        
        if not klines:
            return jsonify({'error': 'Sem dados'})
        
        # Analisar
        analysis = analyzer.analyze_klines(klines)
        
        # Retornar últimas 20 velas + análise
        recent_klines = klines[-20:]
        
        return jsonify({
            'analysis': analysis,
            'recent_candles': [
                {
                    'timestamp': k['timestamp'],
                    'close': k['close'],
                    'open': k['open'],
                    'high': k['high'],
                    'low': k['low']
                }
                for k in recent_klines
            ],
            'parameters': {
                'rsi_period': 15,
                'stoch_period': 5,
                'k_smooth': 3,
                'd_smooth': 3
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

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
        # Iniciar trading se ainda não iniciou
        start_trading()
    
    socketio.emit('state_update', {'bot_state': bot_state})
    return jsonify({'success': True, 'is_paused': bot_state['is_paused']})

@app.route('/api/close_all', methods=['POST'])
def close_all_positions():
    """Fecha todas as posições abertas"""
    global open_positions
    
    if not open_positions:
        return jsonify({'success': False, 'message': 'Nenhuma posição aberta'})
    
    # Obter preço atual
    current_price = bot_state.get('btc_price', 0)
    
    if current_price == 0:
        return jsonify({'success': False, 'message': 'Preço atual não disponível'})
    
    # Fechar todas as posições
    for position in open_positions[:]:  # Cópia da lista
        close_position(position, current_price, 'Fechamento Manual')
    
    bot_state['status'] = 'Todas posições fechadas manualmente'
    update_statistics()
    
    socketio.emit('state_update', {
        'bot_state': bot_state, 
        'open_positions': open_positions,
        'historical_trades': load_trades()
    })
    
    return jsonify({'success': True})

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    # Iniciar atualizações se ainda não iniciou
    start_market_updates()
    
    # Iniciar trading loop (mas só vai executar trades se não estiver pausado)
    start_trading()
    
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
        print("⏳ Carregando dados históricos de 30 dias...")
        data_provider.get_historical_klines(days=30)
        print("✅ Dados carregados")
    else:
        print("⚠️  Binance API não disponível")
    
    if ANALYZER_AVAILABLE:
        print("✅ Analyzer carregado (Stoch RSI 15,5,3,3)")
    else:
        print("⚠️  Analyzer não disponível")
    
    if TRADER_AVAILABLE:
        print("✅ Trader carregado (50x leverage, $25/trade)")
    else:
        print("⚠️  Trader não disponível")
    
    print("=" * 50)
    print("⚠️  Bot inicia PAUSADO - Clique em 'Iniciar Bot'")
    print("=" * 50)
    
    socketio.run(app, debug=False, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
