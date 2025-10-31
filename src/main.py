import tkinter as tk
from tkinter import messagebox
import serial.tools.list_ports

class Application:
    def __init__(self, root, username, db, logout):
        # Private attributes
        self.__root = root
        self.__username = username
        self.__db = db
        self.__logout_comp = logout
        self.__serial_port = None
        self.__current_serial = None

        # Clear existing widgets (if any) before creating this screen
        for widget in self.__root.winfo_children():
            widget.destroy()

        # Configure main window
        self.__root.title("Pacemaker DCM")
        self.__root.geometry("800x600")
        self.__root.resizable(False, False)

        # Initialize UI sections
        self.__create_status_display()
        self.__create_param_display()
        self.__create_state_display()
        self.__create_serial_display()

        # Start device check loop
        self.__check_device()

    def __create_status_display(self):
        self.__status_frame = tk.Frame(self.__root)
        self.__status_frame.place(relx=0, rely=0.05, anchor="nw")

        tk.Label(self.__status_frame, text="Device Connection Status:", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        # LED indicator for connection
        self.__led_canvas = tk.Canvas(self.__status_frame, width=20, height=20, highlightthickness=0)
        self.__led_circle = self.__led_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.__led_canvas.pack(side="left", padx=5)

        # Status text beside LED
        self.__status_label = tk.Label(self.__status_frame, text="Not Connected", fg="red", font=("Arial", 12, "bold"))
        self.__status_label.pack(side="left", padx=5)

    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root)
        self.__param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.__param_frame, text="Parameters", fg="black", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 11))

        # Parameters
        self.__parameters = {
            "Lower Rate Limit": tk.StringVar(),
            "Upper Rate Limit": tk.StringVar(),
            "Atrial Amplitude": tk.StringVar(),
            "Atrial Pulse Width": tk.StringVar(),
            "Ventricular Amplitude": tk.StringVar(),
            "Ventricular Pulse Width": tk.StringVar(),
            "VRP": tk.StringVar(),
            "ARP": tk.StringVar()
        }

        # Load existing parameters (if saved for this user)
        exist = self.__db.get_parameters(self.__username)   
        if exist:
            for param, var in self.__parameters.items():
                if param in exist:
                    var.set(str(exist[param]))

        # Display input fields for all parameters
        row = 1
        for param, var in self.__parameters.items():
            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(row=row, column=0, sticky="e", padx=10, pady=4)
            tk.Entry(self.__param_frame, textvariable=var, width=25).grid(row=row, column=1, padx=10, pady=4)
            row += 1

        # Save and Logout buttons
        tk.Button(self.__param_frame, text="Save", command=self.__save_parameters, bg="lightgreen", width=12).grid(row=row, column=0, pady=15, sticky="e")
        tk.Button(self.__param_frame, text="Logout", command=self.__logout, bg="lightcoral", width=12).grid(row=row, column=2, pady=15, sticky="w")

    def __create_state_display(self):
        self.__state_frame = tk.Frame(self.__root)
        self.__state_frame.place(relx=0.75, rely=0.45, anchor="center")

        tk.Label(self.__state_frame, text="States", fg="black", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Pacing modes button
        self.__state_buttons = {}
        for name in ["AOO", "VOO", "AAI", "VVI"]:
            btn = tk.Button(self.__state_frame, text=name, width=15, height=2, bg="white", font=("Arial", 10, "bold"),
                            command=lambda n=name: self.__select_state(n))
            btn.pack(pady=10)
            self.__state_buttons[name] = btn

        # Restore the last selected pacing mode (if saved)
        last_state = self.__db.get_state(self.__username)
        if last_state and last_state in self.__state_buttons:
            self.__select_state(last_state)

    def __create_serial_display(self):
        # Displays the serial number of the hardware
        self.__serial_label = tk.Label(self.__root, text="Serial: None", font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # bottom-right corner

    # PRIVATE LOGIC METHODS  

    def __select_state(self, name):
        # Highlights selecting pacing mode
        for state, button in self.__state_buttons.items():
            button.config(bg="lightgreen" if state == name else "white")
        self.__db.save_state(self.__username, name)

    def __save_parameters(self):
        # Validate then save the parameters into json
        saved_data = {param: var.get() for param, var in self.__parameters.items()}
        if not self.__validate_parameters(saved_data):
            return
        _, msg = self.__db.save_parameters(self.__username, saved_data)
        messagebox.showinfo("Saved", msg)

    def __validate_parameters(self, params):
        # Ensures parameters falls within the limits
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
        
        numeric_values = {}
        for param, value in params.items():
            try:
                val = float(value)
            except ValueError:  # If the parameter is not a number
                messagebox.showerror("Invalid Input", f"{param} must be a number.")
                return False

            low, high = limits[param]
            if not (low <= val <= high):  # If parameter is out of range
                messagebox.showerror("Out of Range", f"{param} must be between {low} and {high}.")
                return False

            numeric_values[param] = val

        if numeric_values["Lower Rate Limit"] >= numeric_values["Upper Rate Limit"]: # Checks if lower limit is higher than upper limit
            messagebox.showerror(
                "Invalid Limits",
                "Lower Rate Limit must be less than Upper Rate Limit."
            )
            return False

        return True

    def __check_device(self):
        # Checks for device every 2 seconds 
        ports = list(serial.tools.list_ports.comports())
        if ports:
            serial_number = getattr(ports[0], "serial_number", None)
            if serial_number != self.__current_serial: #Checks if the current serial number is the same as the new serial number
                self.__current_serial = serial_number
                self.__set_led(True) 
        else:
            self.__current_serial = None
            self.__set_led(False)
        self.__update_serial_label()
        self.__root.after(2000, self.__check_device)

    def __set_led(self, connected):
        # Sets LED based on connection state
        if connected :
            self.__led_canvas.itemconfig(self.__led_circle, fill="green")
            self.__status_label.config(text="Connected", fg="green")
        else:
            self.__led_canvas.itemconfig(self.__led_circle, fill="red")
            self.__status_label.config(text="Not Connected", fg="red")

    def __update_serial_label(self):
        # Update the serial labelling
        if self.__current_serial:
            self.__serial_label.config(text=f"Serial: {self.__current_serial}", fg="black")
        else:
            self.__serial_label.config(text="Serial: None", fg="gray")

    def __logout(self):
        # Handles log out and close all serial port
        if self.__serial_port and getattr(self.__serial_port, "is_open", False):
            self.__serial_port.close()
        self.__logout_comp()
