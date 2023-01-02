import tkinter as tk
from tkinter import scrolledtext
import tkinter.ttk as ttk
from tkinter import messagebox
import shutil
import os
from os import listdir
import glob
import stat
import subprocess
from subprocess import Popen, PIPE, STDOUT
import time
from sys import platform
import serial.tools.list_ports
import zipfile

import rui3_my_serial
from rui3_my_serial import *

if platform == "darwin":
    from tkmacosx import Button


# Variables

# All AT commands
most_used_commands = ['AT?', 'AT+BOOT', 'ATZ', 'AT+BAT', 'AT+VER', 'AT+LPM', 'AT+APPEUI', 'AT+APPKEY',
                      'AT+DEVEUI', 'AT+JOIN', 'AT+NJM', 'AT+CFM', 'AT+SEND', 'AT+DR', 'AT+BAND', 'AT+NWM', 'ATC+STATUS=?', 'ATC+SENDINT']

# Platform dependend Arduino-CLI path
arduino_cli_cmd = "./arduino-cli_0.27.1_Windows_64bit/arduino-cli.exe"

# Buffer for Arduino-CLI calls
compile_command = ""

# UART port for downloading the code
upload_port = ""

# Update interval for Serial Terminal
guiUpdateInterval = 40

# Flag if BSP's are installed
installation_complete = False

# Arduino names of the WisDuo modules
rak3372_board = "rak_rui:stm32:WisDuoRAK3172EvaluationBoard"
rak4631_board = "rak_rui:nrf52:WisCoreRAK4631Board"
rak11722_board = "rak_rui:apollo3:WisCoreRAK11720Board"

# Placeholder for the selected board
selected_board = ""

# Flags which modules are selected and which sensor slot they are using
rak1901 = False
rak1902 = False
rak1903 = False
rak1904 = False
rak1904_slot = 'A'
rak1905 = False
rak1905_slot = 'A'
rak1906 = False
rak1921 = False
rak12002 = False
rak12003 = False
rak12008 = False
rak12010 = False
rak12014 = False
rak12014_slot = 'A'
rak12019 = False
rak12027 = False
rak12027_slot = 'A'
rak12037 = False
rak12039 = False
rak12040 = False
rak12047 = False
rak12500 = False
rak13011 = False
rak13011_slot = 'A'
rak3372 = False
rak4631 = False
rak11722 = False

# Temporary placeholder for the selected sensor slot
selected_slot = 'A'

rec_reader = None

debug_on = False

# Detect available serial ports
# return - list with found serial ports
def serial_ports():
    return serial.tools.list_ports.comports()

# Serial port selection handler
# var event - what event triggered the callback
def select_port_selected(event):
    global found_ports
    global get_port_window
    global upload_port
    port_index = event.widget.curselection()[0]

    print("Selected: ", found_ports[port_index])

    upload_port = found_ports[port_index]
    port_label.config(text="Port: " + upload_port)

    print("Selected: ", upload_port)

    serialPortManager.set_name(upload_port)
    serialPortManager.set_baud(115200)
    get_port_window.destroy()

# Menu Message Box Select Port
def select_port():
    global get_port_window
    global found_ports
    global port_menu
    get_port_window = tk.Toplevel(main_window)
    menu_x = port_menu.winfo_rootx()
    menu_y = port_menu.winfo_rooty()
    get_port_window.geometry("+{}+{}".format(menu_x, menu_y))

    found_ports = []

    for n, (port, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports()), 1):
        print('--- {:2}: {:20} {}\n'.format(n, port, desc))
        found_ports.append(port)
    get_port_window.config(background="#FFDEAD")
    for x in range(len(found_ports)):
        print(found_ports[x],)

    if (len(found_ports) != 0):
        port_label = tk.Label(get_port_window, text="Select a port")
    else:
        port_label = tk.Label(get_port_window, text="No port found")
    port_label.pack()
    get_port_listbox = tk.Listbox(get_port_window, selectmode=tk.SINGLE)
    for x in range(len(found_ports)):
        get_port_listbox.insert(tk.END, found_ports[x])
    get_port_listbox.bind('<<ListboxSelect>>', select_port_selected)
    get_port_listbox.pack()

    return

# Manually connect/disconnect Serial Terminal
def connect_cb():
    if (upload_port == ""):
        messagebox.showerror("ERROR", "Select an upload port first")
        return
    if serialPortManager.isRunning:
        serialPortManager.stop()
        port_connect_bt.config(text="Connect", background="#1E90FF")
    else:
        port_connect_bt.config(text="Disconnect", background="#00FF00")
        serialPortManager.start()
        # Start updating textbox in GUI
        recursive_update_textbox()

# Send string over serial port
def send_serial_cb(self):
    buffer = serial_send_buffer.get()
    if serialPortManager.isRunning:
        print("Sending >>" + buffer + "<<")
        serialPortManager.send_buffer(buffer)
    serial_send_eb.delete(0, "end")
    serial_send_eb.update()

# Clear serial log
def clear_cb():
    print("Clear log")
    serial_box.config(state=tk.NORMAL)
    serial_box.delete("1.0", "end")
    serial_box.update()
    serial_box.config(state=tk.DISABLED)

# Callback for AT command buttons
# var index -  selected AT command
def at_command_selected(index):
    serial_send_eb.delete(0, "end")
    serial_send_eb.insert(tk.END, most_used_commands[index])
    serial_send_eb.update()
    serial_send_eb.focus_set()

# Callback for selected OS
# var selected - selected OS
def select_os_cb(selected):
    global os_select_window
    global file_menu_window
    if (selected == 2):
        print("Selected Linux")
        arduino_cli_cmd = "./arduino-cli_0.29.0_Linux_64bit/arduino-cli"
    elif (selected == 1):
        print("Selected MacOS")
        arduino_cli_cmd = "./arduino-cli_0.29.0_macOS_64bit/arduino-cli"
    elif (selected == 0):
        print("Selected Windows")
        arduino_cli_cmd = "./arduino-cli_0.27.1_Windows_64bit/arduino-cli.exe"

    os_select_window.destroy()
    file_menu_window.destroy()

# Select OS window
# Opens a window to select the OS
def select_os():
    global file_menu_window
    global os_select_window
    os_select_window = tk.Toplevel(file_menu_window)
    menu_x = options_menu.winfo_rootx()
    menu_y = options_menu.winfo_rooty()

    os_select_window.geometry(
        "+{}+{}".format(menu_x, menu_y))
    os_select_window.config(background="#FFDEAD")

    os_select_bt = tk.Button(os_select_window, text="Windows",
                             background="#00FFFF", command=lambda: select_os_cb(0))
    os_select_bt.pack(fill="both", expand=True)

    os_select_bt = tk.Button(os_select_window, text="MacOS",
                             background="#00FFFF", command=lambda: select_os_cb(1))
    os_select_bt.pack(fill="both", expand=True)

    os_select_bt = tk.Button(os_select_window, text="Linux",
                             background="#00FFFF", command=lambda: select_os_cb(2))
    os_select_bt.pack(fill="both", expand=True)

    main_window.wait_window(os_select_window)

def toggle_debug():
    global debug_on
    global debug_select_bt
    global debug_label
    if debug_on:
        debug_on = False
        print("Debug disabled")
        debug_select_bt.config(text="Debug off")
        debug_label.config(text="Debug off")
    else:
        debug_on = True
        print("Debug enabled")
        debug_select_bt.config(text="Debug on")
        debug_label.config(text="Debug on")


