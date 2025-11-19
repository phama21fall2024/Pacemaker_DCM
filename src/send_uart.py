# send_uart.py

from datamanager import DataManager
from uart_handler import UARTHandler


# Fixed parameter order per mode (what gets sent over UART)
MODE_SEND_ORDER = {
    "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
    "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
    "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
}

MODE_ID = {
    "AOO": 1,
    "VOO": 2,
    "AAI": 3,
    "VVI": 4,
    "AOOR": 5,
    "VOOR": 6,
    "AAIR": 7,
    "VVIR": 8,
}


class UARTSender:
    # High-level interface for sending a full parameter set to the device
    def __init__(self, receiver_ref=None):
        self.db = DataManager()
        self.uart = UARTHandler()
        self.receiver = receiver_ref  # optional UARTReceiver reference

    def send_to_device(self, username):
        if self.receiver:
            print("[UARTSender] Stopping UART receiver before send...")
            try:
                self.receiver.stop()
            except:
                pass

        mode = self.db.get_state(username)
        if not mode:
            raise Exception("No pacing mode selected.")

        params = self.db.get_parameters(username, state_name=mode)
        if not params:
            raise Exception(f"No parameters saved for mode {mode}.")

        # choose order
        if mode in MODE_SEND_ORDER:
            order = MODE_SEND_ORDER[mode]
        else:
            order = sorted(params.keys())

        # 🔥 NEW — prepend mode ID
        values = [MODE_ID.get(mode, 0)]   # insert mode ID first

        # then append ordered parameters
        for name in order:
            values.append(params.get(name, 0))

        print(f"[UARTSender] Mode: {mode}  (ID={MODE_ID.get(mode,0)})")
        print(f"[UARTSender] Order: {order}")
        print(f"[UARTSender] Values to send: {values}")

        packet = self.uart.send_values(values)
        print("[UARTSender] Send complete.")
        return packet
