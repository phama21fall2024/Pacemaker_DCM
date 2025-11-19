import serial
import serial.tools.list_ports


class UARTHandler:
    # Handles low-level UART communication
    def __init__(self, baudrate=9600):
        self.baudrate = baudrate

    def find_device(self):
        # Find the first USB/Serial/UART device
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if ("USB" in p.description) or ("UART" in p.description) or ("Serial" in p.description):
                return p.device
        return None

    def send_values(self, values_list):
        port = self.find_device()
        if port is None:
            raise Exception("Pacemaker device not found.")

        print(f"[UART] Trying to open port: {port}")

        try:
            ser = serial.Serial(port, self.baudrate, timeout=1)
        except Exception as e:
            raise Exception(f"[UART] FAILED to open {port}: {e}")

        try:
            formatted = []
            for v in values_list:
                f = float(v)
                if f.is_integer():
                    formatted.append(str(int(f)))
                else:
                    formatted.append(f"{f:.3f}")

            packet = ",".join(formatted) + "\n"
            ser.write(packet.encode("ascii"))
            print(f"[UART] Sent: {packet}")

        finally:
            ser.close()

        return packet
