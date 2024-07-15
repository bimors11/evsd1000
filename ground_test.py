import serial
import time
import csv
import signal
import sys
import telnetlib  # Menambahkan library telnet
import keyboard

# Konfigurasi port serial Raspberry Pi
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 57600
MAIN_SCRIPT = 'main2.py'
CSV_FILENAME = 'stream_data.csv'

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
        "AM-MOD_CRS_UF/150Hz[%]", "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]",
        "DDM_CRS_UF(90-150)[1]", "SDM_CRS_UF[%]", "PHI-90/150_CRS_UF[°]",
        "PHI-90/90[°]", "PHI-150/150[°]", "ResFM90[Hz]", "ResFM150[Hz]",
        "K2/90Hz[%]", "K2/150Hz[%]", "K3/90Hz[%]", "K3/150Hz[%]",
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
        "Lettergap[ms]", "LEV_CLR_LF[dBm]", "LEV_CRS_UF[dBm]",
        "AM-MOD_CLR_LF/90Hz[%]", "AM-MOD_CLR_LF/150Hz[%]",
        "FREQ_90_CLR_LF[Hz]", "FREQ_150_CLR_LF[Hz]", "DDM_CLR_LF(90-150)[1]",
        "SDM_CLR_LF[%]", "PHI-90/150_CLR_LF[°]", "AM-MOD_CRS_UF/90Hz[%]",
        "AM-MOD_CRS_UF/150Hz[%]", "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]",
        "DDM_CRS_UF(90-150)[1]", "SDM_CRS_UF[%]", "PHI-90/150_CRS_UF[°]",
        "PHI-90/90[°]", "PHI-150/150[°]", "ResFM90[Hz]", "ResFM150[Hz]",
        "K2/90Hz[%]", "K2/150Hz[%]", "K3/90Hz[%]", "K3/150Hz[%]",
        "K4/90Hz[%]", "K4/150Hz[%]", "THD/90Hz[%]", "THD/150Hz[%]",
        "AM240[%]", "GPS_lat.", "GPS_long.", "GPS_alt[m]", "GPS_speed[km/h]",
        "GPS_date", "GPS_time", "GPS_Sat", "GPS_Status", "GPS_Fix",
        "GPS_HDOP", "GPS_VDOP", "GPS_Und.[m]", "Temp[°C]", "MeasTime[ms]",
        "MeasMode", "LOC_GP", "ATT.MODE", "DemodOffset_1F", "DemodOffset_CRS",
        "DemodOffset_CLR", "Autotune_1F", "Autotune_CRS", "Autotune_CLR",
        "IFBW_Man_WIDE", "IFBW_Man_UCLC", "TrigCounter", "IQPosition", "IQSamples"
    ]
}

def connect_to_raspi_via_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at baudrate {BAUD_RATE}")
        return ser
    except serial.SerialException as e:
        print(f"Error: {e}")
        return None

def execute_main_script(ser, mode):
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

        # Eksekusi script main2.py dengan mode yang diberikan
        command = f"sudo python3 {MAIN_SCRIPT} {mode}\n"
        ser.write(command.encode('utf-8'))
        print(f"Executing {MAIN_SCRIPT} on Raspberry Pi in {mode} mode via serial...")

        # Membaca output dari Raspberry Pi via serial sampai muncul "READY."
        while True:
            data = ser.readline().decode('utf-8').strip()
            print(data)
            if "READY." in data:
                print("Found 'READY.', starting recording.")
                break

        # Membaca dan merekam data setelah muncul 'READY.'
        csv_filename = f'stream_data_{mode}.csv'
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(CSV_HEADER[mode])  # Menulis header CSV sesuai mode

            while True:
                try:
                    data = ser.readline().decode('utf-8').strip()
                    if data:
                        row = data.split(',')
                        if len(row) == len(CSV_HEADER[mode]):
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

def send_ctrl_c_to_raspi(ser):
    # Mengirimkan perintah Ctrl+C ke Raspberry Pi
    ser.write(b"\x03\n")  # Mengirim Ctrl+C

def send_stopstream_via_telnet():
    try:
        HOST = "raspberrypi_hostname_or_ip"  # Ganti dengan hostname atau IP Raspberry Pi
        tn = telnetlib.Telnet(HOST)
        tn.read_until(b"login: ")
        tn.write(b"username\n")
        tn.read_until(b"Password: ")
        tn.write(b"password\n")
        tn.read_until(b"$ ")
        tn.write(b"sudo systemctl stop stream.service\n")  # Ganti dengan perintah yang sesuai
        tn.read_until(b"password for username: ")
        tn.write(b"password\n")
        print("Sent STOPSTREAM command via telnet.")
        tn.close()
    except Exception as e:
        print(f"Error sending STOPSTREAM command via telnet: {e}")

def signal_handler(sig, frame):
    print("\nCtrl+C detected on laptop. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    # Tangani sinyal KeyboardInterrupt di laptop
    signal.signal(signal.SIGINT, signal_handler)

    # Mendapatkan mode dari pengguna (VOR, ILS, GP)
    mode = input("Masukkan mode (VOR, ILS, GP): ").upper()
    while mode not in ['VOR', 'ILS', 'GP']:
        mode = input("Mode tidak valid. Masukkan mode (VOR, ILS, GP): ").upper()

    serial_connection = connect_to_raspi_via_serial()
    if serial_connection:
        execute_main_script(serial_connection, mode)

        # Deteksi jika Alt+X ditekan di laptop untuk mengirim Ctrl+C ke Raspberry Pi
        while True:
            if keyboard.is_pressed('alt+x'):
                send_ctrl_c_to_raspi(serial_connection)
                break

        # Deteksi jika Alt+S ditekan di laptop untuk mengirim STOPSTREAM command via telnet
        while True:
            if keyboard.is_pressed('alt+s'):
                send_stopstream_via_telnet()
                break
