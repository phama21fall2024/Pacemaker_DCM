import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque
import random

class FloatQueue:
    def __init__(self, maxlen=50):
        self._buf = deque(maxlen=maxlen)

    def enqueue(self, value: float):
        """Add a new float sample to the queue."""
        if isinstance(value, float):
            self._buf.append(value)

    def dequeue_all(self):
        """Return all samples currently in the queue and clear it."""
        data = list(self._buf)
        self._buf.clear()
        return data

    def __len__(self):
        return len(self._buf)


def open_egram_window(parent, egram_queue: FloatQueue):
    win = tk.Toplevel(parent)
    win.title("Egram Display")
    win.geometry("650x450")
    win.resizable(False, False)

    tk.Label(
        win,
        text="Egram Visualization",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    # Matplotlib Figure
    fig = Figure(figsize=(6, 3), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Electrogram Signal")
    ax.set_xlabel("Time")
    ax.set_ylabel("Amplitude (mV)")

    # Empty line plot

    ax.set_xticklabels([])
    
    line, = ax.plot([], [], color="blue")
    data_buffer = deque(maxlen=50)

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_plot():
        # Pull all new samples
        new_data = egram_queue.dequeue_all()

        # Temporarily add fake noise if empty (remove once UART is wired)
        if not new_data:
            new_data = [random.uniform(-1, 1)]

        data_buffer.extend(new_data)

        # Update plot
        line.set_xdata(range(len(data_buffer)))
        line.set_ydata(list(data_buffer))

        ax.relim()
        ax.autoscale_view()
        canvas.draw_idle()

        win.after(40, update_plot)  

    update_plot()
