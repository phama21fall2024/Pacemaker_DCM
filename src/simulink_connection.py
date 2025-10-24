import json

# WIP

class SimulinkInterface:
    def __init__(self, model_name="Pacemaker Simulink"):
        self.eng = None
        self.model_name = model_name
        self.is_connected = False

    def connect(self):
        self.is_connected = True
        print(f"Connected to {self.model_name}")

    def send_parameters(self, parameters):
        if not self.is_connected:
            raise RuntimeError("Simulink not connected.")

        for key, value in parameters.items():
            try:
                val = float(value)
                var_name = key.replace(" ", "_")
                print(f"{var_name} = {val}")
            except ValueError:
                print(f"Invalid parameter {key}={value}")

        print("Parameters updated")

    def run_simulation(self):
        if not self.is_connected:
            raise RuntimeError("Simulink not connected")
        print("Simulation started")

    def disconnect(self):
        if self.is_connected:
            self.is_connected = False
            print("Disconnected")
