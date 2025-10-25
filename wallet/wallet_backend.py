#!/usr/bin/env python3
"""
Unicrium Wallet Backend
Transaction signing service
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.crypto import KeyPair
from blockchain.models import Transaction, TxType

app = Flask(__name__)
CORS(app)

NODE_URL = "http://91.99.170.174:5000"
BACKEND_PORT = 5555

print("╔════════════════════════════════════════════════════╗")
print("║      ⚛️  UNICRIUM WALLET BACKEND                  ║")
print("║         Transaction Signing Service               ║")
print("╚════════════════════════════════════════════════════╝")
print(f"✓ Node: {NODE_URL}")
print(f"✓ Backend: http://localhost:{BACKEND_PORT}")
print("🔐 Features:")
print("   - Transaction signing")
print("   - Balance queries")
print("   - Node communication")


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "wallet-backend"})


@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """Get balance from node"""
    try:
        response = requests.get(f"{NODE_URL}/balance/{address}", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/info', methods=['GET'])
def get_info():
    """Get blockchain info"""
    try:
        response = requests.get(f"{NODE_URL}/info", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/transaction/send', methods=['POST'])
def send_transaction():
    """Create, sign and send transaction"""
    try:
        data = request.json
        
        sender = data.get('sender')
        recipient = data.get('recipient')
        amount = data.get('amount')
        private_key = data.get('private_key')
        
        if not all([sender, recipient, amount, private_key]):
            return jsonify({"error": "Missing required fields"}), 400
        
        amount_units = int(float(amount) * 10**8)
        
        # Get nonce
        balance_response = requests.get(f"{NODE_URL}/balance/{sender}", timeout=5)
        if balance_response.status_code != 200:
            return jsonify({"error": "Failed to get nonce"}), 500
        
        nonce = balance_response.json().get('nonce', 0)
        
        # Create transaction
        tx = Transaction(
            sender=sender,
            nonce=nonce,
            tx_type=TxType.TRANSFER.value,
            amount=amount_units,
            recipient=recipient,
            fee=1000000,
            timestamp=int(time.time())
        )
        
        # Sign
        keypair = KeyPair.from_private_key(private_key)
        tx.sign(keypair)
        
        # Send to node
        submit_response = requests.post(
            f"{NODE_URL}/transaction",
            json=tx.to_dict(),
            timeout=10
        )
        
        if submit_response.status_code == 200:
            return jsonify({
                "success": True,
                "txid": tx.hash,
                "message": "Transaction sent successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": submit_response.text
            }), submit_response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting server...")
    app.run(host='127.0.0.1', port=BACKEND_PORT, debug=False)
