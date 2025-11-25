import json
import hashlib
import os
from datetime import datetime

class DataManager:
    def __init__(self, filename="pacemaker_data.json"):
        self.filename = filename
        self.data = {
            "users": {},
            "parameters": {},
            "states": {},
            "devices": {}
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                try:
                    self.data = json.load(f)

                    if "devices" not in self.data:
                        self.data["devices"] = {}

                except json.JSONDecodeError:
                    self.data = {
                        "users": {},
                        "parameters": {},
                        "states": {},
                        "devices": {}
                    }
        else:
            self.save_data()

    def save_data(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_user(self, username, password):
        if username in self.data["users"]:
            return False, "User already exists"
        if len(self.data["users"]) >= 10:
            return False, "User limit reached (10)"

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        self.data["users"][username] = hashed_pw
        self.save_data()
        return True, "User registered"

    def validate_user(self, username, password):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        return self.data["users"].get(username) == hashed_pw

    def save_parameters(self, username, params, state_name="default"):
        if username not in self.data["parameters"]:
            self.data["parameters"][username] = {}
        self.data["parameters"][username][state_name] = params
        self.save_data()
        return True, f"Parameters for {state_name} saved successfully."

    def get_parameters(self, username, state_name="default"):
        return self.data["parameters"].get(username, {}).get(state_name)

    def save_state(self, username, state):
        if username not in self.data["users"]:
            return False, "User not found"
        self.data["states"][username] = state
        self.save_data()
        return True, f"State '{state}' saved"

    def get_state(self, username):
        return self.data["states"].get(username)

    def save_device_id(self, username, serial_number, device_id):
        if not serial_number:
            return  # don't save invalid key

        if username not in self.data["devices"]:
            self.data["devices"][username] = {}

        self.data["devices"][username][serial_number] = {
            "device_id": device_id,
            "last_used": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.save_data()


    def get_device_id(self, username, serial_number):
        user_devs = self.data["devices"].get(username, {})
        dev = user_devs.get(serial_number)
        if dev:
            return dev.get("device_id")
        return None

    def get_devices(self, username):
        return self.data["devices"].get(username, [])

    def update_device_last_used(self, username, serial_number):
        devs = self.data["devices"].get(username, {})
        if serial_number in devs:
            devs[serial_number]["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save_data()
