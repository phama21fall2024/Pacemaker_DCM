import tkinter as tk
from tkinter import messagebox
import serial.tools.list_ports

class Application:
    def __init__(self, root, username, db, on_logout):
        self.root = root
        self.username = username
        self.db = db
        self.on_logout = on_logout
        self.serial_port = None
        self.current_serial = None

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Pacemaker DCM")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Connection Status Display
        self.status_frame = tk.Frame(self.root)
        self.status_frame.place(relx=0, rely=0.05, anchor="nw")

        tk.Label(self.status_frame, text="Device Connection Status:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.led_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0)
        self.led_circle = self.led_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.led_canvas.pack(side="left", padx=5)
        self.status_label = tk.Label(self.status_frame, text="Not Connected", fg="red", font=("Arial", 12, "bold"))
        self.status_label.pack(side="left", padx=5)

        # Parameters Input Display
        self.param_frame = tk.Frame(self.root)
        self.param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.param_frame, text="Parameters", fg="black", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 11))

        # Initiate Required Parameters
        self.parameters = {
            "Lower Rate Limit": tk.StringVar(),
            "Upper Rate Limit": tk.StringVar(),
            "Atrial Amplitude": tk.StringVar(),
            "Atrial Pulse Width": tk.StringVar(),
            "Ventricular Amplitude": tk.StringVar(),
            "Ventricular Pulse Width": tk.StringVar(),
            "VRP": tk.StringVar(),
            "ARP": tk.StringVar()
        }

        exist = self.db.get_parameters(self.username)
        if exist:
            for param, var in self.parameters.items():
                if param in exist:
                    var.set(str(exist[param]))

        row = 1
        for param, var in self.parameters.items():
            tk.Label(self.param_frame, text=param, font=("Arial", 11)).grid(row=row, column=0, sticky="e", padx=10, pady=4)
            tk.Entry(self.param_frame, textvariable=var, width=25).grid(row=row, column=1, padx=10, pady=4)
            row += 1

        tk.Button(self.param_frame, text="Save", command=self.save_parameters, bg="lightgreen", width=12).grid(row=row, column=0, pady=15, sticky="e")
        tk.Button(self.param_frame, text="Logout", command=self.logout, bg="lightcoral", width=12).grid(row=row, column=2, pady=15, sticky="w")

        # States Displays
        self.state_frame = tk.Frame(self.root)
        self.state_frame.place(relx=0.75, rely=0.45, anchor="center")
        tk.Label(self.state_frame, text="States", fg="black", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Displays All Buttons  
        self.state_buttons = {}
        for name in ["AOO", "VOO", "AAI", "VVI"]:
            btn = tk.Button(self.state_frame, text=name, width=15, height=2, bg="white", font=("Arial", 10, "bold"),
                            command=lambda n=name: self.select_state(n))
            btn.pack(pady=10)
            self.state_buttons[name] = btn

        last_state = self.db.get_state(self.username)
        if last_state and last_state in self.state_buttons:
            self.select_state(last_state)

        # Start Checking Device Connection
        self.check_device()

    # Select States
    def select_state(self, name):
        # Checks Each State Button
        for state, button in self.state_buttons.items():
            # If State is selected, background is highlighted green
            button.config(bg="lightgreen" if state == name else "white")
        self.db.save_state(self.username, name) # Saves The State to the user


    def save_parameters(self):
        saved_data = {param: var.get() for param, var in self.parameters.items()}
        if not self.validate_parameters(saved_data):
            return
        _, msg = self.db.save_parameters(self.username, saved_data)
        messagebox.showinfo("Saved", msg)

    def validate_parameters(self, params):
        #Sets Limits for each parameters
        limits = {
            "Lower Rate Limit": (30, 175),
            "Upper Rate Limit": (50, 175),
            "Atrial Amplitude": (0.5, 7.0),
            "Atrial Pulse Width": (0.05, 1.9),
            "Ventricular Amplitude": (0.5, 7.0),
            "Ventricular Pulse Width": (0.05, 1.9),
            "VRP": (150, 500),
            "ARP": (150, 500)
        }

        # For each parameters and its value in the inputs
        for param, value in params.items():
            try:
                val = float(value) # Changes value inputted into a float
            except ValueError:
                messagebox.showerror("Invalid Input", f"{param} must be a number.") # Error when input is not a number
                return False
            low, high = limits[param] # Take low and high based on 
            if not (low <= val <= high):
                messagebox.showerror("Out of Range", f"{param} must be between {low} and {high}.")
                return False
        return True

    def check_device(self):
        ports = list(serial.tools.list_ports.comports())
        if ports:
            serial_number = getattr(ports[0], "serial_number", None)
            if serial_number != self.current_serial:
                self.current_serial = serial_number
                self.set_led(True)
        else:
            self.current_serial = None
            self.set_led(False)
        self.root.after(2000, self.check_device)

    def set_led(self, connected):
        if connected:
            self.led_canvas.itemconfig(self.led_circle, fill="green")
            self.status_label.config(text="Connected", fg="green")
        else:
            self.led_canvas.itemconfig(self.led_circle, fill="red")
            self.status_label.config(text="Not Connected", fg="red")

    def logout(self):
        if self.serial_port and getattr(self.serial_port, "is_open", False):
            self.serial_port.close()
        self.on_logout()
