import tkinter as tk
from tkinter import messagebox

class WelcomeScreen:
    def __init__(self, root, db, login_comp):
        self._root = root
        self._db = db
        self._login_comp = login_comp
        self._root.bind("<Return>", self._enter_login)

        self._frame = tk.Frame(self._root)

        self._username_var = tk.StringVar()
        self._password_var = tk.StringVar()

        self._create_widgets()

    def show(self):
        if self._frame.winfo_exists():
            self._frame.pack(pady=100)

    def _create_widgets(self):
        tk.Label(self._frame, text="Pacemaker DCM", font=("Arial", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        tk.Label(self._frame, text="Name:").grid(row=1, column=0, sticky="e", padx=5)
        self._entry_name = tk.Entry(self._frame, textvariable=self._username_var)
        self._entry_name.grid(row=1, column=1, padx=5)
        self._entry_name.bind("<KeyRelease>", self._update_user_info)

        tk.Label(self._frame, text="Password:").grid(row=2, column=0, sticky="e", padx=5)
        self._entry_password = tk.Entry(self._frame, show="*", textvariable=self._password_var)
        self._entry_password.grid(row=2, column=1, padx=5)

        self._label_device = tk.Label(self._root, text="Last Device: -", fg="gray", font=("Arial", 10))
        self._label_device.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=40)

        self._label_mode = tk.Label(self._root, text="Last Mode: -", fg="gray", font=("Arial", 10))
        self._label_mode.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=60)

        tk.Button(self._frame, text="Register", command=self._register).grid(row=5, column=0, pady=5)
        tk.Button(self._frame, text="Login", command=self._login).grid(row=5, column=2, pady=5)

        quit_button = tk.Button(self._root, text="Quit", command=self._root.quit,
                                bg="red", fg="white", font=("Arial", 14, "bold"),
                                width=10, height=1)
        quit_button.place(relx=0.5, rely=0.5, anchor="n")

    def _login(self):
        username = self._username_var.get().strip()
        password = self._password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Error", "Please enter both username and password")
            return

        if self._db.validate_user(username, password):
            if self._frame.winfo_exists():
                self._frame.destroy()
            self._login_comp(username)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def _enter_login(self, event):
        self._login()

    def _register(self):
        username = self._username_var.get().strip()
        password = self._password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        success, msg = self._db.add_user(username, password)
        if success:
            messagebox.showinfo("Register", msg)
        else:
            messagebox.showerror("Error", msg)

    def _update_user_info(self, *args):
        username = self._username_var.get().strip()
        if not username:
            self._label_device.config(text="Last Device: -")
            self._label_mode.config(text="Last Mode: -")
            return

        devices = self._db.get_devices(username)
        last_device = list(devices.keys())[-1] if devices else "-"

        mode = self._db.get_state(username) or "-"

        self._label_device.config(text=f"Last Device: {last_device}")
        self._label_mode.config(text=f"Last Mode: {mode}")