# Callback for File Menu
# Opens a list with menu entries
def options_menu_cb():
    global options_menu
    global file_menu_window
    global debug_on
    global debug_select_bt
    file_menu_window = tk.Toplevel(main_window)
    file_menu_window.title("FILE")
    menu_x = options_menu.winfo_rootx()
    menu_y = options_menu.winfo_rooty()
    file_menu_window.geometry(
        "+{}+{}".format(menu_x, menu_y))
    file_menu_window.config(background="#FFDEAD")

    if debug_on:
        bt_text = "Debug on"
    else:
        bt_text = "Debug off"
    debug_select_bt = tk.Button(file_menu_window, text=bt_text,
                                background="#00FFFF", command=toggle_debug)
    debug_select_bt.pack(fill="both", expand=True)

    divider1_bt = tk.Button(file_menu_window, text="     ", background="#FFDEAD")
    divider1_bt.pack(fill="both", expand=True)

    # os_select_bt = tk.Button(file_menu_window, text="Select OS",
    #                          background="#00FFFF", command=select_os)
    # os_select_bt.pack(fill="both", expand=True)

    # divider1_bt = tk.Button(file_menu_window, text="     ", background="#FFDEAD")
    # divider1_bt.pack(fill="both", expand=True)

    if not os.path.exists("./.bsp"):
        install_bt = tk.Button(
            file_menu_window, text="INSTALL\nREQUIRED!", background="#FA8072", command=check_installation)
        install_bt.pack(fill="both", expand=True)
        installation_complete = False
    else:
        install_bt = tk.Button(file_menu_window, text="Refresh\nInstallation!",
                               background="#00FFFF", command=refresh_installation)
        install_bt.pack(fill="both", expand=True)
        installation_complete = True

    divider1_bt = tk.Button(file_menu_window, text="     ", background="#FFDEAD")
    divider1_bt.pack(fill="both", expand=True)

    exit_bt = tk.Button(file_menu_window, text="Exit",
                        background="#00FFFF", command=on_closing)
    exit_bt.pack(fill="both", expand=True)

    main_window.wait_window(file_menu_window)

# Callback for Slot selection
# Saves selected slot in "selected_slot"
# Closes the selection window
# var slot - selected slot name
def slot_selected_cb(slot):
    global get_slot_window
    global selected_slot
    selected_slot = slot
    print("Selected Slot " + slot + " for module")
    get_slot_window.destroy()
    return

# Slot selection window
# Setup of pop-up window with a list of Sensor Slots
# var module - which module the selection is used for
def ask_slot(module):
    global selected_module
    global get_slot_window
    global rak3372_bt
    selected_module = module
    get_slot_window = tk.Toplevel(main_window)
    menu_x = rak3372_bt.winfo_rootx()
    menu_y = rak3372_bt.winfo_rooty()
    get_slot_window.geometry(
        "+{}+{}".format(menu_x, menu_y))
    get_slot_window.config(background="#FFDEAD")
    slot_label = tk.Label(
        get_slot_window, text="Select a module slot", background="#FA8072")
    slot_label.pack()
    slot_a_bt = tk.Button(get_slot_window, text="Slot A",
                          command=lambda: slot_selected_cb('A'))
    slot_a_bt.pack()
    slot_b_bt = tk.Button(get_slot_window, text="Slot B",
                          command=lambda: slot_selected_cb('B'))
    slot_b_bt.pack()
    slot_c_bt = tk.Button(get_slot_window, text="Slot C",
                          command=lambda: slot_selected_cb('C'))
    slot_c_bt.pack()
    slot_d_bt = tk.Button(get_slot_window, text="Slot D",
                          command=lambda: slot_selected_cb('D'))
    slot_d_bt.pack()
    slot_e_bt = tk.Button(get_slot_window, text="Slot E",
                          command=lambda: slot_selected_cb('E'))
    slot_e_bt.pack()
    slot_f_bt = tk.Button(get_slot_window, text="Slot F",
                          command=lambda: slot_selected_cb('F'))
    slot_f_bt.pack()

# Remove unselected modules
# Deletes files associated to the unselected module
# var module_bt - button associated with the module
# var source_name - name of the module to be removed
def remove_source(module_bt, source_name):
    print(source_name)
    module_bt.config(background="#FA8072")
    fileList = glob.glob("./RUI3-Modular/"+source_name+"*")
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)
    return False

# Add selected modules
# Copies files associoated with the selected module
# into the project folder
# var module_bt - button assigned with the module
# var source_name - source file required for the module
# var header_name - header file required for the module (not required for all modules)
def enable_source(module_bt, source_name, header_name=""):
    module_bt.config(background="#00FF00")
    shutil.copy("./RUI3-Modular/module-files/"+source_name, "./RUI3-Modular")
    if not (header_name == ""):
        shutil.copy("./RUI3-Modular/module-files/" +
                    header_name, "./RUI3-Modular")
    return True


# Callback for RAK1901 selection button
# Enables or disable the module, depending on the last status
def rak1901_cb():
    global rak1901
    global rak1901_bt
    if (rak1901):
        rak1901 = remove_source(rak1901_bt, "RAK1901")
    else:
        rak1901 = enable_source(rak1901_bt, "RAK1901_temp.cpp")
    return


# Callback for RAK1902 selection button
# Enables or disable the module, depending on the last status
def rak1902_cb():
    global rak1902
    global rak1902_bt
    if (rak1902):
        rak1902 = remove_source(rak1902_bt, "RAK1902")
    else:
        rak1902 = enable_source(rak1902_bt, "RAK1902_press.cpp")
    return


# Callback for RAK1903 selection button
# Enables or disable the module, depending on the last status
def rak1903_cb():
    global rak1903
    global rak1903_bt
    if (rak1903):
        rak1903 = remove_source(rak1903_bt, "RAK1903")
    else:
        rak1903 = enable_source(rak1903_bt, "RAK1903_light.cpp")
    return


# Callback for RAK1904 selection button
# Enables or disable the module, depending on the last status
def rak1904_cb():
    global rak1904
    global rak1904_bt
    global rak1904_slot
    header_name = "RAK1904_acc_S_"
    if (rak1904):
        rak1904 = remove_source(rak1904_bt, "RAK1904")
        rak1904_bt.config(text="RAK1904\nAcc")
    else:
        ask_slot(rak1904)
        main_window.wait_window(get_slot_window)
        if (selected_slot == 'A'):
            rak1904_slot = 'A'
            header_name = header_name + "A.h"
            rak1904_bt.config(text="RAK1904\nAcc (A)")
        elif (selected_slot == 'B'):
            rak1904_slot = 'B'
            header_name = header_name + "B.h"
            rak1904_bt.config(text="RAK1904\nAcc (B)")
        elif (selected_slot == 'C'):
            rak1904_slot = 'C'
            header_name = header_name + "C.h"
            rak1904_bt.config(text="RAK1904\nAcc (C)")
        elif (selected_slot == 'D'):
            rak1904_slot = 'D'
            header_name = header_name + "D.h"
            rak1904_bt.config(text="RAK1904\nAcc (D)")
        elif (selected_slot == 'E'):
            rak1904_slot = 'E'
            header_name = header_name + "E.h"
            rak1904_bt.config(text="RAK1904\nAcc (E)")
        elif (selected_slot == 'F'):
            rak1904_slot = 'F'
            header_name = header_name + "F.h"
            rak1904_bt.config(text="RAK1904\nAcc (F)")
        rak1904 = enable_source(rak1904_bt, "RAK1904_acc.cpp", header_name)
    return


