import serial
import serial.tools.list_ports

class UARTHandler:
    def __init__(self, baudrate=9600):
        self.baudrate = baudrate

    def find_device(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if ("USB" in p.description) or ("UART" in p.description) or ("Serial" in p.description):
                return p.device
        return None

    def send_parameters(self, param_dict):
        port = self.find_device()
        if port is None:
            raise Exception("Device not found.")

        ser = serial.Serial(port, self.baudrate, timeout=1)
        packet = ",".join(str(v) for v in param_dict.values()) + "\n"
        ser.write(packet.encode())
        ser.close()
        return True

    def send_from_database(self, db, username):
        mode = db.get_state(username)
        if not mode:
            raise Exception("No pacing mode selected.")

        params = db.get_parameters(username, state_name=mode)
        if not params:
            raise Exception(f"No parameters saved for mode {mode}.")

        if hasattr(db, "get_mode_parameters"):
            allowed = db.get_mode_parameters(mode)
            filtered = {p: params[p] for p in allowed if p in params}
        else:
            filtered = params

        self.send_parameters(filtered)
        return filtered
