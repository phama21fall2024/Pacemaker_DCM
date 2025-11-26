from datamanager import DataManager
import serial
import serial.tools.list_ports
from struct import pack, unpack_from, calcsize
import time
import json
import os
from datetime import datetime
from threading import Lock


MODE_BITMASK = {
    "AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4,
    "AOOR": 5, "VOOR": 6, "AAIR": 7, "VVIR": 8
}

PARAM_FORMAT = "=3BfB2fBf3H5B"

PARAM_ORDER = [
    "Mode",
    "Lower Rate Limit",
    "Upper Rate Limit",
    "Atrial Amplitude",
    "Atrial Pulse Width",
    "Atrial Sensitivity",
    "Ventricular Amplitude",
    "Ventricular Pulse Width",
    "Ventricular Sensitivity",
    "VRP",
    "ARP",
    "PVARP",
    "Reaction Time",
    "Response Factor",
    "Recovery Time",
    "Activity Threshold",
    "Maximum Sensor Rate"
]


ECG_FLOATS = 20
ECG_PACKET_LEN = calcsize(f"={ECG_FLOATS}f")
REQ_ECG = b"\x16\x47" + b"\x00"*50
ECG_TOTAL_BYTES = ECG_PACKET_LEN + 1


class UARTComm:

    def __init__(self, queue=None, baudrate=115200):
        self.db = DataManager()
        self.queue = queue
        self.baudrate = baudrate
        self.ser = None
        self.lock = Lock()


    def connect(self):
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("NO SERIAL DEVICES FOUND")
            return False

        print("AVAILABLE PORTS:")
        for p in ports:
            print(" ", p.device, "-", p.description)

        for p in ports:
            if p.vid == 0x1366 and p.pid == 0x1015:
                try:
                    self.ser = serial.Serial(p.device, self.baudrate, timeout=0)
                    print("CONNECTED:", p.device)
                    return True
                except Exception as e:
                    print("OPEN FAILED:", e)
                    return False

        print("PACEMAKER NOT FOUND (VID/PID mismatch)")
        return False


    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None
            print("SERIAL CLOSED")


    def send_to_device(self, username):
        mode = self.db.get_state(username)
        params = self.db.get_parameters(username, state_name=mode)

        if not self.ser or not self.ser.is_open:
            raise Exception("Device not connected")

        if not mode or not params:
            raise Exception("Invalid mode or parameters")

        packet = self._build_packet(mode, params)

        with self.lock:
            self.ser.write(packet)

        print("TX:", packet.hex())
        self._log(username, mode, params, packet)

        return packet


    def _build_packet(self, mode, params):

        values = [
            MODE_BITMASK.get(mode, 0),
            int(params.get("Lower Rate Limit", 60)),
            int(params.get("Upper Rate Limit", 120)),
            float(params.get("Atrial Amplitude", 5)),
            int(params.get("Atrial Pulse Width", 1)),
            float(params.get("Atrial Sensitivity", 0)),
            float(params.get("Ventricular Amplitude", 5)),
            int(params.get("Ventricular Pulse Width", 1)),
            float(params.get("Ventricular Sensitivity", 0)),
            int(params.get("VRP", 320)),
            int(params.get("ARP", 250)),
            int(params.get("PVARP", 250)),
            int(params.get("Reaction Time", 30)),
            int(params.get("Response Factor", 8)),
            int(params.get("Recovery Time", 5)),
            int(params.get("Activity Threshold", 4)),
            int(params.get("Maximum Sensor Rate", 120))
        ]

        return pack(PARAM_FORMAT, *values)


    def poll_egram(self):
        if not self.ser or not self.ser.is_open:
            return None

        with self.lock:
            self.ser.write(REQ_ECG)

        time.sleep(0.01)

        if self.ser.in_waiting < ECG_TOTAL_BYTES:
            return None

        raw = self.ser.read(ECG_TOTAL_BYTES)

        control = raw[0]
        data = raw[1:]

        if control == 0:
            a_data = unpack_from("=10f", data, 0)
            v_data = unpack_from("=10f", data, 40)

            if self.queue:
                self.queue.push({"A": a_data[-1], "V": v_data[-1]})

            return a_data, v_data

        elif control == 1:
            print("PARAM VERIFY PACKET RECEIVED")

        return None


    def _log(self, username, mode, params, packet):
        path = "uart_log.json"
        entry = {
            "username": username,
            "mode": mode,
            "packet_hex": packet.hex(),
            "params": params,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        }

        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
            else:
                data = []
        except:
            data = []

        data.append(entry)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def test_receive(self):
        print("LISTEN-ONLY MODE")
        print("Waiting for incoming data...")

        while True:
            n = self.ser.in_waiting
            if n > 0:
                data = self.ser.read(n)
                print("RX RAW:", data.hex())
            else:
                print("...no data")
            time.sleep(0.5)
