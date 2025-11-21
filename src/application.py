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
            "AAI":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width",
                     "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVI":  ["Lower Rate Limit", "Upper Rate Limit",  "Ventricular Amplitude", "Ventricular Pulse Width",
                     "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
            "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude",
                     "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude",
                     "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"]
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
        f = tk.Frame(self.__root)
        f.place(relx=0, rely=0.05, anchor="nw")

        tk.Label(f, text="Device Connection Status:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.__led_canvas = tk.Canvas(f, width=20, height=20, highlightthickness=0)
        self.__led_circle = self.__led_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.__led_canvas.pack(side="left", padx=5)
        self.__status_label = tk.Label(f, text="Not Connected", fg="red", font=("Arial", 12, "bold"))
        self.__status_label.pack(side="left", padx=5)

    def __create_egram_panel(self):
        f = tk.Frame(self.__root)
        f.place(relx=0.50, rely=0.50, anchor="center")

        tk.Label(f, text="Egram Viewer", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Button(f, text="Atrial Egram", width=18, bg="lightblue", command=lambda: self.__open_egram("A")).pack(pady=5)
        tk.Button(f, text="Ventricular Egram", width=18, bg="lightblue", command=lambda: self.__open_egram("V")).pack(pady=5)
        tk.Button(f, text="Both Egrams", width=18, bg="lightblue", command=lambda: self.__open_egram("BOTH")).pack(pady=5)

    def __adjust_amplitude_step(self, value):
        try:
            v = float(value)
        except:
            return None

        if v <= 0:
            return 0.0
        if 0.5 <= v <= 3.2:
            return round(v * 10) / 10.0
        if 3.2 < v < 3.5:
            return 3.2 if abs(v - 3.2) < abs(v - 3.5) else 3.5
        if 3.5 <= v <= 7.0:
            return round(v / 0.5) * 0.5
        if v < 0.5:
            return 0.5
        return 7.0

    def __adjust_lrl_step(self, value):
        v = int(value)
        if 30 <= v <= 50:
            return 30 + round((v - 30) / 5) * 5
        elif 50 < v <= 90:
            return 51 + round((v - 51) / 1) * 1
        return 90 + round((v - 90) / 5) * 5

    def __round_and_set(self, param_name, var, sv, slider, lo, hi, step):
        if param_name == "Lower Rate Limit":
            rounded = self.__adjust_lrl_step(sv.get())
        elif param_name in ("Atrial Amplitude", "Ventricular Amplitude"):
            rounded = self.__adjust_amplitude_step(sv.get())
        else:
            rounded = RoundingHelper.round_value(sv.get(), lo, hi, step)

        if rounded is None:
            sv.set(str(var.get()))
            return

        var.set(rounded)
        slider.set(rounded)
        sv.set(str(rounded))

    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root)
        self.__param_frame.place(relx=0.25, rely=0.5, anchor="center")

        tk.Label(self.__param_frame, text="Parameters", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3)

        self.__parameters = {
            "Lower Rate Limit": tk.IntVar(value=60),
            "Upper Rate Limit": tk.IntVar(value=120),
            "Maximum Sensor Rate": tk.IntVar(value=120),
            "Atrial Amplitude": tk.DoubleVar(value=3.5),
            "Atrial Pulse Width": tk.DoubleVar(value=0.4),
            "Ventricular Amplitude": tk.DoubleVar(value=3.5),
            "Ventricular Pulse Width": tk.DoubleVar(value=0.4),
            "Atrial Sensitivity": tk.DoubleVar(value=0.75),
            "Ventricular Sensitivity": tk.DoubleVar(value=2.5),
            "PVARP": tk.DoubleVar(value=250),
            "Hysteresis": tk.IntVar(value=0),
            "Rate Smoothing": tk.DoubleVar(value=0),
            "VRP": tk.DoubleVar(value=320),
            "ARP": tk.DoubleVar(value=250),
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
            for p, v in self.__parameters.items():
                if p in existing:
                    try:
                        v.set(float(existing[p]))
                    except:
                        pass

        mode = self.__db.get_state(self.__username) or "AOO"
        self.__rebuild_parameter_rows(mode)

    def __rebuild_parameter_rows(self, mode):
        for w in self.__param_frame.grid_slaves():
            if int(w.grid_info()["row"]) > 0:
                w.grid_forget()

        row = 1
        allowed = self.__mode_parameters.get(mode, [])

        for param in allowed:
            var = self.__parameters[param]
            tk.Label(self.__param_frame, text=param, font=("Arial", 11)).grid(row=row, column=0, sticky="e")

            if param == "Hysteresis":
                tv = tk.StringVar(value="On" if var.get() == 1 else "Off")
                def upd(*a, v=var, t=tv): v.set(1 if t.get() == "On" else 0)
                tv.trace_add("write", upd)
                tk.OptionMenu(self.__param_frame, tv, "Off", "On").grid(row=row, column=1)
                row += 1
                continue

            if param == "Rate Smoothing":
                opts = ["Off", "3", "6", "9", "12", "15", "18", "21", "25"]
                mapping = {o: (0 if o == "Off" else float(o)) for o in opts}
                tv = tk.StringVar(value=next((k for k, v2 in mapping.items() if v2 == var.get()), "Off"))
                def upd(*a, v=var, t=tv): v.set(mapping[t.get()])
                tv.trace_add("write", upd)
                tk.OptionMenu(self.__param_frame, tv, *opts).grid(row=row, column=1)
                row += 1
                continue

            low, high, step = self.__param_config[param]

            val_var = tk.StringVar(value=str(var.get()))

            if param == "Lower Rate Limit":
                slider = tk.Scale(self.__param_frame, from_=low, to=high,
                                orient="horizontal", resolution=1,
                                variable=var, length=200)

                def sync(*a, v=var, sv=val_var, s=slider):
                    raw = v.get()
                    snap = self.__adjust_lrl_step(raw)
                    if snap != raw:
                        v.set(snap)
                    sv.set(str(snap))
                    s.set(snap)

                var.trace_add("write", sync)

            elif param in ("Atrial Amplitude", "Ventricular Amplitude"):
                mode_var = tk.StringVar(value="Off" if var.get() == 0 else "On")

                def mode_change(*a, v=var, mv=mode_var, sl=None, sv=val_var):
                    if mv.get() == "Off":
                        v.set(0.0)
                        sl.config(state="disabled")
                        sv.set("0.0")
                    else:
                        sl.config(state="normal")

                tk.OptionMenu(self.__param_frame, mode_var, "Off", "On").grid(row=row, column=1, sticky="w")

                slider = tk.Scale(self.__param_frame, from_=low, to=high,
                                orient="horizontal", resolution=0.1,
                                variable=var, length=200)

                def sync(*a, v=var, sv=val_var, s=slider, mv=mode_var):
                    if mv.get() == "Off":
                        v.set(0.0)
                        sv.set("0.0")
                        return

                    snap = self.__adjust_amplitude_step(v.get())

                    if 0.5 <= snap <= 3.2:
                        s.config(resolution=0.1)
                    elif 3.5 <= snap <= 7.0:
                        s.config(resolution=0.5)
                    else:
                        s.config(resolution=0.1)

                    v.set(snap)
                    sv.set(str(snap))

                var.trace_add("write", sync)
                mode_var.trace_add("write", lambda *a, sl=slider: mode_change(sl=sl))

                # disable if off
                if mode_var.get() == "Off":
                    slider.config(state="disabled")

                slider.grid(row=row, column=1, padx=80)


            else:
                slider = tk.Scale(self.__param_frame, from_=low, to=high, orient="horizontal",
                                  resolution=step, variable=var, length=200)
                def sync(*a, v=var, sv=val_var): 
                    sv.set(str(v.get()))
                var.trace_add("write", sync)

            slider.grid(row=row, column=1)
            entry = tk.Entry(self.__param_frame, textvariable=val_var, width=6)
            entry.grid(row=row, column=2)

            entry.bind("<Return>", lambda e, p=param, v=var, sv=val_var,
                       sl=slider, lo=low, hi=high, st=step:
                       self.__round_and_set(p, v, sv, sl, lo, hi, st))

            entry.bind("<FocusOut>", lambda e, p=param, v=var, sv=val_var,
                       sl=slider, lo=low, hi=high, st=step:
                       self.__round_and_set(p, v, sv, sl, lo, hi, st))

            row += 1

        tk.Button(self.__param_frame, text="Save", bg="lightgreen",
                  command=self.__save_parameters).grid(row=row, column=0, pady=15)

        tk.Button(self.__param_frame, text="Logout", bg="lightcoral",
                  command=self.__logout).grid(row=row, column=2, pady=15)

        tk.Button(self.__param_frame, text="Send to Device", bg="lightyellow",
                  command=self.__send_to_device).grid(row=row+1, column=1, pady=10)

    def __create_state_display(self):
        f = tk.Frame(self.__root)
        f.place(relx=0.75, rely=0.45, anchor="center")

        tk.Label(f, text="States", font=("Arial", 12, "bold")).pack()
        self.__state_buttons = {}

        for name in ["AOO", "VOO", "AAI", "VVI", "AOOR", "VOOR", "AAIR", "VVIR"]:
            b = tk.Button(f, text=name, width=15, height=2, font=("Arial", 10, "bold"),
                          command=lambda n=name: self.__select_state(n))
            b.pack(pady=5)
            self.__state_buttons[name] = b

        last = self.__db.get_state(self.__username)
        if last:
            self.__select_state(last)

    def __select_state(self, name):
        for s, b in self.__state_buttons.items():
            b.config(bg="lightgreen" if s == name else "white")

        last = self.__db.get_state(self.__username)
        if last:
            allowed_last = self.__mode_parameters.get(last, [])
            saved = {p: self.__parameters[p].get() for p in allowed_last}
            self.__db.save_parameters(self.__username, saved, state_name=last)

        self.__db.save_state(self.__username, name)
        params = self.__db.get_parameters(self.__username, state_name=name)
        allowed = self.__mode_parameters.get(name, [])

        defaults = {
            "Lower Rate Limit": 60, "Upper Rate Limit": 120, "Maximum Sensor Rate": 120,
            "Atrial Amplitude": 3.5, "Atrial Pulse Width": 0.4,
            "Ventricular Amplitude": 3.5, "Ventricular Pulse Width": 0.4,
            "Atrial Sensitivity": 0.75, "Ventricular Sensitivity": 2.5,
            "PVARP": 250, "Hysteresis": 0, "Rate Smoothing": 0,
            "VRP": 320, "ARP": 250
        }

        for p, v in self.__parameters.items():
            if p in allowed:
                v.set(float(params.get(p, defaults[p]))) if params else v.set(defaults[p])

        self.__rebuild_parameter_rows(name)

    def __create_serial_display(self):
        self.__serial_label = tk.Label(self.__root, text="Serial: None", font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def __open_egram(self, mode):
        try:
            egram_manager.open_egram_window(self.__root, self.__egram_queue, mode)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def __save_parameters(self):
        mode = self.__db.get_state(self.__username)
        if not mode:
            messagebox.showerror("Error", "No pacing mode selected.")
            return

        allowed = self.__mode_parameters.get(mode, [])
        lrl = self.__parameters["Lower Rate Limit"].get()
        url = self.__parameters["Upper Rate Limit"].get()

        if lrl > url:
            messagebox.showerror("Invalid Parameter", "LRL cannot exceed URL")
            return

        data = {p: self.__parameters[p].get() for p in allowed}
        _, msg = self.__db.save_parameters(self.__username, data, state_name=mode)
        messagebox.showinfo("Saved", f"{msg} (Mode: {mode})")

    def __send_to_device(self):
        sender = send_uart.UARTSender(receiver_ref=self.__uart_receiver)
        try:
            sender.send_to_device(self.__username)
            messagebox.showinfo("Success", "Parameters sent.")
        except Exception as e:
            messagebox.showerror("UART Error", str(e))

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

                if not self.__uart_receiver:
                    self.__uart_receiver = UARTReceiver(self.__egram_queue, baudrate=9600)
                    self.__uart_receiver.start()

        else:
            self.__current_serial = None
            self.__set_led(False)

            if self.__uart_receiver:
                self.__uart_receiver.stop()
                self.__uart_receiver = None

        self.__update_serial_label()
        self.__root.after(2000, self.__check_device)

    def __set_led(self, connected):
        self.__led_canvas.itemconfig(self.__led_circle, fill="green" if connected else "red")
        self.__status_label.config(text="Connected" if connected else "Not Connected",
                                   fg="green" if connected else "red")

    def __update_serial_label(self):
        if self.__current_serial:
            self.__serial_label.config(text=f"Serial: {self.__current_serial}", fg="black")
        else:
            self.__serial_label.config(text="Serial: None", fg="gray")

    def __logout(self):
        if self.__serial_port and getattr(self.__serial_port, "is_open", False):
            self.__serial_port.close()
        if self.__uart_receiver:
            self.__uart_receiver.stop()
        self.__logout_comp()
