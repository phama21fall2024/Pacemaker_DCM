import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

def open_egram_window(parent):
    # Create a new popup window (not replacing the main one)
    egram_window = tk.Toplevel(parent)
    egram_window.title("Egram Display")
    egram_window.geometry("600x400")
    egram_window.resizable(False, False)

    tk.Label(egram_window, text="Egram Visualization", font=("Arial", 14, "bold")).pack(pady=10)

    # Create a Matplotlib figure
    fig = Figure(figsize=(6, 3), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Electrogram Signal")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude (mV)")

    # Temporary random data
    y = [random.uniform(-1, 1) for _ in range(100)]
    ax.plot(y, color='blue')

    # Embed in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=egram_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    ttk.Button(egram_window, text="Close", command=egram_window.destroy).pack(pady=10)
