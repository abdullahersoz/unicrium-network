"""
Unicrium API Server
FastAPI-based high-performance API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blockchain.blockchain import Blockchain
from blockchain.models import Transaction

app = FastAPI(title="Unicrium API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize blockchain
chain = Blockchain()


@app.get("/")
def root():
    """API root"""
    return {"name": "Unicrium API", "version": "1.0"}


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok"}


@app.get("/info")
def get_info():
    """Blockchain info"""
    return {
        "chain_id": chain.chain_id,
        "height": chain.get_height(),
        "validators": len(chain.consensus.get_active_validators())
    }


@app.get("/balance/{address}")
def get_balance(address: str):
    """Get balance"""
    balance = chain.get_balance(address)
    return {
        "address": address,
        "balance": balance,
        "formatted": f"{balance / 10**8:.8f} UNI"
    }


@app.post("/transaction")
def submit_transaction(tx_data: dict):
    """Submit transaction"""
    try:
        tx = Transaction.from_dict(tx_data)
        if chain.add_transaction(tx):
            return {"success": True, "txid": tx.hash}
        else:
            raise HTTPException(400, "Invalid transaction")
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/blocks/latest")
def get_latest_blocks(limit: int = 10):
    """Get latest blocks"""
    blocks = chain.blocks[-limit:]
    return {"blocks": [b.to_dict() for b in blocks]}


@app.get("/block/{height}")
def get_block(height: int):
    """Get block by height"""
    if height < 0 or height >= len(chain.blocks):
        raise HTTPException(404, "Block not found")
    return chain.blocks[height].to_dict()


if __name__ == "__main__":
    print("🚀 Starting Unicrium API Server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
