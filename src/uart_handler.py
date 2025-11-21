import serial
import serial.tools.list_ports


class UARTHandler:
    # Handles low-level UART communication
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout

    def find_device(self):
        # Find the first USB/Serial/UART device
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if ("USB" in p.description) or ("UART" in p.description) or ("Serial" in p.description):
                return p.device
        return None

    def send_bytes(self, packet_bytes: bytes):
        port = self.find_device()
        if port is None:
            raise Exception("Pacemaker device not found.")

        print(f"Trying to open port: {port}")

        try:
            ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            raise Exception(f"FAILED to open {port}: {e}")

        try:
            ser.write(packet_bytes)
            print(f"Sent {len(packet_bytes)} bytes (hex={packet_bytes.hex()})")
        finally:
            ser.close()

        return len(packet_bytes)
