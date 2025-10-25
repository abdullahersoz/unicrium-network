#!/usr/bin/env python3
"""
Unicrium Network Faucet
Distributes test coins to addresses
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging
from typing import Dict, Optional

# Import from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.crypto import KeyPair
from blockchain.models import Transaction, TxType

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FAUCET_AMOUNT = 1000 * 10**8  # 1000 UNI per claim
CLAIM_COOLDOWN = 86400  # 24 hours
NODE_URL = "http://localhost:5000"

# Faucet keypair (load from environment or config)
FAUCET_PRIVATE_KEY = "your_faucet_private_key_here"
FAUCET_ADDRESS = "0xfaucet123456789abcdef123456789abcdef12345"

# Track claims
last_claims: Dict[str, float] = {}


print("╔════════════════════════════════════════════════════╗")
print("║      💧 UNICRIUM NETWORK FAUCET                   ║")
print("╚════════════════════════════════════════════════════╝")
print(f"✓ Amount per claim: {FAUCET_AMOUNT / 10**8:,.0f} UNI")
print(f"✓ Cooldown: {CLAIM_COOLDOWN / 3600:.0f} hours")
print(f"✓ Node: {NODE_URL}")
print()


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "faucet"})


@app.route('/info', methods=['GET'])
def info():
    """Faucet information"""
    return jsonify({
        "faucet_address": FAUCET_ADDRESS,
        "amount_per_claim": FAUCET_AMOUNT,
        "amount_formatted": f"{FAUCET_AMOUNT / 10**8:,.2f} UNI",
        "cooldown_seconds": CLAIM_COOLDOWN,
        "cooldown_hours": CLAIM_COOLDOWN / 3600
    })


@app.route('/balance', methods=['GET'])
def get_faucet_balance():
    """Get faucet balance"""
    try:
        response = requests.get(f"{NODE_URL}/balance/{FAUCET_ADDRESS}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('balance', 0)
            return jsonify({
                "address": FAUCET_ADDRESS,
                "balance": balance,
                "formatted": f"{balance / 10**8:,.2f} UNI",
                "can_fund": balance >= FAUCET_AMOUNT
            })
        else:
            return jsonify({"error": "Failed to get balance"}), 500
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/claim', methods=['POST'])
def claim():
    """Claim coins from faucet"""
    try:
        data = request.json
        recipient = data.get('address')
        
        if not recipient:
            return jsonify({
                "success": False,
                "error": "Address required"
            }), 400
        
        # Validate address format
        if not recipient.startswith('0x') or len(recipient) != 42:
            return jsonify({
                "success": False,
                "error": "Invalid address format"
            }), 400
        
        # Check cooldown
        now = time.time()
        last_claim = last_claims.get(recipient, 0)
        if now - last_claim < CLAIM_COOLDOWN:
            remaining = CLAIM_COOLDOWN - (now - last_claim)
            return jsonify({
                "success": False,
                "error": "Cooldown active",
                "retry_after_seconds": int(remaining),
                "retry_after_hours": remaining / 3600
            }), 429
        
        # Get faucet balance
        balance_response = requests.get(f"{NODE_URL}/balance/{FAUCET_ADDRESS}", timeout=5)
        if balance_response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Failed to check faucet balance"
            }), 500
        
        faucet_balance = balance_response.json().get('balance', 0)
        if faucet_balance < FAUCET_AMOUNT:
            return jsonify({
                "success": False,
                "error": "Faucet is empty",
                "faucet_balance": f"{faucet_balance / 10**8:,.2f} UNI"
            }), 503
        
        # Get nonce
        nonce = balance_response.json().get('nonce', 0)
        
        # Create transaction
        tx = Transaction(
            sender=FAUCET_ADDRESS,
            nonce=nonce,
            tx_type=TxType.TRANSFER.value,
            amount=FAUCET_AMOUNT,
            recipient=recipient,
            fee=1000000,  # 0.01 UNI
            timestamp=int(time.time())
        )
        
        # Sign transaction
        keypair = KeyPair.from_private_key(FAUCET_PRIVATE_KEY)
        tx.sign(keypair)
        
        # Submit to node
        submit_response = requests.post(
            f"{NODE_URL}/transaction",
            json=tx.to_dict(),
            timeout=10
        )
        
        if submit_response.status_code == 200:
            # Update cooldown
            last_claims[recipient] = now
            
            logger.info(f"💧 Faucet claim: {FAUCET_AMOUNT / 10**8:,.0f} UNI → {recipient[:10]}...")
            
            return jsonify({
                "success": True,
                "amount": FAUCET_AMOUNT,
                "formatted": f"{FAUCET_AMOUNT / 10**8:,.0f} UNI",
                "txid": tx.hash,
                "recipient": recipient,
                "message": f"Successfully sent {FAUCET_AMOUNT / 10**8:,.0f} UNI!",
                "next_claim_available": now + CLAIM_COOLDOWN
            })
        else:
            return jsonify({
                "success": False,
                "error": "Transaction failed",
                "details": submit_response.text
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing claim: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/recent', methods=['GET'])
def recent_claims():
    """Get recent claims"""
    # Return last 10 claims
    sorted_claims = sorted(last_claims.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        "recent_claims": [
            {
                "address": addr,
                "timestamp": ts,
                "time_ago": int(time.time() - ts)
            }
            for addr, ts in sorted_claims
        ]
    })


if __name__ == '__main__':
    print("🚀 Starting faucet server...")
    app.run(host='0.0.0.0', port=5001, debug=False)
