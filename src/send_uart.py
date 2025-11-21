from datamanager import DataManager
from uart_handler import UARTHandler
import struct
import json
import os
from datetime import datetime

MODE_BITMASK = {
    "AOO":  0b00000001,
    "VOO":  0b00000010,
    "AAI":  0b00000011,
    "VVI":  0b00000100,
    "AOOR": 0b00000101,
    "VOOR": 0b00000110,
    "AAIR": 0b00000111,
    "VVIR": 0b00001000,
}

# Always send parameters in this order (missing ones => 0)
FULL_ORDER = [
    "Lower Rate Limit",
    "Upper Rate Limit",
    "Maximum Sensor Rate",
    "Atrial Amplitude",
    "Ventricular Amplitude",
    "Atrial Pulse Width",
    "Ventricular Pulse Width",
    "Atrial Sensi1tivity",
    "Ventricular Sensitivity",
    "PVARP",
    "VRP",
    "ARP",
    "Hysteresis",
    "Rate Smoothing",
]


class UARTSender:
    def __init__(self, receiver_ref=None):
        self.db = DataManager()
        self.uart = UARTHandler()
        self.receiver = receiver_ref

    def _encode_param(self, name, value):
        try:
            fval = float(value)
        except:
            fval = 0.0

        # 8-bit ints
        if name in ("Lower Rate Limit", "Upper Rate Limit",
                    "Maximum Sensor Rate", "Hysteresis"):
            return bytes([max(0, min(255, int(fval)))])

        # 32-bit floats
        if name in (
            "Atrial Amplitude", "Ventricular Amplitude",
            "Atrial Pulse Width", "Ventricular Pulse Width",
            "Atrial Sensitivity", "Ventricular Sensitivity"
        ):
            return struct.pack(">f", fval)

        # 16-bit ints
        if name in ("PVARP", "VRP", "ARP"):
            return struct.pack(">H", max(0, min(65535, int(fval))))

        # Rate smoothing: 16-bit composed
        if name == "Rate Smoothing":
            if fval <= 0:
                return bytes([0, 0])
            return bytes([1, max(0, min(255, int(fval)))])

        # fallback float
        return struct.pack(">f", fval)

    def _build_packet(self, mode, params):
        bitmask = MODE_BITMASK.get(mode, 0)

        payload = bytearray()
        payload.append(bitmask)

        for name in FULL_ORDER:
            val = params.get(name, 0)
            payload.extend(self._encode_param(name, val))

        return bytes(payload)

    def _log(self, username, mode, params, packet):
        path = "uart_log.json"

        entry = {
            "username": username,
            "mode": mode,
            "packet_hex": packet.hex(),
            "packet_len": len(packet),
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

    def send_to_device(self, username):
        if self.receiver:
            try:
                self.receiver.stop()
            except:
                pass

        mode = self.db.get_state(username)
        params = self.db.get_parameters(username, state_name=mode)

        if not mode:
            raise Exception("No pacing mode selected.")
        if not params:
            raise Exception("No parameters saved for this mode.")

        packet = self._build_packet(mode, params)

        self.uart.send_bytes(packet)
        self._log(username, mode, params, packet)

        return packet
