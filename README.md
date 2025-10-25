# ⚛️ Unicrium Network - Production Ready Blockchain

**The Element of Uniqueness**

A production-grade, Byzantine Fault Tolerant blockchain with Proof-of-Stake consensus, featuring advanced security, performance optimizations, and comprehensive finality mechanisms.

---

## 🎯 **Features**

### Core Features
- ✅ **Proof-of-Stake Consensus** - Energy-efficient validator-based consensus
- ✅ **BFT Finality** - Supermajority voting for irreversible blocks
- ✅ **Slashing** - Automatic penalties for malicious validators
- ✅ **MerkleTree** - SPV support and efficient transaction verification
- ✅ **Gas System** - Resource metering and fee calculation
- ✅ **VRF** - Verifiable random proposer selection

### Security
- ✅ **Message Verification** - All P2P messages cryptographically signed
- ✅ **Rate Limiting** - DDoS protection on all endpoints
- ✅ **Client-Side Signing** - Private keys never leave wallet
- ✅ **Fork Detection** - Automatic detection and resolution
- ✅ **Double-Sign Detection** - Prevents validator misbehavior

### Performance
- ✅ **FastAPI** - High-performance async API server
- ✅ **Optimized Storage** - Batch loading and lazy evaluation
- ✅ **Indexed Ledger** - Fast balance and transaction lookups
- ✅ **Connection Pooling** - Efficient resource usage
- ✅ **Caching** - Response caching for common queries

---

## 📊 **Token Economics**

### Initial Distribution (Genesis)

| Allocation | Address | Amount | Percentage |
|-----------|---------|--------|-----------|
| **Faucet** | `0xfaucet123456789abcdef123456789abcdef12345` | 1,000,000 UNI | 1% |
| **Founder** | `0xbfb0ccc63e08e83eec1a5f7925ce3a655b530d67` | 10,000,000 UNI | 10% |
| **Treasury** | `0xtreasury456789abcdef123456789abcdef12345` | 89,000,000 UNI | 89% |
| **Total Supply** | - | **100,000,000 UNI** | 100% |

### Tokenomics
- **Ticker:** UNI
- **Decimals:** 8
- **Block Time:** ~6 seconds
- **Block Reward:** Dynamic based on stake
- **Minimum Stake:** 100,000 UNI
- **Unbonding Period:** 21 days

---

## 🚀 **Quick Start**

### Prerequisites
```bash
# Python 3.10+
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/unicrium-network.git
cd unicrium-network

# Install
pip install -r requirements.txt

# Create genesis
python3 config/genesis_production.py

# Start node
python3 blockchain/node.py
```

### Running Services
```bash
# API Server (FastAPI)
python3 network/api_fast.py

# Faucet
python3 tools/faucet.py

# Validator Node
python3 blockchain/validator.py
```

---

## 📁 **Project Structure**

```
unicrium-network/
├── core/                   # Core blockchain components
│   ├── merkle.py          # MerkleTree implementation
│   ├── finality.py        # BFT finality mechanism
│   ├── slashing.py        # Validator slashing system
│   ├── pos_enhanced.py    # Enhanced PoS consensus
│   └── gas.py             # Gas and fee system
├── network/               # Network layer
│   ├── p2p_secure.py     # Secure P2P networking
│   ├── api_fast.py       # FastAPI server
│   └── rate_limiter.py   # Rate limiting
├── storage/              # Data persistence
│   ├── storage_optimized.py
│   └── ledger_indexed.py
├── blockchain/           # Blockchain logic
│   ├── blockchain_production.py
│   ├── models.py
│   └── validator.py
├── config/              # Configuration
│   ├── config_production.py
│   └── genesis_production.py
├── deployment/          # Deployment scripts
│   ├── setup.sh
│   └── systemd/
├── tests/              # Test suite
│   ├── unit/
│   ├── integration/
│   └── stress/
├── docs/               # Documentation
│   ├── API.md
│   ├── VALIDATOR_GUIDE.md
│   └── SECURITY.md
└── tools/              # Utilities
    ├── wallet.py
    ├── faucet.py
    └── explorer.py
```

