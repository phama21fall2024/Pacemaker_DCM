import tkinter as tk
from tkinter import messagebox
from rounding_helper import RoundingHelper
import serial.tools.list_ports
import send_uart

class Application:
    def __init__(self, root, username, db, logout):
        self.__root = root
        self.__username = username
        self.__db = db
        self.__logout_comp = logout
        self.__serial_port = None
        self.__current_serial = None

        self.__mode_parameters = {
            "AOO":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOO":  ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAI":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"],
            "VVI":  ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"],

            "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width","Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"]
        }

        for widget in self.__root.winfo_children():
            widget.destroy()

        self.__root.title("Pacemaker DCM")
        self.__root.geometry("800x600")
        self.__root.resizable(False, False)

        self.__create_status_display()
        self.__create_param_display()
        self.__create_state_display()
        self.__create_serial_display()

        self.__check_device()

    def __create_status_display(self):
        self.__status_frame = tk.Frame(self.__root)
        self.__status_frame.place(relx=0, rely=0.05, anchor="nw")

        tk.Label(self.__status_frame, text="Device Connection Status:", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        self.__led_canvas = tk.Canvas(self.__status_frame, width=20, height=20, highlightthickness=0)
        self.__led_circle = self.__led_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.__led_canvas.pack(side="left", padx=5)

        self.__status_label = tk.Label(self.__status_frame, text="Not Connected", fg="red", font=("Arial", 12, "bold"))
        self.__status_label.pack(side="left", padx=5)
    
    def __round_and_set(self, param_name, var, sv, slider, lo, hi, step):
        
        if param_name == "Lower Rate Limit":
            rounded = RoundingHelper.round_lrl(sv.get(), lo, hi)
        else:
            rounded = RoundingHelper.round_value(sv.get(), lo, hi, step)

        if rounded is None:
            sv.set(str(var.get()))
            return

        var.set(rounded)
        slider.set(rounded)
        sv.set(str(rounded))

    def __adjust_lrl_step(self, value):
        value = int(value)
        if 30 <= value <= 50:
            step = 5
            base = 30
        elif 50 < value <= 90:
            step = 1
            base = 51
        else:
            step = 5
            base = 90
        snapped = base + round((value - base) / step) * step
        return max(30, min(175, snapped))


    def __rebuild_parameter_rows(self, mode):
        for widget in self.__param_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:
                widget.grid_forget()

        row = 1
        allowed = self.__mode_parameters.get(mode, [])
        self.__sliders = {}
        self.__value_entries = {}

        for param in allowed:
            var = self.__parameters[param]
            low, high, step = self.__param_config[param]

            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(
                row=row, column=0, sticky="e", padx=10, pady=4
            )

            val_var = tk.StringVar()
            val_var.set(str(var.get()))

            if param == "Lower Rate Limit":
                slider = tk.Scale(
                    self.__param_frame,
                    from_=low,
                    to=high,
                    orient="horizontal",
                    resolution=1,
                    variable=var,
                    length=200
                )

                def on_lrl_move(*args, v=var, sv=val_var, s=slider):
                    current = v.get()
                    snapped = self.__adjust_lrl_step(current)
                    if snapped != current:
                        v.set(snapped)
                        s.set(snapped)
                    sv.set(str(snapped))

                var.trace_add("write", on_lrl_move)

            else:
                slider = tk.Scale(
                    self.__param_frame,
                    from_=low,
                    to=high,
                    orient="horizontal",
                    resolution=step,
                    variable=var,
                    length=200
                )

                def on_slider_change(*args, v=var, sv=val_var):
                    sv.set(str(v.get()))

                var.trace_add("write", on_slider_change)

            slider.grid(row=row, column=1, padx=10, pady=4)

            entry = tk.Entry(self.__param_frame, textvariable=val_var, width=6)
            entry.grid(row=row, column=2, padx=5)

            entry.bind("<Return>", lambda e, p=param, v=var, sv=val_var, s=slider, lo=low, hi=high, st=step: self.__round_and_set(p, v, sv, s, lo, hi, st))
            entry.bind("<FocusOut>", lambda e, p=param, v=var, sv=val_var, s=slider, lo=low, hi=high, st=step: self.__round_and_set(p, v, sv, s, lo, hi, st))

            self.__sliders[param] = slider
            self.__value_entries[param] = entry
            row += 1

        tk.Button(self.__param_frame, text="Save", command=self.__save_parameters, bg="lightgreen", width=12).grid(row=row, column=0, pady=15)
        tk.Button(self.__param_frame, text="Egram", command=self.__open_egram, bg="lightblue", width=12).grid(row=row, column=1, pady=15)
        tk.Button(self.__param_frame, text="Logout", command=self.__logout, bg="lightcoral", width=12).grid(row=row, column=2, pady=15)
        tk.Button(self.__param_frame, text="Send to Device", bg="lightyellow", width=12, command=self.__send_to_device).grid(row=row+1, column=1, pady=10)

    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root)
        self.__param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.__param_frame, text="Parameters", fg="black", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 11)
        )

        self.__parameters = {
            "Lower Rate Limit": tk.DoubleVar(),
            "Upper Rate Limit": tk.DoubleVar(),
            "Atrial Amplitude": tk.DoubleVar(),
            "Atrial Pulse Width": tk.DoubleVar(),
            "Ventricular Amplitude": tk.DoubleVar(),
            "Ventricular Pulse Width": tk.DoubleVar(),
            "Atrial Sensitivity": tk.DoubleVar(),
            "Ventricular Sensitivity": tk.DoubleVar(),
            "PVARP": tk.DoubleVar(),
            "Hysteresis": tk.DoubleVar(),
            "Rate Smoothing": tk.DoubleVar(),
            "VRP": tk.DoubleVar(),
            "ARP": tk.DoubleVar()
        }

        self.__param_config = {
            "Lower Rate Limit": (30, 175, 1),
            "Upper Rate Limit": (50, 175, 5),
            "Atrial Amplitude": (0.5, 7.0, 0.1),
            "Atrial Pulse Width": (0.05, 1.9, 0.05),
            "Ventricular Amplitude": (0.5, 7.0, 0.1),
            "Ventricular Pulse Width": (0.05, 1.9, 0.05),
            "Atrial Sensitivity": (0.25, 10.0, 0.25),        
            "Ventricular Sensitivity": (1.0, 10.0, 0.5),
            "PVARP": (150, 500, 10),
            "Hysteresis": (0, 175, 1),                         
            "Rate Smoothing": (0, 25, 1),
            "VRP": (150, 500, 5),
            "ARP": (150, 500, 5)
        }

        exist = self.__db.get_parameters(self.__username)
        if exist:
            for param, var in self.__parameters.items():
                if param in exist:
                    try:
                        var.set(float(exist[param]))
                    except:
                        var.set(0)

        self.__sliders = {}
        self.__value_entries = {}
        row = 1

        for param, var in self.__parameters.items():
            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(
                row=row, column=0, sticky="e", padx=10, pady=4
            )

            low, high, step = self.__param_config[param]

            slider = tk.Scale(
                self.__param_frame,
                from_=low,
                to=high,
                orient="horizontal",
                resolution=step,
                variable=var,
                length=200
            )
            slider.grid(row=row, column=1, padx=10, pady=4)

            val_var = tk.StringVar()
            val_var.set(str(var.get()))
            entry = tk.Entry(self.__param_frame, textvariable=val_var, width=6)
            entry.grid(row=row, column=2, padx=5)

            entry.bind("<Return>", lambda e, p=param, v=var, sv=val_var, s=slider, lo=low, hi=high, st=step: self.__round_and_set(v, sv, s, lo, hi, st))
            entry.bind("<FocusOut>", lambda e, p=param, v=var, sv=val_var, s=slider, lo=low, hi=high, st=step: self.__round_and_set(v, sv, s, lo, hi, st))

            def on_slider_change(*args, v=var, sv=val_var):
                sv.set(str(v.get()))

            var.trace_add("write", on_slider_change)

            self.__sliders[param] = slider
            self.__value_entries[param] = entry
            row += 1

        tk.Button(self.__param_frame, text="Save", command=self.__save_parameters, bg="lightgreen", width=12).grid(
            row=row, column=0, pady=15, sticky="e"
        )
        tk.Button(self.__param_frame, text="Egram", command=self.__open_egram, bg="lightblue", width=12).grid(
            row=row, column=1, pady=15
        )
        tk.Button(self.__param_frame, text="Logout", command=self.__logout, bg="lightcoral", width=12).grid(
            row=row, column=2, pady=15, sticky="w"
        )
        tk.Button(self.__param_frame, text="Send to Device", bg="lightyellow", width=12,
                command=self.__send_to_device).grid(row=row + 1, column=1, pady=10)

        current_mode = self.__db.get_state(self.__username) or "AOO"
        self.__rebuild_parameter_rows(current_mode)

    def __create_state_display(self):
        self.__state_frame = tk.Frame(self.__root)
        self.__state_frame.place(relx=0.75, rely=0.45, anchor="center")

        tk.Label(self.__state_frame, text="States", fg="black", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        self.__state_buttons = {}
        for name in ["AOO", "VOO", "AAI", "VVI", "AOOR", "VOOR", "AAIR", "VVIR"]:
            btn = tk.Button(self.__state_frame, text=name, width=15, height=2, bg="white",
                            font=("Arial", 10, "bold"), command=lambda n=name: self.__select_state(n))
            btn.pack(pady=5)
            self.__state_buttons[name] = btn

        last = self.__db.get_state(self.__username)
        if last and last in self.__state_buttons:
            self.__select_state(last)

    def __create_serial_display(self):
        self.__serial_label = tk.Label(self.__root, text="Serial: None", font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def __select_state(self, name):
        # Highlight button
        for state, button in self.__state_buttons.items():
            button.config(bg="lightgreen" if state == name else "white")

        # Save previous state's values, but **only allowed ones**
        last = self.__db.get_state(self.__username)
        if last:
            allowed_last = self.__mode_parameters.get(last, [])
            saved = {}

            for param, var in self.__parameters.items():
                if param in allowed_last:
                    saved[param] = var.get()

            self.__db.save_parameters(self.__username, saved, state_name=last)

        # Update current state
        self.__db.save_state(self.__username, name)

        # Load parameters for the new state
        state_params = self.__db.get_parameters(self.__username, state_name=name)
        allowed_new = self.__mode_parameters.get(name, [])

        if state_params:
            for param, var in self.__parameters.items():
                if param in allowed_new:
                    var.set(float(state_params.get(param, 0)))
                else:
                    var.set(0)
        else:
            for var in self.__parameters.values():
                var.set(0)

        # Rebuild GUI sliders
        self.__rebuild_parameter_rows(name)

    def __open_egram(self):
        try:
            import egram_ui
            egram_ui.open_egram_window(self.__root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Egram UI:\n{e}")

    def __save_parameters(self):
        current_state = self.__db.get_state(self.__username) or "default"
        allowed = self.__mode_parameters.get(current_state, [])

        # LRL / URL validation
        lrl = self.__parameters["Lower Rate Limit"].get()
        url = self.__parameters["Upper Rate Limit"].get()

        if lrl > url:
            messagebox.showerror(
                "Invalid Parameter",
                "Lower Rate Limit cannot be greater than Upper Rate Limit."
            )
            return

        # Your original logic
        all_data = {param: var.get() for param, var in self.__parameters.items()}
        saved_data = {}

        for param, value in all_data.items():
            if param in allowed:
                saved_data[param] = value
            else:
                self.__parameters[param].set(0)

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

    def __send_to_device(self):
        sender = send_uart.UARTSender()
        try:
            sent = sender.send_to_device(self.__username)
            messagebox.showinfo("Success", f"Sent to device:\n{sent}")
        except Exception as e:
            messagebox.showerror("UART Error", str(e))

    def __logout(self):
        if self.__serial_port and getattr(self.__serial_port, "is_open", False):
            self.__serial_port.close()
        self.__logout_comp()
