#!/usr/bin/env python3
"""
Unicrium Wallet GUI with Mnemonic Support
12-word seed phrase backup
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.crypto import KeyPair
from core.mnemonic import generate_mnemonic, validate_mnemonic

BACKEND_URL = "http://localhost:5555"
WINDOW_WIDTH = 650
WINDOW_HEIGHT = 750


class UnicriumWallet:
    def __init__(self, root):
        self.root = root
        self.root.title("⚛️ Unicrium Wallet")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # Wallet data
        self.keypair = None
        self.address = None
        self.mnemonic = None
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
        
        btn_frame = tk.Frame(balance_frame)
        btn_frame.pack(pady=10)
        
        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=self.refresh_balance,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            padx=15,
            pady=5
        )
        refresh_btn.pack(side="left", padx=5)
        
        backup_btn = tk.Button(
            btn_frame,
            text="🔑 Show Seed",
            command=self.show_mnemonic,
            font=("Arial", 10),
            bg="#FF9800",
            fg="white",
            relief="flat",
            padx=15,
            pady=5
        )
        backup_btn.pack(side="left", padx=5)
        
        # Address section
        addr_frame = tk.LabelFrame(main, text="📍 Your Address", font=("Arial", 12, "bold"))
        addr_frame.pack(fill="x", pady=10)
        
        self.address_label = tk.Label(
            addr_frame,
            text="",
            font=("Arial", 9),
            wraplength=550
        )
        self.address_label.pack(pady=10)
        
        # Tabs
        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Send tab
        send_frame = tk.Frame(notebook)
        notebook.add(send_frame, text="📤 Send")
        
        tk.Label(send_frame, text="Recipient Address:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.recipient_entry = tk.Entry(send_frame, font=("Arial", 9), width=60)
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
        
        self.receive_address = tk.Text(receive_frame, height=2, font=("Arial", 9), wrap="word")
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
        
        # Restore tab
        restore_frame = tk.Frame(notebook)
        notebook.add(restore_frame, text="🔄 Restore")
        
        tk.Label(
            restore_frame,
            text="Restore wallet from 12-word seed phrase:",
            font=("Arial", 10, "bold")
        ).pack(pady=20)
        
        tk.Label(restore_frame, text="Enter your 12 words (space-separated):").pack()
        self.restore_entry = tk.Text(restore_frame, height=3, font=("Arial", 9), wrap="word")
        self.restore_entry.pack(pady=10, padx=20, fill="x")
        
        restore_btn = tk.Button(
            restore_frame,
            text="🔄 Restore Wallet",
            command=self.restore_wallet,
            font=("Arial", 10),
            bg="#9C27B0",
            fg="white",
            relief="flat",
            padx=20,
            pady=5
        )
        restore_btn.pack(pady=10)
    
    def load_or_create_wallet(self):
        """Load existing wallet or create new one"""
        wallet_file = "wallet.json"
        
        if os.path.exists(wallet_file):
            try:
                with open(wallet_file, 'r') as f:
                    data = json.load(f)
                    
                    if 'mnemonic' in data:
                        # Restore from mnemonic
                        self.mnemonic = data['mnemonic']
                        self.keypair = KeyPair.from_mnemonic(self.mnemonic)
                    else:
                        # Old wallet without mnemonic
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
        """Create new wallet with mnemonic"""
        # Generate mnemonic
        self.mnemonic = generate_mnemonic(128)  # 12 words
        
        # Create keypair from mnemonic
        self.keypair = KeyPair.from_mnemonic(self.mnemonic)
        self.address = self.keypair.get_address()
        
        # Save wallet
        with open(wallet_file, 'w') as f:
            json.dump({
                'mnemonic': self.mnemonic,
                'private_key': self.keypair.get_private_key_hex(),
                'address': self.address
            }, f)
        
        # Show mnemonic
        msg = f"New wallet created!\n\n🔑 BACKUP YOUR SEED PHRASE:\n\n{self.mnemonic}\n\n"
        msg += "⚠️ Write it down and store safely!\n⚠️ Anyone with these words can access your wallet!"
        messagebox.showwarning("IMPORTANT - Backup Seed Phrase", msg)
    
    def show_mnemonic(self):
        """Show seed phrase"""
        if not self.mnemonic:
            messagebox.showwarning("No Mnemonic", "This wallet doesn't have a seed phrase (old format)")
            return
        
        # Confirm password/PIN (simplified - in production use proper auth)
        confirm = simpledialog.askstring(
            "Confirm",
            "Enter 'SHOW' to display seed phrase:",
            show='*'
        )
        
        if confirm != "SHOW":
            messagebox.showerror("Cancelled", "Incorrect confirmation")
            return
        
        # Show mnemonic in popup
        popup = tk.Toplevel(self.root)
        popup.title("🔑 Seed Phrase")
        popup.geometry("500x300")
        popup.configure(bg="#FFF3E0")
        
        tk.Label(
            popup,
            text="⚠️ YOUR 12-WORD SEED PHRASE ⚠️",
            font=("Arial", 14, "bold"),
            bg="#FFF3E0",
            fg="#E65100"
        ).pack(pady=20)
        
        seed_text = tk.Text(popup, height=4, font=("Arial", 11), wrap="word", bg="white")
        seed_text.pack(pady=10, padx=20, fill="both", expand=True)
        seed_text.insert("1.0", self.mnemonic)
        seed_text.config(state="disabled")
        
        tk.Label(
            popup,
            text="⚠️ Never share these words with anyone!\n⚠️ Anyone with these words can access your funds!",
            font=("Arial", 9),
            bg="#FFF3E0",
            fg="#E65100"
        ).pack(pady=10)
        
        def copy_seed():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.mnemonic)
            messagebox.showinfo("Copied", "Seed phrase copied to clipboard!")
        
        tk.Button(
            popup,
            text="📋 Copy Seed Phrase",
            command=copy_seed,
            font=("Arial", 10),
            bg="#FF9800",
            fg="white",
            relief="flat",
            padx=20,
            pady=5
        ).pack(pady=10)
    
    def restore_wallet(self):
        """Restore wallet from mnemonic"""
        mnemonic = self.restore_entry.get("1.0", "end").strip()
        
        if not mnemonic:
            messagebox.showwarning("Empty", "Please enter your 12-word seed phrase")
            return
        
        # Validate mnemonic
        if not validate_mnemonic(mnemonic):
            messagebox.showerror("Invalid", "Invalid seed phrase. Please check your words.")
            return
        
        # Confirm restoration
        confirm = messagebox.askyesno(
            "Confirm Restore",
            "This will replace your current wallet. Are you sure?"
        )
        
        if not confirm:
            return
        
        try:
            # Restore from mnemonic
            self.mnemonic = mnemonic
            self.keypair = KeyPair.from_mnemonic(self.mnemonic)
            self.address = self.keypair.get_address()
            
            # Save wallet
            with open("wallet.json", 'w') as f:
                json.dump({
                    'mnemonic': self.mnemonic,
                    'private_key': self.keypair.get_private_key_hex(),
                    'address': self.address
                }, f)
            
            # Update UI
            self.address_label.config(text=self.address)
            self.receive_address.config(state="normal")
            self.receive_address.delete("1.0", "end")
            self.receive_address.insert("1.0", self.address)
            self.receive_address.config(state="disabled")
            
            self.restore_entry.delete("1.0", "end")
            self.refresh_balance()
            
            messagebox.showinfo("Success", f"Wallet restored!\n\nAddress: {self.address[:20]}...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore wallet: {e}")
    
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
        if not messagebox.askyesno("Confirm", f"Send {amount} UNI to\n{recipient[:30]}...?"):
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
