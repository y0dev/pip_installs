import os
import serial
import threading
import time
from datetime import datetime
import tkinter as tk

class SerialPortLogger:
    def __init__(self, config, log_output, status_callback):
        """
        Initializes the SerialPortLogger.

        :param config: Configuration dictionary.
        :param log_output: The Tkinter ScrolledText widget for displaying log output.
        :param status_callback: Function to update the connection status circle in the GUI.
        """
        self.config = config
        self.log_output = log_output  # Tkinter ScrolledText widget
        self.status_callback = status_callback  # Function to update the status indicator
        self.log_dir = self.create_log_directory()
        self.serial_port = None
        self.is_logging = False
        self.log_file = None
        self.current_log_size = 0
        self.last_data_received = time.time()  # Track last data received time for status update

    def create_log_directory(self):
        """
        Creates the directory for logs based on the current date.

        :return: Path to the log directory.
        """
        base_dir = os.path.join("logs", datetime.now().strftime("%Y"), datetime.now().strftime("%m_%b"),
                                 datetime.now().strftime("%d_%m_%Y"))
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    def create_new_log_file(self):
        """
        Creates a new log file for each new logging session.

        :return: Path to the new log file.
        """
        log_file_name = datetime.now().strftime("%H_%M_%S") + '.txt'
        self.log_file = os.path.join(self.log_dir, log_file_name)
        return self.log_file

    def run(self, ports, baudrate):
        """
        Starts logging data from the specified serial ports.

        :param ports: List of serial ports to log from.
        :param baudrate: Baud rate for the serial connection.
        """
        self.is_logging = True
        for port in ports:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            threading.Thread(target=self.log_data, daemon=True).start()
            threading.Thread(target=self.check_connection_status, daemon=True).start()

    def log_data(self):
        """
        Continuously reads from the serial port and logs the data, ensuring proper line formatting.
        """
        buffer = ""
        while self.is_logging:
            try:
                if self.serial_port.in_waiting:
                    # Read data from serial port
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore') # ascii or latin-1
                    buffer += data

                    # Process complete lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)  # Split by the first newline
                        line = line.strip()  # Remove any leading/trailing whitespace or extra newlines
                        self.write_to_log_file(line + "\n")  # Log the line to the file
                        self.update_gui_output(line + "\n")  # Update the GUI output

                    self.rotate_logs_if_needed()

            except serial.SerialException:
                self.update_gui_output("Serial connection lost.\n")
                self.status_callback("red")  # Update the status circle to red on failure
                self.reconnect_after_delay()



    def write_to_log_file(self, data):
        """
        Writes data to the log file.

        :param data: Data to write to the file.
        """
        with open(self.log_file, 'a') as f:
            f.write(data)
        self.current_log_size += len(data)

    def update_gui_output(self, data):
        """
        Updates the log output in the GUI.

        :param data: Data to write to the Tkinter ScrolledText widget.
        """
        self.log_output.insert(tk.END, data)
        self.log_output.see(tk.END)  # Scroll to the end

    def rotate_logs_if_needed(self):
        """
        Rotates the log file when the current log size exceeds the max size.
        """
        log_max_size = self.config.get("log_max_size", 1024 * 1024)  # Example 1 MB limit

        if os.path.getsize(self.log_file) >= log_max_size:
            self.log_file = self.create_new_log_file()

    def check_connection_status(self):
        """
        Periodically checks the status of the serial connection and updates the GUI.
        """
        while self.is_logging:
            elapsed_time = time.time() - self.last_data_received

            if elapsed_time > 60:  # No data in the last minute, set to yellow
                self.status_callback("yellow")
            else:
                self.status_callback("green")

            time.sleep(10)  # Check every 10 seconds

    def reconnect_after_delay(self):
        """
        Attempts to reconnect after 10 minutes if the connection is lost.
        """
        time.sleep(600)  # Wait for 10 minutes
        if self.serial_port is not None and not self.serial_port.is_open:
            self.serial_port.open()

        if self.serial_port.is_open:
            self.status_callback("green")  # Indicate reconnection

    def stop_logging(self):
        """
        Stops the logging process and makes the log file read-only.
        """
        self.is_logging = False
        if self.serial_port:
            self.serial_port.close()
        if self.log_file:
            os.chmod(self.log_file, 0o444)  # Make log file read-only after stopping
