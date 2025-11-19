import tkinter as tk
from app_controller import AppController

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pacemaker DCM")
    root.state("zoomed")  
    AppController(root)
    root.mainloop()
    