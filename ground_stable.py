import serial
import time
import signal
import sys
import threading
import csv

# Konfigurasi port serial Raspberry Pi
SERIAL_PORT = '/dev/ttyUSB2'
BAUD_RATE = 57600
MAIN_SCRIPT = 'execute.py'
CSV_FILENAME_TEMPLATE = '{}_stream_data.csv'  # Template untuk nama file CSV

# Data header untuk VOR, ILS, dan GP Mode
CSV_HEADER = {
    "VOR": [
        "Channel", "STIOCPM", "Index", "Date", "Time", "FREQ[MHz]",
        "CRS_UF/SINGLE[kHz]", "CLR_LF[kHz]", "LEVEL[dBm]", "AM-MOD./90Hz[%]",
        "AM-MOD./150Hz[%]", "FREQ_90[Hz]", "FREQ_150[Hz]", "DDM(90-150)[1]",
        "SDM[%]", "PHI-90/150[°]", "VOICE-MOD.[%]", "ID-MOD.[%]", "ID-F.[Hz]",
        "ID-CODE", "LEV_CLR_LF[dBm]", "LEV_CRS_UF[dBm]",
        "AM-MOD_CLR_LF/90Hz[%]", "AM-MOD_CLR_LF/150Hz[%]",
        "DDM_CLR_LF(90-150)[1]", "SDM_CLR_LF[%]", "AM-MOD_CRS_UF/90Hz[%]",
        "AM-MOD_CRS_UF/150Hz[%]", "DDM_CRS_UF(90-150)[1]", "SDM_CRS_UF[%]",
        "PHI-90/90[°]", "PHI-150/150[°]", "K2/90Hz[%]", "K2/150Hz[%]",
        "K3/90Hz[%]", "K3/150Hz[%]", "THD/90Hz[%]", "THD/150Hz[%]", "GPS_lat.",
        "GPS_long.", "GPS_alt[m]", "GPS_speed[km/h]", "GPS_date", "GPS_time",
        "GPS_Sat", "GPS_Status", "GPS_Fix", "GPS_HDOP", "GPS_VDOP", "Temp[°C]",
        "MeasTime[ms]", "MeasMode", "LOC_GP", "ATT.MODE", "TrigCounter", "test"
    ],
    "ILS": [
        "RX", "STIOCPM", "Index", "Date", "Time", "FREQ[MHz]", "SINGLE[kHz]", "CRS_UF",
        "CLR_LF[kHz]", "LEVEL[dBm]", "AM-MOD./90Hz[%]", "AM-MOD./150Hz[%]",
        "FREQ_90[Hz]", "FREQ_150[Hz]", "DDM(90-150)[1]", "SDM[%]",
        "PHI-90/150[°]", "VOICE-MOD.[%]", "ID-MOD.[%]", "ID-F.[Hz]", "ID-CODE",
        "ID-Per.[s]", "Last_ID[s]", "DotLen[ms]", "DashLen[ms]", "DotDashGap[ms]",
        "Lettergap[ms]", "LEV_CLR_LF[dBm]", "LEV_CRS_UF[dBm]",
        "AM-MOD_CLR_LF/90Hz[%]", "AM-MOD_CLR_LF/150Hz[%]",
        "FREQ_90_CLR_LF[Hz]", "FREQ_150_CLR_LF[Hz]", "DDM_CLR_LF(90-150)[1]",
        "SDM_CLR_LF[%]", "PHI-90/150_CLR_LF[°]", "AM-MOD_CRS_UF/90Hz[%]",
        "AM-MOD_CRS_UF/150Hz[%]",
        "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]", "DDM_CRS_UF(90-150)[1]",
        "SDM_CRS_UF[%]", "PHI-90/150_CRS_UF[°]", "PHI-90/90[°]", "PHI-150/150[°]",
        "ResFM90[Hz]", "ResFM150[Hz]", "K2/90Hz[%]", "K2/150Hz[%]",
        "K3/90Hz[%]", "K3/150Hz[%]",
        "K4/90Hz[%]", "K4/150Hz[%]", "THD/90Hz[%]", "THD/150Hz[%]",
        "AM240[%]", "GPS_lat.", "GPS_long.", "GPS_alt[m]", "GPS_speed[km/h]",
        "GPS_date", "GPS_time", "GPS_Sat", "GPS_Status", "GPS_Fix",
        "GPS_HDOP", "GPS_VDOP", "GPS_Und.[m]", "Temp[°C]", "MeasTime[ms]",
        "MeasMode", "LOC_GP", "ATT.MODE", "DemodOffset_1F", "DemodOffset_CRS",
        "DemodOffset_CLR", "Autotune_1F", "Autotune_CRS", "Autotune_CLR",
        "IFBW_Man_WIDE", "IFBW_Man_UCLC", "TrigCounter", "IQPosition", "IQSamples"
    ],
    "GP": [
        "RX", "STIOCPM", "Index", "Date", "Time", "FREQ[MHz]", "SINGLE[kHz]", "CRS_UF",
        "CLR_LF[kHz]", "LEVEL[dBm]", "AM-MOD./90Hz[%]", "AM-MOD./150Hz[%]",
        "FREQ_90[Hz]", "FREQ_150[Hz]", "DDM(90-150)[1]", "SDM[%]",
        "PHI-90/150[°]", "VOICE-MOD.[%]", "ID-MOD.[%]", "ID-F.[Hz]", "ID-CODE",
        "ID-Per.[s]", "Last_ID[s]", "DotLen[ms]", "DashLen[ms]", "DotDashGap[ms]",
        "Lettergap[ms]", "FREQ_90_CLR_LF[Hz]", "FREQ_150_CLR_LF[Hz]",
        "DDM_CLR_LF(90-150)[1]", "SDM_CLR_LF[%]", "PHI-90/150_CLR_LF[°]",
        "AM-MOD_CRS_UF/90Hz[%]", "AM-MOD_CRS_UF/150Hz[%]",
        "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]", "DDM_CRS_UF(90-150)[1]",
        "SDM_CRS_UF[%]", "PHI-90/150_CRS_UF[°]", "PHI-90/90[°]", "PHI-150/150[°]",
        "K2/90Hz[%]", "K2/150Hz[%]", "K3/90Hz[%]", "K3/150Hz[%]",
        "K4/90Hz[%]", "K4/150Hz[%]", "THD/90Hz[%]", "THD/150Hz[%]", "GPS_lat.",
        "GPS_long.", "GPS_alt[m]", "GPS_speed[km/h]", "GPS_date", "GPS_time",
        "GPS_Sat", "GPS_Status", "GPS_Fix", "GPS_HDOP", "GPS_VDOP", "GPS_Und.[m]",
        "Temp[°C]", "MeasTime[ms]", "MeasMode", "LOC_GP", "ATT.MODE",
        "DemodOffset_1F", "DemodOffset_CRS", "DemodOffset_CLR", "Autotune_1F",
        "Autotune_CRS", "Autotune_CLR", "IFBW_Man_WIDE", "IFBW_Man_UCLC",
        "TrigCounter", "IQPosition", "IQSamples"
    ]
}

