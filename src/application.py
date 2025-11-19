import tkinter as tk
from tkinter import messagebox
from rounding_helper import RoundingHelper
import serial.tools.list_ports
import send_uart
import egram_manager
from uart_receiver import UARTReceiver


class Application:
    def __init__(self, root, username, db, logout):
        self.__root = root
        self.__username = username
        self.__db = db
        self.__logout_comp = logout
        self.__serial_port = None
        self.__current_serial = None
        self.__uart_receiver = None
        self.__egram_queue = egram_manager.FloatQueue()

        self.__mode_parameters = {
            "AOO":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOO":  ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAI":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVI":  ["Lower Rate Limit", "Upper Rate Limit",  "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
            "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"]
        }

        for widget in self.__root.winfo_children():
            widget.destroy()

        self.__root.title("Pacemaker DCM")
        self.__root.geometry("800x600")
        self.__root.resizable(False, False)

        self.__create_status_display()
        self.__create_param_display()
        self.__create_state_display()
        self.__create_egram_panel()
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


    def __create_egram_panel(self):
        self.__egram_frame = tk.Frame(self.__root)

        # Center-right of the window
        self.__egram_frame.place(relx=0.50, rely=0.50, anchor="center")

        tk.Label(self.__egram_frame, text="Egram Viewer",
                font=("Arial", 12, "bold")).pack(pady=5)

        tk.Button(self.__egram_frame, text="Atrial Egram", width=18,
                bg="lightblue",
                command=lambda: self.__open_egram("A")).pack(pady=5)

        tk.Button(self.__egram_frame, text="Ventricular Egram", width=18,
                bg="lightblue",
                command=lambda: self.__open_egram("V")).pack(pady=5)

        tk.Button(self.__egram_frame, text="Both Egrams", width=18,
                bg="lightblue",
                command=lambda: self.__open_egram("BOTH")).pack(pady=5)



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

            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(row=row, column=0, sticky="e", padx=10, pady=4)

            if param == "Hysteresis":
                options = ["Off", "On"]
                tv = tk.StringVar()

                tv.set("On" if float(var.get()) == 1.0 else "Off")

                def update(*args, v=var, t=tv):
                    v.set(1.0 if t.get() == "On" else 0.0)

                tv.trace_add("write", update)
                tk.OptionMenu(self.__param_frame, tv, *options).grid(row=row, column=1, padx=10, pady=4)
                row += 1
                continue


            if param == "Rate Smoothing":
                options = ["Off", "3", "6", "9", "12", "15", "18", "21", "25"]
                mapping = {o: (0.0 if o == "Off" else float(o)) for o in options}
                reverse = {v: k for k, v in mapping.items()}

                tv = tk.StringVar()
                tv.set(reverse.get(float(var.get()), "Off"))

                def update(*args, v=var, t=tv):
                    v.set(mapping[t.get()])

                tv.trace_add("write", update)
                tk.OptionMenu(self.__param_frame, tv, *options).grid(row=row, column=1, padx=10, pady=4)
                row += 1
                continue


            low, high, step = self.__param_config[param]
            val_var = tk.StringVar()
            val_var.set(str(var.get()))

            if param == "Lower Rate Limit":
                slider = tk.Scale(self.__param_frame, from_=low, to=high, orient="horizontal",
                                  resolution=1, variable=var, length=200)

                def sync(*args, v=var, sv=val_var, s=slider):
                    snapped = self.__adjust_lrl_step(v.get())
                    if snapped != v.get():
                        v.set(snapped)
                        s.set(snapped)
                    sv.set(str(snapped))

                var.trace_add("write", sync)

            else:
                slider = tk.Scale(self.__param_frame, from_=low, to=high, orient="horizontal",
                                  resolution=step, variable=var, length=200)

                def sync(*args, v=var, sv=val_var):
                    sv.set(str(v.get()))

                var.trace_add("write", sync)

            slider.grid(row=row, column=1, padx=10, pady=4)

            entry = tk.Entry(self.__param_frame, textvariable=val_var, width=6)
            entry.grid(row=row, column=2, padx=5)

            entry.bind("<Return>",
                       lambda e, p=param, v=var, sv=val_var, sl=slider,
                       lo=low, hi=high, st=step:
                       self.__round_and_set(p, v, sv, sl, lo, hi, st))

            entry.bind("<FocusOut>",
                       lambda e, p=param, v=var, sv=val_var, sl=slider,
                       lo=low, hi=high, st=step:
                       self.__round_and_set(p, v, sv, sl, lo, hi, st))

            self.__sliders[param] = slider
            self.__value_entries[param] = entry
            row += 1

        tk.Button(self.__param_frame, text="Save",
                  command=self.__save_parameters,
                  bg="lightgreen", width=12).grid(row=row, column=0, pady=15)

        tk.Button(self.__param_frame, text="Logout",
                  command=self.__logout,
                  bg="lightcoral", width=12).grid(row=row, column=2, pady=15)

        tk.Button(self.__param_frame, text="Send to Device",
                  command=self.__send_to_device,
                  bg="lightyellow", width=12).grid(row=row+1, column=1, pady=10)


    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root)
        self.__param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.__param_frame, text="Parameters", fg="black",
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 11))

        self.__parameters = {
            "Lower Rate Limit": tk.DoubleVar(value=60.0),
            "Upper Rate Limit": tk.DoubleVar(value=120.0),
            "Maximum Sensor Rate": tk.DoubleVar(value=120.0),
            "Atrial Amplitude": tk.DoubleVar(value=3.5),
            "Atrial Pulse Width": tk.DoubleVar(value=0.4),
            "Ventricular Amplitude": tk.DoubleVar(value=3.5),
            "Ventricular Pulse Width": tk.DoubleVar(value=0.4),
            "Atrial Sensitivity": tk.DoubleVar(value=0.75),
            "Ventricular Sensitivity": tk.DoubleVar(value=2.5),
            "PVARP": tk.DoubleVar(value=250.0),
            "Hysteresis": tk.DoubleVar(value=0.0),    
            "Rate Smoothing": tk.DoubleVar(value=0.0),  
            "VRP": tk.DoubleVar(value=320.0),
            "ARP": tk.DoubleVar(value=250.0),
        }

        self.__param_config = {
            "Lower Rate Limit": (30, 175, 1),
            "Upper Rate Limit": (50, 175, 5),
            "Maximum Sensor Rate": (50, 175, 5),
            "Atrial Amplitude": (0.5, 7.0, 0.1),
            "Atrial Pulse Width": (0.05, 1.9, 0.05),
            "Ventricular Amplitude": (0.5, 7.0, 0.1),
            "Ventricular Pulse Width": (0.05, 1.9, 0.05),
            "Atrial Sensitivity": (0.25, 10.0, 0.25),
            "Ventricular Sensitivity": (1.0, 10.0, 0.5),
            "PVARP": (150, 500, 10),
            "VRP": (150, 500, 5),
            "ARP": (150, 500, 5),
            "Hysteresis": (0, 1, 1),
            "Rate Smoothing": (0, 25, 1),
        }

        existing = self.__db.get_parameters(self.__username)
        if existing:
            for p, var in self.__parameters.items():
                if p in existing:
                    try:
                        var.set(float(existing[p]))
                    except:
                        var.set(0)

        current_mode = self.__db.get_state(self.__username) or "AOO"
        self.__rebuild_parameter_rows(current_mode)


    def __create_state_display(self):
        self.__state_frame = tk.Frame(self.__root)
        self.__state_frame.place(relx=0.75, rely=0.45, anchor="center")

        tk.Label(self.__state_frame, text="States",
                 fg="black", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        self.__state_buttons = {}
        states = ["AOO", "VOO", "AAI", "VVI", "AOOR", "VOOR", "AAIR", "VVIR"]

        for name in states:
            btn = tk.Button(self.__state_frame, text=name, width=15, height=2,
                            bg="white", font=("Arial", 10, "bold"),
                            command=lambda n=name: self.__select_state(n))
            btn.pack(pady=5)
            self.__state_buttons[name] = btn

        last = self.__db.get_state(self.__username)
        if last and last in self.__state_buttons:
            self.__select_state(last)


    def __create_serial_display(self):
        self.__serial_label = tk.Label(self.__root, text="Serial: None",
                                       font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)


    def __select_state(self, name):
        for state, button in self.__state_buttons.items():
            button.config(bg="lightgreen" if state == name else "white")

        last_state = self.__db.get_state(self.__username)
        if last_state:
            allowed = self.__mode_parameters.get(last_state, [])
            saved = {}
            for p, var in self.__parameters.items():
                if p in allowed:
                    saved[p] = var.get()
            self.__db.save_parameters(self.__username, saved, state_name=last_state)

        self.__db.save_state(self.__username, name)

        state_params = self.__db.get_parameters(self.__username, state_name=name)
        allowed_new = self.__mode_parameters.get(name, [])

        if state_params:
            for p, var in self.__parameters.items():
                if p in allowed_new:
                    var.set(float(state_params.get(p, var.get())))
                else:
                    var.set(0)
        else:
            defaults = {
                "Lower Rate Limit": 60,
                "Upper Rate Limit": 120,
                "Maximum Sensor Rate": 120,
                "Atrial Amplitude": 3.5,
                "Atrial Pulse Width": 0.4,
                "Ventricular Amplitude": 3.5,
                "Ventricular Pulse Width": 0.4,
                "Atrial Sensitivity": 0.75,
                "Ventricular Sensitivity": 2.5,
                "PVARP": 250,
                "Hysteresis": 0,
                "Rate Smoothing": 0,
                "VRP": 320,
                "ARP": 250,
            }
            for p, var in self.__parameters.items():
                if p in allowed_new:
                    var.set(defaults[p])
                else:
                    var.set(0)

        self.__rebuild_parameter_rows(name)


    def __open_egram(self, channel_mode):
        try:
            egram_manager.open_egram_window(self.__root, self.__egram_queue, channel_mode)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Egram UI:\n{e}")


    def __save_parameters(self):
        current_state = self.__db.get_state(self.__username) or "default"
        allowed = self.__mode_parameters.get(current_state, [])

        lrl = self.__parameters["Lower Rate Limit"].get()
        url = self.__parameters["Upper Rate Limit"].get()

        if lrl > url:
            messagebox.showerror("Invalid Parameter", "Lower Rate Limit cannot be greater than Upper Rate Limit.")
            return

        all_data = {p: v.get() for p, v in self.__parameters.items()}
        filtered = {}

        for p, v in all_data.items():
            if p in allowed:
                filtered[p] = v
            else:
                self.__parameters[p].set(0)

        _, msg = self.__db.save_parameters(self.__username, filtered, state_name=current_state)
        messagebox.showinfo("Saved", f"{msg} (Mode: {current_state})")


    def __save_device(self, serial_number):
        if serial_number:
            self.__db.save_device(self.__username, serial_number)


    def __check_device(self):
        ports = list(serial.tools.list_ports.comports())

        if ports:
            serial_number = getattr(ports[0], "serial_number", None)

            if serial_number != self.__current_serial:
                self.__current_serial = serial_number
                self.__save_device(serial_number)
                self.__set_led(True)

                if not getattr(self, "__uart_receiver", None):
                    self.__uart_receiver = UARTReceiver(self.__egram_queue, baudrate=9600)
                    self.__uart_receiver.start()

        else:
            self.__current_serial = None
            self.__set_led(False)

            if getattr(self, "__uart_receiver", None):
                self.__uart_receiver.stop()
                self.__uart_receiver = None

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
        sender = send_uart.UARTSender(receiver_ref=self.__uart_receiver)
        try:
            sent = sender.send_to_device(self.__username)
            messagebox.showinfo("Success", f"Sent to device:\n{sent}")
        except Exception as e:
            messagebox.showerror("UART Error", str(e))


    def __logout(self):
        if self.__serial_port and getattr(self.__serial_port, "is_open", False):
            self.__serial_port.close()

        if self.__uart_receiver:
            self.__uart_receiver.stop()

        self.__logout_comp()
