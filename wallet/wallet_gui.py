#!/usr/bin/env python3
"""
Unicrium Wallet GUI
Desktop wallet application
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.crypto import KeyPair

BACKEND_URL = "http://localhost:5555"
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 700


class UnicriumWallet:
    def __init__(self, root):
        self.root = root
        self.root.title("⚛️ Unicrium Wallet")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # Wallet data
        self.keypair = None
        self.address = None
        self.balance = 0
        
        self.create_widgets()
        self.load_or_create_wallet()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Header
        header = tk.Frame(self.root, bg="#2196F3", height=80)
        header.pack(fill="x")
        
        title = tk.Label(
            header,
            text="⚛️ UNICRIUM WALLET",
            font=("Arial", 20, "bold"),
            bg="#2196F3",
            fg="white"
        )
        title.pack(pady=20)
        
        # Main container
        main = tk.Frame(self.root, bg="white")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Balance section
        balance_frame = tk.LabelFrame(main, text="💰 Balance", font=("Arial", 12, "bold"))
        balance_frame.pack(fill="x", pady=10)
        
        self.balance_label = tk.Label(
            balance_frame,
            text="0.00000000 UNI",
            font=("Arial", 24, "bold"),
            fg="#2196F3"
        )
        self.balance_label.pack(pady=20)
        
        refresh_btn = tk.Button(
            balance_frame,
            text="🔄 Refresh",
            command=self.refresh_balance,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            padx=20,
            pady=5
        )
        refresh_btn.pack(pady=10)
        
        # Address section
        addr_frame = tk.LabelFrame(main, text="📍 Your Address", font=("Arial", 12, "bold"))
        addr_frame.pack(fill="x", pady=10)
        
        self.address_label = tk.Label(
            addr_frame,
            text="",
            font=("Arial", 10),
            wraplength=500
        )
        self.address_label.pack(pady=10)
        
        # Tabs
        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Send tab
        send_frame = tk.Frame(notebook)
        notebook.add(send_frame, text="📤 Send")
        
        tk.Label(send_frame, text="Recipient Address:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.recipient_entry = tk.Entry(send_frame, font=("Arial", 10), width=50)
        self.recipient_entry.pack(pady=5)
        
        tk.Label(send_frame, text="Amount (UNI):", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.amount_entry = tk.Entry(send_frame, font=("Arial", 10), width=20)
        self.amount_entry.pack(pady=5)
        
        send_btn = tk.Button(
            send_frame,
            text="📤 Send Transaction",
            command=self.send_transaction,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            relief="flat",
            padx=30,
            pady=10
        )
        send_btn.pack(pady=20)
        
        # Receive tab
        receive_frame = tk.Frame(notebook)
        notebook.add(receive_frame, text="📥 Receive")
        
        tk.Label(
            receive_frame,
            text="Share this address to receive UNI:",
            font=("Arial", 10, "bold")
        ).pack(pady=20)
        
        self.receive_address = tk.Text(receive_frame, height=3, font=("Arial", 10), wrap="word")
        self.receive_address.pack(pady=10, padx=20, fill="x")
        
        copy_btn = tk.Button(
            receive_frame,
            text="📋 Copy Address",
            command=self.copy_address,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            padx=20,
            pady=5
        )
        copy_btn.pack(pady=10)
    
    def load_or_create_wallet(self):
        """Load existing wallet or create new one"""
        wallet_file = "wallet.json"
        
        if os.path.exists(wallet_file):
            try:
                with open(wallet_file, 'r') as f:
                    data = json.load(f)
                    self.keypair = KeyPair.from_private_key(data['private_key'])
                    self.address = self.keypair.get_address()
                    messagebox.showinfo("Success", "Wallet loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load wallet: {e}")
                self.create_new_wallet(wallet_file)
        else:
            self.create_new_wallet(wallet_file)
        
        self.address_label.config(text=self.address)
        self.receive_address.insert("1.0", self.address)
        self.receive_address.config(state="disabled")
        self.refresh_balance()
    
    def create_new_wallet(self, wallet_file):
        """Create new wallet"""
        self.keypair = KeyPair.generate()
        self.address = self.keypair.get_address()
        
        # Save wallet
        with open(wallet_file, 'w') as f:
            json.dump({
                'private_key': self.keypair.get_private_key_hex(),
                'address': self.address
            }, f)
        
        messagebox.showinfo("New Wallet", f"New wallet created!\n\nAddress: {self.address[:20]}...")
    
    def refresh_balance(self):
        """Refresh balance from backend"""
        try:
            response = requests.get(f"{BACKEND_URL}/balance/{self.address}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.balance = data.get('balance', 0)
                formatted = f"{self.balance / 10**8:,.8f} UNI"
                self.balance_label.config(text=formatted)
            else:
                messagebox.showerror("Error", "Failed to get balance")
        except Exception as e:
            messagebox.showerror("Error", f"Backend not running!\n\n{e}")
    
    def send_transaction(self):
        """Send transaction"""
        recipient = self.recipient_entry.get().strip()
        amount = self.amount_entry.get().strip()
        
        if not recipient or not amount:
            messagebox.showwarning("Invalid Input", "Please fill all fields")
            return
        
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                messagebox.showwarning("Invalid Amount", "Amount must be positive")
                return
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Amount must be a number")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm", f"Send {amount} UNI to\n{recipient[:20]}...?"):
            return
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/transaction/send",
                json={
                    'sender': self.address,
                    'recipient': recipient,
                    'amount': amount,
                    'private_key': self.keypair.get_private_key_hex()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    messagebox.showinfo("Success", f"Transaction sent!\n\nTXID: {data['txid'][:20]}...")
                    self.recipient_entry.delete(0, tk.END)
                    self.amount_entry.delete(0, tk.END)
                    self.root.after(2000, self.refresh_balance)
                else:
                    messagebox.showerror("Error", data.get('error', 'Unknown error'))
            else:
                messagebox.showerror("Error", "Transaction failed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send transaction!\n\n{e}")
    
    def copy_address(self):
        """Copy address to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.address)
        messagebox.showinfo("Copied", "Address copied to clipboard!")


if __name__ == '__main__':
    root = tk.Tk()
    app = UnicriumWallet(root)
    root.mainloop()
