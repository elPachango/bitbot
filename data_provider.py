"""
Data Provider - Coleta dados em tempo real da Binance
"""
import requests
import time
from datetime import datetime, timedelta
import json

class BinanceDataProvider:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.symbol = "BTCUSDT"
        self.interval = "5m"  # 5 minutos
        self.cache = {
            'klines': [],
            'last_update': 0,
            'current_price': 0
        }
    
    def get_current_price(self):
        """Obtém o preço atual do BTC"""
        try:
            url = f"{self.base_url}/ticker/price"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                self.cache['current_price'] = price
                return price
            else:
                print(f"Erro ao obter preço: {response.status_code}")
                return self.cache.get('current_price', 0)
        except Exception as e:
            print(f"Erro na requisição de preço: {e}")
            return self.cache.get('current_price', 0)
    
    def get_24h_change(self):
        """Obtém a variação de 24h"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['priceChangePercent'])
            else:
                return 0.0
        except Exception as e:
            print(f"Erro ao obter variação 24h: {e}")
            return 0.0
    
    def get_historical_klines(self, days=30):
        """Obtém velas históricas de X dias"""
        try:
            # Calcular timestamp de início
            end_time = int(time.time() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)
            
            all_klines = []
            current_start = start_time
            
            print(f"📊 Carregando {days} dias de dados (5min)...")
            
            # Binance permite max 1000 velas por request
            while current_start < end_time:
                url = f"{self.base_url}/klines"
                params = {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'startTime': current_start,
                    'limit': 1000
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    klines = response.json()
                    if not klines:
                        break
                    
                    all_klines.extend(klines)
                    current_start = klines[-1][0] + 1  # Próximo timestamp
                    
                    # Pequeno delay para não sobrecarregar a API
                    time.sleep(0.1)
                else:
                    print(f"Erro ao obter klines: {response.status_code}")
                    break
            
            print(f"✅ {len(all_klines)} velas carregadas")
            self.cache['klines'] = all_klines
            self.cache['last_update'] = time.time()
            
            return self._format_klines(all_klines)
            
        except Exception as e:
            print(f"Erro ao obter dados históricos: {e}")
            return []
    
    def get_latest_klines(self, limit=100):
        """Obtém as últimas N velas"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': self.symbol,
                'interval': self.interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                klines = response.json()
                return self._format_klines(klines)
            else:
                return []
                
        except Exception as e:
            print(f"Erro ao obter últimas velas: {e}")
            return []
    
    def _format_klines(self, klines):
        """Formata velas para um formato mais amigável"""
        formatted = []
        for k in klines:
            formatted.append({
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': k[6],
                'quote_volume': float(k[7]),
                'trades': k[8]
            })
        return formatted
    
    def calculate_price_change(self, klines, minutes):
        """Calcula variação percentual nos últimos X minutos"""
        if not klines or len(klines) < 2:
            return 0.0
        
        try:
            # Número de velas necessárias (5min cada)
            num_candles = minutes // 5
            
            if len(klines) < num_candles:
                num_candles = len(klines)
            
            # Preço atual (última vela)
            current_price = klines[-1]['close']
            
            # Preço há X minutos
            past_price = klines[-num_candles]['close']
            
            if past_price == 0:
                return 0.0
            
            change_percent = ((current_price - past_price) / past_price) * 100
            return round(change_percent, 2)
            
        except Exception as e:
            print(f"Erro ao calcular variação: {e}")
            return 0.0
    
    def get_market_data(self):
        """Retorna todos os dados de mercado atualizados"""
        try:
            # Obter preço atual
            current_price = self.get_current_price()
            
            # Obter variação 24h
            change_24h = self.get_24h_change()
            
            # Obter últimas velas para calcular variações
            latest_klines = self.get_latest_klines(limit=20)
            
            # Calcular variações
            change_15min = self.calculate_price_change(latest_klines, 15)
            change_5min = self.calculate_price_change(latest_klines, 5)
            
            return {
                'price': current_price,
                'change_24h': change_24h,
                'change_15min': change_15min,
                'change_5min': change_5min,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Erro ao obter dados de mercado: {e}")
            return {
                'price': 0,
                'change_24h': 0,
                'change_15min': 0,
                'change_5min': 0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }


# Instância global
data_provider = BinanceDataProvider()


if __name__ == '__main__':
    # Teste
    print("🧪 Testando Binance Data Provider...\n")
    
    provider = BinanceDataProvider()
    
    # Testar preço atual
    price = provider.get_current_price()
    print(f"💰 Preço atual BTC: ${price:,.2f}")
    
    # Testar variação 24h
    change = provider.get_24h_change()
    print(f"📊 Variação 24h: {change:+.2f}%")
    
    # Testar dados de mercado
    market_data = provider.get_market_data()
    print(f"\n📈 Dados completos:")
    print(json.dumps(market_data, indent=2))
    
    # Testar histórico
    print(f"\n⏳ Carregando histórico de 30 dias...")
    klines = provider.get_historical_klines(days=30)
    print(f"✅ {len(klines)} velas carregadas")
