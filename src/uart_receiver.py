import serial
import serial.tools.list_ports
import threading
import struct
import time


class UARTReceiver:
    # Continuously receives egram samples from pacemaker
    def __init__(self, queue, baudrate=9600):
        self.queue = queue
        self.baudrate = baudrate
        self.running = False
        self.thread = None
        self.ser = None

    def find_device(self):
        # Reuse your detection logic
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if ("USB" in p.description) or ("UART" in p.description) or ("Serial" in p.description):
                return p.device
        return None

    def start(self):
        # Open serial port
        port = self.find_device()
        if port is None:
            return False

        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=0.01)
        except Exception:
            return False

        # Start background thread
        self.running = True
        self.thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        # Stop receiver safely
        self.running = False
        try:
            if self.ser:
                self.ser.close()
        except:
            pass

    def receive_loop(self):
        # Pacemaker packet format:
        # 0xA5 0x5A  AtrialFloat32  VentFloat32  0x0D 0x0A
        packet_size = 12

        while self.running:
            try:
                if self.ser.in_waiting < packet_size:
                    time.sleep(0.002)
                    continue

                header = self.ser.read(2)
                if header != b'\xA5\x5A':
                    continue

                a_bytes = self.ser.read(4)
                v_bytes = self.ser.read(4)
                footer = self.ser.read(2)

                if footer != b'\x0D\x0A':
                    continue

                atrial = struct.unpack('<f', a_bytes)[0]
                vent = struct.unpack('<f', v_bytes)[0]

                # Push sample into queue
                self.queue.push({"A": atrial, "V": vent})

            except Exception:
                continue
