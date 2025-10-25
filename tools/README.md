# 🛠️ Unicrium Tools

## 💧 Faucet

### Backend (Python)
```bash
# Start faucet server
python3 tools/faucet.py

# Runs on http://localhost:5001
```

### Web UI
```bash
# Open in browser
open tools/faucet_ui.html

# Or serve with Python
cd tools
python3 -m http.server 8000
# Then visit: http://localhost:8000/faucet_ui.html
```

### API Endpoints
```bash
# Claim coins
curl -X POST http://localhost:5001/claim \
  -H "Content-Type: application/json" \
  -d '{"address":"0x..."}'

# Get faucet balance
curl http://localhost:5001/balance

# Get faucet info
curl http://localhost:5001/info
```

---

## 💰 Wallet

### Backend
```bash
# Start wallet backend
python3 wallet/wallet_backend.py

# Runs on http://localhost:5555
```

### GUI
```bash
# Start wallet GUI
python3 wallet/wallet_gui.py
```

### Features
- ✅ Create/load wallet
- ✅ Check balance
- ✅ Send transactions
- ✅ Receive UNI
- ✅ Address management

---

## 📝 Configuration

Edit the following in the files:

**Faucet (`tools/faucet.py`):**
- `FAUCET_AMOUNT` - Amount per claim
- `CLAIM_COOLDOWN` - Time between claims
- `FAUCET_PRIVATE_KEY` - Your faucet private key

**Wallet Backend (`wallet/wallet_backend.py`):**
- `NODE_URL` - API server URL
- `BACKEND_PORT` - Backend port

---

## 🚀 Quick Start

```bash
# 1. Start API server
python3 network/api_server.py &

# 2. Start faucet
python3 tools/faucet.py &

# 3. Start wallet backend
python3 wallet/wallet_backend.py &

# 4. Open wallet GUI
python3 wallet/wallet_gui.py
```

---

## 💡 Tips

- Keep wallet backend running while using GUI
- Faucet requires funded faucet address
- Check logs if issues occur
- Use web UI for easier faucet access