# Callback for RAK1905 selection button
# Enables or disable the module, depending on the last status
def rak1905_cb():
    global rak1905
    global rak1905_bt
    global rak1905_slot
    header_name = "RAK1905_9dof_S_"

    if (rak1905):
        rak1905 = remove_source(rak1905_bt, "RAK1905")
        rak1905_bt.config(text="RAK1905\n9DOF")
    else:
        ask_slot(rak1905)
        main_window.wait_window(get_slot_window)
        if (selected_slot == 'A'):
            rak1905_slot = 'A'
            header_name = header_name + "A.h"
            rak1905_bt.config(text="RAK1905\n9DOF (A)")
        elif (selected_slot == 'B'):
            rak1905_slot = 'B'
            header_name = header_name + "B.h"
            rak1905_bt.config(text="RAK1905\n9DOF (B)")
        elif (selected_slot == 'C'):
            rak1905_slot = 'C'
            header_name = header_name + "C.h"
            rak1905_bt.config(text="RAK1905\n9DOF (C)")
        elif (selected_slot == 'D'):
            rak1905_slot = 'D'
            header_name = header_name + "D.h"
            rak1905_bt.config(text="RAK1905\n9DOF (D)")
        elif (selected_slot == 'E'):
            rak1905_slot = 'E'
            header_name = header_name + "E.h"
            rak1905_bt.config(text="RAK1905\n9DOF (E)")
        elif (selected_slot == 'F'):
            rak1905_slot = 'F'
            header_name = header_name + "F.h"
            rak1905_bt.config(text="RAK1905\n9DOF (E)")
        rak1905 = enable_source(rak1905_bt, "RAK1905_9dof.cpp", header_name)
    return


# Callback for RAK1906 selection button
# Enables or disable the module, depending on the last status
def rak1906_cb():
    global rak1906
    global rak1906_bt
    if (rak1906):
        rak1906 = remove_source(rak1906_bt, "RAK1906")
    else:
        rak1906 = enable_source(rak1906_bt, "RAK1906_env.cpp")
    return


# Callback for RAK1921 selection button
# Enables or disable the module, depending on the last status
def rak1921_cb():
    global rak1921
    global rak1921_bt
    if (rak1921):
        rak1921 = remove_source(rak1921_bt, "RAK1905")
    else:
        rak1921 = enable_source(rak1921_bt, "RAK1921_display.cpp")
    return


# Callback for RAK12002 selection button
# Enables or disable the module, depending on the last status
def rak12002_cb():
    global rak12002
    global rak12002_bt
    if (rak12002):
        rak12002 = remove_source(rak12002_bt, "RAK12002")
    else:
        rak12002 = enable_source(rak12002_bt, "RAK12002_rtc.cpp")
    return


# Callback for RAK12003 selection button
# Enables or disable the module, depending on the last status
def rak12003_cb():
    global rak12003
    global rak12003_bt
    if (rak12003):
        rak12003 = remove_source(rak12003_bt, "RAK12003")
    else:
        rak12003 = enable_source(rak12003_bt, "RAK12003_fir.cpp")
    return


# Callback for RAK12008 selection button
# Enables or disable the module, depending on the last status
def rak12008_cb():
    global rak12008
    global rak12008_bt
    if (rak12008):
        rak12008 = remove_source(rak12008_bt, "RAK12008")
    else:
        rak12008 = enable_source(rak12008_bt, "RAK12008_gas.cpp")
    return


# Callback for RAK12010 selection button
# Enables or disable the module, depending on the last status
def rak12010_cb():
    global rak12010
    global rak12010_bt
    if (rak12010):
        rak12010 = remove_source(rak12010_bt, "RAK12010")
    else:
        rak12010 = enable_source(rak12010_bt, "RAK12010_light.cpp")
    return


# Callback for RAK12014 selection button
# Enables or disable the module, depending on the last status
def rak12014_cb():
    global rak12014
    global rak12014_bt
    global rak12014_slot
    header_name = "RAK12014_tof_S_"

    if (rak12014):
        rak12014 = remove_source(rak12014_bt, "RAK12014")
        rak12014_bt.config(text="RAK12014\nToF")
    else:
        ask_slot(rak12014)
        main_window.wait_window(get_slot_window)
        if (selected_slot == 'A'):
            rak12014_slot = 'A'
            header_name = header_name + "A.h"
            rak12014_bt.config(text="RAK12014\nToF (A)")
        elif (selected_slot == 'B'):
            rak12014_slot = 'B'
            header_name = header_name + "B.h"
            rak12014_bt.config(text="RAK12014\nToF (B)")
        elif (selected_slot == 'C'):
            rak12014_slot = 'C'
            header_name = header_name + "C.h"
            rak12014_bt.config(text="RAK12014\nToF (C)")
        elif (selected_slot == 'D'):
            rak12014_slot = 'D'
            header_name = header_name + "D.h"
            rak12014_bt.config(text="RAK12014\nToF (D)")
        elif (selected_slot == 'E'):
            rak12014_slot = 'E'
            header_name = header_name + "E.h"
            rak12014_bt.config(text="RAK12014\nToF (E)")
        elif (selected_slot == 'F'):
            rak12014_slot = 'F'
            header_name = header_name + "F.h"
            rak12014_bt.config(text="RAK12014\nToF (F)")
        rak12014 = enable_source(rak12014_bt, "RAK12014_tof.cpp", header_name)
    return


# Callback for RAK12019 selection button
# Enables or disable the module, depending on the last status
def rak12019_cb():
    global rak12019
    global rak12019_bt
    if (rak12019):
        rak12019 = remove_source(rak12019_bt, "RAK12019")
    else:
        rak12019 = enable_source(rak12019_bt, "RAK12019_uv.cpp")
    return


# Callback for RAK12027 selection button
# Enables or disable the module, depending on the last status
def rak12027_cb():
    global rak12027
    global rak12027_bt
    global rak12027_slot
    header_name = "RAK12027_seismic_S_"

    if (rak12027):
        rak12027 = remove_source(rak12027_bt, "RAK12027")
        rak12027_bt.config(text="RAK12027\nQuake")
    else:
        ask_slot(rak12027)
        main_window.wait_window(get_slot_window)
        if (selected_slot == 'A'):
            rak12027_slot = 'A'
            header_name = header_name + "A.h"
            rak12027_bt.config(text="RAK12027\nQuake (A)")
        elif (selected_slot == 'B'):
            rak12027_slot = 'B'
            header_name = header_name + "B.h"
            rak12027_bt.config(text="RAK12027\nQuake (B)")
        elif (selected_slot == 'C'):
            rak12027_slot = 'C'
            header_name = header_name + "C.h"
            rak12027_bt.config(text="RAK12027\nQuake (C)")
        elif (selected_slot == 'D'):
            rak12027_slot = 'D'
            header_name = header_name + "D.h"
            rak12027_bt.config(text="RAK12027\nQuake (D)")
        elif (selected_slot == 'E'):
            rak12027_slot = 'E'
            header_name = header_name + "E.h"
            rak12027_bt.config(text="RAK12027\nQuake (E)")
        elif (selected_slot == 'F'):
            rak12027_slot = 'F'
            header_name = header_name + "F.h"
            rak12027_bt.config(text="RAK12027\nQuake (F)")
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", header_name)
    return


# Callback for RAK12037 selection button
# Enables or disable the module, depending on the last status
def rak12037_cb():
    global rak12037
    global rak12037_bt
    if (rak12037):
        rak12037 = remove_source(rak12037_bt, "RAK12037")
    else:
        rak12037 = enable_source(rak12037_bt, "RAK12037_co2.cpp")
    return


# Callback for RAK12039 selection button
# Enables or disable the module, depending on the last status
def rak12039_cb():
    global rak12039
    global rak12039_bt
    if (rak12039):
        rak12039 = remove_source(rak12039_bt, "RAK12039")
    else:
        rak12039 = enable_source(rak12039_bt, "RAK12039_pm.cpp")
    return


