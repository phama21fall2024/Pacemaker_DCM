from datamanager import DataManager
from uart_handler import UARTHandler

class UARTSender:
    def __init__(self):
        self.db = DataManager()
        self.uart = UARTHandler()

    def send_to_device(self, username):
        return self.uart.send_from_database(self.db, username)
