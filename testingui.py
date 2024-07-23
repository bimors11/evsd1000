import sys
import serial
import time
import threading
import csv
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
import signal

# Konfigurasi port serial Raspberry Pi
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 57600
MAIN_SCRIPT = 'execute.py'
CSV_FILENAME_TEMPLATE = '{}_stream_data.csv'  # Template untuk nama file CSV

# Data header untuk VOR, ILS, dan GP Mode
CSV_HEADER = {
    "VOR": [
        "RX", "STIOCPMV", "Index", "Date", "Time", "FREQ[MHz]", "MEAS.F[kHz]",
        "LEVEL[dBm]", "AM-MOD./30Hz[%]", "AM-MOD./9960Hz[%]", "FREQ_30[Hz]",
        "FREQ_9960[Hz]", "FREQ_FM30[Hz]", "BEARING(from)[°]", "FM-DEV.[Hz]",
        "FM-INDEX", "VOICE-MOD.[%]", "ID-MOD.[%]", "ID-F.[Hz]", "ID-CODE",
        "ID-Per.[s]", "Last_ID[s]", "DotLen[ms]", "DashLen[ms]", "DotDashGap[ms]",
        "Lettergap[ms]", "SubCarr_K2[dB]", "SubCarr_K3[dB]", "SubCarr_K4[dB]",
        "SubCarr_K5[dB]", "AM60Hz[%]", "AM1k44[%]", "AM1k50[%]", "No.Of Segm",
        "GPS_lat.", "GPS_long.", "GPS_alt[m]", "GPS_speed[km/h]", "GPS_date",
        "GPS_time", "GPS_Sat", "GPS_Status", "GPS_Fix", "GPS_HDOP", "GPS_VDOP",
        "GPS_Und.[m]", "Temp[°C]", "IFBW Manual", "MeasTime[ms]", "ATT.MODE",
        "BaseBand_Lev[V]", "BaseBand_DC[V]", "TrigCounter", "I/Q_Position",
        "I/Q_Samples"
    ],
    "ILS": [
        "RX", "STIOCPMV", "Index", "Date", "Time", "FREQ[MHz]", "SINGLE[kHz]", "CRS_UF[kHz]",
        "CLR_LF[kHz]", "LEVEL[dBm]", "AM-MOD./90Hz[%]", "AM-MOD./150Hz[%]", "FREQ_90[Hz]",
        "FREQ_150[Hz]", "DDM(90-150)[1]", "SDM[%]", "PHI-90/150[°]", "ID-MOD.[%]", "ID-F.[Hz]",
        "ID-CODE", "ID-Per.[s]", "Last_ID[s]", "DotLen[ms]", "DashLen[ms]", "DotDashGap[ms]",
        "Lettergap[ms]", "LEV_CLR_LF[dBm]", "LEV_CRS_UF[dBm]", "AM-MOD_CLR_LF/90Hz[%]",
        "AM-MOD_CLR_LF/150Hz[%]", "FREQ_90_CLR_LF[Hz]", "FREQ_150_CLR_LF[Hz]", "DDM_CLR_LF(90-150)[1]",
        "SDM_CLR_LF[%]", "PHI-90/150_CLR_LF[°]", "AM-MOD_CRS_UF/90Hz[%]", "AM-MOD_CRS_UF/150Hz[%]",
        "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]", "DDM_CRS_UF(90-150)[1]", "SDM_CRS_UF[%]",
        "PHI-90/150_CRS_UF[°]", "PHI-90/90[°]", "PHI-150/150[°]", "ResFM90[Hz]", "ResFM150[Hz]",
        "K2/90Hz[%]", "K2/150Hz[%]", "K3/90Hz[%]", "K3/150Hz[%]", "K4/90Hz[%]", "K4/150Hz[%]",
        "THD/90Hz[%]", "THD/150Hz[%]", "AM240[%]", "GPS_lat.", "GPS_long.", "GPS_alt[m]",
        "GPS_speed[km/h]", "GPS_date", "GPS_time", "GPS_Sat", "GPS_Status", "GPS_Fix", "GPS_HDOP",
        "GPS_VDOP", "GPS_Und.[m]", "Temp[°C]", "MeasTime[ms]", "MeasMode", "LOC_GP", "ATT.MODE",
        "DemodOffset_1F[kHz]", "DemodOffset_CRS[kHz]", "DemodOffset_CLR[kHz]", "Autotune_1F",
        "Autotune_CRS", "Autotune_CLR", "IFBW_Man_WIDE", "IFBW_Man_UCLC", "BaseBand_Lev[V]",
        "BaseBand_DC[V]", "TrigCounter", "I/Q_Position", "I/Q_Samples"
    ],
    "GP": [
        "RX", "STIOCPMV", "Index", "Date", "Time", "FREQ[MHz]", "SINGLE[kHz]", "CRS_UF[kHz]",
        "CLR_LF[kHz]", "LEVEL[dBm]", "AM-MOD./90Hz[%]", "AM-MOD./150Hz[%]", "FREQ_90[Hz]",
        "FREQ_150[Hz]", "DDM(90-150)[1]", "SDM[%]", "PHI-90/150[°]", "ID-MOD.[%]", "ID-F.[Hz]",
        "ID-CODE", "ID-Per.[s]", "Last_ID[s]", "DotLen[ms]", "DashLen[ms]", "DotDashGap[ms]",
        "Lettergap[ms]", "LEV_CLR_LF[dBm]", "LEV_CRS_UF[dBm]", "AM-MOD_CLR_LF/90Hz[%]",
        "AM-MOD_CLR_LF/150Hz[%]", "FREQ_90_CLR_LF[Hz]", "FREQ_150_CLR_LF[Hz]", "DDM_CLR_LF(90-150)[1]",
        "SDM_CLR_LF[%]", "PHI-90/150_CLR_LF[°]", "AM-MOD_CRS_UF/90Hz[%]", "AM-MOD_CRS_UF/150Hz[%]",
        "FREQ_90_CRS_UF[Hz]", "FREQ_150_CRS_UF[Hz]", "DDM_CRS_UF(90-150)[1]", "SDM_CRS_UF[%]",
        "PHI-90/150_CRS_UF[°]", "PHI-90/90[°]", "PHI-150/150[°]", "ResFM90[Hz]", "ResFM150[Hz]",
        "K2/90Hz[%]", "K2/150Hz[%]", "K3/90Hz[%]", "K3/150Hz[%]", "K4/90Hz[%]", "K4/150Hz[%]",
        "THD/90Hz[%]", "THD/150Hz[%]", "AM240[%]", "GPS_lat.", "GPS_long.", "GPS_alt[m]",
        "GPS_speed[km/h]", "GPS_date", "GPS_time", "GPS_Sat", "GPS_Status", "GPS_Fix", "GPS_HDOP",
        "GPS_VDOP", "GPS_Und.[m]", "Temp[°C]", "MeasTime[ms]", "MeasMode", "LOC_GP", "ATT.MODE",
        "DemodOffset_1F[kHz]", "DemodOffset_CRS[kHz]", "DemodOffset_CLR[kHz]", "Autotune_1F",
        "Autotune_CRS", "Autotune_CLR", "IFBW_Man_WIDE", "IFBW_Man_UCLC", "BaseBand_Lev[V]",
        "BaseBand_DC[V]", "TrigCounter", "I/Q_Position", "I/Q_Samples"
    ]
}

