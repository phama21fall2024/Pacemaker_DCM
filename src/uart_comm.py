from datamanager import DataManager
import serial
import serial.tools.list_ports
from struct import pack, unpack_from, calcsize
from threading import Lock

MODE_BITMASK = {
    "AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4,
    "AOOR": 5, "VOOR": 6, "AAIR": 7, "VVIR": 8
}

HDR1 = 0xAA    # First header byte for parameter packets
HDR2 = 0x55    # Second header byte for parameter packets
ECG_HDR = 0xEE # Header byte for ECG packets

class UARTComm:

    def __init__(self, queue=None, baudrate=57600):
        self.db = DataManager()      
        self.queue = queue         
        self.baudrate = baudrate   
        self.ser = None            
        self.lock = Lock()         

        # Flags to indicate what data we are waiting for
        self.waiting_for_echo = False
        self.waiting_for_ecg = False

        self.ECHO_FMT = "=BBB6f3H5B"

        # Total number of bytes for one parameter packet
        self.ECHO_LEN = calcsize(self.ECHO_FMT)

    def connect(self):
        # Scan all available serial ports
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("NO SERIAL DEVICES FOUND")
            return False

        # Try connecting to each detected serial port
        for p in ports:
            try:
                self.ser = serial.Serial(p.device, self.baudrate, timeout=0.3)
                print("CONNECTED:", p.device)
                return True
            except:
                pass

        # If no ports successfully opened
        print("NO WORKING SERIAL PORT")
        return False

    def disconnect(self):
        # Close serial connection if open
        if self.ser:
            self.ser.close()
            self.ser = None

    def send_to_device(self, username):
        # Get pacemaker mode and parameters from database
        mode = self.db.get_state(username)
        params = self.db.get_parameters(username, state_name=mode)

        # Ensure serial port is connected
        if not self.ser or not self.ser.is_open:
            raise Exception("Device not connected")

        # Build UART packet
        packet = self._build_packet(mode, params)

        # Send packet safely using lock
        with self.lock:
            self.ser.reset_output_buffer()
            self.ser.write(packet)
            self.ser.flush()

        # Expect a response from the device
        self.waiting_for_echo = True
        self.waiting_for_ecg = True

        # Debug output
        print("TX:", packet.hex())
        print("MODE SENT:", mode)

        return packet

    def _build_packet(self, mode, params):
        # Default parameter values (used if database is missing values)
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

        # Override defaults with database values
        if params:
            full.update(params)

        # Activity Threshold can be a string label or number
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

        # Pack values into binary payload
        payload = pack(self.ECHO_FMT, *values)

        # Add framing headers
        framed = bytes([HDR1, HDR2]) + payload

        return framed

    def poll_egram(self):
        # Return immediately if serial is not open
        if not self.ser or not self.ser.is_open:
            return None

        with self.lock:
            # Read while bytes are available
            while self.ser.in_waiting:
                byte = self.ser.read(1)[0]   

                # Check for parameter packet header
                if byte == HDR1:
                    if self.ser.in_waiting and self.ser.read(1)[0] == HDR2:
                        # Wait until full payload arrives
                        if self.ser.in_waiting < self.ECHO_LEN:
                            return None

                        payload = self.ser.read(self.ECHO_LEN)
                        decoded = unpack_from(self.ECHO_FMT, payload)

                        self.waiting_for_echo = False

                        labels = [
                            "Mode","LRL","URL",
                            "Atrial Amplitude","Atrial Pulse Width","Atrial Sensitivity",
                            "Ventricular Amplitude","Ventricular Pulse Width","Ventricular Sensitivity",
                            "VRP","ARP","PVARP",
                            "Maximum Sensor Rate","Reaction Time","Response Factor","Recovery Time",
                            "Activity Threshold"
                        ]

                        # Return dictionary of parameters
                        return dict(zip(labels, decoded))

                if byte == ECG_HDR:
                    if self.ser.in_waiting < 2:
                        return None

                    # Read atrial and ventricular data
                    a_raw = self.ser.read(1)[0]
                    v_raw = self.ser.read(1)[0]

                    # Convert 0–255 readings to voltage scale
                    a_val = (a_raw / 255.0) * 5.0
                    v_val = (v_raw / 255.0) * 5.0

                    # Push values to queue for plotting / processing
                    if self.queue:
                        self.queue.push({"A": a_val, "V": v_val})

                    return a_val, v_val

        return None