stop_event = threading.Event()
ser = None
recording = False
csv_writer = None
csv_file = None
current_mode = None

def connect_to_raspi_via_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at baudrate {BAUD_RATE}")
    except serial.SerialException as e:
        print(f"Error: {e}")
        ser = None

def login_to_raspberry_pi():
    global ser
    try:
        if ser is None or not ser.is_open:
            return False
        # Membaca prompt login dari Raspberry Pi
        output = ser.read_until(b"login: ").decode('utf-8')
        print(output.strip())
        
        # Mengirimkan username dan password
        ser.write(b"beta\n")
        time.sleep(1)
        output = ser.read_until(b"Password: ").decode('utf-8')
        print(output.strip())
        ser.write(b"beta123\n")
        time.sleep(1)
        
        # Membaca output setelah login
        output = ser.read_until(b"$ ").decode('utf-8')
        print(output.strip())
        
        return True
    except Exception as e:
        print(f"Login error: {e}")
        return False

def execute_main_script():
    global ser
    try:
        if ser is None or not ser.is_open:
            return
        ser.write(f"sudo python3 {MAIN_SCRIPT}\n".encode())
        print(f"Executing {MAIN_SCRIPT} on Raspberry Pi")
        time.sleep(2)
    except Exception as e:
        print(f"Execution error: {e}")

