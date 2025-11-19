from datamanager import DataManager
from uart_handler import UARTHandler

class UARTSender:
    def __init__(self):
        self.db = DataManager()
        self.uart = UARTHandler()

    def send_to_device(self, username):
        mode = self.db.get_state(username)
        if not mode:
            raise Exception("No pacing mode selected.")

        # Load all parameters saved for this mode
        params = self.db.get_parameters(username, state_name=mode)
        if not params:
            raise Exception(f"No parameters saved for mode {mode}.")

        # Determine allowed order (the mode’s parameter list)
        if hasattr(self.db, "get_mode_parameters"):
            allowed_order = self.db.get_mode_parameters(mode)
        else:
            # Fallback: alphabetical order
            allowed_order = sorted(params.keys())

        # Build ordered value list
        values_list = []
        for param in allowed_order:
            if param in params:
                values_list.append(params[param])
            else:
                # if missing, send 0
                values_list.append(0)

        # Send ONLY values
        return self.uart.send_values(values_list)
