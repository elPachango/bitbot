# 🤖 BitBot - Bitcoin Auto Trading Bot

Bot de trading automatizado para scalping de Bitcoin com interface web moderna.

## 📊 Características

- ✅ Interface web responsiva estilo Aero Dark
- ✅ Dados em tempo real via Binance API
- ✅ Simulação de trades com alavancagem 50x
- ✅ Indicadores técnicos (Stoch RSI)
- ✅ Gestão de risco rigorosa (5% stop loss + trailing)
- ⏳ Integração com dYdX (em desenvolvimento)

## 🚀 Instalação
```bash
# Clone o repositório
git clone https://github.com/elPachango/bitbot.git
cd bitbot

# Instale as dependências
pip install -r requirements.txt

# Execute o bot
python run.py
```

## 📁 Estrutura
```
bitbot/
├── app.py              # Backend Flask + WebSocket
├── data_provider.py    # Conexão com Binance API
├── analyzer.py         # Análise de indicadores (em desenvolvimento)
├── trader.py           # Lógica de trading (em desenvolvimento)
├── templates/          # Interface HTML
├── static/            # CSS e JavaScript
└── data/              # Histórico de trades (JSON)
```

## 🎯 Roadmap

- [x] Interface web funcional
- [x] Integração com Binance (dados reais)
- [ ] Cálculo de Stoch RSI
- [ ] Sistema de trading simulado
- [ ] Backtesting
- [ ] Integração com dYdX
- [ ] Notificações (Telegram)

## ⚠️ Aviso

Este bot está em **desenvolvimento ativo**. Não use dinheiro real sem testes extensivos.

## 📝 Versão

**v0.1 Alpha** - Interface e coleta de dados