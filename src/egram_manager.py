import tkinter as tk
from collections import deque
import random

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class FloatQueue:
    def __init__(self):
        self.buffer = deque()

    def push(self, sample):
        self.buffer.append(sample)

    def pop(self):
        if self.buffer:
            return self.buffer.popleft()
        return None

    def empty(self):
        return len(self.buffer) == 0


class EgramGraph(tk.Frame):
    def __init__(self, parent, queue, mode):
        super().__init__(parent)
        self.queue = queue
        self.mode = mode

        self.max_points = 30
        self.atrium_data = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.vent_data = deque([0.0] * self.max_points, maxlen=self.max_points)

        if self.mode == "BOTH":
            self.fig = Figure(figsize=(7, 4), dpi=100)
            self.axA = self.fig.add_subplot(211)
            self.axV = self.fig.add_subplot(212)
        else:
            self.fig = Figure(figsize=(7, 3), dpi=100)
            self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        self.after(50, self.update_plot)

    def hide_numbers_keep_labels(self, axis):
        axis.set_xticklabels([])   # remove x numbers
        axis.set_yticklabels([])   # remove y numbers

        axis.tick_params(axis='both', length=4)  

    def update_plot(self):
        if self.queue.empty():
            fakeA = random.uniform(0, 5)
            fakeV = random.uniform(0, 5)
            self.queue.push({"A": fakeA, "V": fakeV})

        while not self.queue.empty():
            sample = self.queue.pop()
            a_val = sample.get("A")
            v_val = sample.get("V")
            if a_val is not None:
                self.atrium_data.append(float(a_val))
            if v_val is not None:
                self.vent_data.append(float(v_val))

        if self.mode == "BOTH":
            self.axA.clear()
            self.axV.clear()

            self.axA.plot(list(self.atrium_data))
            self.axV.plot(list(self.vent_data))

            self.axA.set_ylim(0, 5)
            self.axV.set_ylim(0, 5)

            self.axA.invert_xaxis()   
            self.axV.invert_xaxis()

            # axis names preserved
            self.axA.set_ylabel("Atrial")
            self.axV.set_ylabel("Ventricular")
            self.axV.set_xlabel("Samples")

            # remove numeric labels only
            self.hide_numbers_keep_labels(self.axA)
            self.hide_numbers_keep_labels(self.axV)

        elif self.mode == "A":
            self.ax.clear()
            self.ax.plot(list(self.atrium_data))
            self.ax.set_ylim(0, 5)
            self.ax.invert_xaxis()

            self.ax.set_ylabel("Atrial")
            self.ax.set_xlabel("Samples")

            self.hide_numbers_keep_labels(self.ax)

        elif self.mode == "V":
            self.ax.clear()
            self.ax.plot(list(self.vent_data))
            self.ax.set_ylim(0, 5)
            self.ax.invert_xaxis() 

            self.ax.set_ylabel("Ventricular")
            self.ax.set_xlabel("Samples")

            self.hide_numbers_keep_labels(self.ax)

        self.canvas.draw_idle()
        self.after(50, self.update_plot)


def open_egram_window(root, queue, channel_mode="BOTH"):
    mode = channel_mode if channel_mode in ("A", "V", "BOTH") else "BOTH"

    win = tk.Toplevel(root)
    win.title(f"Egram - {mode}")
    win.geometry("900x500")

    graph = EgramGraph(win, queue, mode)
    graph.pack(fill="both", expand=True)

    return win

def embed_live_egram(parent, queue, mode):
    # Clear previous embedded plots
    for w in parent.winfo_children():
        w.destroy()

    graph = EgramGraph(parent, queue, mode)
    graph.pack(fill="both", expand=True)


