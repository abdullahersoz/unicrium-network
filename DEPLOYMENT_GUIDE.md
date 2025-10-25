# 🚀 Unicrium Network - Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux
- Python 3.10+
- 4GB+ RAM
- 50GB+ disk space
- Root/sudo access

## Quick Deploy

```bash
# 1. Extract package
tar -xzf unicrium-production-ready.tar.gz
cd unicrium-production-ready

# 2. Run setup
sudo bash deployment/setup.sh

# 3. Create genesis
python3 config/genesis_production.py

# 4. Start services
python3 blockchain/node.py &
python3 network/api_server.py &
python3 tools/faucet.py &
```

## Systemd Services

```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Enable services
sudo systemctl enable unicrium-node
sudo systemctl enable unicrium-api
sudo systemctl enable unicrium-faucet

# Start services
sudo systemctl start unicrium-node
sudo systemctl start unicrium-api  
sudo systemctl start unicrium-faucet

# Check status
sudo systemctl status unicrium-*
```

## Configuration

Edit `config/config_production.py` for custom settings.

## Monitoring

```bash
# View logs
tail -f /var/log/unicrium-node.log
tail -f /var/log/unicrium-api.log

# Check blockchain
curl http://localhost:5000/info

# Check balance
curl http://localhost:5000/balance/0xbfb0ccc63e08e83eec1a5f7925ce3a655b530d67
```

## Troubleshooting

### Genesis fails
```bash
rm -rf blockchain_data/
python3 config/genesis_production.py
```

### API not responding
```bash
sudo systemctl restart unicrium-api
curl http://localhost:5000/health
```

### Port conflicts
Edit port numbers in config files.

## Support

- GitHub Issues: https://github.com/yourusername/unicrium-network/issues
- Email: support@unicrium.network
