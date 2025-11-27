import tkinter as tk
from tkinter import messagebox
from rounding_helper import RoundingHelper
import serial.tools.list_ports
import uart_comm
import egram_manager
import uart_comm
from reports import generate_report


class Application:
    def __init__(self, root, username, db, logout):
        self.__root = root
        self.__username = username
        self.__db = db
        self.__logout_comp = logout
        self.__serial_port = None
        self.__current_serial = None
        self.__uart = None
        self.__egram_queue = egram_manager.FloatQueue()

        self.__mode_parameters = {
            "AOO":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
            "VOO":  ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
            "AAI":  ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
            "VVI":  ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
            "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width","Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
            "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width","Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
            "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
            "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"]
        }

        self.__root.title("Pacemaker DCM")
        self.__root.geometry("800x600")
        self.__root.resizable(False, False)
        self.__create_status_display()
        self.__create_param_display()

        self.__create_top_right_panel()      
        self.__create_state_display()       
        self.__create_device_id_section()    
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

        self.__egram_frame = tk.Frame(self.__root, bd=1, relief="solid", padx=10, pady=10)
        self.__egram_frame.place(relx=0.65, rely=0.58, anchor="center")  # left edge of right half
        self.__egram_frame.config(width=1000, height=600)
        self.__egram_frame.grid_propagate(False)

        switch_frame = tk.Frame(self.__egram_frame)
        switch_frame.grid(row=0, column=0, sticky="w")

        tk.Label(switch_frame, text="Egram Viewer", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")

        self.__egram_enabled = tk.StringVar(value="On")

        tk.OptionMenu(switch_frame, self.__egram_enabled, "On", "Off",
                    command=lambda m: self.__toggle_egram()).grid(row=0, column=1, padx=(10,0))

        self.__btn_frame = tk.Frame(self.__egram_frame)
        self.__btn_frame.grid(row=1, column=0, pady=(10, 10), sticky="w")

        self.__btn_A = tk.Button(self.__btn_frame, text="Atrial", width=12, bg="lightblue",
                                command=lambda: self.__show_egram("A"))
        self.__btn_A.grid(row=0, column=0, padx=5)

        self.__btn_V = tk.Button(self.__btn_frame, text="Ventricular", width=12, bg="lightblue",
                                command=lambda: self.__show_egram("V"))
        self.__btn_V.grid(row=0, column=1, padx=5)

        self.__btn_B = tk.Button(self.__btn_frame, text="Both", width=12, bg="lightblue",
                                command=lambda: self.__show_egram("BOTH"))
        self.__btn_B.grid(row=0, column=2, padx=5)


        self.__egram_canvas = tk.Frame(self.__egram_frame, bg="white")
        self.__egram_canvas.grid(row=2, column=0, sticky="nsew")

        self.__egram_frame.rowconfigure(2, weight=1)
        self.__egram_frame.columnconfigure(0, weight=1)

    def __toggle_egram(self):
        if self.__egram_enabled.get() == "Off":
            for w in self.__egram_canvas.winfo_children():
                w.destroy()
            self.__btn_A.config(state="disabled")
            self.__btn_V.config(state="disabled")
            self.__btn_B.config(state="disabled")
        else:
            self.__btn_A.config(state="normal")
            self.__btn_V.config(state="normal")
            self.__btn_B.config(state="normal")

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
        else:
            rounded = RoundingHelper.round_value(sv.get(), lo, hi, step)

        if rounded is None:
            sv.set(str(var.get()))
            return

        var.set(rounded)
        slider.set(rounded)
        sv.set(str(rounded))

    def __create_param_display(self):
        self.__param_frame = tk.Frame(self.__root, bd=1, relief="solid", padx=10, pady=10)
        self.__param_frame.place(relx=0.17, rely=0.58, anchor="center")

        self.__param_frame.config(width=440, height=600)
        self.__param_frame.grid_propagate(False)

        tk.Label(self.__param_frame, text="Parameters",
                font=("Arial", 8, "bold")).grid(row=0, column=0, columnspan=3, pady=(0,5))

        self.__param_frame.grid_columnconfigure(0, pad=3)
        self.__param_frame.grid_columnconfigure(1, pad=3)
        self.__param_frame.grid_columnconfigure(2, pad=3)

        self.__parameters = {
            "Lower Rate Limit": tk.IntVar(value=60),
            "Upper Rate Limit": tk.IntVar(value=120),
            "Maximum Sensor Rate": tk.IntVar(value=120),
            "Atrial Amplitude": tk.DoubleVar(value=5),
            "Atrial Pulse Width": tk.DoubleVar(value=1),
            "Ventricular Amplitude": tk.DoubleVar(value=5),
            "Ventricular Pulse Width": tk.DoubleVar(value=1),
            "Atrial Sensitivity": tk.DoubleVar(value=0),
            "Ventricular Sensitivity": tk.DoubleVar(value=0),
            "PVARP": tk.DoubleVar(value=250),
            "VRP": tk.DoubleVar(value=320),
            "ARP": tk.DoubleVar(value=250),
            "Hysteresis": tk.IntVar(value=0),
            "Rate Smoothing": tk.DoubleVar(value=0),
            "Activity Threshold": tk.IntVar(value=4), 
            "Reaction Time": tk.IntVar(value=30),      
            "Response Factor": tk.IntVar(value=8),     
            "Recovery Time": tk.IntVar(value=5),       
        }

        self.__param_config = {
            "Lower Rate Limit": (30, 175, 1),
            "Upper Rate Limit": (50, 175, 5),
            "Maximum Sensor Rate": (50, 175, 5),
            "Atrial Amplitude": (0.0, 5.0, 0.1),
            "Atrial Pulse Width": (1, 30, 1),
            "Ventricular Amplitude": (0.0, 5.0, 0.1),
            "Ventricular Pulse Width": (1, 30, 1),
            "Atrial Sensitivity": (0.0, 5.0, 0.1),
            "Ventricular Sensitivity": (0.0, 5.0, 0.1),
            "PVARP": (150, 500, 10),
            "VRP": (150, 500, 5),
            "ARP": (150, 500, 5),
            "Hysteresis": (0, 1, 1),
            "Rate Smoothing": (0, 25, 1),
            "Activity Threshold": (1, 7, 1),
            "Reaction Time": (10, 50, 10),
            "Response Factor": (1, 16, 1),
            "Recovery Time": (2, 16, 1),
        }

        self.__param_units = {
            "Lower Rate Limit": "ppm",
            "Upper Rate Limit": "ppm",
            "Maximum Sensor Rate": "ppm",
            "Atrial Amplitude": "V",
            "Atrial Pulse Width": "ms",
            "Ventricular Amplitude": "V",
            "Ventricular Pulse Width": "ms",
            "Atrial Sensitivity": "mV",
            "Ventricular Sensitivity": "mV",
            "PVARP": "ms",
            "VRP": "ms",
            "ARP": "ms",
            "Hysteresis": "",
            "Rate Smoothing": "%",
            "Activity Threshold": "",
            "Reaction Time": "sec",
            "Response Factor": "",
            "Recovery Time": "min",
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
            label_text = f"{param} ({self.__param_units.get(param, '')})" if self.__param_units.get(param, "") else param

            tk.Label(self.__param_frame, text=label_text, font=("Arial", 10)) .grid(row=row, column=0, sticky="e", pady=1, padx=(0, 5))

            # SPECIAL CASE: Activity Threshold
            if param == "Activity Threshold":
                opts = ["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"]
                mapping = {o: i + 1 for i, o in enumerate(opts)}
                reverse = {v: k for k, v in mapping.items()}
                tv = tk.StringVar(value=reverse.get(var.get(), "Med"))
                tv.trace_add("write", lambda *a, v=var, t=tv: v.set(mapping[t.get()]))
                tk.OptionMenu(self.__param_frame, tv, *opts).grid(row=row, column=1, sticky="w")
                row += 1
                continue

            # SPECIAL CASE: Hysteresis
            if param == "Hysteresis":
                tv = tk.StringVar(value="On" if var.get() else "Off")
                tv.trace_add("write", lambda *a, v=var, t=tv: v.set(1 if t.get() == "On" else 0))
                tk.OptionMenu(self.__param_frame, tv, "Off", "On").grid(row=row, column=1, sticky="w")
                row += 1
                continue

            # SPECIAL CASE: Rate Smoothing
            if param == "Rate Smoothing":
                opts = ["Off", "3", "6", "9", "12", "15", "18", "21", "25"]
                mapping = {o: (0 if o == "Off" else float(o)) for o in opts}
                reverse = {v: k for k, v in mapping.items()}
                tv = tk.StringVar(value=reverse.get(var.get(), "Off"))
                tv.trace_add("write", lambda *a, v=var, t=tv: v.set(mapping[t.get()]))
                tk.OptionMenu(self.__param_frame, tv, *opts).grid(row=row, column=1, sticky="w")
                row += 1
                continue

            
            low, high, step = self.__param_config[param]
            val_var = tk.StringVar()
            val_var.set(str(var.get()))


            # SPECIAL CASE: LRL
            if param == "Lower Rate Limit":
                slider = tk.Scale(self.__param_frame, from_=low, to=high,
                                orient="horizontal", length=140, resolution=1,
                                variable=var, showvalue=0)

                def sync_lrl(*a, v=var, sv=val_var, s=slider):
                    raw = v.get()
                    snap = self.__adjust_lrl_step(raw)
                    if snap != raw:
                        v.set(snap)
                    sv.set(str(snap))
                    s.set(snap)

                var.trace_add("write", sync_lrl)

            # STANDARD SLIDERS
            else:
                slider = tk.Scale(self.__param_frame, from_=low, to=high,
                                orient="horizontal", length=140,
                                resolution=step, variable=var, showvalue=0)

                def sync_std(*a, v=var, sv=val_var):
                    sv.set(str(v.get()))

                var.trace_add("write", sync_std)

            # Slider and Entry for standard or LRL
            slider.grid(row=row, column=1, padx=(5, 5))

            entry = tk.Entry(self.__param_frame, textvariable=val_var, width=6)
            entry.grid(row=row, column=2, padx=(5, 0))

            entry.bind("<Return>", lambda e, p=param, v=var, sv=val_var,
                    sl=slider, lo=low, hi=high, st=step:
                    self.__round_and_set(p, v, sv, sl, lo, hi, st))

            entry.bind("<FocusOut>", lambda e, p=param, v=var, sv=val_var,
                    sl=slider, lo=low, hi=high, st=step:
                    self.__round_and_set(p, v, sv, sl, lo, hi, st))

            row += 1

        # Save and Send buttons
        tk.Button(self.__param_frame, text="Save", bg="lightgreen",
                font=("Arial", 10, "bold"), width=10,
                command=self.__save_parameters).grid(row=row, column=0, pady=8)

        tk.Button(self.__param_frame, text="Send", bg="lightyellow",
                font=("Arial", 10, "bold"), width=10,
                command=self.__send_to_device).grid(row=row, column=1, pady=8)
    
        tk.Button(self.__param_frame, text="Report", bg="lightblue",
          font=("Arial", 10, "bold"), width=10,
          command=self.__generate_report).grid(row=row, column=2, pady=8)


    
    def __create_top_right_panel(self):
        self.__top_right_panel = tk.Frame(self.__root, bd=1, relief="solid")
        self.__top_right_panel.place(relx=0.98, rely=0.05, anchor="ne", width=500, height=120)

        # Create a grid layout Inside the panel
        self.__top_right_panel.grid_columnconfigure(0, weight=1)
        self.__top_right_panel.grid_columnconfigure(1, weight=1)


    def __create_state_display(self):
        frame = tk.Frame(self.__top_right_panel)
        frame.grid(row=0, column=0, sticky="nw", padx=10, pady=5)
        tk.Label(frame, text="States", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        self.__state_buttons = {}
        modes = ["AOO", "VOO", "AAI", "VVI", "AOOR", "VOOR", "AAIR", "VVIR"]
        row = 1
        col = 0
        for name in modes:
            b = tk.Button(frame, text=name, width=6, height=1, font=("Arial", 9),
                        command=lambda n=name: self.__select_state(n))
            b.grid(row=row, column=col, padx=3, pady=2)
            self.__state_buttons[name] = b

            col += 1
            if col == 4:   # wrap to next row after 4 buttons
                col = 0
                row += 1

        # Highlight last selected state
        last = self.__db.get_state(self.__username)
        if last:
            self.__select_state(last)

        logout_btn = tk.Button(
            frame,
            text="Logout",
            font=("Arial", 8, "bold"),
            bg="red",
            fg="white",
            width= 7,
            height=1,
            command=self.__logout
        )
        logout_btn.grid(row=1, column=6, sticky="e", padx=(20, 0), pady=(5, 0))



    def __create_device_id_section(self):
        frame = tk.Frame(self.__top_right_panel)
        frame.grid(row=0, column=1, sticky="ne", padx=10)

        tk.Label(frame, text="Device ID", font=("Arial", 10, "bold")).pack(anchor="e")

        self.__device_id_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.__device_id_var, width=16)
        entry.pack(anchor="e", pady=(2, 3))

        def save_id():
            val = self.__device_id_var.get().strip()
            if self.__current_serial and val:
                self.__db.save_device_id(self.__username, self.__current_serial, val)
                messagebox.showinfo("Saved", "Device ID updated.")

        tk.Button(frame, text="Save", width=12, command=save_id).pack(anchor="e")


    def __select_state(self, name):
        for s, b in self.__state_buttons.items():
            b.config(bg="lightgreen" if s == name else "white")

        # Save last state's values before switching
        last = self.__db.get_state(self.__username)
        if last:
            allowed_last = self.__mode_parameters.get(last, [])
            saved = {p: self.__parameters[p].get() for p in allowed_last}
            self.__db.save_parameters(self.__username, saved, state_name=last)

        # Update DB
        self.__db.save_state(self.__username, name)
        params = self.__db.get_parameters(self.__username, state_name=name)
        allowed = self.__mode_parameters.get(name, [])

        # FULL defaults including NEW PARAMETERS
        defaults = {
            "Lower Rate Limit": 60,
            "Upper Rate Limit": 120,
            "Maximum Sensor Rate": 120,
            "Atrial Amplitude": 5,
            "Atrial Pulse Width": 1,
            "Ventricular Amplitude": 5,
            "Ventricular Pulse Width": 1,
            "Atrial Sensitivity": 0,
            "Ventricular Sensitivity": 0,
            "PVARP": 250,
            "VRP": 320,
            "ARP": 250,
            "Hysteresis": 0,
            "Rate Smoothing": 0,
            "Activity Threshold": 4,
            "Reaction Time": 30,
            "Response Factor": 8,
            "Recovery Time": 5,
        }

        # Load parameters into Tk variables
        for p, v in self.__parameters.items():
            if p in allowed:
                if params and p in params:
                    v.set(float(params[p]))
                else:
                    v.set(defaults[p])

        # Rebuild rows
        self.__rebuild_parameter_rows(name)


    def __create_serial_display(self):
        self.__serial_label = tk.Label(self.__root, text="Serial: None", font=("Arial", 10, "italic"), fg="gray")
        self.__serial_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def __show_egram(self, mode):
        if self.__egram_enabled.get() == "Off":
            return

        from egram_manager import EgramGraph

        for w in self.__egram_canvas.winfo_children():
            w.destroy()

        graph = EgramGraph(self.__egram_canvas, self.__egram_queue, mode)
        graph.pack(fill="both", expand=True)


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
        try:
            if not self.__uart:
                self.__uart = uart_comm.UARTComm(queue=self.__egram_queue)

            self.__uart.send_to_device(self.__username)
            messagebox.showinfo("Success", "Parameters sent.")
        except Exception as e:
            messagebox.showerror("UART Error", str(e))


    def __save_device(self, serial_number):
        saved_id = self.__db.get_device_id(self.__username, serial_number)

        if saved_id is None:
            popup = tk.Toplevel(self.__root)
            popup.title("Device ID")

            tk.Label(popup, text="Enter Device ID:").pack(pady=5)
            dev_var = tk.StringVar()
            entry = tk.Entry(popup, textvariable=dev_var)
            entry.pack(pady=5)
            entry.focus()

            def save_and_close():
                device_id = dev_var.get().strip()
                if device_id:
                    self.__db.save_device_id(self.__username, serial_number, device_id)
                popup.destroy()

            tk.Button(popup, text="Save", command=save_and_close).pack(pady=5)
        else:
            self.__db.update_device_last_used(self.__username, serial_number)


    def __check_device(self):
        ports = list(serial.tools.list_ports.comports())

        if ports:
            p = ports[0]

            serial_number = (
                getattr(p, "serial_number", None)
                or getattr(p, "device", None)
                or f"{getattr(p, 'vid', '0')}:{getattr(p, 'pid', '0')}"
            )

            if serial_number != self.__current_serial:
                self.__current_serial = serial_number
                self.__save_device(serial_number)
                self.__set_led(True)

                if not self.__uart:
                    self.__uart = uart_comm.UARTComm(queue=self.__egram_queue)

                    ok = self.__uart.connect()

                    if ok:
                        self.__current_serial = self.__uart.ser.port
                        self.__save_device(self.__current_serial)
                        self.__pump_egram()
                    
                    else:
                        self.__current_serial = None


        else:
            self.__current_serial = None
            self.__serial_label.config(text="Serial: None", fg="gray")
            self.__set_led(False)

            if self.__uart:
                try:
                    self.__uart.ser.close()
                except:
                    pass
                self.__uart = None


        self.__update_serial_label()
        self.__root.after(2000, self.__check_device)

    def __generate_report(self):
        mode = self.__db.get_state(self.__username)

        if not mode:
            messagebox.showerror("Error", "No mode selected.")
            return

        device_id = self.__device_id_var.get() or "UNKNOWN"
        dcm_serial = self.__username

        parameters = []
        labels = []

        for p in self.__mode_parameters[mode]:
            labels.append(p)
            parameters.append(self.__parameters[p].get())

        output_name = f"{self.__username}_{mode}_report.pdf".replace(" ", "_")

        try:
            generate_report(
                device_model="Pacemaker",
                device_serial=device_id,
                application_model="Pacemaker",
                application_version="1.0",
                dcm_serial=dcm_serial,
                report_name=f"{mode} Parameter Report",
                labels=labels,
                parameters=parameters,
                output_filename=output_name
            )

            messagebox.showinfo("Report Generated", f"Saved as {output_name}")

        except Exception as e:
            messagebox.showerror("PDF Error", str(e))


    def __pump_egram(self):
        if self.__uart:
            self.__uart.poll_egram()
        self.__root.after(40, self.__pump_egram)



    def __set_led(self, connected):
        self.__led_canvas.itemconfig(self.__led_circle, fill="green" if connected else "red")
        self.__status_label.config(text="Connected" if connected else "Not Connected",
                                   fg="green" if connected else "red")

    def __update_serial_label(self):
        if self.__current_serial:
            device_id = self.__db.get_device_id(self.__username, self.__current_serial)

            # Only update the entry if the value actually changed
            if device_id:
                if self.__device_id_var.get() != device_id:
                    self.__device_id_var.set(device_id)

                self.__serial_label.config(text=f"Device: {device_id}", fg="black")

            else:
                self.__serial_label.config(text=f"Serial: {self.__current_serial}", fg="black")

        else:
            self.__serial_label.config(text="Serial: None", fg="gray")


    def __logout(self):
        if self.__uart and self.__uart.ser:
            self.__uart.ser.close()

        self.__logout_comp()