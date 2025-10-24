import json
import hashlib
import os

class DataManager:
    def __init__(self, filename="pacemaker_data.json"):
        self.filename = filename
        self.data = {"users": {}, "parameters": {}, "states": {}}
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                try:
                    self.data = json.load(f)
                except json.JSONDecodeError:
                    self.data = {"users": {}, "parameters": {}, "states": {}}
        else:
            self.save_data()

    def save_data(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_user(self, username, password):
        if len(self.data["users"]) >= 10:
            return False, "User limit reached (10)"

        if username in self.data["users"]:
            return False, "User already exists"

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        self.data["users"][username] = hashed_pw
        self.save_data()
        return True, "User registered"

    def validate_user(self, username, password):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        return self.data["users"].get(username) == hashed_pw

    def save_parameters(self, username, params):
        if username not in self.data["users"]:
            return False, "User not found"
        
        self.data["parameters"][username] = params
        self.save_data()
        return True, "Parameters saved"

    def get_parameters(self, username):
        return self.data["parameters"].get(username, {})

    def save_state(self, username, state):
        if username not in self.data["users"]:
            return False, "User not found"
        
        self.data["states"][username] = state
        self.save_data()
        return True, f"State '{state}' saved"

    def get_state(self, username):
        return self.data["states"].get(username)
