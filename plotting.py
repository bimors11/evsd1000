import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import  QFileDialog
import matplotlib.image as mpimg
from utils import get_user_inputs
def update_plot(window):
    try:
        if window.file_path:
            encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1']
            for encoding in encodings_to_try:
                try:
                    window.data = pd.read_csv(window.file_path, encoding=encoding, on_bad_lines='skip')
                    break
                except UnicodeDecodeError:
                    continue

            if not window.data.empty:
                window.figure.clear()
                columns = get_columns_based_on_mode(window)
                selected_columns = window.get_selected_columns()
                columns = [col for col in columns if col in selected_columns]
                num_plots = len(columns)
                if columns:
                    for i, column in enumerate(columns):
                        if column in window.data.columns:
                            ax = window.figure.add_subplot(num_plots, 1, i + 1)
                            plot_height = 0.9 / num_plots
                            plot_bottom = 0.05 + (num_plots - i - 1) * plot_height
                            ax.set_position([0.1, plot_bottom, 0.8, plot_height])

                            # Convert column data to numeric and handle non-numeric values
                            column_data = pd.to_numeric(window.data[column], errors='coerce').dropna()

                            if column_data.empty:
                                continue

                            data_min, data_max = column_data.min(), column_data.max()
                            range_margin = 0.2 * (data_max - data_min)
                            upper_bound = data_max - range_margin
                            lower_bound = data_min + range_margin

                            ax.axhline(upper_bound, color='red', linestyle='--', linewidth=1, label='Upper Bound')
                            ax.axhline(lower_bound, color='red', linestyle='--', linewidth=1, label='Lower Bound')

                            color_normal = 'blue'
                            color_above = 'red'
                            color_below = 'orange'

                            x_values = column_data.index
                            y_values = column_data

                            # Ensure x_values and y_values are lists or arrays
                            if isinstance(x_values, pd.Index):
                                x_values = x_values.tolist()
                            
                            if isinstance(y_values, pd.Series):
                                y_values = y_values.tolist()

                            ax.plot(x_values, y_values, color=color_normal)
                            ax.plot([x for x, y in zip(x_values, y_values) if y > upper_bound], 
                                    [y for y in y_values if y > upper_bound], color=color_above)
                            ax.plot([x for x, y in zip(x_values, y_values) if y < lower_bound], 
                                    [y for y in y_values if y < lower_bound], color=color_below)

                            ax.grid(True)
                            ax.set_xlabel('Time', fontsize=9)
                            ax.set_ylabel(column, fontsize=9)
                            ax.tick_params(axis='both', which='major', labelsize=8)

                            y_min, y_max = column_data.min(), column_data.max()
                            y_margin = 4.0
                            ax.set_ylim(min(y_min, lower_bound) - y_margin, max(y_max, upper_bound) + y_margin)

                            last_value = column_data.iloc[-1]
                            ax.text(1.01, 0.5, f'Latest: {last_value:.2f}', transform=ax.transAxes, verticalalignment='center', fontsize=8)

                    window.canvas.draw()
    except Exception as e:
        print(f"Error updating plot: {e}")

def get_columns_based_on_mode(self):
    columns = {
        'VOR': ['LEVEL[dBm]', 'BEARING(from)[°]', 'FM-DEV.[Hz]', 'FM-INDEX'],
        'ILS': ['LEVEL[dBm]', 'AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[uA]', 'SDM[%]'],
        'GP': ['LEVEL[dBm]', 'AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[uA]', 'SDM[%]'],
    }
    return columns.get(self.mode, [])

def clear_plot(self):
    self.figure.clear()
    self.canvas.draw()

