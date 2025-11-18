import json
import hashlib
import os

class DataManager:
    def __init__(self, filename="pacemaker_data.json"):
        self.filename = filename
        self.data = {
            "users": {},
            "parameters": {},
            "states": {},
            "devices": {}    # <-- NEW
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename): 
            with open(self.filename, "r") as f:
                try: 
                    self.data = json.load(f)

                    # Ensure new keys exist in older JSON files
                    if "devices" not in self.data:
                        self.data["devices"] = {}

                except json.JSONDecodeError:
                    self.data = {"users": {}, "parameters": {}, "states": {}, "devices": {}}
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
        return self.data["parameters"].get(username, {}).get(state_name, None)

    def save_state(self, username, state):
        if username not in self.data["users"]:
            return False, "User not found"
        
        self.data["states"][username] = state
        self.save_data()
        return True, f"State '{state}' saved"

    def get_state(self, username):
        return self.data["states"].get(username)

    def save_device(self, username, serial_number):
        """Save a detected device serial number to JSON."""
        if username not in self.data["devices"]:
            self.data["devices"][username] = []

        if serial_number not in self.data["devices"][username]:
            self.data["devices"][username].append(serial_number)
            self.save_data()

    def get_devices(self, username):
        """Retrieve all saved devices for a user."""
        return self.data["devices"].get(username, [])
