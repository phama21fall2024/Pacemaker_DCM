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

    def send_values(self, values_list):
        """Send ONLY the values as a CSV packet."""
        port = self.find_device()
        if port is None:
            raise Exception("Pacemaker device not found.")

        ser = serial.Serial(port, self.baudrate, timeout=1)

        packet = ",".join(str(v) for v in values_list) + "\n"
        ser.write(packet.encode())

        ser.close()
        return packet  # return what was sent for confirmation
