import tkinter as tk
from tkinter import messagebox

class WelcomeScreen:
    def __init__(self, root, db, on_login_success):
        self.root = root
        self.db = db
        self.on_login_success = on_login_success

        for widget in self.root.winfo_children():
            widget.destroy()

        self.frame = tk.Frame(root)
        self.frame.pack(pady=100)

        tk.Label(self.frame, text="Pacemaker DCM", font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(self.frame, text="Name:").grid(row=1, column=0, sticky="e", padx=5)
        self.entry_name = tk.Entry(self.frame)
        self.entry_name.grid(row=1, column=1, padx=5)

        tk.Label(self.frame, text="Password:").grid(row=2, column=0, sticky="e", padx=5)
        self.entry_password = tk.Entry(self.frame, show="*")
        self.entry_password.grid(row=2, column=1, padx=5)

        tk.Button(self.frame, text="Register", command=self.register).grid(row=3, column=1, pady=5)
        tk.Button(self.frame, text="Login", command=self.login).grid(row=4, column=1, pady=5)

    def login(self):
        username = self.entry_name.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Error", "Please enter both username and password")
            return

        if self.db.validate_user(username, password):
            self.frame.destroy()
            self.on_login_success(username)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def register(self):
        username = self.entry_name.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        success, msg = self.db.add_user(username, password)
        if success:
            messagebox.showinfo("Register", msg)
        else:
            messagebox.showerror("Error", msg)
