from datamanager import DataManager
import serial
import serial.tools.list_ports
from struct import pack, unpack_from, calcsize
from threading import Lock


MODE_BITMASK = {
    "AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4,
    "AOOR": 5, "VOOR": 6, "AAIR": 7, "VVIR": 8
}

ECG_FLOATS = 20
ECG_PACKET_LEN = calcsize("=20f")

ECG_HEADER = 0xAA   # Must match FPGA


class UARTComm:

    def __init__(self, queue=None, baudrate=115200):
        self.db = DataManager()
        self.queue = queue
        self.baudrate = baudrate
        self.ser = None
        self.lock = Lock()

        self.waiting_for_echo = False
        self.waiting_for_ecg = False

        self.ECHO_FMT = "=BBB6f3H5B"
        self.ECHO_LEN = calcsize(self.ECHO_FMT)


    def connect(self):
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("NO SERIAL DEVICES FOUND")
            return False

        for p in ports:
            try:
                self.ser = serial.Serial(p.device, self.baudrate, timeout=0)
                print("CONNECTED:", p.device)
                return True
            except Exception as e:
                print("FAILED:", p.device, e)

        print("NO WORKING SERIAL PORT")
        return False


    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None


    def send_to_device(self, username):
        mode = self.db.get_state(username)
        params = self.db.get_parameters(username, state_name=mode)

        if not self.ser or not self.ser.is_open:
            raise Exception("Device not connected")

        packet = self._build_packet(mode, params)

        with self.lock:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.write(packet)
            self.ser.flush()

        self.waiting_for_echo = True
        self.waiting_for_ecg = True

        print("TX:", packet.hex())
        print("MODE SENT:", mode)

        return packet



    def _build_packet(self, mode, params):

        full = {
            "Lower Rate Limit": 60,
            "Upper Rate Limit": 120,
            "Atrial Amplitude": 5,
            "Atrial Pulse Width": 1,
            "Atrial Sensitivity": 0,
            "Ventricular Amplitude": 5,
            "Ventricular Pulse Width": 1,
            "Ventricular Sensitivity": 0,
            "VRP": 320,
            "ARP": 250,
            "PVARP": 250,
            "Maximum Sensor Rate": 120,
            "Reaction Time": 30,
            "Response Factor": 8,
            "Recovery Time": 5,
            "Activity Threshold": 4
        }

        if params:
            full.update(params)

        thr = full["Activity Threshold"]
        if isinstance(thr, str):
            mapping = {
                "V-Low": 1, "Low": 2, "Med-Low": 3,
                "Med": 4, "Med-High": 5, "High": 6, "V-High": 7
            }
            full["Activity Threshold"] = mapping.get(thr, 4)
        else:
            full["Activity Threshold"] = int(thr)

        values = [
            MODE_BITMASK.get(mode, 0),
            int(full["Lower Rate Limit"]),
            int(full["Upper Rate Limit"]),
            float(full["Atrial Amplitude"]),
            float(full["Atrial Pulse Width"]),
            float(full["Atrial Sensitivity"]),
            float(full["Ventricular Amplitude"]),
            float(full["Ventricular Pulse Width"]),
            float(full["Ventricular Sensitivity"]),
            int(full["VRP"]),
            int(full["ARP"]),
            int(full["PVARP"]),
            int(full["Maximum Sensor Rate"]),
            int(full["Reaction Time"]),
            int(full["Response Factor"]),
            int(full["Recovery Time"]),
            int(full["Activity Threshold"])
        ]

        return pack(self.ECHO_FMT, *values)


    def poll_egram(self):
        if not self.ser or not self.ser.is_open:
            return None

        if not (self.waiting_for_echo or self.waiting_for_ecg):
            return None

        with self.lock:

            while self.ser.in_waiting > 0:

                header = self.ser.read(1)
                if not header:
                    return None

                byte = header[0]


                if self.waiting_for_echo and 1 <= byte <= 8 and self.ser.in_waiting >= self.ECHO_LEN - 1:

                    rest = self.ser.read(self.ECHO_LEN - 1)
                    raw = bytes([byte]) + rest

                    decoded = unpack_from(self.ECHO_FMT, raw)

                    labels = [
                        "Mode","LRL","URL",
                        "Atrial Amplitude","Atrial Pulse Width","Atrial Sensitivity",
                        "Ventricular Amplitude","Ventricular Pulse Width","Ventricular Sensitivity",
                        "VRP","ARP","PVARP",
                        "Maximum Sensor Rate","Reaction Time","Response Factor","Recovery Time",
                        "Activity Threshold"
                    ]

                    parsed = dict(zip(labels, decoded))

                    print("[ECHO RECEIVED]")
                    for k, v in parsed.items():
                        print(f"{k}: {v}")

                    return parsed


                if self.waiting_for_ecg and byte == ECG_HEADER:

                    if self.ser.in_waiting < ECG_PACKET_LEN:
                        return None

                    payload = self.ser.read(ECG_PACKET_LEN)

                    samples = unpack_from("=20f", payload)
                    a = samples[:10]
                    v = samples[10:]

                    print("[ECG RECEIVED]")
                    print("A:", a)
                    print("V:", v)

                    if self.queue:
                        self.queue.push({"A": a[-1], "V": v[-1]})

                    return a, v


                else:
                    # Drop garbage byte and resync
                    continue

        return None
