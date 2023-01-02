import serial
import threading
import os

class SerialPortManager:
    # A class for management of serial port data in a separate thread
    def __init__(self, serialPortBaud=115200, port_connect_bt=0):
        self.isRunning = False
        self.serialPortName = None
        self.serialPortBaud = serialPortBaud
        self.serialPort = serial.Serial()
        # Create a byte array to store incoming data
        self.serialPortBuffer = bytearray()
        self.port_connect_button = port_connect_bt
        self.thread_stopped = True

    def set_name(self, serialPortName):
        self.serialPortName = serialPortName

    def set_baud(self, serialPortBaud):
        self.serialPortBaud = serialPortBaud

    def start(self):
        self.isRunning = True
        self.serialPortThread = threading.Thread(target=self.thread_handler)
        self.serialPortThread.start()
        self.thread_stopped = False

    def send_buffer(self, buffer):
        if self.isRunning:
            send_buffer = buffer + "\r\n"
            self.serialPort.write(send_buffer.encode())

    def stop(self):
        self.isRunning = False

    def thread_handler(self):

        while self.isRunning:
            try:
                if not self.serialPort.isOpen():

                    self.serialPort = serial.Serial(
                        port=self.serialPortName,
                        baudrate=self.serialPortBaud,
                        bytesize=8,
                        timeout=2,
                        stopbits=serial.STOPBITS_ONE,
                    )

                    self.port_connect_button.config(
                        text="Disconnect", bg="lime")
                else:
                    # Wait until there is data waiting in the serial buffer
                    while self.serialPort.in_waiting > 0:
                        # Read only one byte from serial port
                        serialPortByte = self.serialPort.read(1)
                        self.serialPortBuffer.append(
                            int.from_bytes(serialPortByte, byteorder='big'))

            except:
                print("Serial Port exception")
                self.port_connect_button.config(
                    text="Connect", bg="dodgerblue")
                self.isRunning = False
                break
        
        print("Thread stop")

        if self.serialPort.isOpen():
            self.serialPort.close()
        self.port_connect_button.config(text="Connect", bg="dodgerblue")
        self.isRunning = False
        self.thread_stopped = True

    def read_buffer(self):
        # Return a copy of serial port buffer
        buffer = self.serialPortBuffer
        # Clear serial port buffer
        self.serialPortBuffer = bytearray()
        return buffer

    def __del__(self):
        self.isRunning = False
        if self.serialPort.isOpen():
            self.serialPort.close()

