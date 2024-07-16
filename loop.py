import pandas as pd
import time

# Baca data dari file CSV
data = pd.read_csv('D:\\Magang\\stream_data.csv')

# Buat file baru dan tulis headernya untuk localizer.csv
with open('D:\\Magang\\localizer.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

# Buat file baru dan tulis headernya untuk glidepath.csv
with open('D:\\Magang\\glidepath.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

# Buat file baru dan tulis headernya untuk vor.csv
with open('D:\\Magang\\vor.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

# Looping melalui setiap baris data dan menulisnya satu per satu ke masing-masing file baru dengan jeda 0.5 detik
for i, row in data.iterrows():
    row.to_frame().T.to_csv('D:\\Magang\\localizer.csv', mode='a', header=False, index=False)
    row.to_frame().T.to_csv('D:\\Magang\\glidepath.csv', mode='a', header=False, index=False)
    row.to_frame().T.to_csv('D:\\Magang\\vor.csv', mode='a', header=False, index=False)
    time.sleep(0.5)
    print(f"Baris ke-{i+1} telah ditulis ke localizer.csv, glidepath.csv, dan vor.csv")

print("Semua data telah berhasil ditulis ke localizer.csv, glidepath.csv, dan vor.csv")