def save_plot(self):
    if self.file_path and not self.data.empty:
        pdf_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf);;All Files (*)")
        if pdf_path:
            columns = get_columns_based_on_mode(self)
            num_plots = len(columns)
            plots_per_page = 2
            num_pages = (num_plots + plots_per_page - 1) // plots_per_page

            user_inputs = get_user_inputs()
            if user_inputs is None:
                return
            
            bandara, alat, pengujian = user_inputs

            columns = columns = get_columns_based_on_mode(self)
            num_plots = len(columns)

            with PdfPages(pdf_path) as pdf:
                for page in range(num_pages):
                    fig = plt.figure(figsize=(11.69, 8.27))
                    fig.subplots_adjust(top=0.8, bottom=0.1, left=0.1, right=0.9, hspace=0.4)

                    logo_ax = fig.add_axes([0.02, 0.9, 0.3, 0.05])
                    logo_ax.axis('off')
                    image_path = 'rsxbeta.png'
                    if os.path.exists(image_path):
                        img = mpimg.imread(image_path)
                        logo_ax.imshow(img, aspect='auto')

                    header_ax = fig.add_axes([0.35, 0.88, 0.4, 0.07])
                    header_ax.axis('off')

                    header_text = (
                        f'MODE: {self.mode}\n'
                        f'DATE: {pd.Timestamp.now().strftime("%Y-%m-%d")}\n'
                        f'TIME: {pd.Timestamp.now().strftime("%H:%M:%S")}\n'
                    )
                    header_ax.text(0.0, 0.35, header_text, fontsize=12, ha='left', va='center', wrap=True)

                    header_ax2 = fig.add_axes([0.53, 0.88, 0.4, 0.07])
                    header_ax2.axis('off')
                    header_text_right = (
                        f'Airport: {bandara}\n'
                        f'Transmitter: {alat}\n'
                        f'Attempt: {pengujian}'
                    )
                    header_ax2.text(0.0, 1.0, header_text_right, fontsize=12, ha='left', va='top')

                    start_index = page * plots_per_page
                    end_index = min(start_index + plots_per_page, num_plots)
                    columns_for_page = columns[start_index:end_index]

                    plot_height = 0.6 if num_plots == 1 else 0.35
                    plot_spacing = 0.05
                    start_height = 0.20 if num_plots == 1 else 0.51

                    for i, column in enumerate(columns_for_page):
                        if column in self.data.columns:
                            plot_bottom = start_height - (i * (plot_height + plot_spacing))
                            ax = fig.add_axes([0.1, plot_bottom, 0.8, plot_height])
                            column_data = self.data[column].dropna()

                            data_min, data_max = column_data.min(), column_data.max()
                            range_margin = 0.2 * (data_max - data_min)
                            upper_bound = data_max - range_margin
                            lower_bound = data_min + range_margin

                            ax.axhline(upper_bound, color='black', linestyle='--', linewidth=1, label='Upper Bound')
                            ax.axhline(lower_bound, color='black', linestyle='--', linewidth=1, label='Lower Bound')

                            if column_data.empty:
                                continue

                            color_normal = 'blue'
                            color_above = 'red'
                            color_below = 'orange'

                            ax.plot(column_data.index, column_data, color=color_normal)
                            ax.plot(column_data.index[column_data > upper_bound], column_data[column_data > upper_bound], color=color_above)
                            ax.plot(column_data.index[column_data < lower_bound], column_data[column_data < lower_bound], color=color_below)

                            ax.grid(True)
                            ax.set_xlabel('Time', fontsize=9)
                            ax.set_ylabel(column, fontsize=7)
                            ax.tick_params(axis='both', which='major', labelsize=8)

                            y_min, y_max = column_data.min(), column_data.max()
                            y_margin = 4.0
                            ax.set_ylim(min(y_min, lower_bound) - y_margin, max(y_max, upper_bound) + y_margin)

                    fig.text(0.55, 0.04, "-- : Upper and Lower", fontsize=10, ha='right', va='top', color='red')
                    fig.text(0.69, 0.04, "Blue : Normal Range", fontsize=10, ha='right', va='top', color='blue')
                    fig.text(0.83, 0.04, "Red : Above Upper", fontsize=10, ha='right', va='top', color='red')
                    fig.text(0.98, 0.04, "Orange : Below Lower", fontsize=10, ha='right', va='top', color='orange')

                    pdf.savefig(fig)
                    plt.close(fig)

