import os
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QSizePolicy, QSpacerItem, QHBoxLayout

def get_latest_csv_files():
    try:
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        print(f"CSV files found: {csv_files}")

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

        latest_files = {k: v for k, v in latest_files.items() if v is not None}
        print(f"Filtered latest files: {latest_files}")

        return latest_files.values()
    except Exception as e:
        print(f"Error in get_latest_csv_files: {e}")
        return []

def detect_mode(self):
    if 'VOR' in self.file_path:
        self.mode = 'VOR'
    elif 'ILS' in self.file_path:
        self.mode = 'ILS'
    elif 'GP' in self.file_path:
        self.mode = 'GP'
    else:
        self.mode = ''
    self.update_checkboxes_based_on_mode()

def get_user_inputs():
    dialog = QDialog()
    dialog.setWindowTitle('Enter Details')
    dialog.setStyleSheet("background-color: white; color: black;")
    
    dialog.setFixedSize(400, 200)

    main_layout = QVBoxLayout()

    form_layout = QFormLayout()
    form_layout.setSpacing(20)

    bandara = QLineEdit()
    alat = QLineEdit()
    pengujian = QLineEdit()

    form_layout.addRow('Airport:', bandara)
    form_layout.addRow('Transmitter:', alat)
    form_layout.addRow('Attempts:', pengujian)

    main_layout.addLayout(form_layout)

    main_layout.addStretch()

    buttons_layout = QHBoxLayout()
    ok_button = QPushButton('OK')

    buttons_layout.addWidget(ok_button)

    main_layout.addLayout(buttons_layout)

    dialog.setLayout(main_layout)

    def validate_fields():
        ok_button.setEnabled(bandara.text().strip() != '' and 
                             alat.text().strip() != '' and 
                             pengujian.text().strip() != '')
    
    def on_text_changed():
        validate_fields()
    
    bandara.textChanged.connect(on_text_changed)
    alat.textChanged.connect(on_text_changed)
    pengujian.textChanged.connect(on_text_changed)

    def on_ok_clicked():
        if bandara.text().strip() and alat.text().strip() and pengujian.text().strip():
            dialog.accept()
    
    ok_button.clicked.connect(on_ok_clicked)

    validate_fields()
    
    result = dialog.exec()
    
    if result == QDialog.Accepted:
        return bandara.text(), alat.text(), pengujian.text()
    else:
        return None