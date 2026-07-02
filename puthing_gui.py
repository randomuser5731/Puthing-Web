#!/usr/bin/env python3
"""
Puthing Around - GUI Server
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

# Ensure puthing_server.py is in path
sys.path.insert(0, str(Path(__file__).parent))

from puthing_server import (
    init_db, set_code, get_code, serve as start_server, get_stats, set_winner, get_winner, reset_all
)

DB_PATH = Path(__file__).parent / "puthing.db"
DEFAULT_PORT = 8787


class PuthingGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Puthing Around Server")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        
        self.server_running = False
        self.server_instance = None
        
        self.setup_ui()
        self.check_db()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="PUTHING AROUND", font=("Courier", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status
        self.status_var = tk.StringVar(value="Status: Stopped")
        ttk.Label(main_frame, textvariable=self.status_var, font=("Courier", 10)).grid(
            row=1, column=0, columnspan=3, pady=(0, 5)
        )
        
        # URL
        self.url_var = tk.StringVar(value=f"http://localhost:{DEFAULT_PORT}")
        ttk.Label(main_frame, textvariable=self.url_var, font=("Courier", 9)).grid(
            row=2, column=0, columnspan=3, pady=(0, 20)
        )
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(0, 20))
        
        self.start_btn = ttk.Button(btn_frame, text="START SERVER", command=self.start_server)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(btn_frame, text="STOP SERVER", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.reset_btn = ttk.Button(btn_frame, text="RESET ALL", command=self.reset_all)
        self.reset_btn.grid(row=0, column=2)
        
        # Config frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(config_frame, text="Set Code", command=self.set_code_dialog).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(config_frame, text="Set Winner", command=self.set_winner_dialog).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(config_frame, text="View Stats", command=self.view_stats).grid(row=0, column=2)
        
        # Log
        ttk.Label(main_frame, text="Log:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = tk.Text(main_frame, height=6, width=50, font=("Courier", 8))
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        
    def check_db(self):
        if not DB_PATH.exists():
            init_db()
            self.log("Database created.")
        else:
            self.log("Database found.")
            
        code = get_code()
        if code:
            self.log(f"Current code: {'*' * len(code)}")
        else:
            self.log("No code set yet.")
            
    def start_server(self):
        if self.server_running:
            return
            
        self.server_running = True
        self.status_var.set("Status: Running")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def run():
            try:
                self.log("Starting server...")
                start_server(DEFAULT_PORT)
            except Exception as e:
                self.log(f"Error: {e}")
                self.server_running = False
                self.status_var.set("Status: Stopped")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                
        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.log(f"Server running at http://localhost:{DEFAULT_PORT}")
        
    def stop_server(self):
        self.server_running = False
        self.status_var.set("Status: Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Server stopped.")
        
    def set_code_dialog(self):
        code = simpledialog.askstring("Set Code", "Enter new secret code:", show='*')
        if code:
            set_code(code)
            self.log(f"Code updated: {'*' * len(code)}")
            messagebox.showinfo("Success", "Code updated successfully!")
            
    def set_winner_dialog(self):
        name = simpledialog.askstring("Set Winner", "Enter winner name:")
        if name:
            result = set_winner(name)
            winner = result.get("winner", "Unknown")
            self.log(f"Winner set to: {winner}")
            messagebox.showinfo("Success", f"Winner set to: {winner}")
            
    def view_stats(self):
        stats = get_stats()
        msg = f"Total Attempts: {stats['total_attempts']}\nTotal Solved: {stats['total_solved']}"
        messagebox.showinfo("Statistics", msg)
        
    def reset_all(self):
        if messagebox.askyesno("Reset All", "This will reset the database and winner. Continue?"):
            result = reset_all()
            self.log(f"Reset complete. Local: {result.get('local', 'ok')}, Supabase: {result.get('supabase', 'ok')}")
            messagebox.showinfo("Reset", "All data has been reset.")
            self.check_db()
        
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PuthingGUI()
    app.run()
