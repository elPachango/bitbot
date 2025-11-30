"""
Analyzer - Calcula indicadores técnicos e gera sinais de trading
"""
import numpy as np
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.last_signal = None
        self.last_signal_time = None
        
    def calculate_rsi(self, prices, period=14):
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_stochastic(self, highs, lows, closes, period=14):
        """Calcula Stochastic Oscillator"""
        if len(closes) < period:
            return None, None
        
        # Pegar os últimos N períodos
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            return 50, 50
        
        # %K
        k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        return k, None  # Retornamos só K por enquanto
    
    def calculate_stoch_rsi(self, prices, rsi_period=14, stoch_period=14, k_smooth=3, d_smooth=3):
        """
        Calcula Stochastic RSI
        Parâmetros padrão: (14, 14, 3, 3)
        Para nossa estratégia: (15, 5, 3, 3)
        """
        if len(prices) < rsi_period + stoch_period + k_smooth + d_smooth:
            return None, None
        
        # 1. Calcular RSI para cada ponto
        rsi_values = []
        for i in range(rsi_period, len(prices)):
            price_slice = prices[i-rsi_period:i+1]
            rsi = self.calculate_rsi(price_slice, rsi_period)
            if rsi is not None:
                rsi_values.append(rsi)
        
        if len(rsi_values) < stoch_period:
            return None, None
        
        # 2. Aplicar Stochastic no RSI
        stoch_rsi_values = []
        for i in range(stoch_period - 1, len(rsi_values)):
            rsi_slice = rsi_values[i - stoch_period + 1:i + 1]
            highest_rsi = max(rsi_slice)
            lowest_rsi = min(rsi_slice)
            
            if highest_rsi == lowest_rsi:
                stoch_rsi = 50
            else:
                stoch_rsi = ((rsi_values[i] - lowest_rsi) / (highest_rsi - lowest_rsi)) * 100
            
            stoch_rsi_values.append(stoch_rsi)
        
        if len(stoch_rsi_values) < k_smooth:
            return None, None
        
        # 3. Suavizar com SMA (K)
        k_values = []
        for i in range(k_smooth - 1, len(stoch_rsi_values)):
            k_slice = stoch_rsi_values[i - k_smooth + 1:i + 1]
            k = np.mean(k_slice)
            k_values.append(k)
        
        if len(k_values) < d_smooth:
            return None, None
        
        # 4. Suavizar K para obter D
        d_values = []
        for i in range(d_smooth - 1, len(k_values)):
            d_slice = k_values[i - d_smooth + 1:i + 1]
            d = np.mean(d_slice)
            d_values.append(d)
        
        # Retornar os valores mais recentes
        current_k = k_values[-1] if k_values else None
        current_d = d_values[-1] if d_values else None
        
        return current_k, current_d
    
    def analyze_klines(self, klines, rsi_period=15, stoch_period=5, k_smooth=3, d_smooth=3):
        """
        Analisa velas e retorna indicadores + sinais
        Estratégia: Stoch RSI (15, 5, 3, 3)
        """
        if not klines or len(klines) < rsi_period + stoch_period + k_smooth + d_smooth + 10:
            return {
                'stoch_rsi_k': None,
                'stoch_rsi_d': None,
                'signal': None,
                'reason': 'Dados insuficientes'
            }
        
        # Extrair preços de fechamento
        closes = [k['close'] for k in klines]
        
        # Calcular Stoch RSI
        k, d = self.calculate_stoch_rsi(closes, rsi_period, stoch_period, k_smooth, d_smooth)
        
        if k is None or d is None:
            return {
                'stoch_rsi_k': None,
                'stoch_rsi_d': None,
                'signal': None,
                'reason': 'Erro no cálculo'
            }
        
        # Analisar última vela completa (a penúltima no array, pois a última pode estar aberta)
        last_complete_candle = klines[-2] if len(klines) >= 2 else klines[-1]
        
        # Recalcular para a vela anterior para verificar se ficou em oversold/overbought por 1 vela inteira
        closes_prev = closes[:-1]
        k_prev, d_prev = self.calculate_stoch_rsi(closes_prev, rsi_period, stoch_period, k_smooth, d_smooth)
        
        signal = None
        reason = 'Aguardando condições'
        
        # LONG: Stoch RSI estava < 20 por 1 vela inteira
        if k_prev is not None and k_prev < 20 and k >= 20:
            signal = 'LONG'
            reason = f'Stoch RSI saiu de oversold ({k_prev:.2f} → {k:.2f})'
        
        # SHORT: Stoch RSI estava > 80 por 1 vela inteira  
        elif k_prev is not None and k_prev > 80 and k <= 80:
            signal = 'SHORT'
            reason = f'Stoch RSI saiu de overbought ({k_prev:.2f} → {k:.2f})'
        
        # Condição de saída LONG: Stoch RSI > 80
        elif k > 80:
            signal = 'EXIT_LONG'
            reason = f'Stoch RSI em overbought ({k:.2f}), sair de LONG'
        
        # Condição de saída SHORT: Stoch RSI < 20
        elif k < 20:
            signal = 'EXIT_SHORT'
            reason = f'Stoch RSI em oversold ({k:.2f}), sair de SHORT'
        
        return {
            'stoch_rsi_k': round(k, 2),
            'stoch_rsi_d': round(d, 2) if d else None,
            'signal': signal,
            'reason': reason,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': klines[-1]['close']
        }
    
    def check_entry_conditions(self, klines, signal_type):
        """
        Verifica condições adicionais de entrada conforme especificado:
        - Esperar a vela que deu o sinal fechar
        - Se o preço começar a descer no próximo minuto, aguardar mais um minuto
        - Se a vela fechar abaixo da anterior, aguardar a próxima vela
        """
        if len(klines) < 3:
            return False, "Dados insuficientes"
        
        current_candle = klines[-1]
        previous_candle = klines[-2]
        
        # Para LONG: verificar se não está caindo
        if signal_type == 'LONG':
            # Se a vela atual fechou abaixo da anterior, aguardar
            if current_candle['close'] < previous_candle['close']:
                return False, "Vela fechou abaixo da anterior, aguardando próxima vela"
            
            # Se está subindo, pode entrar
            return True, "Condições de entrada para LONG confirmadas"
        
        # Para SHORT: verificar se não está subindo
        elif signal_type == 'SHORT':
            # Se a vela atual fechou acima da anterior, aguardar
            if current_candle['close'] > previous_candle['close']:
                return False, "Vela fechou acima da anterior, aguardando próxima vela"
            
            # Se está caindo, pode entrar
            return True, "Condições de entrada para SHORT confirmadas"
        
        return False, "Tipo de sinal inválido"


# Instância global
analyzer = TechnicalAnalyzer()


if __name__ == '__main__':
    # Teste com dados fictícios
    print("🧪 Testando Technical Analyzer...\n")
    
    # Simular alguns preços
    test_prices = [100 + np.sin(i/5) * 10 + np.random.randn() * 2 for i in range(100)]
    test_klines = [{'close': p, 'high': p+1, 'low': p-1, 'open': p} for p in test_prices]
    
    result = analyzer.analyze_klines(test_klines)
    
    print(f"📊 Stoch RSI K: {result['stoch_rsi_k']}")
    print(f"📊 Stoch RSI D: {result['stoch_rsi_d']}")
    print(f"🎯 Sinal: {result['signal']}")
    print(f"📝 Razão: {result['reason']}")
