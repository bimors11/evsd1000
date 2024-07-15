import serial
import time
import csv
import signal
import sys
import keyboard  # Import pustaka keyboard jika tersedia

# Konfigurasi port serial Raspberry Pi
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 57600
MAIN_SCRIPT = 'main2.py'
CSV_FILENAME = 'stream_data.csv'
CSV_HEADER = [
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
]

def connect_to_raspi_via_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at baudrate {BAUD_RATE}")
        return ser
    except serial.SerialException as e:
        print(f"Error: {e}")
        return None

def execute_main_script(ser):
    try:
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
        
        # Membaca prompt setelah login
        output = ser.read_until(b"$ ").decode('utf-8')
        print(output.strip())

        # Eksekusi script main2.py
        command = f"sudo python3 {MAIN_SCRIPT}\n"
        ser.write(command.encode('utf-8'))
        print(f"Executing {MAIN_SCRIPT} on Raspberry Pi via serial...")

        # Membaca output dari Raspberry Pi via serial sampai muncul "READY."
        while True:
            data = ser.readline().decode('utf-8').strip()
            print(data)
            if "READY." in data:
                print("Found 'READY.', starting recording.")
                break

        # Membaca dan merekam data setelah muncul 'READY.'
        with open(CSV_FILENAME, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(CSV_HEADER)  # Menulis header CSV

            while True:
                try:
                    data = ser.readline().decode('utf-8').strip()
                    if data:
                        row = data.split(',')
                        if len(row) == len(CSV_HEADER):
                            csv_writer.writerow(row)
                            csvfile.flush()
                        else:
                            print(f"Data length mismatch: {data}")
                except UnicodeDecodeError:
                    raw_data = ser.readline().strip()
                    print(f"Received raw data: {raw_data}")
                    csv_writer.writerow([raw_data])
                    csvfile.flush()
                except KeyboardInterrupt:
                    # Mengirimkan perintah untuk menghentikan stream di Raspberry Pi
                    ser.write(b"\x03\n")  # Mengirim Ctrl+C
                    print("Stream stopped on Raspberry Pi.")
                    break

    except Exception as e:
        print(f"Serial communication or script execution error: {e}")
    finally:
        ser.close()
        print("Connection closed.")

def signal_handler(sig, frame):
    print("\nCtrl+C detected on laptop. Exiting...")
    sys.exit(0)

def send_ctrl_c_to_raspi(ser):
    # Mengirimkan perintah Ctrl+C ke Raspberry Pi
    ser.write(b"\x03\n")  # Mengirim Ctrl+C

if __name__ == "__main__":
    # Tangani sinyal KeyboardInterrupt di laptop
    signal.signal(signal.SIGINT, signal_handler)

    serial_connection = connect_to_raspi_via_serial()
    if serial_connection:
        execute_main_script(serial_connection)

        # Deteksi jika Alt+X ditekan di laptop
        while True:
            if keyboard.is_pressed('alt+x'):
                send_ctrl_c_to_raspi(serial_connection)
                break
