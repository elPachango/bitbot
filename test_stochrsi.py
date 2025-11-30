"""
Teste para validar cálculo do Stoch RSI
Compare com TradingView manualmente
"""
from data_provider import data_provider
from analyzer import analyzer
from datetime import datetime

print("="*60)
print("🧪 TESTE STOCH RSI - Comparação com TradingView")
print("="*60)

# Obter dados
print("\n📊 Obtendo últimas 100 velas de 5min do BTC/USDT...")
klines = data_provider.get_latest_klines(limit=100)

if not klines:
    print("❌ Erro ao obter dados")
    exit(1)

print(f"✅ {len(klines)} velas obtidas\n")

# Mostrar últimas 20 velas
print("📋 Últimas 20 velas (use para comparar com TradingView):")
print("="*60)
print(f"{'Horário':<10} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12}")
print("-"*60)

for k in klines[-20:]:
    dt = datetime.fromtimestamp(k['timestamp'] / 1000)
    print(f"{dt.strftime('%H:%M'):<10} ${k['open']:<11.2f} ${k['high']:<11.2f} ${k['low']:<11.2f} ${k['close']:<11.2f}")

print("\n" + "="*60)

# Calcular Stoch RSI manualmente passo a passo
print("\n🔢 CÁLCULO DETALHADO DO STOCH RSI:")
print("="*60)

closes = [k['close'] for k in klines]

# Mostrar parâmetros
print(f"\nParâmetros:")
print(f"  RSI Period: 15")
print(f"  Stochastic Period: 5") 
print(f"  K Smooth: 3")
print(f"  D Smooth: 3")
print(f"  Método RSI: EMA (Wilder)")

# Calcular para as últimas 10 velas
print(f"\n📊 Stoch RSI das últimas 10 velas:")
print("-"*60)

for i in range(-10, 0):
    closes_subset = closes[:len(closes)+i+1]
    k_val, d_val = analyzer.calculate_stoch_rsi(closes_subset, 15, 5, 3, 3)
    
    dt = datetime.fromtimestamp(klines[i]['timestamp'] / 1000)
    k_str = f"{k_val:.2f}" if k_val is not None else "N/A"
    d_str = f"{d_val:.2f}" if d_val is not None else "N/A"
    
    status = ""
    if k_val is not None:
        if k_val < 20:
            status = "🟢 OVERSOLD"
        elif k_val > 80:
            status = "🔴 OVERBOUGHT"
    
    print(f"{dt.strftime('%H:%M')}  |  K: {k_str:<6}  |  D: {d_str:<6}  |  Close: ${klines[i]['close']:.2f}  {status}")

print("\n" + "="*60)
print("📋 INSTRUÇÕES PARA COMPARAR COM TRADINGVIEW:")
print("="*60)
print("\n1. Abra TradingView: https://www.tradingview.com/chart/")
print("2. Símbolo: BINANCE:BTCUSDT (Perpetual Futures)")
print("   OU procure diretamente: BTCUSD PERP")
print("3. Timeframe: 5 minutos")
print("4. Adicione indicador: Stochastic RSI")
print("5. Configure (clique na engrenagem):")
print("   - RSI Length: 15")
print("   - Stochastic Length: 5")
print("   - K: 3")
print("   - D: 3")
print("   - RSI Source: close")
print("\n6. Passe o mouse nas últimas 10 velas acima")
print("   e compare os valores K e D")
print("\n7. ⚠️ IMPORTANTE:")
print("   - Ignore a ÚLTIMA vela (pode estar incompleta)")
print("   - Compare a PENÚLTIMA vela")
print("\n8. Se ainda houver diferença:")
print("   - Anote qual vela")
print("   - Valor K no bot")
print("   - Valor K no TradingView")
print("   - Screenshot se possível")
print("\n" + "="*60)
