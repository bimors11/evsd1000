import pandas as pd
import time

def filter_row(row):
    # Mengabaikan baris yang mengandung kata 'READY' atau 'STOP' di semua kolom
    return not row.astype(str).str.contains('READY.|STOP').any()

# Membaca data dari sumber yang berbeda
data_source1 = pd.read_csv('ILS_stream_data.csv')
data_source2 = pd.read_csv('GP_stream_data.csv')
data_source3 = pd.read_csv('VOR_stream_data.csv')

# Menulis header kosong ke file target
with open('localizer.csv', 'w') as file:
    data_source1.head(0).to_csv(file, index=False)

with open('glidepath.csv', 'w') as file:
    data_source2.head(0).to_csv(file, index=False)

with open('vor.csv', 'w') as file:
    data_source3.head(0).to_csv(file, index=False)

# Menulis data dari setiap sumber ke file target masing-masing
for (row1, row2, row3) in zip(data_source1.iterrows(), data_source2.iterrows(), data_source3.iterrows()):
    _, row1 = row1
    _, row2 = row2
    _, row3 = row3

    if filter_row(row1):
        row1.to_frame().T.to_csv('localizer.csv', mode='a', header=False, index=False)

    if filter_row(row2):
        row2.to_frame().T.to_csv('glidepath.csv', mode='a', header=False, index=False)

    if filter_row(row3):
        row3.to_frame().T.to_csv('vor.csv', mode='a', header=False, index=False)

    time.sleep(0.5)

print("Semua data telah berhasil ditulis ke localizer.csv, glidepath.csv, dan vor.csv, dengan mengabaikan baris yang mengandung 'READY' atau 'STOP'.")