stop_event = threading.Event()
ser = None
recording = False
csv_writer = None
csv_file = None
current_mode = None

class Communicate(QObject):
    data_signal = pyqtSignal(str)

comm = Communicate()

def connect_to_raspi_via_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Connected to Raspberry Pi via serial port")
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

def login_to_raspberry_pi():
    global ser
    try:
        if ser is None or not ser.is_open:
            return False
        ser.write(b"beta\n")
        time.sleep(1)
        output = ser.read_until(b"Password: ").decode('utf-8')
        print(output.strip())
        ser.write(b"beta123\n")  # Change 'password' to the actual password
        time.sleep(1)
        
        output = ser.read_until(b"$ ").decode('utf-8')
        print(output.strip())
        
        return True
    except Exception as e:
        print(f"Login error: {e}")
        return False

def start_recording():
    global recording, csv_writer, csv_file, current_mode
    if current_mode is None:
        print("Mode is not set. Cannot start recording.")
        return
    recording = True
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{current_mode}_{CSV_FILENAME_TEMPLATE.format(current_mode)}"
    csv_file = open(filename, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(CSV_HEADER[current_mode])
    print(f"Recording started. Saving to {filename}")

def stop_recording():
    global recording, csv_writer, csv_file
    recording = False
    if csv_file:
        csv_file.close()
    csv_writer = None
    csv_file = None
    print("Recording stopped.")

def read_data_from_serial():
    global ser, csv_writer
    try:
        if ser is None or not ser.is_open:
            return
        while not stop_event.is_set():
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if recording and csv_writer:
                    # Pisahkan data berdasarkan delimiter (misalnya koma)
                    # Gantilah delimiter sesuai dengan format data Anda
                    data_list = data.split(',')
                    csv_writer.writerow(data_list)
                print(data)
                comm.data_signal.emit(data)
    except serial.SerialException as e:
        print(f"Error: {e}")


def execute_script_on_raspberry_pi():
    global ser
    try:
        if ser is None or not ser.is_open:
            return
        ser.write(f"sudo python3 {MAIN_SCRIPT}\n".encode('utf-8'))
        time.sleep(1)
    except serial.SerialException as e:
        print(f"Error: {e}")

def signal_handler(sig, frame):
    stop_event.set()
    stop_recording()
    if ser and ser.is_open:
        ser.close()
    print("\nProgram terminated")
    sys.exit(0)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Controller)')
        
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton('Connect', self)
        self.connect_btn.clicked.connect(self.connect_to_raspi)
        top_layout.addWidget(self.connect_btn)
        
        self.login_btn = QPushButton('Login', self)
        self.login_btn.clicked.connect(self.login_to_raspi)
        top_layout.addWidget(self.login_btn)
        
        self.execute_btn = QPushButton('Execute', self)
        self.execute_btn.clicked.connect(self.execute_script)
        top_layout.addWidget(self.execute_btn)
        
        main_layout.addLayout(top_layout)
        
        mid_layout = QHBoxLayout()

        self.start_recording_btn = QPushButton('Start Recording', self)
        self.start_recording_btn.clicked.connect(self.start_recording)
        mid_layout.addWidget(self.start_recording_btn)
        
        self.stop_recording_btn = QPushButton('Stop Recording', self)
        self.stop_recording_btn.clicked.connect(self.stop_recording)
        mid_layout.addWidget(self.stop_recording_btn)
        
        main_layout.addLayout(mid_layout)

        button_layout = QHBoxLayout()

        self.vor_btn = QPushButton('VOR', self)
        self.vor_btn.clicked.connect(lambda: self.set_mode('VOR'))
        button_layout.addWidget(self.vor_btn)
        
        self.ils_btn = QPushButton('ILS', self)
        self.ils_btn.clicked.connect(lambda: self.set_mode('ILS'))
        button_layout.addWidget(self.ils_btn)
        
        self.gp_btn = QPushButton('GP', self)
        self.gp_btn.clicked.connect(lambda: self.set_mode('GP'))
        button_layout.addWidget(self.gp_btn)

        self.stop_btn = QPushButton('STOP', self)
        self.stop_btn.clicked.connect(lambda: self.send_command('STOP'))
        button_layout.addWidget(self.stop_btn)
        
        self.quit_btn = QPushButton('QUIT', self)
        self.quit_btn.clicked.connect(self.send_ctrl_c)
        button_layout.addWidget(self.quit_btn)
        
        main_layout.addLayout(button_layout)
        
        self.data_display = QTextEdit(self)
        main_layout.addWidget(self.data_display)
        
        self.open_csv_btn = QPushButton('Open CSV File', self)
        self.open_csv_btn.clicked.connect(self.open_csv_file)
        main_layout.addWidget(self.open_csv_btn)
        
        self.csv_table = QTableWidget(self)
        main_layout.addWidget(self.csv_table)
        
        self.setLayout(main_layout)
        
        comm.data_signal.connect(self.update_data_display)
    
    def connect_to_raspi(self):
        connect_to_raspi_via_serial()
    
    def login_to_raspi(self):
        if login_to_raspberry_pi():
            self.data_display.append("Login successful")
        else:
            self.data_display.append("Login failed")
    
    def execute_script(self):
        execute_script_on_raspberry_pi()
    
    def start_recording(self):
        global recording, csv_writer, csv_file, current_mode
        if current_mode is None:
            self.data_display.append("Mode is not set. Cannot start recording.")
            return
        
        if current_mode not in CSV_HEADER:
            self.data_display.append(f"Invalid mode: {current_mode}")
            return

        recording = True
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Menentukan nama file
        file_name = f"{timestamp}_{current_mode}_stream_data.csv"
        
        try:
            # Membuka file CSV untuk penulisan
            csv_file = open(file_name, 'w', newline='')
            csv_writer = csv.writer(csv_file)
            
            # Menulis header sesuai mode
            header = CSV_HEADER[current_mode]
            if header:
                csv_writer.writerow(header)
                self.data_display.append(f"Recording started in {current_mode} mode to {file_name}")
            else:
                self.data_display.append(f"Header for mode {current_mode} is empty.")
                recording = False
                csv_file.close()
        except Exception as e:
            self.data_display.append(f"Error starting recording: {e}")
            recording = False


    def stop_recording(self):
        stop_recording()
        self.data_display.append("Stopped recording")
    
    def send_command(self, command):
        global ser
        try:
            if ser and ser.is_open:
                ser.write(f"{command}\n".encode('utf-8'))
                self.data_display.append(f"Sent command: {command}")
        except serial.SerialException as e:
            print(f"Error sending command: {e}")
    
    def set_mode(self, mode):
        global current_mode
        current_mode = mode
        self.data_display.append(f"Mode set to: {mode}")
        
        # Tentukan perintah sesuai dengan mode yang dipilih
        if mode == 'VOR':
            command = 'VOR\n'
        elif mode == 'ILS':
            command = 'ILS\n'
        elif mode == 'GP':
            command = 'GP\n'
        else:
            self.data_display.append(f"Unknown mode: {mode}")
            return
        
        # Kirimkan perintah ke perangkat serial
        self.send_command(command)

    def send_ctrl_c(self):
        global ser
        try:
            if ser and ser.is_open:
                ser.write(b'\x03')
                self.data_display.append("Sent Ctrl+C")
        except serial.SerialException as e:
            print(f"Error sending Ctrl+C: {e}")

    def open_csv_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            self.load_csv_file(file_name)
    
    def load_csv_file(self, file_name):
        with open(file_name, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            header = next(csvreader)
            self.csv_table.setRowCount(0)
            self.csv_table.setColumnCount(len(header))
            self.csv_table.setHorizontalHeaderLabels(header)
            for row_data in csvreader:
                row = self.csv_table.rowCount()
                self.csv_table.insertRow(row)
                for column, item in enumerate(row_data):
                    cell = QTableWidgetItem(item)
                    self.csv_table.setItem(row, column, cell)
            self.csv_table.resizeColumnsToContents()
            self.csv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    @pyqtSlot(str)
    def update_data_display(self, data):
        self.data_display.append(data)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    connect_to_raspi_via_serial()
    
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    
    read_thread = threading.Thread(target=read_data_from_serial)
    read_thread.start()
    
    try:
        sys.exit(app.exec_())
    finally:
        stop_event.set()  # Menghentikan thread baca
        read_thread.join()  # Menunggu thread baca berhenti
        if ser and ser.is_open:
            ser.close()  # Menutup koneksi serial jika masih terbuka
