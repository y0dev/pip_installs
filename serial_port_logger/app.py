import os
import json
import threading
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from serial_port_logger import SerialPortLogger
from serial_port_analyzer import SerialPortAnalyzer

class SerialLoggerApp:
    def __init__(self, root):
        """
        Initializes the GUI application for serial port logging.
        
        :param root: The main Tkinter window.
        """
        self.root = root
        self.root.title("Serial Logger")
        
        # Set the icon for the application
        self.root.iconbitmap("app_icon.ico")  # Change to your icon file path
        
        # Load configuration
        self.load_config()

        # Create GUI components
        self.create_widgets()

        # Initialize classes
        self.logger = None
        self.analyzer = SerialPortAnalyzer(self.config)

    def load_config(self):
        """
        Loads the configuration from a JSON file.
        """
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def create_widgets(self):
        """
        Creates the GUI components for the application.
        """
        # Serial Port Selection
        self.port_label = tk.Label(self.root, text="Select Serial Port:")
        self.port_label.pack(pady=5)

        self.port_combobox = tk.StringVar()
        self.port_menu = tk.OptionMenu(self.root, self.port_combobox, *self.get_serial_ports())
        self.port_menu.pack(pady=5)

        # Baudrate Selection
        self.baudrate_label = tk.Label(self.root, text="Baud Rate:")
        self.baudrate_label.pack(pady=5)

        self.baudrate_entry = tk.Entry(self.root)
        self.baudrate_entry.insert(0, '115200')  # Default baudrate
        self.baudrate_entry.pack(pady=5)

        # Button Frame (for Start/Stop Buttons)
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        # Start Logging Button
        self.start_button = tk.Button(button_frame, text="Start Logging", command=self.start_logging)
        self.start_button.grid(row=0, column=0, padx=10)

        # Stop Logging Button
        self.stop_button = tk.Button(button_frame, text="Stop Logging", command=self.stop_logging)
        self.stop_button.grid(row=0, column=1, padx=10)

        # Connection Status Indicator
        self.connection_status_label = tk.Label(self.root, text="Connection Status:")
        self.connection_status_label.pack(pady=5)

        self.canvas = tk.Canvas(self.root, width=20, height=20)
        self.canvas.pack()
        self.status_circle = self.canvas.create_oval(5, 5, 20, 20, fill="red")  # Start with red (disconnected)

        # Log Output
        self.log_output = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.log_output.pack(pady=5)

        # Analyze Logs Button
        self.analyze_button = tk.Button(self.root, text="Analyze Logs", command=self.analyze_logs)
        self.analyze_button.pack(pady=5)

        # Status Label
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=5)

    def get_serial_ports(self):
        """
        Returns a list of available serial ports.
        """
        return [port.device for port in serial.tools.list_ports.comports()]

    def start_logging(self):
        """
        Starts logging from the selected serial port and creates a new log file.
        """
        selected_port = self.port_combobox.get()
        baudrate = int(self.baudrate_entry.get())

        if not selected_port:
            messagebox.showerror("Error", "Please select a serial port.")
            return

        self.logger = SerialPortLogger(self.config, self.log_output, self.update_connection_status)
        self.logger.create_new_log_file()  # Create a new log file for this session
        logging_thread = threading.Thread(target=self.logger.run, args=([selected_port], baudrate), daemon=True)
        logging_thread.start()

        self.status_label.config(text=f"Logging started on {selected_port}...")
        self.log_output.insert(tk.END, f"Logging started on {selected_port}...\n")
        self.update_connection_status("green")  # Indicate connection established
        self.root.update_idletasks()

    def stop_logging(self):
        """
        Stops the logging process.
        """
        if self.logger:
            self.logger.stop_logging()
            self.status_label.config(text="Logging stopped.")
            self.log_output.insert(tk.END, "Logging stopped.\n")
            self.update_connection_status("red")  # Connection lost
            self.root.update_idletasks()

    def update_connection_status(self, status_color):
        """
        Updates the color of the connection status indicator.

        :param status_color: The color to set the connection status circle (green, yellow, red).
        """
        self.canvas.itemconfig(self.status_circle, fill=status_color)

    def analyze_logs(self):
        """
        Analyzes the logs in the log directory.
        """
        log_files = self.get_log_files()
        if not log_files:
            messagebox.showwarning("Warning", "No log files to analyze.")
            return
        
        for log_file in log_files:
            self.analyzer.analyze_log(log_file)

        self.status_label.config(text="Logs analyzed.")
        self.log_output.insert(tk.END, "Logs analyzed.\n")
        self.root.update_idletasks()

    def get_log_files(self):
        """
        Retrieves log files from the log directory.
        
        :return: List of log file paths.
        """
        log_dir = self.logger.log_dir if self.logger else "logs"
        return [os.path.join(log_dir, file) for file in os.listdir(log_dir) if file.endswith('.txt')]

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialLoggerApp(root)
    root.mainloop()