# Callback for RAK12040 selection button
# Enables or disable the module, depending on the last status
def rak12040_cb():
    global rak12040
    global rak12040_bt
    if (rak12040):
        rak12040 = remove_source(rak12040_bt, "RAK12040")
    else:
        rak12040 = enable_source(rak12040_bt, "RAK12040_temp_arr.cpp")
    return


# Callback for RAK12047 selection button
# Enables or disable the module, depending on the last status
def rak12047_cb():
    global rak12047
    global rak12047_bt
    if (rak12047):
        rak12047 = remove_source(rak12047_bt, "RAK12047")
    else:
        rak12047 = enable_source(rak12047_bt, "RAK12047_voc.cpp")
    return


# Callback for RAK12500 selection button
# Enables or disable the module, depending on the last status
# REMARK: Does not work with RAK3372 (yet)
def rak12500_cb():
    global rak12500
    global rak12500_bt
    if (selected_board == "rak_rui:stm32:WisDuoRAK3172EvaluationBoard"):
        messagebox.showerror(
            "ERROR", "RAK3372 does not support RAK12500 (yet)")
        rak12500 = False
        rak12500_bt.config(background="#FA8072")
        os.remove("./RUI3-Modular/rak12500_gnss.cpp")
        return
    if (rak12500):
        rak12500 = remove_source(rak12500_bt, "RAK12500")
    else:
        rak12500 = enable_source(rak12500_bt, "rak12500_gnss.cpp")
    return


# Callback for RAK13011 selection button
# Enables or disable the module, depending on the last status
def rak13011_cb():
    global rak13011
    global rak13011_bt
    global rak13011_slot
    header_name = "RAK13011_switch_S_"

    if (rak13011):
        rak13011 = remove_source(rak13011_bt, "RAK13011")
        rak13011_bt.config(text="RAK13011\nSwitch")
    else:
        ask_slot(rak13011)
        main_window.wait_window(get_slot_window)
        if (selected_slot == 'A'):
            rak13011_slot = 'A'
            header_name = header_name + "A.h"
            rak13011_bt.config(text="RAK13011\nSwitch (A)")
        elif (selected_slot == 'B'):
            rak13011_slot = 'B'
            header_name = header_name + "B.h"
            rak13011_bt.config(text="RAK13011\nSwitch (B)")
        elif (selected_slot == 'C'):
            rak13011_slot = 'C'
            header_name = header_name + "C.h"
            rak13011_bt.config(text="RAK13011\nSwitch (C)")
        elif (selected_slot == 'D'):
            rak13011_slot = 'D'
            header_name = header_name + "D.h"
            rak13011_bt.config(text="RAK13011\nSwitch (D)")
        elif (selected_slot == 'E'):
            rak13011_slot = 'E'
            header_name = header_name + "E.h"
            rak13011_bt.config(text="RAK13011\nSwitch (E)")
        elif (selected_slot == 'F'):
            rak13011_slot = 'F'
            header_name = header_name + "F.h"
            rak13011_bt.config(text="RAK13011\nSwitch (F)")
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", header_name)
    return


# Callback for RAK3372 selection button
# Enables the core module
# Unselects other core modules
def rak3372_cb():
    global selected_board
    global rak4631
    global rak3372
    global rak11722
    global module_label
    if not (selected_board == rak3372_board):
        clean_build_cb()
    selected_board = rak3372_board
    rak3372 = True
    rak4631 = False
    rak11722 = False
    rak3372_bt.config(background="#00FF00")
    rak4631_bt.config(background="#FA8072")
    rak11722_bt.config(background="#FA8072")
    module_label.config(text="Core: RAK3372")
    return


# Callback for RAK4631 selection button
# Enables the core module
# Unselects other core modules
def rak4631_cb():
    global selected_board
    global rak4631
    global rak3372
    global rak11722
    global module_label
    if not (selected_board == rak4631_board):
        clean_build_cb()
    selected_board = rak4631_board
    rak3372 = False
    rak4631 = True
    rak11722 = False
    rak3372_bt.config(background="#FA8072")
    rak4631_bt.config(background="#00FF00")
    rak11722_bt.config(background="#FA8072")
    module_label.config(text="Core: RAK4631")
    return


# Callback for RAK11722 selection button
# Enables the core module
# Unselects other core modules
def rak11722_cb():
    global selected_board
    global rak4631
    global rak3372
    global rak11722
    global module_label
    if not (selected_board == rak11722_board):
        clean_build_cb()
    selected_board = rak11722_board
    rak3372 = False
    rak4631 = False
    rak11722 = True
    rak3372_bt.config(background="#FA8072")
    rak4631_bt.config(background="#FA8072")
    rak11722_bt.config(background="#00FF00")
    module_label.config(text="RAK11722")

    return

# Opens a thread to process the command
# Starts the command, captures its output and
# shows the output in the log window
# var command - command to be executed
# var headline - first line to print in ouput window
# var clear - flag if the output window should be cleared first
# return - result of command execution
def ext_app_to_log(command, headline, clear):
    output_field.config(state=tk.NORMAL)
    if clear:
        output_field.delete("1.0", "end")
        output_field.update()
    output_field.insert(tk.END, headline)
    output_field.insert(tk.END, "\n\n")
    output_field.focus()
    output_field.update()
    output_field.update_idletasks()

    SW_MINIMIZE = 6
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_MINIMIZE
    info.creationflags = subprocess.HIGH_PRIORITY_CLASS

    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            startupinfo=info,
                            universal_newlines=True,
                            creationflags=subprocess.HIGH_PRIORITY_CLASS)

    while True:
        line = proc.stdout.readline()
        if not line:
            break
        output_field.insert(tk.END, line)
        # this triggers an update of the text area, otherwise it doesn't update
        output_field.update()
        output_field.update_idletasks()
        output_field.see(tk.END)

    output_field.config(state=tk.DISABLED)

    # Wait until process terminates (without using p.wait())
    while proc.poll() is None:
        # Process hasn't exited yet, let's wait some
        time.sleep(0.5)

    result = proc.returncode

    print("Finished " + command + " Result " + str(result))

    return result

# Start Arduino-CLI to verify the code
# The result is shown in the result button result_bt
def verify_cb():
    global selected_board

    if (not installation_complete):
        messagebox.showerror("ERROR", "Installation required first")
        return
    if (selected_board == ""):
        messagebox.showerror("ERROR", "Select a board first")
        return

    if not os.path.exists("./RUI3-Modular/build"):
        os.mkdir("./RUI3-Modular/build")
    if not os.path.exists("./RUI3-Modular/cache"):
        os.mkdir("./RUI3-Modular/cache")
    if not os.path.exists("./RUI3-Modular/flash-files"):
        os.mkdir("./RUI3-Modular/flash-files")

    verify_menu.config(text="busy", background="#FA8072")
    result_bt.config(background="#1E90FF", text="Result")

    if debug_on:
        build_flag = ' --build-property compiler.cpp.extra_flags=-DMY_DEBUG=1 '
    else:
        build_flag = ' --build-property compiler.cpp.extra_flags=-DMY_DEBUG=0 '

    compile_command = arduino_cli_cmd + " compile -b " + selected_board + build_flag + "--output-dir ./RUI3-Modular/flash-files --build-path ./RUI3-Modular/build --build-cache-path ./RUI3-Modular/cache --no-color --verbose --library ./RUI3-Modular/libraries ./RUI3-Modular/RUI3-Modular.ino"
    headline = "Verify, this can take some time, be patient"
    return_code = ext_app_to_log(compile_command, headline, True)

    if (return_code == 0):
        result_bt.config(background="#00FF00", text="SUCCESS")
    else:
        result_bt.config(background="#FA8072", text="FAIL")

    verify_menu.config(text="Verify", background="#CDB79E")

    return


