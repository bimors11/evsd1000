import os
import pandas as pd
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QCheckBox, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGroupBox, QLabel, QSpacerItem, QSizePolicy, QSlider)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QFileSystemWatcher
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import subprocess
from plotting import update_plot, save_plot, get_columns_based_on_mode
from utils import get_latest_csv_files, detect_mode, get_bounds_inputs

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.upper_bound = None
        self.lower_bound = None
        self.bounds = {}
        self.mode = ''
        self.initUI()
        self.initFileWatcher()
        self.existing_csv_files = set(self.get_existing_csv_files())

    def get_existing_csv_files(self):
        return [f for f in os.listdir('.') if f.endswith('.csv')]

    def initUI(self):
        self.setWindowTitle('RS X BETA Data Viewer')
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #002060;")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: #002060; color: white;")
        self.left_panel.setFixedWidth(250)
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.main_layout.addWidget(self.left_panel)
        
        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("background-color: #002060;")
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        self.main_layout.addWidget(self.right_panel)
        
        self.logo_layout = QVBoxLayout()
        self.logo_layout.setContentsMargins(0, 0, 0, 0)
        self.logo_layout.setSpacing(2)
        self.left_layout.addLayout(self.logo_layout)
        self.addLogos()
        
        self.mode_label = QLabel(f"MODE : {self.mode}")
        self.mode_label.setStyleSheet("font-size: 30px; font-weight: bold; color: white;")
        self.left_layout.addWidget(self.mode_label)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.file1_label = QLabel("File 1: None")
        self.file1_label.setStyleSheet("font-size: 14px; color: white;")
        self.left_layout.addWidget(self.file1_label)
        
        self.file2_label = QLabel("File 2: None")
        self.file2_label.setStyleSheet("font-size: 14px; color: white;")
        self.left_layout.addWidget(self.file2_label)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.connect_controller_button = QPushButton('Connect to Controller')
        self.connect_controller_button.clicked.connect(self.connect_controller)
        self.left_layout.addWidget(self.connect_controller_button)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.select_file_button = QPushButton('Select File')
        self.select_file_button.clicked.connect(self.select_csv_file)
        self.left_layout.addWidget(self.select_file_button)

        self.data_selection_group_box = QGroupBox("Select Data to Plot")
        self.data_selection_group_box.setStyleSheet("background-color: white; color: black; font-size: 16px; font-weight: bold;")

        self.data_selection_group_box.setMinimumSize(200, 200)

        self.data_selection_layout = QVBoxLayout()
        self.data_selection_group_box.setLayout(self.data_selection_layout)
        self.left_layout.addWidget(self.data_selection_group_box)

        self.add_data_selection_checkboxes()

        self.compare_file_button = QPushButton('Compare File')
        self.compare_file_button.clicked.connect(self.select_compare_csv_file)
        self.left_layout.addWidget(self.compare_file_button)

        self.remove_compare_button = QPushButton('Remove Compared File')  
        self.remove_compare_button.clicked.connect(self.remove_compare_csv_file)
        self.left_layout.addWidget(self.remove_compare_button)

        self.explanation_group_box = QGroupBox("LEGENDS")
        self.explanation_group_box.setStyleSheet("background-color: white; color: black; font-size: 20px; font-weight: bold;")
        self.explanation_layout = QVBoxLayout()
        self.explanation_group_box.setLayout(self.explanation_layout)
        self.left_layout.addWidget(self.explanation_group_box)

        explanation_text = (
            '<p style="color: red;">-- : Upper and Lower'
            '<p style="color: blue;">BLUE : File 1'
            '<p style="color: green;">GREEN : File 2'
            '<p style="color: red;">Red : Above Upper'
            '<p style="color: orange;">Orange : Below Lower'
        )
        explanation_label = QLabel(explanation_text)
        explanation_label.setStyleSheet("font-size: 18px;")
        self.explanation_layout.addWidget(explanation_label)

        self.left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)

        data_limit_layout = QHBoxLayout()
        data_limit_label = QLabel('Data Limit:')
        data_limit_label.setStyleSheet("color: white;")
        data_limit_layout.addWidget(data_limit_label)
        
        self.data_limit_slider = QSlider(Qt.Horizontal)
        self.data_limit_slider.setMinimum(1)
        self.data_limit_slider.setMaximum(100)
        self.data_limit_slider.setValue(100)
        self.data_limit_slider.setTickPosition(QSlider.TicksBelow)
        self.data_limit_slider.setTickInterval(10)
        self.data_limit_slider.setSingleStep(1)
        self.data_limit_slider.valueChanged.connect(self.update_plot)
        data_limit_layout.addWidget(self.data_limit_slider)
        
        self.right_layout.addLayout(data_limit_layout)
        
        data_range_layout = QHBoxLayout()
        data_range_label = QLabel('Data Range:')
        data_range_label.setStyleSheet("color: white;")
        data_range_layout.addWidget(data_range_label)
        
        self.data_range_slider = QSlider(Qt.Horizontal)
        self.data_range_slider.setMinimum(0)
        self.data_range_slider.setMaximum(100)
        self.data_range_slider.setValue(100)
        self.data_range_slider.setTickPosition(QSlider.TicksBelow)
        self.data_range_slider.setTickInterval(10)
        self.data_range_slider.setSingleStep(1)
        self.data_range_slider.valueChanged.connect(self.update_plot)
        data_range_layout.addWidget(self.data_range_slider)
        
        self.right_layout.addLayout(data_range_layout)
        
        self.save_pdf_button = QPushButton('Save PDF')
        self.save_pdf_button.clicked.connect(self.save_plot)
        self.left_layout.addWidget(self.save_pdf_button)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)

        self.file_path = ''
        self.second_file_path = ''
        self.data = pd.DataFrame()
        self.gps_lat = None
        self.gps_long = None

        self.set_button_styles()

    def set_button_styles(self):
        button_style = "background-color: white; color: black;"
        self.save_pdf_button.setStyleSheet(button_style)
        self.connect_controller_button.setStyleSheet(button_style)
        self.select_file_button.setStyleSheet(button_style)
        self.compare_file_button.setStyleSheet(button_style)
        self.remove_compare_button.setStyleSheet(button_style)

    def addLogos(self):
        image_paths = ["rs_no_icc.png", "beta_no_icc.png"]
        for image_path in image_paths:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(200, int(pixmap.height() * 200 / pixmap.width()), Qt.KeepAspectRatio)
                logo_label = QLabel(self)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                self.logo_layout.addWidget(logo_label)

    def select_last_csv_file(self):
        try:
            latest_files = get_latest_csv_files()
            if latest_files:
                self.file_path = max(latest_files, key=os.path.getmtime)
                detect_mode(self)
                self.update_checkboxes_based_on_mode()
                self.file1_label.setText(f"File 1: {os.path.basename(self.file_path)}")
        except Exception as e:
            print(f"Error in select_last_csv_file: {e}")

    def select_csv_file(self):
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if file_path:
                self.file_path = file_path
                detect_mode(self)
                self.update_checkboxes_based_on_mode()
                self.update_plot()
                self.update_mode_label()
                self.file1_label.setText(f"File 1: {os.path.basename(self.file_path)}")
        except Exception as e:
            print(f"Error in select_csv_file: {e}")

    def update_mode_label(self):
        self.mode_label.setText(f"MODE : {self.mode}")

    def prompt_for_bounds(self):
        columns = get_columns_based_on_mode(self)
        bounds = get_bounds_inputs(self.mode, columns)
        if bounds:
            self.bounds = bounds
            self.update_plot()
        else:
            print("Bounds input was not valid or was canceled.")

    def add_data_selection_checkboxes(self):
        self.data_checkboxes = {}
        self.update_checkboxes_based_on_mode()

    def update_checkboxes_based_on_mode(self):
        for checkbox in list(self.data_checkboxes.values()):
            checkbox.deleteLater()
        self.data_checkboxes.clear()

        columns = get_columns_based_on_mode(self)
        for column in columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            self.data_selection_layout.addWidget(checkbox)
            self.data_checkboxes[column] = checkbox

    def get_selected_columns(self):
        selected_columns = [column for column, checkbox in self.data_checkboxes.items() if checkbox.isChecked()]
        return selected_columns
    
    def select_compare_csv_file(self):
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File to Compare", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if file_path:
                self.second_file_path = file_path
                self.update_plot()
                self.file2_label.setText(f"File 2: {os.path.basename(self.second_file_path)}")
        except Exception as e:
            print(f"Error in select_compare_csv_file: {e}")

    def remove_compare_csv_file(self):
        try:
            self.second_file_path = ''
            self.update_plot()
            self.file2_label.setText("File 2: None")
        except Exception as e:
            print(f"Error in remove_compare_csv_file: {e}")

    def update_plot(self):
        update_plot(self)

    def clear_plot(self):
        self.figure.clear()
        self.canvas.draw()
    
    def save_plot(self):
        save_plot(self)

    def connect_controller(self):
        try:
            subprocess.Popen(['python', 'controller.py'])
        except Exception as e:
            print(f"Error connecting to controller: {e}")

    def initFileWatcher(self):
        self.file_watcher = QFileSystemWatcher([os.getcwd()])
        self.file_watcher.directoryChanged.connect(self.on_directory_changed)

    def on_directory_changed(self, path):
        current_csv_files = set(self.get_existing_csv_files())
        new_files = current_csv_files - self.existing_csv_files
        if new_files:
            self.existing_csv_files = current_csv_files
            self.select_last_csv_file()