import os
import logging
import pandas as pd
import subprocess
import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

# Lokasi file CSV untuk setiap kategori
LOCALIZER_CSV = "localizer.csv"
GLIDEPATH_CSV = "glidepath.csv"
VOR_CSV = "vor.csv"

DELAY = 0.5
SCRIPT_PATH = "loop.py"

LOCALIZER_COLUMNS = ['AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'LEVEL[dBm]', 'tes']
GLIDEPATH_COLUMNS = ['AM-MOD./90Hz[%]', 'AM-MOD./150Hz[%]', 'DDM(90-150)[1]', 'LEVEL[dBm]', 'GPS_alt[m]', 'tes']
VOR_COLUMNS = ['LEVEL[dBm]', 'PHI-90/150[°]', 'PHI-90/90[°]', 'PHI-150/150[°]', 'tes']

class CSVViewerApp(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, style=wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE)
        self.setup_colors()

        self.data = None
        self.figures = []
        self.file_path = None
        self.last_modified_time = None
        self.selected_columns = []
        self.process = None

        self.init_ui()
        self.load_and_initialize_data()

    def init_ui(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(self.background_color)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        left_panel = wx.Panel(panel)
        left_panel.SetBackgroundColour(self.background_color)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        image_paths = ["D:/Magang/beta_no_icc.png", "D:/Magang/rs_no_icc.png"]
        for image_path in image_paths:
            img = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
            img = img.Scale(200, int(img.GetHeight() * 200 / img.GetWidth()), wx.IMAGE_QUALITY_HIGH)
            bmp = wx.StaticBitmap(left_panel, bitmap=wx.Bitmap(img))
            left_sizer.Add(bmp, 0, wx.ALIGN_CENTER | wx.RIGHT, 10)

        header_text = wx.StaticText(left_panel, label="EVSD1000 Data Viewer")
        header_text.SetFont(wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        header_text.SetForegroundColour(wx.WHITE)
        left_sizer.Add(header_text, 0, wx.ALIGN_CENTER | wx.TOP, 10)

        choose_category_label = wx.StaticText(left_panel, label="Choose Category:")
        choose_category_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))
        choose_category_label.SetForegroundColour(wx.WHITE)
        left_sizer.Add(choose_category_label, 0, wx.ALIGN_LEFT | wx.TOP, 20)

        self.category_choice = wx.Choice(left_panel, choices=["Localizer", "Glidepath", "VOR"])
        self.category_choice.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.category_choice.Bind(wx.EVT_CHOICE, self.on_category_select)
        left_sizer.Add(self.category_choice, 0, wx.EXPAND | wx.ALL, 10)

        choose_data_label = wx.StaticText(left_panel, label="Choose Data:")
        choose_data_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))
        choose_data_label.SetForegroundColour(wx.WHITE)
        left_sizer.Add(choose_data_label, 0, wx.ALIGN_LEFT | wx.TOP, 20)

        self.checkbox_panel = wx.Panel(left_panel)
        self.checkbox_panel.SetBackgroundColour(self.background_color)
        self.checkbox_sizer = wx.BoxSizer(wx.VERTICAL)
        self.checkbox_panel.SetSizer(self.checkbox_sizer)
        left_sizer.Add(self.checkbox_panel, 1, wx.EXPAND | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.clear_all_button = wx.Button(left_panel, label="Clear All Choices")
        self.clear_all_button.Bind(wx.EVT_BUTTON, self.clear_all_selection)
        button_sizer.Add(self.clear_all_button, 0, wx.ALIGN_LEFT | wx.ALL, 10)

        self.start_button = wx.Button(left_panel, label="Start Stream")
        self.start_button.Bind(wx.EVT_BUTTON, self.start_stream)
        button_sizer.Add(self.start_button, 0, wx.ALIGN_LEFT | wx.ALL, 10)

        self.stop_button = wx.Button(left_panel, label="Stop Stream")
        self.stop_button.Bind(wx.EVT_BUTTON, self.stop_stream)
        button_sizer.Add(self.stop_button, 0, wx.ALIGN_LEFT | wx.ALL, 10)

        button_sizer.AddStretchSpacer()

        self.save_button = wx.Button(left_panel, label="Save PDF")
        self.save_button.Bind(wx.EVT_BUTTON, self.save_to_pdf)
        button_sizer.Add(self.save_button, 0, wx.ALIGN_LEFT | wx.ALL, 10)

        left_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)

        left_panel.SetSizer(left_sizer)
        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 10)

        self.figure_panel = wx.Panel(panel)
        self.figure_sizer = wx.BoxSizer(wx.VERTICAL)
        self.figure_panel.SetSizer(self.figure_sizer)
        main_sizer.Add(self.figure_panel, 2, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def setup_colors(self):
        self.background_color = "#002060"

    def clear_all_selection(self, event):
        for checkbox in self.checkboxes:
            checkbox.SetValue(False)
        self.selected_columns.clear()
        self.update_plot()

    def read_csv_file(self, file_path):
        return pd.read_csv(file_path, encoding='latin1').tail(100)

    def plot_line(self, data, figsize=(10, 6)):  
        fig, axes = plt.subplots(len(data.columns), 1, figsize=figsize, sharex=True)
        
        # Check if data.columns is not empty
        if len(data.columns) > 0:
            if len(data.columns) == 1:
                axes = [axes]  # Ensure axes is a list when there's only one column

            for i, column in enumerate(data.columns):
                axes[i].plot(data.index, data[column], label=column)
                axes[i].legend()

            fig.tight_layout()
            self.figures.append(fig)

    def update_plot(self):
        try:
            self.data = self.read_csv_file(self.file_path)
            self.figures.clear()
            if self.selected_columns:
                self.plot_line(self.data[self.selected_columns])
            else:
                self.plot_line(self.data)
            self.update_figure_panel()
        except Exception as e:
            logging.error(f"Failed to update plot: {str(e)}")

    def update_figure_panel(self):
        self.figure_sizer.Clear(True)
        if self.figures:
            for fig in self.figures:
                canvas = FigureCanvas(self.figure_panel, -1, fig)
                self.figure_sizer.Add(canvas, 1, wx.EXPAND)
        self.figure_panel.Layout()

    def start_polling(self):
        self.polling_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.poll_file_changes, self.polling_timer)
        self.polling_timer.Start(int(DELAY * 1000))

    def poll_file_changes(self, event):
        if self.file_path:
            try:
                current_modified_time = os.path.getmtime(self.file_path)
                if self.last_modified_time != current_modified_time:
                    self.last_modified_time = current_modified_time
                    self.update_plot()
            except Exception as e:
                logging.error(f"Error polling file: {str(e)}")

    def load_and_initialize_data(self):
        try:
            self.update_column_list()
            self.update_plot()
            if self.file_path:
                self.last_modified_time = os.path.getmtime(self.file_path)
                self.start_polling()
        except Exception as e:
            logging.error(f"Failed to load file: {str(e)}")

    def update_column_list(self):
        self.checkbox_sizer.Clear(True)
        self.checkboxes = []

        category = self.category_choice.GetStringSelection()
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
            checkbox = wx.CheckBox(self.checkbox_panel, label=column)
            checkbox.SetForegroundColour(wx.WHITE)  # Set text color of checkboxes
            checkbox.Bind(wx.EVT_CHECKBOX, self.on_checkbox_toggle)
            self.checkboxes.append(checkbox)
            self.checkbox_sizer.Add(checkbox, 0, wx.EXPAND | wx.ALL, 5)

        self.checkbox_panel.Layout()

    def on_checkbox_toggle(self, event):
        checkbox = event.GetEventObject()
        if checkbox.GetValue():
            self.selected_columns.append(checkbox.GetLabel())
        else:
            self.selected_columns.remove(checkbox.GetLabel())
        self.update_plot()

    def on_category_select(self, event):
        self.update_column_list()
        self.update_plot()

    def save_to_pdf(self, event):
        with wx.FileDialog(self, "Save PDF", wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            file_path = file_dialog.GetPath()
            try:
                with PdfPages(file_path) as pdf:
                    for fig in self.figures:
                        pdf.savefig(fig)
                wx.MessageBox("PDF saved successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Failed to save PDF: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def start_stream(self, event):
        if self.process is None:
            self.process = subprocess.Popen(['python', SCRIPT_PATH])
            wx.MessageBox("Streaming started", "Info", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Streaming already running", "Warning", wx.OK | wx.ICON_WARNING)

    def stop_stream(self, event):
        if self.process is not None:
            self.process.terminate()
            self.process = None
            wx.MessageBox("Streaming stopped", "Info", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No streaming process to stop", "Warning", wx.OK | wx.ICON_WARNING)

    def on_close(self, event):
        if hasattr(self, 'polling_timer'):
            self.polling_timer.Stop()
        if self.process is not None:
            self.process.terminate()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = CSVViewerApp(None, title="EVSD1000 Data Viewer")
    frame.Show()
    app.MainLoop()