# Start Arduino-CLI to compile and download the code
# The result is shown in the result button result_bt
def upload_cb():
    global selected_board

    if (not installation_complete):
        messagebox.showerror("ERROR", "Installation required first")
        return
    if (selected_board == ""):
        messagebox.showerror("ERROR", "Select a board first")
        return
    if (upload_port == ""):
        messagebox.showerror("ERROR", "Select an upload port first")
        return

    if not os.path.exists("./RUI3-Modular/build"):
        os.mkdir("./RUI3-Modular/build")
    if not os.path.exists("./RUI3-Modular/cache"):
        os.mkdir("./RUI3-Modular/cache")
    if not os.path.exists("./RUI3-Modular/flash-files"):
        os.mkdir("./RUI3-Modular/flash-files")
        
    if serialPortManager.isRunning:
        serialPortManager.stop()
        port_connect_bt.config(text="Connect", background="#1E90FF")

    upload_menu.config(text="busy", background="#FA8072")
    result_bt.config(background="#1E90FF", text="Result")

    old_upload_port = upload_port
    print("Upload port was "+old_upload_port)

    if debug_on:
        build_flag = ' --build-property compiler.cpp.extra_flags=-DMY_DEBUG=1 '
    else:
        build_flag = ' --build-property compiler.cpp.extra_flags=-DMY_DEBUG=0 '

    compile_command = arduino_cli_cmd + " compile -b " + selected_board + build_flag + "--output-dir ./RUI3-Modular/flash-files --build-path ./RUI3-Modular/build --build-cache-path ./RUI3-Modular/cache --upload -p " + \
        upload_port + " --no-color --verbose --library ./RUI3-Modular/libraries ./RUI3-Modular/RUI3-Modular.ino"

    headline = "Upload to device, this can take some time, be patient"
    return_code = ext_app_to_log(compile_command, headline, True)

    port_success = True

    if rak4631:
        retry_cnt = 0
        wait_port = True
        port_success = False
        print("Waiting for the RAK4630 USB port")
        while wait_port:
            time.sleep(5)
            found_ports = serial.tools.list_ports.comports()
            print("Updated COM port list")
            for port, desc, hwid in sorted(found_ports):
                print("{}: {} [{}]".format(port, desc, hwid))
                if port.startswith(old_upload_port):
                    print("Found Port")
                    wait_port = False
                    port_success = True
                    break
            retry_cnt += 1
            if retry_cnt == 60:
                print("Timeout Waiting")
                wait_port = False
                break

    if (return_code == 0):
        result_bt.config(background="#00FF00", text="SUCCESS")
        if port_success:
            serialPortManager.start()
            # Start updating textbox in GUI
            recursive_update_textbox()
            port_connect_bt.config(text="Disconnect", background="#00FF00")
    else:
        result_bt.config(background="#FA8072", text="FAIL")

    upload_menu.config(text="Upload", background="#CDB79E")

    return


# Clean up the build folders
# The result is shown in the result button result_bt
def clean_build_cb():
    clean_menu.config(text="busy", background="#FA8072")

    if os.path.exists("./RUI3-Modular/build"):
        shutil.rmtree("./RUI3-Modular/build")
    if os.path.exists("./RUI3-Modular/cache"):
        shutil.rmtree("./RUI3-Modular/cache")
    if os.path.exists("./RUI3-Modular/flash-files"):
        shutil.rmtree("./RUI3-Modular/flash-files")

    clean_menu.config(text="Clean", background="#CDB79E")
    return


# Refresh the BSP's installed
# The result is shown in the result button result_bt
def refresh_installation():
    global installation_complete

    # install_bt.config(text="busy", background="#FA8072")
    # result_bt.config(background="#1E90FF", text="Result")

    compile_command = arduino_cli_cmd + " config delete board_manager.additional_urls"
    headline = "Cleaning up additional BSP URL's"
    return_code1 = ext_app_to_log(compile_command, headline, False)
    time.sleep(10)

    compile_command = arduino_cli_cmd + \
        " config add board_manager.additional_urls https://raw.githubusercontent.com/beegee-tokyo/test/main/beegee-patch-rui3.json"
    # compile_command = arduino_cli_cmd + " config add board_manager.additional_urls https://raw.githubusercontent.com/RAKWireless/RAKwireless-Arduino-BSP-Index/staging/RUI_3.5.3/package_rakwireless.com_rui_index.json"

    headline = "Installing additional BSP URL's"
    return_code1 = ext_app_to_log(compile_command, headline, False)
    time.sleep(10)

    compile_command = arduino_cli_cmd + " core update-index"
    headline = "Updating BSP's index"
    return_code2 = ext_app_to_log(compile_command, headline, False)
    time.sleep(10)

    compile_command = arduino_cli_cmd + " core install rak_rui:nrf52"
    headline = "Installing RAK4630 BSP, this can take quite some time"
    return_code4 = ext_app_to_log(compile_command, headline, False)
    time.sleep(10)

    compile_command = arduino_cli_cmd + " core install rak_rui:stm32"
    headline = "Installing RAK3372 BSP, this can take quite some time"
    return_code3 = ext_app_to_log(compile_command, headline, False)
    time.sleep(10)

    # RAK11722 BSP is not yet release, no refresh possible
    #
    # compile_command = arduino_cli_cmd + " core install rak_rui:apollo3"
    # headline = "Installing RAK11722 BSP, this can take quite some time"
    # return_code3 = ext_app_to_log(compile_command, headline, False)
    # time.sleep(10)

    result = False
    if (return_code1 == 0) and (return_code2 == 0) and (return_code3 == 0) and (return_code4 == 0):
        # result_bt.config(background="#00FF00", text="SUCCESS")
        with open('./.bsp', 'w') as f:
            f.write('Installation success!')
            f.close()
        installation_complete = True
        result = True
    # else:
        # result_bt.config(background="#FA8072", text="FAIL")

    # install_bt.config(text="Refresh\nInstallation!", background="#00FF00")

    return result

# Check if BSP's are already installed
# If not installed it starts refresh_installation
# to install all required BSP's
def check_installation():
    print("Checking installation")
    if not os.path.exists("Arduino15"):
        print("Arduino15 folder doesn't exist")
    if not os.path.exists("Arduino15.zip"):
        print("Arduino15 ZIP file doesn't exist")

    result = False
    try:
        if not os.path.exists("Arduino15"):
            output_field.config(state=tk.NORMAL)
            output_field.delete("1.0", "end")
            output_field.update()
            output_field.insert(tk.END, "Installing the BSP's, be patient")
            output_field.insert(tk.END, "\n\n")
            output_field.focus()
            output_field.update()
            output_field.update_idletasks()
            with zipfile.ZipFile('Arduino15.zip', 'r') as zip:
                zip.extractall('.')
        else:
            print("BSP's already installed")
            result = True
    except:
        print("Failed to unzip BSP's")
    else:
        print("Successfully installed BSP's")
        with open('./.bsp', 'w') as f:
            f.write('Installation success!')
            f.close()
        output_field.insert(tk.END, "\n\nSuccessfully installed BSP's")
        output_field.insert(tk.END, "\n\n")
        output_field.focus()
        output_field.update()
        output_field.update_idletasks()
        result = True

    if os.path.exists("./.bsp"):
        result = True
    else:
        if (refresh_installation() == 0):
            install_bt.destroy()
    return result