---

## 🔧 **Configuration**

### Mainnet Config
```python
# config/config_production.py
CHAIN_ID = "unicrium-mainnet-1"
BLOCK_TIME = 6
FINALITY_DEPTH = 10
SUPERMAJORITY_THRESHOLD = 0.67
```

### Genesis
```bash
# Create genesis with proper allocations
python3 config/genesis_production.py

# Verify genesis
python3 config/genesis_production.py --verify
```

---

## 🛡️ **Security**

### Audit Compliance
This implementation addresses all findings from the security audit:
- ✅ MerkleTree for SPV clients
- ✅ Finality mechanism with supermajority
- ✅ Slashing for malicious validators
- ✅ P2P message verification
- ✅ API security (client-side signing)
- ✅ Rate limiting and DDoS protection
- ✅ Gas system for resource control

### Best Practices
- All transactions signed client-side
- Private keys never transmitted
- Rate limiting on all endpoints
- Input validation everywhere
- Comprehensive error handling

---

## 📡 **API Documentation**

### Endpoints

#### Health Check
```bash
GET /health
Response: {"status": "ok"}
```

#### Get Balance
```bash
GET /balance/{address}
Response: {
  "address": "0x...",
  "balance": 1000000000000000,
  "staked": 0,
  "total": 1000000000000000
}
```

#### Submit Transaction
```bash
POST /transaction
Body: {
  "sender": "0x...",
  "recipient": "0x...",
  "amount": 1000000000,
  "signature": "...",
  "nonce": 0
}
```

Full API documentation: [docs/API.md](docs/API.md)

---

## 🧪 **Testing**

### Run Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Full test suite
pytest tests/

# With coverage
pytest --cov=. tests/
```

### Stress Testing
```bash
# High load simulation
python3 tests/stress/tx_flood.py

# Validator stress test
python3 tests/stress/validator_stress.py
```

---

## 🚀 **Deployment**

### Production Deployment

#### 1. Setup Server
```bash
# Run setup script
sudo bash deployment/setup.sh
```

#### 2. Configure Services
```bash
# Copy systemd services
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Enable services
sudo systemctl enable unicrium-api
sudo systemctl enable unicrium-node
sudo systemctl enable unicrium-faucet
```

#### 3. Start Services
```bash
sudo systemctl start unicrium-api
sudo systemctl start unicrium-node
sudo systemctl start unicrium-faucet
```

#### 4. Setup Nginx
```bash
# Copy nginx config
sudo cp deployment/nginx/unicrium.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/unicrium.conf /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

---

## 📈 **Monitoring**

### Metrics
- Block production rate
- Transaction throughput
- Validator uptime
- Finalized block height
- Network peers

### Logs
```bash
# Node logs
tail -f /var/log/unicrium-node.log

# API logs
tail -f /var/log/unicrium-api.log

# System logs
journalctl -u unicrium-node -f
```

---

## 🤝 **Contributing**

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md)

### Development Setup
```bash
# Clone repo
git clone https://github.com/yourusername/unicrium-network.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file

---

## 🔗 **Links**

- **Website:** https://unicrium.network
- **Documentation:** https://docs.unicrium.network
- **Explorer:** https://explorer.unicrium.network
- **GitHub:** https://github.com/yourusername/unicrium-network
- **Discord:** https://discord.gg/unicrium

---

## 💬 **Support**

- **Email:** support@unicrium.network
- **Discord:** https://discord.gg/unicrium
- **Twitter:** [@UnicriumNet](https://twitter.com/unicriumnet)

---

## ⭐ **Star Us!**

If you find Unicrium useful, please give us a star on GitHub! It helps us grow the community.

---

**Built with ⚛️ by the Unicrium Team**
