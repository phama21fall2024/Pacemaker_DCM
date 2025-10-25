import tkinter as tk
from datamanager import DataManager
from welcome import WelcomeScreen
from main import Application

class AppController:
    def __init__(self, root):
        self.root = root
        self.db = DataManager()
        self.current_screen = None
        self.show_welcome(first=True)

    def show_welcome(self, first=False):
        # Only clear widgets if switching from another screen
        if not first and self.current_screen:
            for widget in self.root.winfo_children():
                widget.destroy()

        # Create and display Welcome screen
        self.current_screen = WelcomeScreen(self.root, self.db, self.show_main)
        if hasattr(self.current_screen, "show"):
            self.current_screen.show()

    def show_main(self, username):
        # Clear widgets before showing main app
        if self.current_screen:
            for widget in self.root.winfo_children():
                widget.destroy()

        # Create and display main Application
        self.current_screen = Application(self.root, username, self.db, self.show_welcome)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pacemaker DCM")
    root.geometry("600x400")
    app = AppController(root)
    root.mainloop()