# Read saved configuration
# If a configuration exits, the last
# selected modules are enabled again
def check_config():
    global debug_label
    global debug_on
    check_installation()

    main_window.bind('<Return>', send_serial_cb)

    print("Win width: "+str(main_window.winfo_width()) +
          " height: "+str(main_window.winfo_height()))
    if os.path.exists("./.config"):
        # read last config
        print("Get last config")
        with open('./.config', 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.rstrip()
                print("Got >>" + line + "<<")
                get_last_config(line)
            f.close()

    if debug_on:
        debug_label.config(text = "Debug on")
    else:
        debug_label.config(text = "Debug off")
    return

# Parse configuration line
# Enables the module that is found in the line
# var check_line - a single line of the configuration file
def get_last_config(check_line):
    global selected_board
    global rak1901
    global rak1902
    global rak1903
    global rak1904
    global rak1904_slot
    global rak1905
    global rak1905_slot
    global rak1906
    global rak1921
    global rak12002
    global rak12003
    global rak12008
    global rak12010
    global rak12014
    global rak12014_slot
    global rak12019
    global rak12027
    global rak12037
    global rak12039
    global rak12040
    global rak12047
    global rak12500
    global rak13011
    global rak4631
    global rak3372
    global rak11722
    global debug_on
    if check_line == 'debug':
        debug_on = True
    if check_line == 'RAK1901':
        rak1901 = enable_source(rak1901_bt, "RAK1901_temp.cpp")
    elif check_line == 'RAK1902':
        rak1902 = enable_source(rak1902_bt, "RAK1902_press.cpp")
    elif check_line == "RAK1903":
        rak1903 = enable_source(rak1903_bt, "RAK1903_light.cpp")
    elif check_line == "RAK1904A":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_A.h")
        rak1904_bt.config(text="RAK1904\nAcc (A)")
    elif check_line == "RAK1904B":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_B.h")
        rak1904_bt.config(text="RAK1904\nAcc (B)")
    elif check_line == "RAK1904C":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_C.h")
        rak1904_bt.config(text="RAK1904\nAcc (C)")
    elif check_line == "RAK1904D":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_D.h")
        rak1904_bt.config(text="RAK1904\nAcc (D)")
    elif check_line == "RAK1904E":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_E.h")
        rak1904_bt.config(text="RAK1904\nAcc (E)")
    elif check_line == "RAK1904F":
        rak1904 = enable_source(
            rak1904_bt, "RAK1904_acc.cpp", "RAK1904_acc_S_F.h")
        rak1904_bt.config(text="RAK1904\nAcc (F)")
    elif check_line == "RAK1905A":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_A.h")
        rak1905_bt.config(text="RAK1905\n9DOF (A)")
    elif check_line == "RAK1905B":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_B.h")
        rak1905_bt.config(text="RAK1905\n9DOF (B)")
    elif check_line == "RAK1905C":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_C.h")
        rak1905_bt.config(text="RAK1905\n9DOF (C)")
    elif check_line == "RAK1905D":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_D.h")
        rak1905_bt.config(text="RAK1905\n9DOF (D)")
    elif check_line == "RAK1905E":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_E.h")
        rak1905_bt.config(text="RAK1905\n9DOF (E)")
    elif check_line == "RAK1905F":
        rak1905 = enable_source(
            rak1905_bt, "RAK1905_9dof.cpp", "RAK1905_9dof_S_F.h")
        rak1905_bt.config(text="RAK1905\n9DOF (F)")
    elif check_line == "RAK1906":
        rak1906 = enable_source(rak1906_bt, "RAK1906_env.cpp")
    elif check_line == "RAK1921":
        rak1921 = enable_source(rak1921_bt, "RAK1921_display.cpp")
    elif check_line == "RAK12002":
        rak12002 = enable_source(rak12002_bt, "RAK12002_rtc.cpp")
    elif check_line == "RAK12003":
        rak12003 = enable_source(rak12003_bt, "RAK12003_fir.cpp")
    elif check_line == "RAK12008":
        rak12008 = enable_source(rak12008_bt, "RAK12008_gas.cpp")
    elif check_line == "RAK12010":
        rak12010 = enable_source(rak12010_bt, "RAK12010_light.cpp")
    elif check_line == "RAK12014A":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_A.h")
        rak12014_bt.config(text="RAK12014\nToF (A)")
    elif check_line == "RAK12014B":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_B.h")
        rak12014_bt.config(text="RAK12014\nToF (B)")
    elif check_line == "RAK12014C":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_C.h")
        rak12014_bt.config(text="RAK12014\nToF (C)")
    elif check_line == "RAK12014D":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_D.h")
        rak12014_bt.config(text="RAK12014\nToF (D)")
    elif check_line == "RAK12014E":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_E.h")
        rak12014_bt.config(text="RAK12014\nToF (E)")
    elif check_line == "RAK12014F":
        rak12014 = enable_source(
            rak12014_bt, "RAK12014_tof.cpp", "RAK12014_tof_S_F.h")
        rak12014_bt.config(text="RAK12014\nToF (F)")
    elif check_line == "RAK12019":
        rak12019 = enable_source(rak12019_bt, "RAK12019_uv.cpp")
    elif check_line == "RAK12027A":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_A.h")
        rak12027_bt.config(text="RAK12027\nToF (A)")
    elif check_line == "RAK12027B":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_B.h")
        rak12027_bt.config(text="RAK12027\nToF (B)")
    elif check_line == "RAK12027C":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_C.h")
        rak12027_bt.config(text="RAK12027\nToF (C)")
    elif check_line == "RAK12027D":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_D.h")
        rak12027_bt.config(text="RAK12027\nToF (D)")
    elif check_line == "RAK12027E":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_E.h")
        rak12027_bt.config(text="RAK12027\nToF (E)")
    elif check_line == "RAK12027F":
        rak12027 = enable_source(
            rak12027_bt, "RAK12027_seismic.cpp", "RAK12027_seismic_S_F.h")
        rak12027_bt.config(text="RAK12027\nToF (F)")
    elif check_line == "RAK12037":
        rak12037 = enable_source(rak12037_bt, "RAK12037_co2.cpp")
    elif check_line == "RAK12040":
        rak12040 = enable_source(rak12040_bt, "RAK12040_temp_arr.cpp")
    elif check_line == "RAK12047":
        rak12047 = enable_source(rak12047_bt, "RAK12047_voc.cpp")
    elif check_line == "RAK12500":
        rak12500 = enable_source(rak12500_bt, "RAK12500_gnss.cpp")
    elif check_line == "RAK13011A":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_A.h")
        rak13011_bt.config(text="RAK13011\nSwitch (A)")
    elif check_line == "RAK13011B":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_B.h")
        rak13011_bt.config(text="RAK13011\nSwitch (B)")
    elif check_line == "RAK13011C":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_C.h")
        rak13011_bt.config(text="RAK13011\nSwitch (C)")
    elif check_line == "RAK13011D":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_D.h")
        rak13011_bt.config(text="RAK13011\nSwitch (D)")
    elif check_line == "RAK13011E":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_E.h")
        rak13011_bt.config(text="RAK13011\nSwitch (E)")
    elif check_line == "RAK13011F":
        rak13011 = enable_source(
            rak13011_bt, "RAK13011_switch.cpp", "RAK13011_switch_S_F.h")
        rak13011_bt.config(text="RAK13011\nSwitch (F)")
    elif check_line == "RAK3372":
        selected_board = rak3372_board
        rak3372 = True
        rak4631 = False
        rak11722 = False
        selected_board = rak3372_board
        rak3372_bt.config(background="#00FF00")
        rak4631_bt.config(background="#FA8072")
        rak11722_bt.config(background="#FA8072")
        module_label.config(text="Core: RAK3372")
    elif check_line == "RAK4631":
        selected_board = rak4631_board
        rak4631 = True
        rak3372 = False
        rak11722 = False
        selected_board = rak4631_board
        rak4631_bt.config(background="#00FF00")
        rak3372_bt.config(background="#FA8072")
        rak11722_bt.config(background="#FA8072")
        module_label.config(text="Core: RAK4631")
    elif check_line == "RAK11722":
        selected_board = rak11722_board
        rak4631 = False
        rak3372 = False
        rak11722 = True
        selected_board = rak11722_board
        rak4631_bt.config(background="#FA8072")
        rak3372_bt.config(background="#FA8072")
        rak11722_bt.config(background="#00FF00")
        module_label.config(text="Core: RAK11722")

    main_window.update_idletasks()

    return

# Callback on window close
def on_closing():
    global rec_reader

    close_delayed = False
    main_window.unbind('<Return>')

    try:
        if serialPortManager.isRunning:
            serialPortManager.stop()
            print("Serial thread stopped")
            close_delayed = True
    except:
        print("Closing thread failed")
        close_delayed = True

    # while not serialPortManager.thread_stopped:
    #     time.sleep(1)

    if rec_reader is not None:
        print("Stopped rec_reader")
        main_window.after_cancel(rec_reader)
        close_delayed = True

    if close_delayed:
        main_window.after(15, final_close)
        return

    # Serial Terminal was already closed, can exit immediately
    final_close()

# Final close, called with delay if Serial Terminal was still open
# Saves the currently selected modules into configuration file
def final_close():
    global debug_on

    print("Saving config")

    # Remove saved config
    if os.path.exists("./.config"):
        os.remove("./.config")
    # Save current config
    f = open('./.config', 'w')
    if debug_on:
        f.write("debug\n")
    if rak1901:
        f.write("RAK1901\n")
    if rak1902:
        f.write("RAK1902\n")
    if rak1903:
        f.write("RAK1903\n")
    if rak1904:
        f.write("RAK1904"+rak1904_slot+"\n")
    if rak1905:
        f.write("RAK1905"+rak1905_slot+"\n")
    if rak1906:
        f.write("RAK1906\n")
    if rak1921:
        f.write("RAK1921\n")
    if rak12002:
        f.write("RAK12002\n")
    if rak12003:
        f.write("RAK12003\n")
    if rak12008:
        f.write("RAK12008\n")
    if rak12010:
        f.write("RAK12010\n")
    if rak12014:
        f.write("RAK12014"+rak12014_slot+"\n")
    if rak12019:
        f.write("RAK12019\n")
    if rak12027:
        f.write("RAK12027"+rak12027_slot+"\n")
    if rak12037:
        f.write("RAK12037\n")
    if rak12039:
        f.write("RAK12039\n")
    if rak12040:
        f.write("RAK12040\n")
    if rak12047:
        f.write("RAK12047\n")
    if rak12500:
        f.write("RAK12500\n")
    if rak13011:
        f.write("RAK13011"+rak13011_slot+"\n")
    if rak3372:
        f.write("RAK3372\n")
    if rak4631:
        f.write("RAK4631\n")
    if rak11722:
        f.write("RAK11722\n")

    print("Done saving config")
    f.flush()
    print("Done flushing")
    f.close()
    print("Done file close")
    time.sleep(1)
    print("Done sleeping")
    main_window.quit()
    print("Done quitting")
    main_window.destroy()
    print("Done closing window")
    return

# Update Serial terminal text box
# Restarts itself in guiUpdateInterval milliseconds
def recursive_update_textbox():
    global rec_reader
    serialPortBuffer = serialPortManager.read_buffer()
    # Update textbox in a kind of recursive function using Tkinter after() method
    serial_box.config(state=tk.NORMAL)
    serial_box.insert(tk.END, serialPortBuffer.decode("ascii"))
    # autoscroll to the bottom
    serial_box.see(tk.END)
    serial_box.config(state=tk.DISABLED)
    # Recursively call recursive_update_textbox using Tkinter after() method
    if serialPortManager.isRunning:
        rec_reader = main_window.after(guiUpdateInterval, recursive_update_textbox)
    else:
        rec_reader = None
        print("Recursive reader closed")


# ==================================================
# Main
# ==================================================
main_window = tk.Tk()

main_window.title("RUI3-Modular IDE")

# Set the weight of each column and row equally
for column in range(14):
    main_window.grid_columnconfigure(column, weight=1)
for row in range(14):
    main_window.grid_rowconfigure(row, weight=4)
main_window.grid_rowconfigure(11, weight=1)

# Add the explanation texts
modules_label1 = tk.Label(text="Select required Modules")
modules_label1.grid(row=1, column=0, columnspan=3)
modules_label2 = tk.Label(text="Core")
modules_label2.grid(row=1, column=3)

use_row = 2
use_column = 0

# Add the module buttons column 1
rak1901_bt = tk.Button(text="RAK1901\nT&H", background="#FA8072", command=rak1901_cb)
rak1901_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1902_bt = tk.Button(text="RAK1902\nBaro", background="#FA8072", command=rak1902_cb)
rak1902_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1903_bt = tk.Button(text="RAK1903\nLight", background="#FA8072", command=rak1903_cb)
rak1903_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1904_bt = tk.Button(text="RAK1904\nAcc", background="#FA8072", command=rak1904_cb)
rak1904_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1905_bt = tk.Button(text="RAK1905\n9DOF", background="#FA8072", command=rak1905_cb)
rak1905_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1906_bt = tk.Button(text="RAK1906\nEnv", background="#FA8072", command=rak1906_cb)
rak1906_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak1921_bt = tk.Button(text="RAK1921\nOLED", background="#FA8072", command=rak1921_cb)
rak1921_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')

use_row = 2
use_column = use_column + 1

# Add the module buttons column 2
rak12002_bt = tk.Button(text="RAK12002\nRTC", background="#FA8072", command=rak12002_cb)
rak12002_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12003_bt = tk.Button(text="RAK12003\nFIR", background="#FA8072", command=rak12003_cb)
rak12003_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12008_bt = tk.Button(text="RAK12008\nCO2", background="#FA8072", command=rak12008_cb)
rak12008_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12010_bt = tk.Button(text="RAK12010\nLight", background="#FA8072", command=rak12010_cb)
rak12010_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12014_bt = tk.Button(text="RAK12014\nToF", background="#FA8072", command=rak12014_cb)
rak12014_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12019_bt = tk.Button(text="RAK12019\nUV", background="#FA8072", command=rak12019_cb)
rak12019_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12027_bt = tk.Button(text="RAK12027\nQuake",
                        background="#FA8072", command=rak12027_cb)
rak12027_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')

use_row = 2
use_column = use_column + 1

# Add the module buttons column 3
rak12037_bt = tk.Button(text="RAK12037\nCO2", background="#FA8072", command=rak12037_cb)
rak12037_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12039_bt = tk.Button(text="RAK12039\nPM",
                        background="#FA8072", command=rak12039_cb)
rak12039_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12040_bt = tk.Button(text="RAK12040\nTemp Arr",
                        background="#FA8072", command=rak12040_cb)
rak12040_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12047_bt = tk.Button(text="RAK12047\nVOC", background="#FA8072", command=rak12047_cb)
rak12047_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak12500_bt = tk.Button(text="RAK12500\nGNSS",
                        background="#FA8072", command=rak12500_cb)
rak12500_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak13011_bt = tk.Button(text="RAK13011\nSwitch",
                        background="#FA8072", command=rak13011_cb)
rak13011_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')

use_row = 2
use_column = use_column + 1

# Add the core module selection buttons
rak3372_bt = tk.Button(text="RAK3372", background="#FA8072", command=rak3372_cb)
rak3372_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak4631_bt = tk.Button(text="RAK4631", background="#FA8072", command=rak4631_cb)
rak4631_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
use_row = use_row + 1
rak11722_bt = tk.Button(text="RAK11722", background="#FA8072", command=rak11722_cb)
rak11722_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
# rak11722_bt["state"] = "disable"

result_bt = tk.Button(text="Result", background="#1E90FF")
result_bt.grid(row=0, column=8, padx=5, pady=5, sticky='nsew')

# Detect which OS we are running on
if platform == "linux" or platform == "linux2":
    print("Detected Linux")
    arduino_cli_cmd = "./arduino-cli_0.29.0_Linux_64bit/arduino-cli"
elif platform == "darwin":
    print("Detected MacOS")
    arduino_cli_cmd = "./arduino-cli_0.29.0_macOS_64bit/arduino-cli"
elif platform == "win32":
    print("Detected Windows")
    arduino_cli_cmd = "./arduino-cli_0.27.1_Windows_64bit/arduino-cli.exe"
else:
    print("OS detection failed")

# Check if the BSP's are already installed
if not os.path.exists("./.bsp"):
    installation_complete = False
else:
    installation_complete = True

# Add a button to connect to Serial
port_connect_bt = tk.Button(
    text="Connect", background="#1E90FF", command=connect_cb)
port_connect_bt.grid(row=11, column=4)

# Prepare Serial Terminal
serialPortManager = SerialPortManager(115200, port_connect_bt)
serial_box = scrolledtext.ScrolledText(
    main_window, wrap=tk.WORD, font="TkSmallCaptionFont", background="#FFDEAD", state=tk.DISABLED)
serial_box.grid(row=1, column=4, rowspan=10, columnspan=12, sticky='nsew')

# Create input box for Serial Terminal
serial_send_buffer = tk.StringVar()
serial_send_eb = tk.Entry(main_window, textvariable=serial_send_buffer)
serial_send_eb.grid(row=11, column=5, columnspan=11, sticky='nsew')

# Add clear serial log button
# Add a button to connect to Serial
clear_log_bt = tk.Button(text="Clear", background="#1E90FF", command=clear_cb)
clear_log_bt.grid(row=11, column=15)

# Add the widget for the log output
output_field = tk.scrolledtext.ScrolledText(
    main_window, wrap=tk.WORD, font="TkSmallCaptionFont", background="#ADD8E6", state=tk.DISABLED, height=10)
output_field.grid(row=12, column=0, sticky='nsew', columnspan=20)

# Add a status row at the bottom
module_label = tk.Label(text="Core: ???")
module_label.grid(row=15, column=0)
port_label = tk.Label(text="Port: ???")
port_label.grid(row=15, column=3)
debug_label = tk.Label(text="Debug: ???")
debug_label.grid(row=15, column=5)

# Cleanup the project folder
for file_name in listdir("./RUI3-Modular"):
    if file_name.startswith('RAK'):
        os.remove("./RUI3-Modular/" + file_name)

# Add common AT commands
at_query_bt = tk.Button(text="?", background="#1E90FF",
                        command=lambda: at_command_selected(0))
at_query_bt.grid(row=0, column=21, sticky='nsew')
at_boot_bt = tk.Button(text="Boot", background="#1E90FF",
                       command=lambda: at_command_selected(1))
at_boot_bt.grid(row=1, column=21, sticky='nsew')
at_z_bt = tk.Button(text="Reset", background="#1E90FF",
                    command=lambda: at_command_selected(2))
at_z_bt.grid(row=2, column=21, sticky='nsew')
at_bat_bt = tk.Button(text="Batt", background="#1E90FF",
                      command=lambda: at_command_selected(3))
at_bat_bt.grid(row=3, column=21, sticky='nsew')
at_ver_bt = tk.Button(text="Ver", background="#1E90FF",
                      command=lambda: at_command_selected(4))
at_ver_bt.grid(row=4, column=21, sticky='nsew')
at_lpm_bt = tk.Button(text="LPM", background="#1E90FF",
                      command=lambda: at_command_selected(5))
at_lpm_bt.grid(row=5, column=21, sticky='nsew')
at_njm_bt = tk.Button(text="NJM", background="#1E90FF",
                      command=lambda: at_command_selected(10))
at_njm_bt.grid(row=6, column=21, sticky='nsew')
at_cfm_bt = tk.Button(text="CFM", background="#1E90FF",
                      command=lambda: at_command_selected(11))
at_cfm_bt.grid(row=7, column=21, sticky='nsew')
at_join_bt = tk.Button(text="JOIN", background="#1E90FF",
                       command=lambda: at_command_selected(9))
at_join_bt.grid(row=8, column=21, sticky='nsew')
at_deveui_bt = tk.Button(text="DEV\nEUI", background="#1E90FF",
                         command=lambda: at_command_selected(8))
at_deveui_bt.grid(row=0, column=22, sticky='nsew')
at_appeui_bt = tk.Button(text="APP\nEUI", background="#1E90FF",
                         command=lambda: at_command_selected(6))
at_appeui_bt.grid(row=1, column=22, sticky='nsew')
at_appkey_bt = tk.Button(text="APP\nKey", background="#1E90FF",
                         command=lambda: at_command_selected(7))
at_appkey_bt.grid(row=2, column=22, sticky='nsew')
at_dr_bt = tk.Button(text="DR", background="#1E90FF",
                     command=lambda: at_command_selected(13))
at_dr_bt.grid(row=3, column=22, sticky='nsew')
at_band_bt = tk.Button(text="BAND", background="#1E90FF",
                       command=lambda: at_command_selected(14))
at_band_bt.grid(row=4, column=22, sticky='nsew')
at_nwm_bt = tk.Button(text="NWM", background="#1E90FF",
                      command=lambda: at_command_selected(15))
at_nwm_bt.grid(row=5, column=22, sticky='nsew')
at_status_bt = tk.Button(text="STATUS", background="#1E90FF",
                         command=lambda: at_command_selected(16))
at_status_bt.grid(row=6, column=22, sticky='nsew')
at_int_bt = tk.Button(text="SEND\nINT", background="#1E90FF",
                      command=lambda: at_command_selected(17))
at_int_bt.grid(row=7, column=22, sticky='nsew')

# Setup the menu
options_menu = tk.Button(text="Options", background="#CDB79E", command=options_menu_cb)
options_menu.grid(row=0, column=0, sticky='nsew')
port_menu = tk.Button(text="Select Port", background="#CDB79E", command=select_port)
port_menu.grid(row=0, column=2, sticky='nsew')
verify_menu = tk.Button(text="Verify", background="#CDB79E", command=verify_cb)
verify_menu.grid(row=0, column=4, sticky='nsew')
upload_menu = tk.Button(text="Upload", background="#CDB79E", command=upload_cb)
upload_menu.grid(row=0, column=5, sticky='nsew')
clean_menu = tk.Button(text="Clean", background="#CDB79E", command=clean_build_cb)
clean_menu.grid(row=0, column=6, sticky='nsew')

# Setup the callback when the window close button is pushed
main_window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the configuration check after the main window is openend
main_window.after(250, check_config)

# Set the Window icon
main_window.iconbitmap("./rak-blue-dark-whirl.ico")

# Start the main window loop
main_window.mainloop()
