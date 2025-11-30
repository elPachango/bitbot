"""
Trader - Gerencia posições, stop loss, trailing stop e executa trades simulados
"""
from datetime import datetime
import json

class TradeSimulator:
    def __init__(self, initial_capital=35.0, investment_per_trade=25.0, leverage=50):
        self.capital = initial_capital
        self.investment_per_trade = investment_per_trade
        self.leverage = leverage
        self.stop_loss_percent = 5.0  # 5% stop loss
        self.slippage_percent = 0.05  # 0.05% slippage realista
        
        self.open_positions = []
        self.closed_trades = []
        
    def can_open_position(self, position_type):
        """Verifica se há capital disponível para abrir posição"""
        # Verificar se já tem uma posição do mesmo tipo aberta
        for pos in self.open_positions:
            if pos['type'] == position_type:
                return False, "Já existe uma posição deste tipo aberta"
        
        # Verificar capital disponível
        total_invested = sum(pos['amount'] for pos in self.open_positions)
        available = self.capital - total_invested
        
        if available < self.investment_per_trade:
            return False, f"Capital insuficiente (disponível: ${available:.2f})"
        
        return True, "OK"
    
    def calculate_position_size(self):
        """Calcula tamanho da posição com alavancagem"""
        return self.investment_per_trade * self.leverage
    
    def apply_slippage(self, price, is_buy=True):
        """Aplica slippage realista no preço"""
        if is_buy:
            # Compra: preço um pouco maior
            return price * (1 + self.slippage_percent / 100)
        else:
            # Venda: preço um pouco menor
            return price * (1 - self.slippage_percent / 100)
    
    def open_position(self, signal_type, entry_price):
        """Abre uma nova posição (simulada)"""
        can_open, reason = self.can_open_position(signal_type)
        
        if not can_open:
            return None, reason
        
        # Aplicar slippage
        actual_entry_price = self.apply_slippage(entry_price, is_buy=(signal_type == 'LONG'))
        
        # Calcular stop loss inicial
        if signal_type == 'LONG':
            stop_loss_price = actual_entry_price * (1 - self.stop_loss_percent / 100)
        else:  # SHORT
            stop_loss_price = actual_entry_price * (1 + self.stop_loss_percent / 100)
        
        position = {
            'id': f"{signal_type}_{int(datetime.now().timestamp())}",
            'type': signal_type,
            'entry_price': actual_entry_price,
            'current_price': actual_entry_price,
            'amount': self.investment_per_trade,
            'position_size': self.calculate_position_size(),
            'stop_loss': stop_loss_price,
            'initial_stop': stop_loss_price,
            'trailing_stop': stop_loss_price,
            'highest_price': actual_entry_price if signal_type == 'LONG' else None,
            'lowest_price': actual_entry_price if signal_type == 'SHORT' else None,
            'pnl_percent': 0.0,
            'pnl_dollar': 0.0,
            'open_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'close_time': None,
            'status': 'open'
        }
        
        self.open_positions.append(position)
        
        return position, f"Posição {signal_type} aberta em ${actual_entry_price:.2f}"
    
    def update_trailing_stop(self, position, current_price, candle_closed=False):
        """
        Atualiza trailing stop (só se move quando a vela fechar)
        O stop só sobe (LONG) ou desce (SHORT), nunca o contrário
        """
        if not candle_closed:
            return  # Só atualiza quando a vela fechar
        
        if position['type'] == 'LONG':
            # Atualizar highest_price
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
                
                # Calcular novo trailing stop (5% abaixo do maior preço)
                new_trailing = current_price * (1 - self.stop_loss_percent / 100)
                
                # Trailing stop só sobe
                if new_trailing > position['trailing_stop']:
                    position['trailing_stop'] = new_trailing
        
        else:  # SHORT
            # Atualizar lowest_price
            if position['lowest_price'] is None or current_price < position['lowest_price']:
                position['lowest_price'] = current_price
                
                # Calcular novo trailing stop (5% acima do menor preço)
                new_trailing = current_price * (1 + self.stop_loss_percent / 100)
                
                # Trailing stop só desce
                if new_trailing < position['trailing_stop']:
                    position['trailing_stop'] = new_trailing
    
    def check_stop_loss(self, position, current_price):
        """Verifica se o trailing stop foi atingido"""
        if position['type'] == 'LONG':
            if current_price <= position['trailing_stop']:
                return True, 'Trailing Stop'
        else:  # SHORT
            if current_price >= position['trailing_stop']:
                return True, 'Trailing Stop'
        
        return False, None
    
    def update_position(self, position, current_price, candle_closed=False):
        """Atualiza P&L de uma posição e verifica stop loss"""
        position['current_price'] = current_price
        
        # Calcular P&L
        if position['type'] == 'LONG':
            price_change = (current_price - position['entry_price']) / position['entry_price']
        else:  # SHORT
            price_change = (position['entry_price'] - current_price) / position['entry_price']
        
        # P&L percentual (considerando alavancagem)
        position['pnl_percent'] = price_change * 100 * self.leverage
        
        # P&L em dólares (sobre o investimento real)
        position['pnl_dollar'] = position['amount'] * (position['pnl_percent'] / 100)
        
        # Atualizar trailing stop (só quando vela fechar)
        self.update_trailing_stop(position, current_price, candle_closed)
        
        # Verificar stop loss
        hit_stop, stop_type = self.check_stop_loss(position, current_price)
        
        return hit_stop, stop_type
    
    def close_position(self, position, close_price, reason='Manual'):
        """Fecha uma posição"""
        # Aplicar slippage na saída
        actual_close_price = self.apply_slippage(close_price, is_buy=(position['type'] == 'SHORT'))
        
        # Atualizar preço final
        self.update_position(position, actual_close_price)
        
        # Marcar como fechada
        position['close_price'] = actual_close_price
        position['close_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        position['close_reason'] = reason
        position['status'] = 'closed'
        
        # Atualizar capital
        self.capital += position['pnl_dollar']
        
        # Mover para trades fechados
        self.closed_trades.append(position)
        self.open_positions.remove(position)
        
        return position
    
    def get_statistics(self):
        """Retorna estatísticas de trading"""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'won': 0,
                'lost': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'biggest_win': 0,
                'biggest_loss': 0
            }
        
        won = [t for t in self.closed_trades if t['pnl_dollar'] > 0]
        lost = [t for t in self.closed_trades if t['pnl_dollar'] <= 0]
        
        total_pnl = sum(t['pnl_dollar'] for t in self.closed_trades)
        biggest_win = max([t['pnl_dollar'] for t in self.closed_trades]) if self.closed_trades else 0
        biggest_loss = min([t['pnl_dollar'] for t in self.closed_trades]) if self.closed_trades else 0
        
        return {
            'total_trades': len(self.closed_trades),
            'won': len(won),
            'lost': len(lost),
            'win_rate': (len(won) / len(self.closed_trades) * 100) if self.closed_trades else 0,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / 35.0) * 100,  # Baseado no capital inicial
            'biggest_win': biggest_win,
            'biggest_loss': biggest_loss,
            'current_capital': self.capital
        }


