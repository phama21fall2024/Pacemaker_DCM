import json
import hashlib
import os

class DataManager:
    def __init__(self, filename="pacemaker_data.json"):
        self.filename = filename
        self.data = {"users": {}, "parameters": {}, "states": {}} # Data Consists of Users, Parameters and States
        self.load_data() # Loads all the data from the json file

    def load_data(self):
        if os.path.exists(self.filename): 
            with open(self.filename, "r") as f:
                try: 
                    self.data = json.load(f) # Loads the data from the json into self.data
                except json.JSONDecodeError: # If json is corrupted just creates a new one
                    self.data = {"users": {}, "parameters": {}, "states": {}}
        else:
            self.save_data()


    def save_data(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4) # Saves data into json

    def add_user(self, username, password):
        if len(self.data["users"]) >= 10: # Checks if user exceeds 10
            return False, "User limit reached (10)"

        if username in self.data["users"]: # Checks if user already existed
            return False, "User already exists"

        # hashed_pw = hashlib.sha256(password.encode()).hexdigest() # Hashes the password to ensure security
        self.data["users"][username] = password
        self.save_data()
        return True, "User registered"

    def validate_user(self, username, password):
        # hashed_pw = hashlib.sha256(password.encode()).hexdigest() # Make sure the hash password is correct with the saved hashed
        return self.data["users"].get(username) == password

    def save_parameters(self, username, params):
        if username not in self.data["users"]: 
            return False, "User not found"
        
        self.data["parameters"][username] = params # Saves the parameter to username
        self.save_data()
        return True, "Parameters saved"

    def get_parameters(self, username):
        return self.data["parameters"].get(username, {}) # Gets the parameter from the username

    def save_state(self, username, state):
        if username not in self.data["users"]:
            return False, "User not found"
        
        self.data["states"][username] = state # Saves the state to the username
        self.save_data()
        return True, f"State '{state}' saved"

    def get_state(self, username):
        return self.data["states"].get(username) # Gets state from username
