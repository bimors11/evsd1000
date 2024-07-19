import pandas as pd
import time

data = pd.read_csv('stream_data.csv')

with open('localizer.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

with open('glidepath.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

with open('vor.csv', 'w') as file:
    data.head(0).to_csv(file, index=False)

for i, row in data.iterrows():
    row.to_frame().T.to_csv('localizer.csv', mode='a', header=False, index=False)
    row.to_frame().T.to_csv('glidepath.csv', mode='a', header=False, index=False)
    row.to_frame().T.to_csv('vor.csv', mode='a', header=False, index=False)
    time.sleep(0.5)
    print(f"Baris ke-{i+1} telah ditulis ke localizer.csv, glidepath.csv, dan vor.csv")

print("Semua data telah berhasil ditulis ke localizer.csv, glidepath.csv, dan vor.csv")
