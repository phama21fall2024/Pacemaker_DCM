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

        self.__mode_parameters = {
            "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"],
            "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"]
        }

        # Clear existing screen
        for widget in self.__root.winfo_children():
            widget.destroy()

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

        # LED indicator
        self.__led_canvas = tk.Canvas(self.__status_frame, width=20, height=20, highlightthickness=0)
        self.__led_circle = self.__led_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.__led_canvas.pack(side="left", padx=5)

        # Status text
        self.__status_label = tk.Label(self.__status_frame, text="Not Connected", fg="red", font=("Arial", 12, "bold"))
        self.__status_label.pack(side="left", padx=5)

    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root)
        self.__param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.__param_frame, text="Parameters", fg="black", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 11))

        # Parameters
        self.__parameters = {
            "Lower Rate Limit": tk.DoubleVar(),
            "Upper Rate Limit": tk.DoubleVar(),
            "Atrial Amplitude": tk.DoubleVar(),
            "Atrial Pulse Width": tk.DoubleVar(),
            "Ventricular Amplitude": tk.DoubleVar(),
            "Ventricular Pulse Width": tk.DoubleVar(),
            "VRP": tk.DoubleVar(),
            "ARP": tk.DoubleVar()
        }

        # Slider config
        self.__param_config = {
            "Lower Rate Limit": (30, 175, 1),
            "Upper Rate Limit": (50, 175, 1),
            "Atrial Amplitude": (0.5, 7.0, 0.1),
            "Atrial Pulse Width": (0.05, 1.9, 0.05),
            "Ventricular Amplitude": (0.5, 7.0, 0.1),
            "Ventricular Pulse Width": (0.05, 1.9, 0.05),
            "VRP": (150, 500, 5),
            "ARP": (150, 500, 5)
        }

        # Load saved values
        exist = self.__db.get_parameters(self.__username)
        if exist:
            for param, var in self.__parameters.items():
                if param in exist:
                    try: var.set(float(exist[param]))
                    except: var.set(0)

        # Create sliders
        self.__sliders = {}
        row = 1
        for param, var in self.__parameters.items():
            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(row=row, column=0, sticky="e", padx=10, pady=4)

            low, high, step = self.__param_config[param]
            slider = tk.Scale(self.__param_frame, from_=low, to=high, orient="horizontal",
                              resolution=step, variable=var, length=200)
            slider.grid(row=row, column=1, padx=10, pady=4)

            tk.Label(self.__param_frame, textvariable=var, font=("Arial", 10)).grid(row=row, column=2, padx=5)

            self.__sliders[param] = slider
            row += 1

        # Save / Egram / Logout buttons
        tk.Button(self.__param_frame, text="Save", command=self.__save_parameters, bg="lightgreen", width=12)\
            .grid(row=row, column=0, pady=15, sticky="e")
        tk.Button(self.__param_frame, text="Egram", command=self.__open_egram, bg="lightblue", width=12)\
            .grid(row=row, column=1, pady=15, sticky="n")
        tk.Button(self.__param_frame, text="Logout", command=self.__logout, bg="lightcoral", width=12)\
            .grid(row=row, column=2, pady=15, sticky="w")

        # Disable sliders for current mode
        current_mode = self.__db.get_state(self.__username) or "AOO"
        self.__update_slider_states(current_mode)

    def __create_state_display(self):
        self.__state_frame = tk.Frame(self.__root)
        self.__state_frame.place(relx=0.75, rely=0.45, anchor="center")

        tk.Label(self.__state_frame, text="States", fg="black", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Pacing mode buttons
        self.__state_buttons = {}
        for name in ["AOO", "VOO", "AAI", "VVI"]:
            btn = tk.Button(self.__state_frame, text=name, width=15, height=2, bg="white",
                            font=("Arial", 10, "bold"), command=lambda n=name: self.__select_state(n))
            btn.pack(pady=10)
            self.__state_buttons[name] = btn

        last = self.__db.get_state(self.__username)
        if last and last in self.__state_buttons:
            self.__select_state(last)

    def __create_serial_display(self):
        # Serial label
        self.__serial_label = tk.Label(self.__root, text="Serial: None", font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)


    def __update_slider_states(self, mode):
        allowed = set(self.__mode_parameters.get(mode, []))
        for param, slider in self.__sliders.items():
            slider.config(state="normal" if param in allowed else "disabled")

    def __select_state(self, name):
        for state, button in self.__state_buttons.items():
            button.config(bg="lightgreen" if state == name else "white")

        last = self.__db.get_state(self.__username)
        if last:
            saved = {param: var.get() for param, var in self.__parameters.items()}
            self.__db.save_parameters(self.__username, saved, state_name=last)

        self.__db.save_state(self.__username, name)

        state_params = self.__db.get_parameters(self.__username, state_name=name)
        if state_params:
            for param, var in self.__parameters.items():
                var.set(float(state_params.get(param, 0)))
        else:
            for var in self.__parameters.values():
                var.set(0)

        self.__update_slider_states(name)


    def __open_egram(self):
        try:
            import egram_ui
            egram_ui.open_egram_window(self.__root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Egram UI:\n{e}")

    def __save_parameters(self):
        current_state = self.__db.get_state(self.__username) or "default"
        allowed = self.__mode_parameters.get(current_state, [])

        all_data = {param: var.get() for param, var in self.__parameters.items()}

        # Validate mode-specific params
        for param in all_data:
            if param not in allowed and all_data[param] != 0:
                messagebox.showerror("Invalid Parameter", f"{param} is not allowed in {current_state} mode.")
                return

        saved_data = {param: all_data[param] for param in allowed}
        _, msg = self.__db.save_parameters(self.__username, saved_data, state_name=current_state)
        messagebox.showinfo("Saved", f"{msg} (Mode: {current_state})")

    def __check_device(self):
        ports = list(serial.tools.list_ports.comports())
        if ports:
            serial_number = getattr(ports[0], "serial_number", None)
            if serial_number != self.__current_serial:
                self.__current_serial = serial_number
                self.__set_led(True)
        else:
            self.__current_serial = None
            self.__set_led(False)

        self.__update_serial_label()
        self.__root.after(2000, self.__check_device)

    def __set_led(self, connected):
        if connected:
            self.__led_canvas.itemconfig(self.__led_circle, fill="green")
            self.__status_label.config(text="Connected", fg="green")
        else:
            self.__led_canvas.itemconfig(self.__led_circle, fill="red")
            self.__status_label.config(text="Not Connected", fg="red")

    def __update_serial_label(self):
        if self.__current_serial:
            self.__serial_label.config(text=f"Serial: {self.__current_serial}", fg="black")
        else:
            self.__serial_label.config(text="Serial: None", fg="gray")

    def __logout(self):
        if self.__serial_port and getattr(self.__serial_port, "is_open", False):
            self.__serial_port.close()
        self.__logout_comp()
