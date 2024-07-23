import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QPushButton, QCheckBox, QFormLayout, QGroupBox, QLabel, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import subprocess
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import image as mpimg

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
        self.left_panel.setFixedWidth(250)
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
        self.logo_layout.setSpacing(2)
        self.left_layout.addLayout(self.logo_layout)
        self.addLogos()
        
        # Add a spacer to keep logos at the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.left_layout.addItem(spacer)
        
        # GroupBox for radio buttons
        self.radio_group_box = QGroupBox("Select Mode")
        self.radio_group_box.setStyleSheet("color: white; font-size: 23px; font-weight: bold;")
        self.radio_button_layout = QVBoxLayout()
        self.radio_group_box.setLayout(self.radio_button_layout)
        self.left_layout.addWidget(self.radio_group_box)
        
        # CSV file selection via radio buttons
        self.csv_group = QButtonGroup(self)
        self.update_csv_list()
        
        # Add a spacer between radio buttons and Save PDF button
        self.left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # GroupBox for checkboxes
        self.checkbox_group_box = QGroupBox("Select Data")
        self.checkbox_group_box.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.checkbox_layout = QFormLayout()
        self.checkbox_group_box.setLayout(self.checkbox_layout)
        self.left_layout.addWidget(self.checkbox_group_box)
        
        # Checkboxes for column selection
        self.checkboxes = {}

        self.checkbox_group_box.setFixedHeight(200)

        # Add a spacer between radio buttons and Save PDF button
        self.left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Plot area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)

        # Add slider for adjusting total data displayed
        total_slider_layout = QHBoxLayout()
        total_slider_label = QLabel("Total Data Displayed:")
        total_slider_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        total_slider_layout.addWidget(total_slider_label)
        self.slider_total = QSlider(Qt.Horizontal)
        self.slider_total.setRange(1, 100)
        self.slider_total.setValue(100)
        self.slider_total.setTickPosition(QSlider.TicksBelow)
        self.slider_total.setTickInterval(10)
        self.slider_total.valueChanged.connect(self.update_plot)
        total_slider_layout.addWidget(self.slider_total)
        self.right_layout.addLayout(total_slider_layout)

        # Add slider for adjusting data range displayed
        range_slider_layout = QHBoxLayout()
        range_slider_label = QLabel("Data Range:")
        range_slider_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        range_slider_layout.addWidget(range_slider_label)
        self.slider_range = QSlider(Qt.Horizontal)
        self.slider_range.setRange(0, 100)
        self.slider_range.setValue(0)
        self.slider_range.setTickPosition(QSlider.TicksBelow)
        self.slider_range.setTickInterval(10)
        self.slider_range.valueChanged.connect(self.update_plot)
        range_slider_layout.addWidget(self.slider_range)
        self.right_layout.addLayout(range_slider_layout)
        
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
        
        # Set button styles
        self.set_button_styles()

    def set_button_styles(self):
        button_style = "background-color: white; color: black;"
        self.save_pdf_button.setStyleSheet(button_style)
        self.connect_controller_button.setStyleSheet(button_style)
        
    def addLogos(self):
        image_paths = ["beta_no_icc.png", "rs_no_icc.png"]
        for image_path in image_paths:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(200, int(pixmap.height() * 200 / pixmap.width()), Qt.KeepAspectRatio)
                logo_label = QLabel(self)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                self.logo_layout.addWidget(logo_label)

    def update_csv_list(self):
        # Clear existing radio buttons
        for button in self.csv_group.buttons():
            self.csv_group.removeButton(button)
            button.setParent(None)
        
        # Clear existing radio buttons layout
        for i in range(self.radio_button_layout.count()):
            widget = self.radio_button_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_file in csv_files:
            radio_button = QRadioButton(csv_file)
            radio_button.clicked.connect(self.select_file)
            self.csv_group.addButton(radio_button)
            self.radio_button_layout.addWidget(radio_button)

    def select_file(self):
        self.clear_plot()  # Clear the plot area when selecting a new file
        selected_button = self.sender()
        if selected_button:
            self.file_path = selected_button.text()
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
            encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1']
            for encoding in encodings_to_try:
                try:
                    self.data = pd.read_csv(self.file_path, encoding=encoding)
                    break  # If reading is successful, break out of the loop
                except UnicodeDecodeError:
                    continue  # If a UnicodeDecodeError occurs, try the next encoding
            
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
        if self.file_path:
            encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1']
            for encoding in encodings_to_try:
                try:
                    self.data = pd.read_csv(self.file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if not self.data.empty:
                self.figure.clear()
                selected_columns = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
                if selected_columns:
                    # Determine the range of data to be plotted
                    total_data_points = self.slider_total.value()
                    data_range_start = self.slider_range.value()
                    data_range_end = min(data_range_start + total_data_points, len(self.data))

                    for i, column in enumerate(selected_columns):
                        if column in self.data.columns:
                            ax = self.figure.add_subplot(len(selected_columns), 1, i + 1)
                            
                            # Slice data according to slider values
                            column_data = self.data[column].iloc[data_range_start:data_range_end].dropna()

                            if column_data.empty:
                                continue

                            ax.plot(column_data.index, column_data, label=column)
                            ax.grid(True)
                            ax.legend()
                            ax.set_xlabel('Time', fontsize=9)
                            ax.set_ylabel(column, fontsize=9)
                            ax.tick_params(axis='both', which='major', labelsize=8)

                            y_min, y_max = column_data.min(), column_data.max()
                            y_margin = (y_max - y_min) * 2.5
                            ax.set_ylim(y_min - y_margin, y_max + y_margin)

                            last_value = column_data.iloc[-1]
                            ax.text(1.01, 0.5, f'{last_value:.2f}', transform=ax.transAxes, va='center', fontsize=12, color='black')

                    self.canvas.draw()


    def clear_plot(self):
        self.figure.clear()
        self.canvas.draw()
    
    def save_plot(self):
        if self.file_path and not self.data.empty:
            pdf_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf);;All Files (*)")
            if pdf_path:
                # Ukuran A4 dalam inci
                a4_width, a4_height = 8.27, 11.69  # Lebar dan tinggi dalam inci
                
                # Determine the number of selected columns
                selected_columns = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
                num_plots = len(selected_columns)
                
                # Ukuran figur tetap ke ukuran A4
                fig = plt.figure(figsize=(a4_width, a4_height))
                fig.subplots_adjust(top=0.85, bottom=0.1, left=0.1, right=0.9, hspace=0.4)  # Adjust margins and spacing

                # Add the logo at the top
                logo_ax = fig.add_axes([0.1, 0.9, 0.8, 0.07])  # [left, bottom, width, height] in figure fraction
                logo_ax.axis('off')
                image_path = 'rsxbeta.png'
                if os.path.exists(image_path):
                    img = mpimg.imread(image_path)
                    logo_ax.imshow(img, aspect='auto')

                # Add header information
                header_ax = fig.add_axes([0.1, 0.80, 0.8, 0.05])  # Adjust position and size as needed
                header_ax.axis('off')
                gps_info = f'GPS: Lat {self.gps_lat}, Long {self.gps_long}' if self.gps_lat and self.gps_long else ''
                header_ax.text(0.5, 0.5,
                            f'MODE: {self.mode}\n\n'
                            f'DATE: {pd.Timestamp.now().strftime("%Y-%m-%d")}\n\n'
                            f'TIME: {pd.Timestamp.now().strftime("%H:%M:%S")}\n\n'
                            f'{gps_info}',
                            fontsize=12,
                            ha='center',
                            va='center')

                # Add plots
                plot_height = 0.1  # Set a fixed plot height
                plot_spacing = 0.1  # Fixed spacing between plots
                start_height = 0.6  # Starting height for the first plot

                for i, column in enumerate(selected_columns):
                    if column in self.data.columns:
                        # Calculate the position of each plot
                        plot_bottom = start_height - (i * (plot_height //+ plot_spacing))
                        ax = fig.add_axes([0.1, plot_bottom, 0.8, plot_height])  # Fixed position for each plot
                        column_data = self.data[column].dropna()
                        ax.plot(self.data.index, column_data, label=column)
                        ax.grid(True)
                        ax.legend()
                        ax.set_xlabel('Time', fontsize=9)
                        ax.set_ylabel(column, fontsize=9)
                        ax.tick_params(axis='both', which='major', labelsize=8)
                        
                        # Adjust y-limits to add margin
                        y_min, y_max = column_data.min(), column_data.max()
                        y_margin = (y_max - y_min) * 0.1
                        ax.set_ylim(y_min - y_margin, y_max + y_margin)

                        last_value = column_data.iloc[-1]
                        ax.text(1.01, 0.5, f'{last_value:.2f}', transform=ax.transAxes, va='center', fontsize=12, color='black')

                # Save the figure to the PDF
                with PdfPages(pdf_path) as pdf:
                    pdf.savefig(fig)
                    plt.close(fig)

    def connect_controller(self):
        result = subprocess.run(['python', 'testingui.py'], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataPlotter()
    window.showMaximized()
    sys.exit(app.exec_())