# Instância global
trader = TradeSimulator()


if __name__ == '__main__':
    # Teste
    print("🧪 Testando Trade Simulator...\n")
    
    sim = TradeSimulator(initial_capital=35, investment_per_trade=25, leverage=50)
    
    # Simular abertura LONG
    pos, msg = sim.open_position('LONG', 40000)
    print(f"✅ {msg}")
    print(f"📊 Stop Loss: ${pos['stop_loss']:.2f}")
    print(f"💰 Tamanho da posição (com alavancagem): ${pos['position_size']:.2f}\n")
    
    # Simular movimento de preço
    print("📈 Preço sobe para $41,000")
    sim.update_position(pos, 41000, candle_closed=True)
    print(f"💵 P&L: {pos['pnl_percent']:.2f}% (${pos['pnl_dollar']:.2f})")
    print(f"🛡️  Trailing Stop atualizado: ${pos['trailing_stop']:.2f}\n")
    
    # Fechar posição
    closed = sim.close_position(pos, 41000, 'Take Profit')
    print(f"✅ Posição fechada")
    print(f"💰 Capital final: ${sim.capital:.2f}")
    
    stats = sim.get_statistics()
    print(f"\n📊 Estatísticas:")
    print(f"   Total de trades: {stats['total_trades']}")
    print(f"   P&L total: ${stats['total_pnl']:.2f} ({stats['total_pnl_percent']:.2f}%)")
