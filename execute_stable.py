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
    "ILS": "MODE_LOC\n",
    "GP": "MODE_GP\n",
    "VOR": "MODE_VOR\n"
}

stop_stream = False
tn = None  # Koneksi telnet global
input_thread = None  # Thread input global

def refresh_wifi_list():
    print("Refreshing WiFi list...")
    try:
        result = subprocess.run(['nmcli', 'device', 'wifi', 'list'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wifi_list = result.stdout.decode('utf-8')
        print("Available WiFi networks:")
        print(wifi_list)
    except subprocess.CalledProcessError as e:
        print(f"Failed to refresh WiFi list: {e}")

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
    while not stop_stream:
        user_input = input()
        if user_input.strip().upper() == "STOP":
            stop_stream = True
            send_stopstream_command()
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
    global stop_stream, tn, input_thread
    stop_stream = False  # Reset stop_stream flag
    try:
        if not tn:  # Establish connection only if it does not exist
            tn = telnetlib.Telnet(host, port)
            print(f"Connected to {host}:{port}")

        # Mengirim perintah untuk mengubah mode
        tn.write(mode_command.encode('utf-8'))
        print(f"Mode command sent: {mode_command.strip()}")
        time.sleep(1)  # Beri waktu untuk perubahan mode

        # Mengirim perintah untuk memulai streaming data
        tn.write(stream_command.encode('utf-8'))
        print(f"Stream command sent: {stream_command.strip()}")

        # Memulai thread untuk membaca input pengguna
        if input_thread is None or not input_thread.is_alive():
            input_thread = threading.Thread(target=read_input)
            input_thread.start()

        while not stop_stream:
            try:
                data = tn.read_until(b'\n', timeout=1).decode('utf-8', errors='ignore').strip()
                if data:
                    print(data)
            except UnicodeDecodeError:
                # Jika terjadi UnicodeDecodeError, kita bisa langsung print raw data
                raw_data = tn.read_until(b'\n', timeout=1).strip()
                print(f"Received raw data: {raw_data}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
    except Exception as e:
        print(f"Error: {e}")

def signal_handler(sig, frame):
    global stop_stream, tn, input_thread
    print("\nStopping the stream...")
    stop_stream = True
    send_stopstream_command()
    if tn:
        tn.close()
        tn = None  # Setelah ditutup, atur koneksi telnet menjadi None
        print("Telnet connection closed.")
    if input_thread and input_thread.is_alive():
        input_thread.join()  # Tunggu thread input berhenti
    print("Exiting signal handler.")
    sys.exit(0)

if __name__ == "__main__":
    ssid = "EVSD101233"
    password = "RS101233"

    # Tangani sinyal KeyboardInterrupt di laptop
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            refresh_wifi_list()  # Menambahkan pemanggilan fungsi refresh WiFi
            connect_to_wifi(ssid, password)
            
            # Meminta mode dari pengguna
            while True:
                print("Select Mode: ILS, GP, VOR")
                selected_mode = input("Enter mode: ").strip().upper()
                
                if selected_mode in MODES:
                    mode_command = MODES[selected_mode]
                    connect_and_stream_telnet(HOST, PORT, mode_command, COMMAND_STREAM)
                    if stop_stream:
                        stop_stream = False
                        continue
                else:
                    print("Invalid mode selected. Please try again.")
                
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        print("Exiting...")