def start_recording(mode):
    global csv_writer, csv_file
    try:
        file_name = f"{mode}_stream_data.csv"
        csv_file = open(file_name, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(CSV_HEADER[mode])
        print(f"Started recording in {mode} mode to {file_name}")
    except Exception as e:
        print(f"Error starting recording: {e}")

def stop_recording():
    global csv_writer, csv_file
    try:
        if csv_file is not None:
            csv_file.close()
            csv_writer = None
            csv_file = None
        print("Stopped recording")
    except Exception as e:
        print(f"Error stopping recording: {e}")

def read_serial_data():
    global ser, recording, csv_writer, current_mode
    try:
        ready_count = 0
        while not stop_event.is_set():
            if ser and ser.is_open:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(data)  # Cetak data yang diterima
                    if data == "Stream command sent: STREAM ALL, 1":
                        ready_count += 1
                        if ready_count == 1 and current_mode:
                            recording = True
                            start_recording(current_mode)
                            ready_count = 0  # Reset ready count after starting recording
                            print(f"Started recording in {current_mode} mode")
                    elif recording:
                        if data == "STOPSTREAM command sent.":
                            stop_recording()
                            recording = False
                            print(f"Stopped recording {current_mode} mode")
                        else:
                            try:
                                csv_writer.writerow(data.split(','))  # Adjust as needed based on actual data format
                            except Exception as e:
                                print(f"Error writing data to CSV: {e}")
    except Exception as e:
        if not stop_event.is_set():  # Hanya cetak error jika bukan karena penghentian program
            print(f"Error reading data: {e}")


def monitor_user_input():
    global ser, current_mode, recording
    try:
        while not stop_event.is_set():
            print("Select Mode: ILS, GP, VOR")
            user_input = input("Enter mode: ").strip().upper()
            if user_input in ["ILS", "GP", "VOR"]:
                if ser and ser.is_open:
                    ser.write(f"{user_input}\n".encode())
                    print(f"Selected mode: {user_input}")
                    current_mode = user_input  # Set current mode but don't start recording yet
                    if recording:
                        stop_recording()
                        recording = False
            elif user_input == "STOP":
                if ser and ser.is_open:
                    ser.write(b"STOP\n")
                    print("Sent 'STOP' to Raspberry Pi.")
            elif user_input == "QUIT":
                if ser and ser.is_open:
                    ser.write(b'\x03')  # Mengirimkan karakter ASCII untuk CTRL+C
                    print("Sent 'CTRL+C' to Raspberry Pi.")
    except Exception as e:
        if not stop_event.is_set():  # Hanya cetak error jika bukan karena penghentian program
            print(f"Input error: {e}")

def main():
    global ser
    signal.signal(signal.SIGINT, signal_handler)

    connect_to_raspi_via_serial()
    if ser and ser.is_open:
        if login_to_raspberry_pi():
            execute_main_script()
            read_thread = threading.Thread(target=read_serial_data)
            input_thread = threading.Thread(target=monitor_user_input)
            read_thread.start()
            input_thread.start()
            try:
                read_thread.join()
                input_thread.join()
            except KeyboardInterrupt:
                signal_handler(None, None)
        if ser.is_open:
            ser.close()
        print("Connection closed.")

def signal_handler(sig, frame):
    global ser, stop_event
    stop_event.set()
    if ser and ser.is_open:
        ser.close()
    print("\nQuitting the program.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()
