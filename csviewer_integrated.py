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
from datetime import datetime

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.upper_bound = None
        self.lower_bound = None
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
        # self.left_layout.addItem(spacer)
        
        # GroupBox for radio buttons
        self.radio_group_box = QGroupBox("Select Mode")
        self.radio_group_box.setStyleSheet(
            "color: white; font-size: 30px; background-color: #002060;"
        )
        self.radio_button_layout = QVBoxLayout()
        self.radio_group_box.setLayout(self.radio_button_layout)
        self.left_layout.addWidget(self.radio_group_box)

        # Set the font size for radio buttons
        self.radio_group_box.setStyleSheet(
            "QGroupBox { color: white; font-size: 30px; font-weight: bold; background-color: #002060; }"
            "QRadioButton { font-size: 18px; color: white; }"
        )

        # Update CSV list and add radio buttons
        self.csv_group = QButtonGroup(self)
        self.update_csv_list()
        
        # GroupBox for checkboxes
        self.checkbox_group_box = QGroupBox("Select Data")
        self.checkbox_group_box.setStyleSheet(
            "color: white; font-size: 25px; font-weight: bold; background-color: #002060;"
        )
        self.checkbox_layout = QFormLayout()
        self.checkbox_group_box.setLayout(self.checkbox_layout)
        self.left_layout.addWidget(self.checkbox_group_box)

        # Checkboxes for column selection
        self.checkboxes = {}

        # Set the font size for checkboxes
        self.checkbox_group_box.setStyleSheet(
            "QGroupBox { color: white; font-size: 25px; font-weight: bold; background-color: #002060; }"
            "QCheckBox { font-size: 17px; color: white; }"
        )

        self.checkbox_group_box.setFixedHeight(200)

        # GroupBox for explanation
        self.explanation_group_box = QGroupBox("Plot Line Explanation")
        self.explanation_group_box.setStyleSheet("background-color: white; color: black; font-size: 20px; font-weight: bold;")
        self.explanation_layout = QVBoxLayout()
        self.explanation_group_box.setLayout(self.explanation_layout)
        self.left_layout.addWidget(self.explanation_group_box)

        explanation_text = (
            '<p style="color: red;">-- : Upper and Lower<br>'
            '<p style="color: blue;">Blue : Normal Range<br>'
            '<p style="color: red;">Red : Above Upper<br>'
            '<p style="color: orange;">Orange : Below Lower'
        )
        explanation_label = QLabel(explanation_text)
        explanation_label.setStyleSheet("font-size: 13px;")
        self.explanation_layout.addWidget(explanation_label)


        # Add a spacer between explanation and Save PDF button
        self.left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

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
        
        # Timer for updating CSV list
        self.csv_update_timer = QTimer()
        self.csv_update_timer.timeout.connect(self.update_csv_list)
        self.csv_update_timer.start(2000)

        # Data attributes
        self.file_path = ''
        self.mode = ''
        self.data = pd.DataFrame()
        self.gps_lat = None
        self.gps_long = None

        self.update_csv_list()
        
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

    def get_latest_csv_files(self):
        # Retrieve all CSV files in the directory
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        
        # Dictionary to store the latest files for each keyword
        latest_files = {'VOR': None, 'ILS': None, 'GP': None}
        
        for csv_file in csv_files:
            if 'VOR' in csv_file:
                if latest_files['VOR'] is None or os.path.getmtime(csv_file) > os.path.getmtime(latest_files['VOR']):
                    latest_files['VOR'] = csv_file
            elif 'ILS' in csv_file:
                if latest_files['ILS'] is None or os.path.getmtime(csv_file) > os.path.getmtime(latest_files['ILS']):
                    latest_files['ILS'] = csv_file
            elif 'GP' in csv_file:
                if latest_files['GP'] is None or os.path.getmtime(csv_file) > os.path.getmtime(latest_files['GP']):
                    latest_files['GP'] = csv_file
        
        # Filter out None values
        latest_files = {k: v for k, v in latest_files.items() if v is not None}
        
        return latest_files.values()
    
    def update_csv_list(self):
        # Clear existing radio buttons
        while self.radio_button_layout.count():
            item = self.radio_button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Get the latest CSV files
        csv_files = self.get_latest_csv_files()

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
                num_plots = len(selected_columns)
                if selected_columns:
                    for i, column in enumerate(selected_columns):
                        if column in self.data.columns:
                            ax = self.figure.add_subplot(num_plots, 1, i + 1)
                            plot_height = 0.8 / num_plots
                            plot_bottom = 0.1 + (num_plots - i - 1) * plot_height
                            ax.set_position([0.1, plot_bottom, 0.8, plot_height])

                            column_data = self.data[column]

                            # Ensure data and boundaries are in range
                            data_min, data_max = column_data.min(), column_data.max()
                            upper_bound = self.upper_bound if self.upper_bound is not None else data_max
                            lower_bound = self.lower_bound if self.lower_bound is not None else data_min

                            # Plot boundaries
                            ax.axhline(upper_bound, color='red', linestyle='--', linewidth=1, label='Upper Bound')
                            ax.axhline(lower_bound, color='red', linestyle='--', linewidth=1, label='Lower Bound')

                            if column_data.empty:
                                continue

                            # Define the colors
                            color_normal = 'blue'
                            color_above = 'red'
                            color_below = 'orange'

                            # Plot data
                            above_bound = column_data > upper_bound
                            below_bound = column_data < lower_bound

                            ax.plot(column_data.index[~above_bound & ~below_bound], column_data[~above_bound & ~below_bound], color=color_normal, label=column)
                            ax.plot(column_data.index[above_bound], column_data[above_bound], color=color_above, label=f'{column} (Above Bound)')
                            ax.plot(column_data.index[below_bound], column_data[below_bound], color=color_below, label=f'{column} (Below Bound)')

                            ax.grid(True)
                            ax.set_xlabel('Time', fontsize=9)
                            ax.set_ylabel(column, fontsize=9)
                            ax.tick_params(axis='both', which='major', labelsize=8)

                            # Adjust y-limits to add margin
                            y_min, y_max = column_data.min(), column_data.max()
                            y_margin = (y_max - y_min) * 1.0  # Margin for visibility
                            ax.set_ylim(min(y_min, lower_bound) - y_margin, max(y_max, upper_bound) + y_margin)

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
                a4_width, a4_height = 8.27, 11.69  # A4 dimensions in inches
                
                selected_columns = [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
                num_plots = len(selected_columns)
                
                fig = plt.figure(figsize=(a4_width, a4_height))
                fig.subplots_adjust(top=0.85, bottom=0.1, left=0.1, right=0.9, hspace=0.4)

                logo_ax = fig.add_axes([0.1, 0.9, 0.8, 0.07])
                logo_ax.axis('off')
                image_path = 'rsxbeta.png'
                if os.path.exists(image_path):
                    img = mpimg.imread(image_path)
                    logo_ax.imshow(img, aspect='auto')

                header_ax = fig.add_axes([0.1, 0.80, 0.8, 0.1])
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

                plot_height = 0.4 if num_plots == 1 else 0.2 if num_plots == 2 else 0.15 if num_plots == 3 else 0.1
                plot_spacing = 0.04
                start_height = 0.60 if num_plots == 3 else 0.55 if num_plots == 2 else 0.30 if num_plots == 1 else 0.70

                for i, column in enumerate(selected_columns):
                    if column in self.data.columns:
                        plot_bottom = start_height - (i * (plot_height + plot_spacing))
                        ax = fig.add_axes([0.1, plot_bottom, 0.8, plot_height])
                        column_data = self.data[column].dropna()
                        
                        # Ensure data and boundaries are in range
                        data_min, data_max = column_data.min(), column_data.max()
                        upper_bound = self.upper_bound if self.upper_bound is not None else data_max
                        lower_bound = self.lower_bound if self.lower_bound is not None else data_min

                        # Plot boundaries
                        ax.axhline(upper_bound, color='red', linestyle='--', linewidth=1, label='Upper Bound')
                        ax.axhline(lower_bound, color='red', linestyle='--', linewidth=1, label='Lower Bound')

                        if column_data.empty:
                            continue

                        # Define the colors
                        color_normal = 'blue'
                        color_above = 'red'
                        color_below = 'orange'

                        # Plot data
                        above_bound = column_data > upper_bound
                        below_bound = column_data < lower_bound

                        ax.plot(column_data.index[~above_bound & ~below_bound], column_data[~above_bound & ~below_bound], color=color_normal, label=column)
                        ax.plot(column_data.index[above_bound], column_data[above_bound], color=color_above, label=f'{column} (Above Bound)')
                        ax.plot(column_data.index[below_bound], column_data[below_bound], color=color_below, label=f'{column} (Below Bound)')

                        ax.grid(True)
                        ax.set_xlabel('Time', fontsize=9)
                        ax.set_ylabel(column, fontsize=7)
                        ax.tick_params(axis='both', which='major', labelsize=8)

                        # Adjust y-limits to add margin
                        y_min, y_max = column_data.min(), column_data.max()
                        y_margin = (y_max - y_min) * 0.6
                        ax.set_ylim(min(y_min, lower_bound) - y_margin, max(y_max, upper_bound) + y_margin)

                        last_value = column_data.iloc[-1]
                        ax.text(1.01, 0.5, f'{last_value:.2f}', transform=ax.transAxes, va='center', fontsize=10, color='black')

                # Add a color legend in the bottom right corner of the page with color-specific text
                fig.text(0.95, 0.08, "-- : Upper and Lower", fontsize=10, ha='right', va='bottom', color='red')
                fig.text(0.95, 0.06, "Blue : Normal Range", fontsize=10, ha='right', va='bottom', color='blue')
                fig.text(0.95, 0.04, "Red : Above Upper", fontsize=10, ha='right', va='bottom', color='red')
                fig.text(0.95, 0.02, "Orange : Below Lower", fontsize=10, ha='right', va='bottom', color='orange')

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