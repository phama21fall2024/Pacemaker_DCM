def list_all_ports():
            import serial.tools.list_ports
            for p in serial.tools.list_ports.comports():
                print("PORT:", p.device)
                print(" DESC:", p.description)
                print(" HWID:", p.hwid)
                print(" VID:", p.vid)
                print(" PID:", p.pid)
                print(" SER:", p.serial_number)
                print("------")

list_all_ports()