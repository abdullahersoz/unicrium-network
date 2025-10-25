#!/bin/bash
echo "🚀 Unicrium Production Setup"

# Install dependencies
pip3 install -r requirements.txt

# Create directories
mkdir -p blockchain_data logs

# Create genesis
python3 config/genesis_production.py

echo "✅ Setup complete!"
