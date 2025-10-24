import tkinter as tk
from datamanager import DataManager
from welcome import WelcomeScreen
from main import Application

class AppController:
    def __init__(self, root):
        self.root = root
        self.db = DataManager()
        self.show_welcome()

    def show_welcome(self):
        WelcomeScreen(self.root, self.db, self.show_main)

    def show_main(self, username):
        Application(self.root, username, self.db, self.show_welcome)

if __name__ == "__main__":
    root = tk.Tk()
    AppController(root)
    root.mainloop()
