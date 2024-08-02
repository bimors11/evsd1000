import telnetlib
import time
import subprocess
import threading
import signal
import sys

# Konfigurasi koneksi TELNET ke EVSD1000
HOST = "192.168.0.100"
PORT = 8000
COMMAND_STREAM = "STREAM ALL, 1\n"  # Perintah untuk memulai streaming data
COMMAND_STOP_STREAM = "STOPSTREAM\n"  # Perintah untuk menghentikan streaming data

# Perintah untuk mengubah mode
MODES = {
    "LLZ": "MODE_LOC\n",
    "GP": "MODE_GP\n",
    "VOR": "MODE_VOR\n"
}

class TelnetConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tn = None
        self.stop_stream = False
        self.input_thread = None
        signal.signal(signal.SIGINT, self.signal_handler)

    def connect(self):
        try:
            self.tn = telnetlib.Telnet(self.host, self.port)
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Error: {e}")
            self.tn = None

    def disconnect(self):
        if self.tn:
            self.tn.close()
            self.tn = None
            print("Telnet connection closed.")

    def send_command(self, command):
        try:
            if self.tn:
                self.tn.write(command.encode('utf-8'))
                print(f"Command sent: {command.strip()}")
            else:
                print("Telnet connection is not established.")
        except Exception as e:
            print(f"Error sending command: {e}")

    def refresh_wifi_list(self):
        print("Refreshing WiFi list...")
        try:
            result = subprocess.run(['nmcli', 'device', 'wifi', 'list'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            wifi_list = result.stdout.decode('utf-8')
            print("Available WiFi networks:")
            print(wifi_list)
        except subprocess.CalledProcessError as e:
            print(f"Failed to refresh WiFi list: {e}")

    def connect_to_wifi(self, ssid, password):
        print(f"Connecting to WiFi {ssid}...")
        while True:
            try:
                result = subprocess.run(['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password], check=True)
                print("WiFi connected successfully!")
                break
            except subprocess.CalledProcessError:
                print("Connection failed. Retrying in 5 seconds...")
                time.sleep(5)

    def read_input(self):
        while not self.stop_stream:
            user_input = input()
            if user_input.strip().upper() == "STOP":
                self.stop_stream = True
                self.send_command(COMMAND_STOP_STREAM)
                break

    def stream_data(self, stream_command):
        self.stop_stream = False  # Reset stop_stream flag
        try:
            if self.tn:
                self.send_command(stream_command)
                if not self.input_thread or not self.input_thread.is_alive():
                    self.input_thread = threading.Thread(target=self.read_input)
                    self.input_thread.start()
                while not self.stop_stream:
                    try:
                        data = self.tn.read_until(b'\n', timeout=1).decode('utf-8', errors='ignore').strip()
                        if data:
                            print(data)
                    except UnicodeDecodeError:
                        raw_data = self.tn.read_until(b'\n', timeout=1).strip()
                        print(f"Received raw data: {raw_data}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        break
        except Exception as e:
            print(f"Error: {e}")

    def send_frequency_command(self, frequency):
        try:
            if self.tn:
                # Mengubah frekuensi dari MHz ke kHz jika dalam MHz
                if frequency.lower().endswith('mhz'):
                    frequency = float(frequency[:-3]) * 1000
                elif frequency.lower().endswith('khz'):
                    frequency = float(frequency[:-3])
                else:
                    frequency = float(frequency)  # Asumsikan input sudah dalam kHz

                if 70000 <= frequency <= 410000:
                    command = f"RF {int(frequency)}\n"
                    self.send_command(command)
                    print(f"Frequency command sent: {command.strip()}")
                else:
                    print(f"Error: Frequency {frequency} kHz is out of the allowed range (70000-410000 kHz)")
            else:
                print("Telnet connection is not established.")
        except Exception as e:
            print(f"Error sending frequency command: {e}")

    def signal_handler(self, sig, frame):
        print("\nStopping the stream...")
        self.stop_stream = True
        self.send_command(COMMAND_STOP_STREAM)
        self.disconnect()
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join()  # Tunggu thread input berhenti
        print("Exiting signal handler.")
        sys.exit(0)


if __name__ == "__main__":
    ssid = "EVSD101233"
    password = "RS101233"
    telnet_connection = TelnetConnection(HOST, PORT)

    try:
        telnet_connection.refresh_wifi_list()
        telnet_connection.connect_to_wifi(ssid, password)
        telnet_connection.connect()

        while True:
            while True:
                print("Select Mode: LLZ, GP, VOR")
                selected_mode = input("Enter mode: ").strip().upper()

                if selected_mode in MODES:
                    mode_command = MODES[selected_mode]
                    telnet_connection.send_command(mode_command)
                    break
                else:
                    print("Invalid mode selected. Please try again.")

            while True:
                frequency = input("Enter frequency (in MHz or kHz): ").strip()
                telnet_connection.send_frequency_command(frequency)

                print("Enter 'STREAM' to start streaming data or 'STOP' to end the program.")
                user_command = input("Enter command: ").strip().upper()

                if user_command == "STREAM":
                    telnet_connection.stream_data(COMMAND_STREAM)
                    if telnet_connection.stop_stream:
                        break
                elif user_command == "STOP":
                    telnet_connection.stop_stream = True
                    break
                else:
                    print("Invalid command. Please enter 'STREAM' or 'STOP'.")

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        print("Exiting...")
        telnet_connection.disconnect()
