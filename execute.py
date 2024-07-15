import telnetlib
import time
import subprocess
import csv
import threading
import signal
import sys

# Konfigurasi koneksi TELNET ke EVSD1000
HOST = "192.168.0.100"
PORT = 8000
COMMAND_STREAM = "STREAM ALL, 1\n"  # Perintah untuk memulai streaming data
COMMAND_STOP_STREAM = "STOPSTREAM\n"  # Perintah untuk menghentikan streaming data
CSV_FILENAME = "telnet_data.csv"

# Perintah untuk mengubah mode
MODES = {
    "ILS": "MODE_LOC\n",
    "GP": "MODE_GP\n",
    "VOR": "MODE_VOR\n"
}

stop_stream = False
tn = None  # Koneksi telnet global

def connect_to_wifi(ssid, password):
    print(f"Connecting to WiFi {ssid}...")
    while True:
        try:
            result = subprocess.run(['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password], check=True)
            print("WiFi connected successfully!")
            break
        except subprocess.CalledProcessError:
            print("Connection failed. Retrying in 5 seconds...")
            time.sleep(5)

def read_input():
    global stop_stream
    while True:
        user_input = input()
        if user_input.strip().upper() == "STOP":
            stop_stream = True
            break

def send_stopstream_command():
    global tn
    try:
        if tn:
            tn.write(COMMAND_STOP_STREAM.encode('utf-8'))
            print("STOPSTREAM command sent.")
        else:
            print("Telnet connection is not established.")
    except Exception as e:
        print(f"Error sending STOPSTREAM command: {e}")

def connect_and_stream_telnet(host, port, mode_command, stream_command):
    global stop_stream, tn
    try:
        tn = telnetlib.Telnet(host, port)
        print(f"Connected to {host}:{port}")

        # Mengirim perintah untuk mengubah mode
        tn.write(mode_command.encode('utf-8'))
        print(f"Mode command sent: {mode_command.strip()}")
        time.sleep(1)  # Beri waktu untuk perubahan mode

        # Mengirim perintah untuk memulai streaming data
        tn.write(stream_command.encode('utf-8'))
        print(f"Stream command sent: {stream_command.strip()}")

        with open(CSV_FILENAME, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Received Data"])  # Header untuk CSV

            input_thread = threading.Thread(target=read_input)
            input_thread.start()

            while not stop_stream:
                try:
                    data = tn.read_until(b'\n', timeout=1).decode('utf-8', errors='ignore').strip()
                    if data:
                        print(data)
                        csv_writer.writerow([data])
                except UnicodeDecodeError:
                    # Jika terjadi UnicodeDecodeError, kita bisa langsung print raw data
                    raw_data = tn.read_until(b'\n', timeout=1).strip()
                    print(f"Received raw data: {raw_data}")
                    csv_writer.writerow([raw_data])
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if tn is not None:
            try:
                send_stopstream_command()
            except AttributeError:
                pass
            tn.close()
            print("Telnet connection closed.")

def signal_handler(sig, frame):
    global stop_stream, tn
    print("\nStopping the stream...")
    stop_stream = True
    if tn:
        try:
            tn.write(COMMAND_STOP_STREAM.encode('utf-8'))
            print("STOPSTREAM command sent.")
        except Exception as e:
            print(f"Error sending STOPSTREAM command: {e}")
        tn.close()
        tn = None  # Setelah ditutup, atur koneksi telnet menjadi None
        print("Telnet connection closed.")
    print("Exiting signal handler.")


if __name__ == "__main__":
    ssid = "EVSD101233"
    password = "RS101233"

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            connect_to_wifi(ssid, password)
            
            # Meminta mode dari pengguna
            print("Select Mode: ILS, GP, VOR")
            selected_mode = input("Enter mode: ").strip().upper()
            
            if selected_mode in MODES:
                mode_command = MODES[selected_mode]
                connect_and_stream_telnet(HOST, PORT, mode_command, COMMAND_STREAM)
            else:
                print("Invalid mode selected. Exiting.")
                break
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        print("Exiting...")
