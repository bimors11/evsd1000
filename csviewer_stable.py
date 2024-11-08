import sys
import os
import logging
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QRadioButton, QButtonGroup, QCheckBox, QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QLabel, QGroupBox, QSlider
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

LOCALIZER_CSV = "localizer.csv"
GLIDEPATH_CSV = "glidepath.csv"
VOR_CSV = "vor.csv"

DELAY = 0.5
SCRIPT_PATH = "loop.py"

LOCALIZER_COLUMNS = ['AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'LEVEL[dBm]']
GLIDEPATH_COLUMNS = ['AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'LEVEL[dBm]', 'GPS_alt[m]']
VOR_COLUMNS = ['LEVEL[dBm]', 'PHI-90/150[°]', 'PHI-90/90[°]', 'PHI-150/150[°]']

class CSVViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("CSV Viewer App")
        self.setGeometry(500, 170, 1000, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.left_panel.setStyleSheet("background-color: #002060; color: white;")
        self.main_layout.addWidget(self.left_panel)
        self.left_panel.setMaximumWidth(400)  # Atur nilai sesuai kebutuhan

        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        self.right_panel.setStyleSheet("background-color: #002060;")
        self.main_layout.addWidget(self.right_panel)
        self.right_panel.setMaximumWidth(9000)  # Atur nilai sesuai kebutuhan

        # Load and display logos with adjusted size
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.addLayout(logo_layout)
        image_paths = ["beta_no_icc.png", "rs_no_icc.png"]
        for image_path in image_paths:
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(300, int(pixmap.height() * 300 / pixmap.width()), Qt.KeepAspectRatio)
            logo_label = QLabel(self)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignTop)
            logo_layout.addWidget(logo_label)

        # Create group box for category selection
        category_group_box = QGroupBox("Choose Category:")
        category_group_box.setStyleSheet("color: white; font-size: 30px; font-weight: bold;")
        category_layout = QVBoxLayout()
        category_group_box.setLayout(category_layout)
        self.left_layout.addWidget(category_group_box)

        self.category_radio_group = QButtonGroup()
        self.category_radio_buttons = []
        for i, category in enumerate(["Localizer", "Glidepath", "VOR"]):
            radio_button = QRadioButton(category)
            radio_button.setStyleSheet("color: white; font-size: 20px;")
            self.category_radio_group.addButton(radio_button)
            category_layout.addWidget(radio_button, alignment=Qt.AlignLeft | Qt.AlignTop)
            self.category_radio_buttons.append(radio_button)

        self.category_radio_buttons[0].setChecked(True)

        # Create group box for data selection
        data_group_box = QGroupBox("Choose Data to Plot:")
        data_group_box.setStyleSheet("color: white; font-size: 27px; font-weight: bold;")
        data_layout = QVBoxLayout()
        data_group_box.setLayout(data_layout)
        self.left_layout.addWidget(data_group_box)

        self.checkbox_panel = QWidget()
        self.checkbox_layout = QVBoxLayout()
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout.setSpacing(5)
        self.checkbox_panel.setLayout(self.checkbox_layout)
        data_layout.addWidget(self.checkbox_panel)

        self.checkboxes = []

        self.figure, self.ax = plt.subplots()
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

        self.start_button = QPushButton("Start Stream")
        self.start_button.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        self.start_button.clicked.connect(self.start_stream)
        self.left_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Stream")
        self.stop_button.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        self.stop_button.clicked.connect(self.stop_stream)
        self.left_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("Save PDF")
        self.save_button.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        self.save_button.clicked.connect(self.save_to_pdf)
        self.left_layout.addWidget(self.save_button)

        self.data = None
        self.file_path = None
        self.selected_columns = []
        self.process = None
        self.animation = None

        self.update_column_list()

        for radio_button in self.category_radio_buttons:
            radio_button.toggled.connect(self.update_column_list)

        self.setStyleSheet("background-color: #002060; color: white;")

    def update_column_list(self):
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        self.checkboxes.clear()

        category = self.category_radio_group.checkedButton().text()
        columns = []

        if category == "Localizer":
            self.file_path = LOCALIZER_CSV
            columns = LOCALIZER_COLUMNS
        elif category == "Glidepath":
            self.file_path = GLIDEPATH_CSV
            columns = GLIDEPATH_COLUMNS
        elif category == "VOR":
            self.file_path = VOR_CSV
            columns = VOR_COLUMNS

        for column in columns:
            checkbox = QCheckBox(column)
            checkbox.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        self.selected_columns.clear()
        self.update_plot()

    def read_csv_file(self, file_path):
        return pd.read_csv(file_path, encoding='latin1')

    def plot_line(self, data):
        self.figure.clear()
        num_plots = len(self.selected_columns)
        
        self.axs = self.figure.subplots(num_plots, 1, sharex=True)
        
        if num_plots == 1:
            self.axs = [self.axs]
        
        for ax, column in zip(self.axs, self.selected_columns):
            ax.plot(data.index, data[column], label=column)
            ax.set_ylabel(column)
            ax.legend()
            ax.grid(True)  # Enable grid

            last_value = data[column].iloc[-1]
            ax.text(1.01, 0.5, f'{last_value:.2f}', transform=ax.transAxes, va='center', fontsize=12, color='black')
            
            # Adjust y-limits to add margin
            y_min = data[column].min()
            y_max = data[column].max()
            y_margin = (y_max - y_min) * 1.5  # 10% margin
            ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
        self.figure.tight_layout()
        self.canvas.draw()


    def update_plot(self, *args):
        self.selected_columns = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        
        if self.file_path:
            try:
                self.data = self.read_csv_file(self.file_path)
                if not self.data.empty and all(col in self.data.columns for col in self.selected_columns):
                    max_data = len(self.data)
                    
                    # Adjust data range
                    total_display_count = int(self.slider_total.value() / 100 * max_data)
                    range_start = int(self.slider_range.value() / 100 * max_data)
                    range_end = min(range_start + total_display_count, max_data)

                    # Plot the data based on the selected range
                    if range_start < range_end:
                        self.plot_line(self.data[self.selected_columns].iloc[range_start:range_end])
                    else:
                        self.figure.clear()
                        self.canvas.draw()
                else:
                    self.figure.clear()
                    self.canvas.draw()
            except Exception as e:
                print(f"Error reading data: {e}")
                self.figure.clear()
                self.canvas.draw()
        else:
            self.figure.clear()
            self.canvas.draw()

    def start_stream(self):
        if self.process is not None:
            self.show_message("WARNING!", "Stream already started")
            return
        
        self.process = subprocess.Popen(['python', SCRIPT_PATH])
        
        if self.animation is None:
            self.animation = FuncAnimation(self.figure, self.update_plot, interval=DELAY * 500)
            self.canvas.draw()
        
        self.show_message("INFO!", "Streaming started")

    def stop_stream(self):
        if self.process is None:
            self.show_message("WARNING!", "Stream already stopped")
            return
        
        self.process.terminate()
        self.process = None
        
        if self.animation is not None:
            self.animation.event_source.stop()
            self.animation = None
        
        self.show_message("INFO!", "Streaming stopped")

    def save_to_pdf(self):
        file_dialog = QFileDialog(self, "Save PDF", "", "PDF files (*.pdf)|*.pdf")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.figure.savefig(file_path, format='pdf')
            self.show_message("Info", f"PDF saved successfully to {file_path}")

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("QMessageBox {background-color: white;} QPushButton {background-color: #002060; color: white;}")
        msg_box.exec_()

    def closeEvent(self, event):
        if self.process is not None:
            self.process.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVViewerApp()
    window.showMaximized()
    sys.exit(app.exec_())
