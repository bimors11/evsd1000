import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QCheckBox, QFormLayout, QLabel, QComboBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import subprocess
import matplotlib.image as mpimg
import numpy as np

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Data Plotter')
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #002060;")
        
        # Central widget and layouts
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Left panel for controls
        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: #002060; color: white;")
        self.left_panel.setFixedWidth(200)
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.main_layout.addWidget(self.left_panel)
        
        # Right panel for plots
        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("background-color: #002060;")
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        self.main_layout.addWidget(self.right_panel)
        
        # Setup for logos
        self.logo_layout = QVBoxLayout()
        self.logo_layout.setContentsMargins(0, 0, 0, 0)
        self.logo_layout.setSpacing(5)
        self.left_layout.addLayout(self.logo_layout)
        self.addLogos()
        
        # CSV file selection
        self.file_button = QPushButton('Select CSV File')
        self.file_button.clicked.connect(self.select_file)
        self.left_layout.addWidget(self.file_button)
        
        # Mode selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['Select Mode', 'VOR', 'ILS', 'GP'])
        self.mode_combo.currentIndexChanged.connect(self.update_mode)
        self.left_layout.addWidget(self.mode_combo)
        
        # Checkboxes for column selection
        self.checkboxes = {}
        self.checkbox_layout = QFormLayout()
        self.left_layout.addLayout(self.checkbox_layout)
        
        # Plot area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)
        
        # Buttons for saving PDF and connecting controller
        self.save_pdf_button = QPushButton('Save PDF')
        self.save_pdf_button.clicked.connect(self.save_plot)
        self.left_layout.addWidget(self.save_pdf_button)
        
        self.connect_controller_button = QPushButton('Connect Controller')
        self.connect_controller_button.clicked.connect(self.connect_controller)
        self.left_layout.addWidget(self.connect_controller_button)
        
        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)
        
        # Data attributes
        self.file_path = ''
        self.mode = ''
        self.data = pd.DataFrame()
        self.gps_lat = None
        self.gps_long = None
        
    def addLogos(self):
        image_paths = ["beta_no_icc.png", "rs_no_icc.png"]
        for image_path in image_paths:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(150, int(pixmap.height() * 150 / pixmap.width()), Qt.KeepAspectRatio)
                logo_label = QLabel(self)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                self.logo_layout.addWidget(logo_label)
    
    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.detect_mode()
            self.update_checkboxes()
    
    def detect_mode(self):
        if 'VOR' in self.file_path:
            self.mode = 'VOR'
        elif 'ILS' in self.file_path:
            self.mode = 'ILS'
        elif 'GP' in self.file_path:
            self.mode = 'GP'
        else:
            self.mode = ''
        self.mode_combo.setCurrentText(self.mode)
    
    def update_mode(self):
        self.mode = self.mode_combo.currentText()
        self.update_checkboxes()
    
    def update_checkboxes(self):
        for checkbox in self.checkboxes.values():
            checkbox.setParent(None)
        self.checkboxes = {}
        columns = self.get_columns()
        for column in columns:
            checkbox = QCheckBox(column)
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes[column] = checkbox

        if self.file_path:
            self.data = pd.read_csv(self.file_path)
            if len(self.data) > 4:
                if 'GPS_lat.' in self.data.columns:
                    self.gps_lat = self.data.iloc[4]['GPS_lat.']
                else:
                    self.gps_lat = None

                if 'GPS_long.' in self.data.columns:
                    self.gps_long = self.data.iloc[4]['GPS_long.']
                else:
                    self.gps_long = None


    def get_columns(self):
        if self.mode == 'VOR':
            return ['LEVEL[dBm]', 'BEARING(from)[°]', 'FM-DEV.[Hz]', 'FM-INDEX']
        elif self.mode == 'ILS':
            return ['LEVEL[dBm]', 'AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'SDM[%]']
        elif self.mode == 'GP':
            return ['LEVEL[dBm]', 'AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'SDM[%]']
        return []
    
    def update_plot(self):
        if self.file_path and not self.data.empty:
            self.figure.clear()
            selected_columns = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
            if selected_columns:
                for i, column in enumerate(selected_columns):
                    if column in self.data.columns:
                        ax = self.figure.add_subplot(len(selected_columns), 1, i + 1)

                        # Convert data to numeric, forcing errors to NaN
                        self.data[column] = pd.to_numeric(self.data[column], errors='coerce')

                        # Drop rows with NaN values to avoid plotting issues
                        column_data = self.data[column].dropna()

                        # Check if there's valid data to plot
                        if column_data.empty:
                            continue

                        ax.plot(column_data.index, column_data, label=column)
                        ax.grid(True)
                        ax.legend()
                        ax.set_xlabel('Time', fontsize=9)
                        ax.set_ylabel(column, fontsize=9)
                        ax.tick_params(axis='both', which='major', labelsize=8)

                        # Set Y-axis ticks with intervals of 1 or 2 units
                        y_min, y_max = column_data.min(), column_data.max()
                        range_span = y_max - y_min
                        interval = 2 if range_span > 10 else 1
                        y_ticks = np.arange(np.floor(y_min), np.ceil(y_max) + interval, interval)
                        ax.set_yticks(y_ticks)

                self.canvas.draw()

    def save_plot(self):
        if self.file_path and not self.data.empty:
            pdf_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf);;All Files (*)")
            if pdf_path:
                from matplotlib.backends.backend_pdf import PdfPages
                from matplotlib import image as mpimg

                # Determine the number of selected columns
                selected_columns = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
                num_plots = len(selected_columns)
                
                # Calculate figure height dynamically based on the number of plots
                fig_height = 3 + num_plots * 1.5  # Base height + height per plot
                fig = plt.figure(figsize=(8.27, fig_height))  # Width is fixed (A4 width), height is dynamic
                fig.subplots_adjust(top=0.85, bottom=0.1, left=0.1, right=0.9, hspace=0.4)  # Adjust margins and spacing

                # Add the logo at the top
                logo_ax = fig.add_axes([0.1, 0.88, 0.8, 0.07])  # [left, bottom, width, height] in figure fraction
                logo_ax.axis('off')
                image_path = 'rsxbeta.png'
                if os.path.exists(image_path):
                    img = mpimg.imread(image_path)
                    logo_ax.imshow(img, aspect='auto')

                # Add header information
                header_ax = fig.add_axes([0.1, 0.80, 0.8, 0.08])  # Adjust position and size as needed
                header_ax.axis('off')
                gps_info = f'GPS: Lat {self.gps_lat}, Long {self.gps_long}' if self.gps_lat and self.gps_long else ''
                header_ax.text(0.5, 0.5,
                            f'MODE: {self.mode}\n'
                            f'DATE: {pd.Timestamp.now().strftime("%Y-%m-%d")}\n'
                            f'TIME: {pd.Timestamp.now().strftime("%H:%M:%S")}\n'
                            f'{gps_info}',
                            fontsize=12,
                            ha='center',
                            va='center')

                # Add plots
                plot_height = 0.65 / num_plots  # Total height reserved for plots is 0.65 of the figure
                for i, column in enumerate(selected_columns):
                    if column in self.data.columns:
                        ax = fig.add_axes([0.1, 0.10 + (num_plots - i - 1) * plot_height, 0.8, plot_height - 0.05])  # Adjust position dynamically
                        ax.plot(self.data.index, self.data[column], label=column)
                        ax.grid(True)
                        ax.legend()
                        ax.set_xlabel('Time', fontsize=9)
                        ax.set_ylabel(column, fontsize=9)
                        ax.tick_params(axis='both', which='major', labelsize=8)

                # Save the figure to the PDF
                with PdfPages(pdf_path) as pdf:
                    pdf.savefig(fig)
                    plt.close(fig)

    def connect_controller(self):
        result = subprocess.run(['python3', 'testingui.py'], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataPlotter()
    window.show()
    sys.exit(app.exec_())
