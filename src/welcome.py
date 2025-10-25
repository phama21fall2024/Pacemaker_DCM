import tkinter as tk
from tkinter import messagebox

class WelcomeScreen:
    def __init__(self, root, db, on_login_success):
        self._root = root
        self._db = db
        self._on_login_success = on_login_success

        # Create a frame but don't destroy anything yet
        self._frame = tk.Frame(self._root)

        # Build all widgets
        self._create_widgets()

    def show(self):
        # Only pack if frame still exists
        if self._frame.winfo_exists():
            self._frame.pack(pady=100)

    def _create_widgets(self):
        # Create the Pacemaker DCM title
        tk.Label(self._frame, text="Pacemaker DCM", font=("Arial", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )
        # Creat name and password labels/input fields
        tk.Label(self._frame, text="Name:").grid(row=1, column=0, sticky="e", padx=5)
        self._entry_name = tk.Entry(self._frame)
        self._entry_name.grid(row=1, column=1, padx=5)

        tk.Label(self._frame, text="Password:").grid(row=2, column=0, sticky="e", padx=5)
        self._entry_password = tk.Entry(self._frame, show="*")
        self._entry_password.grid(row=2, column=1, padx=5)

        # Create buttons for register and login
        tk.Button(self._frame, text="Register", command=self._register).grid(row=3, column=1, pady=5)
        tk.Button(self._frame, text="Login", command=self._login).grid(row=4, column=1, pady=5)

        # Quit button (top-right corner)
        quit_button = tk.Button(self._root, text="Quit", command=self._root.quit, bg="red", fg="white")
        quit_button.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

    def _login(self):
        username = self._entry_name.get().strip()
        password = self._entry_password.get().strip()

        if not username or not password: # Checks if there is a username or password inputted 
            messagebox.showwarning("Error", "Please enter both username and password")
            return

        # Make sures that the user is valid, function in datamanager
        if self._db.validate_user(username, password):
            self._frame.destroy()
            self._on_login_success(username)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def _register(self):
        username = self._entry_name.get().strip()
        password = self._entry_password.get().strip()

        if not username or not password: # Checks if there is a username or password inputted 
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        success, msg = self._db.add_user(username, password)
        if success:
            messagebox.showinfo("Register", msg)
        else:
            messagebox.showerror("Error", msg)
