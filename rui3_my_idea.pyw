import tkinter as tk
from tkinter import scrolledtext
import tkinter.ttk as ttk
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
import queue
import threading

import rui3_my_serial
from rui3_my_serial import *
from rui3_module_callbacks import *
from rui3_message_box import *

if platform == "darwin":
    from tkmacosx import Button

if platform == "darwin":
    fg_ena = "#006400"
    fg_dis = "#FF0000"
else:
    fg_ena = "#000000"
    fg_dis = "#000000"


# Variables

# All AT commands
most_used_commands = ['AT?', 'AT+BOOT', 'ATZ', 'AT+BAT=?', 'AT+VER=?', 'AT+LPM', 'AT+APPEUI', 'AT+APPKEY',
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

rec_reader = None

cmd_count = 0
cmd_ptr = 1
last_commands = queue.Queue(50)

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
    global upload_port

    found_ports = []

    for n, (port, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports()), 1):
        print('--- {:2}: {:20} {}\n'.format(n, port, desc))
        found_ports.append(port)

    for x in range(len(found_ports)):
        print(found_ports[x],)

    if (len(found_ports) == 1):
        print("Only one port found, autoselect!")
        upload_port = found_ports[0]
        port_label.config(text="Port: " + upload_port)

        print("Selected: ", upload_port)

        serialPortManager.set_name(upload_port)
        serialPortManager.set_baud(115200)

        open_info_box("Auto selected COM port: " +
                      upload_port, "#00FF00", port_menu)
        
        return

    get_port_window = tk.Toplevel(main_window)
    menu_x = port_menu.winfo_rootx()
    menu_y = port_menu.winfo_rooty()
    get_port_window.geometry("+{}+{}".format(menu_x, menu_y))

    get_port_window.config(background="#FFDEAD")

    if (len(found_ports) != 0):
        port_label_win = tk.Label(get_port_window, text="Select a port")
    else:
        port_label_win = tk.Label(get_port_window, text="No port found")
    port_label_win.pack()

    get_port_listbox = tk.Listbox(get_port_window, selectmode=tk.SINGLE)
    for x in range(len(found_ports)):
        get_port_listbox.insert(tk.END, found_ports[x])
    get_port_listbox.bind('<<ListboxSelect>>', select_port_selected)
    get_port_listbox.pack()

    return

# Manually connect/disconnect Serial Terminal
def connect_cb():
    if (upload_port == ""):
        rui3_message(main_window, "Select an upload port first")
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
    global cmd_count
    global cmd_ptr
    buffer = serial_send_buffer.get()
    if serialPortManager.isRunning:
        print("Sending >>" + buffer + "<<")
        serialPortManager.send_buffer(buffer)
        add_cmd = True
        # Check if command queue has entries
        if (last_commands.empty() == False):
            # Check if last command is from buffer
            if (buffer == last_commands.queue[0]):
                add_cmd = False
        if (add_cmd == True):
            cmd_count = cmd_count + 1
            if cmd_count == 51:
                cmd_count = 50
                last_commands.get(49)
            last_commands.put(buffer)

    cmd_ptr = last_commands.qsize()
    serial_send_eb.delete(0, "end")
    serial_send_eb.update()

    if (last_commands.empty() == False):
        for idx in range(last_commands.qsize()):
            print(last_commands.queue[idx])

def command_list_down(self):
    global cmd_count
    global cmd_ptr
    print("UP-Arrow cmd_ptr = " + str(cmd_ptr))
    if (cmd_count > 0):
        buffer = last_commands.queue[cmd_ptr-1]
        if (cmd_ptr < last_commands.qsize()):
            cmd_ptr = cmd_ptr + 1
        else:
            cmd_ptr = 1
        serial_send_eb.delete(0, "end")
        serial_send_eb.insert(tk.END, buffer)
        serial_send_eb.update()
        serial_send_eb.focus_set()
    return


def command_list_up(self):
    global cmd_count
    global cmd_ptr
    print("DOWN-Arrow cmd_ptr = " + str(cmd_ptr))
    if (cmd_count > 0):
        buffer = last_commands.queue[cmd_ptr-1]
        if (cmd_ptr > 1):
            cmd_ptr = cmd_ptr - 1
        else:
            cmd_ptr = last_commands.qsize()
        serial_send_eb.delete(0, "end")
        serial_send_eb.insert(tk.END, buffer)
        serial_send_eb.update()
        serial_send_eb.focus_set()
    return

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

# Switch debug on/off
def toggle_debug():
    global debug_label_bt
    if get_debug():
        set_debug(False)
        print("Disable debug")
        debug_label_bt.config(text="Debug off", background="#FA8072", fg=fg_dis)
    else:
        set_debug(True)
        print("Enable Debug")
        debug_label_bt.config(text="Debug on", background="#00FF00", fg=fg_ena)

# Switch autoconfig DR on/off
def toggle_auto_dr():
    global auto_dr_label_bt
    if get_auto_dr():
        set_auto_dr(False)
        print("Disable autoconfig DR")
        auto_dr_label_bt.config(text="Auto DR off", background="#FA8072", fg=fg_dis)
    else:
        set_auto_dr(True)
        print("Enable autoconfig DR")
        auto_dr_label_bt.config(text="Auto DR on", background="#00FF00", fg=fg_ena)

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
    if (platform == "win32"):
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
    else:
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)

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

    return result

# Start Arduino-CLI to verify the code
# The result is shown in the result button result_bt
def verify_cb():
    selected_board = get_selected_board()

    if (not installation_complete):
        rui3_message(main_window, "Installation required first")
        return
    if (selected_board == ""):
        rui3_message(main_window, "Select a board first")
        return
    if (is_RAK11722()):
        if not os.path.exists("./Arduino15/packages/rak_rui/hardware/apollo3"):
            rui3_message(
                main_window, "RAK11720 BSP is not installed. It requires manual installation! Please contact author of this application")
            return

    open_busy_box("Verifying code\nPlease wait")

    if not os.path.exists("./RUI3-Modular/build"):
        os.mkdir("./RUI3-Modular/build")
    if not os.path.exists("./RUI3-Modular/cache"):
        os.mkdir("./RUI3-Modular/cache")
    if not os.path.exists("./RUI3-Modular/flash-files"):
        os.mkdir("./RUI3-Modular/flash-files")

    verify_menu.config(text="busy", background="#FA8072")
    result_bt.config(background="#1E90FF", text="Result")

    if get_debug():
        if get_auto_dr():
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=1 -DAUTO_DR=1", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
        else:
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=1 -DAUTO_DR=0", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
    else:
        if get_auto_dr():
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=0 -DAUTO_DR=1", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
        else:
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=0 -DAUTO_DR=0", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]

    headline = "Verify, this can take some time, be patient"
    return_code = ext_app_to_log(compile_command, headline, True)

    if (return_code == 0):
        print("Verify successful")
        open_info_box("Verify successful", "#00FF00", verify_menu)
        result_bt.config(background="#00FF00", text="SUCCESS")
    else:
        print("Verify failed")
        open_info_box("Verify failed", "#F00F00", verify_menu)
        result_bt.config(background="#FA8072", text="FAIL")

    verify_menu.config(text="Verify", background="#CDB79E")

    close_busy_box()
    return


# Start Arduino-CLI to compile and download the code
# The result is shown in the result button result_bt
def upload_cb():
    global rak4631
    global rak3372
    global rak11722
    selected_board = get_selected_board()

    if (not installation_complete):
        rui3_message(main_window, "Installation required first")
        return
    if (selected_board == ""):
        rui3_message(main_window, "Select a board first")
        return
    if (upload_port == ""):
        rui3_message(main_window, "Select an upload port first")
        return
    if (is_RAK11722()):
        if not os.path.exists("./Arduino15/packages/rak_rui/hardware/apollo3"):
            rui3_message(
                main_window, "RAK11720 BSP is not installed. It requires manual installation! Please contact author of this application")
            return

    open_busy_box("Compiling and Uploading\nPlease wait")

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

    if get_debug():
        if get_auto_dr():
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=1 -DAUTO_DR=1", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--upload", "-p", upload_port, "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
        else:
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=1 -DAUTO_DR=0", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--upload", "-p", upload_port, "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
    else:
        if get_auto_dr():
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=0 -DAUTO_DR=1", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--upload", "-p", upload_port, "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]
        else:
            compile_command = [arduino_cli_cmd,  "compile", "-b", selected_board, "--build-property", "compiler.cpp.extra_flags=-DMY_DEBUG=0 -DAUTO_DR=0", "--output-dir", "./RUI3-Modular/flash-files",
                               "--build-path", "./RUI3-Modular/build", "--build-cache-path", "./RUI3-Modular/cache", "--upload", "-p", upload_port, "--no-color", "--verbose", "--library", "./RUI3-Modular/libraries", "./RUI3-Modular/RUI3-Modular.ino"]

    headline = "Upload to device, this can take some time, be patient"
    return_code = ext_app_to_log(compile_command, headline, True)

    port_success = True

    if (is_RAK4631()):
        retry_cnt = 0
        wait_port = True
        port_success = False
        print("Waiting for the RAK4630 USB port")
        while wait_port:
            time.sleep(2.5)
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
    else:
        if (is_RAK3372()):
            print("RAK3372, no wait")
        elif (is_RAK11722):
            print("RAK11722, no wait")
        else:
            print("Unknown Core")

    if (return_code == 0):
        print("Upload successful")
        open_info_box("Upload successful", "#00FF00", upload_menu)

        result_bt.config(background="#00FF00", text="SUCCESS")
        if port_success:
            serialPortManager.start()
            # Start updating textbox in GUI
            recursive_update_textbox()
            port_connect_bt.config(text="Disconnect", background="#00FF00")
    else:
        print("Upload failed")
        open_info_box("Upload failed", "#FF0000", upload_menu)
        result_bt.config(background="#FA8072", text="FAIL")

    upload_menu.config(text="Upload", background="#CDB79E")

    close_busy_box()
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

    print("Refresh Installation started")
    open_busy_box("Installing BSP\nPlease wait")

    compile_command = [arduino_cli_cmd, "config", "delete", "board_manager.additional_urls"]
    headline = "Cleaning up additional BSP URL's"
    return_code1 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)

    compile_command = [
            arduino_cli_cmd, "config",  "add", "board_manager.additional_urls", "https://raw.githubusercontent.com/beegee-tokyo/test/main/beegee-patch-rui3.json"]

    headline = "Installing additional BSP URL's"
    return_code1 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)

    compile_command = [arduino_cli_cmd, "core",  "update-index"]
    headline = "Updating BSP's index"
    return_code2 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)

    compile_command = [arduino_cli_cmd, "core", "install", "rak_rui:nrf52"]
    headline = "Installing RAK4630 BSP, this can take quite some time"
    return_code3 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)

    compile_command = [arduino_cli_cmd, "core", "install", "rak_rui:stm32"]
    headline = "Installing RAK3372 BSP, this can take quite some time"
    return_code4 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)

    # RAK11722 BSP is not yet released, no refresh possible
    #
    # headline = "Installing RAK11722 BSP, this can take quite some time"
    compile_command = [arduino_cli_cmd, "core", "install", "rak_rui:apollo3"]
    return_code5 = ext_app_to_log(compile_command, headline, False)
    time.sleep(1)
    # output_field.config(state=tk.NORMAL)
    # output_field.insert(tk.END, "RAK11720 is not yet released, no refresh possible\n\n")
    # output_field.insert(tk.END, "\n\n")

    result = False
    if (return_code1 == 0) and (return_code2 == 0) and (return_code3 == 0) and (return_code4 == 0):
        with open('./.bsp', 'w') as f:
            f.write('Installation success!')
            f.close()
        installation_complete = True
        result = True
        output_field.insert(tk.END, "BSP UPDATE SUCCESS")
    else:
        output_field.insert(tk.END, "BSP UPDATE FAILED")

    output_field.focus()
    output_field.update()
    output_field.update_idletasks()
    output_field.config(state=tk.DISABLED)

    close_busy_box()
    return result

# Check if BSP's are already installed
# If not installed it starts refresh_installation
# to install all required BSP's
def check_installation():
    print("Checking installation")

    result = True
    if not os.path.exists("Arduino15"):
        print("Arduino15 folder doesn't exist")
        try:
                output_field.config(state=tk.NORMAL)
                output_field.delete("1.0", "end")
                output_field.update()
                output_field.insert(tk.END, "Installing the BSP's, be patient\n")
                output_field.focus()
                output_field.update()
                output_field.update_idletasks()

                file_exists = False
                bsp_file = ""
                if platform == "linux" or platform == "linux2":
                    if os.path.exists("Arduino15_linux.zip"):
                        print("Extracting Linux")
                        bsp_file = "Arduino15_linux.zip"
                        file_exists = True
                    else:
                        print("Arduino15 ZIP file doesn't exist")
                        print("Try to download the BSP's from the cloud")
                        result = refresh_installation()
                elif platform == "darwin":
                    if os.path.exists("Arduino15_macos.zip"):
                        print("Extracting Linux")
                        bsp_file = "Arduino15_macos.zip"
                        file_exists = True
                    else:
                        print("Arduino15 ZIP file doesn't exist")
                        print("Try to download the BSP's from the cloud")
                        result = refresh_installation()
                elif platform == "win32":
                    if os.path.exists("Arduino15.zip"):
                        print("Extracting Linux")
                        bsp_file = "Arduino15.zip"
                        file_exists = True
                    else:
                        print("Arduino15 ZIP file doesn't exist")
                        print("Try to download the BSP's from the cloud")
                        result = refresh_installation()
                else:
                    print("OS detection failed")

                if bsp_file == "":
                    result = False
                else:
                    open_busy_box("Installing BSP\nPlease wait")
                    with zipfile.ZipFile(bsp_file, 'r') as zip:
                        zip.extractall('.')
                    result = True
                    close_busy_box()
        except:
                print("Failed to unzip BSP's")
                result = False
        else:
            print("Successfully installed BSP's")
            with open('./.bsp', 'w') as f:
                f.write('Installation success!')
                f.close()
            output_field.insert(tk.END, "\n\nSuccessfully installed BSP's")
            output_field.focus()
            output_field.update()
            output_field.update_idletasks()
            result = True
    else:
        print("BSP's already installed")
        result = True

    return result

# Read saved configuration
# If a configuration exits, the last
# selected modules are enabled again
def check_config():
    global debug_label_bt
    check_installation()

    main_window.bind('<Return>', send_serial_cb)
    main_window.bind('<Up>', command_list_up)
    main_window.bind('<Down>', command_list_down)

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
                get_last_config(line, main_window)
            f.close()

    if get_debug():
        print("Set label to Debug on")
        debug_label_bt.config(text="Debug on", background="#00FF00")
    else:
        print("Set label to Debug off")
        debug_label_bt.config(text="Debug off", background="#FA8072")

    if get_auto_dr():
        print("Set label to autoconf DR on")
        auto_dr_label_bt.config(text="Auto DR on", background="#00FF00")
    else:
        print("Set label to autoconf DR off")
        auto_dr_label_bt.config(text="Auto DR off", background="#FA8072")
    return

# Callback on window close
def on_closing():
    global rec_reader
    global this_msg_box

    close_delayed = False
    main_window.unbind('<Return>')

    try:
        if serialPortManager.isRunning:
            serialPortManager.stop()
            print("Stopping Serial thread")
            close_delayed = True
            time.sleep(1)
            open_info_box("Serial Port still open, wait a moment","#FF0000", upload_menu)
            main_window.wait_window(this_msg_box)
    except:
        print("Closing thread failed")
        close_delayed = True

    # Save current configuration
    save_config(get_debug())

    main_window.quit()
    # print("Done quitting")
    main_window.destroy()
    print("Done closing window")
    exit()


# Update Serial terminal text box
# Restarts itself in guiUpdateInterval milliseconds
def recursive_update_textbox():
    global rec_reader

    # Recursively call recursive_update_textbox using Tkinter after() method
    if serialPortManager.isRunning:
        # Get last data from the buffer
        serialPortBuffer = serialPortManager.read_buffer()
        serial_box.config(state=tk.NORMAL)
        serial_box.insert(tk.END, serialPortBuffer.decode("ascii"))
        # autoscroll to the bottom
        serial_box.see(tk.END)
        serial_box.config(state=tk.DISABLED)
        rec_reader = main_window.after(
            guiUpdateInterval, recursive_update_textbox)
    else:
        rec_reader = None
        print("Recursive reader closed")

def open_info_box(text_to_show, background_color, anchor, wait =  False):
    global this_msg_box

    this_msg_box = tk.Toplevel(main_window)
    this_msg_box.config(background=background_color)
    menu_x = anchor.winfo_rootx()
    menu_x = menu_x + anchor.winfo_width()
    menu_y = anchor.winfo_rooty()
    menu_y = menu_y + anchor.winfo_height()
    this_msg_box.geometry("+{}+{}".format(menu_x, menu_y))
    port_label_win = tk.Label(this_msg_box, text="\n\n\n"+text_to_show+"\n\n\n")
    port_label_win.config(background=background_color)
    port_label_win.pack()
    main_window.after(3000,close_info_box)

def close_info_box():
    global this_msg_box
    this_msg_box.destroy()

def open_busy_box(text_to_show):
    global busy_box

    busy_box = tk.Text(main_window)
    busy_box.config(background="#AAAAAA", font='bold')
    menu_x = 0
    menu_y = 0
    width_x = main_window.winfo_width()
    height_y = clear_log_bt.winfo_rooty() - main_window.winfo_rooty() + clear_log_bt.winfo_height()


    print("clear_log x: " + str(clear_log_bt.winfo_rootx()) +
          " y: " + str(clear_log_bt.winfo_rooty()))
    print ("x: " + str(menu_x) + " y: "+ str(menu_y))
    print("width: " + str(width_x) + " height: " + str(height_y))
    busy_box.place(x=0, y=0, height=height_y, width=width_x)
    busy_box.insert("1.0", "\n\n\n"+text_to_show+"\n\n\n")
    busy_box.tag_configure("tag_name", justify='center')
    busy_box.tag_add("tag_name", "1.0", "end")
    busy_box.update()
    busy_box.update_idletasks()


def close_busy_box():
    global busy_box
    busy_box.destroy()

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

# Initialize module buttons
init_buttons(main_window)

result_bt = tk.Button(text="Result", background="#1E90FF")
result_bt.grid(row=0, column=8, padx=5, pady=5, sticky='nsew')

ico_file = "./rak-blue-dark-whirl.ico"

# Detect which OS we are running on
if platform == "linux" or platform == "linux2":
    print("Detected Linux")
    arduino_cli_cmd = "./arduino-cli_0.29.0_Linux_64bit/arduino-cli"
    ico_file = "@./rak-blue-dark-whirl.xbm"
elif platform == "darwin":
    print("Detected MacOS")
    arduino_cli_cmd = "./arduino-cli_0.29.0_macOS_64bit/arduino-cli"
    ico_file = "@./rak-blue-dark-whirl.icns"
elif platform == "win32":
    print("Detected Windows")
    arduino_cli_cmd = "./arduino-cli_0.27.1_Windows_64bit/arduino-cli.exe"
else:
    print("OS detection failed")

# Setup the menu
# add button for re-installation
if not os.path.exists("./.bsp"):
    install_bt = tk.Button(text="INSTALL\nREQUIRED!", background="#FA8072", command=check_installation)
    install_bt.grid(row=0, column=0, sticky='nsew')
    installation_complete = False
else:
    install_bt = tk.Button(text="Refresh\nInstallation!", background="#CDB79E", command=refresh_installation)
    install_bt.grid(row=0, column=0, sticky='nsew')
    installation_complete = True
# add button to select USB port
port_menu = tk.Button(text="Select Port", background="#CDB79E", command=select_port)
port_menu.grid(row=0, column=2, sticky='nsew')
# add button to verify code
verify_menu = tk.Button(text="Verify", background="#CDB79E", command=verify_cb)
verify_menu.grid(row=0, column=4, sticky='nsew')
# add button to upload code
upload_menu = tk.Button(text="Upload", background="#CDB79E", command=upload_cb)
upload_menu.grid(row=0, column=5, sticky='nsew')
# add button to clean build folders
clean_menu = tk.Button(text="Clean", background="#CDB79E", command=clean_build_cb)
clean_menu.grid(row=0, column=6, sticky='nsew')

# Add a button to connect to Serial
port_connect_bt = tk.Button(
    text="Connect", background="#1E90FF", command=connect_cb)
port_connect_bt.grid(row=11, column=4)

# Prepare Serial Terminal
serial_box = scrolledtext.ScrolledText(
    main_window, wrap=tk.WORD, font="TkSmallCaptionFont", background="#FFDEAD", state=tk.DISABLED)
serial_box.grid(row=1, column=4, rowspan=10, columnspan=12, sticky='nsew')

# Create input box for Serial Terminal
serial_send_buffer = tk.StringVar()
serial_send_eb = tk.Entry(main_window, textvariable=serial_send_buffer)
serial_send_eb.grid(row=11, column=5, columnspan=11, sticky='nsew')

# Start Serial Port Manager
serialPortManager = SerialPortManager(115200, port_connect_bt)

# Add clear serial log button
# Add a button to connect to Serial
clear_log_bt = tk.Button(text="Clear", background="#1E90FF", command=clear_cb)
clear_log_bt.grid(row=11, column=15)

# Add the widget for the log output
output_field = tk.scrolledtext.ScrolledText(
    main_window, wrap=tk.WORD, font="TkSmallCaptionFont", background="#ADD8E6", state=tk.DISABLED, height=10)
output_field.grid(row=12, column=0, sticky='nsew', columnspan=20)

# Add a status row at the bottom
port_label = tk.Label(text="Port: ???")
port_label.grid(row=15, column=3)
debug_label_bt = tk.Button(text="Debug: ???", background="#1E90FF", command=toggle_debug)
debug_label_bt.grid(row=15, column=5)
auto_dr_label_bt = tk.Button(text="Auto DR: ???", background="#1E90FF", command=toggle_auto_dr)
auto_dr_label_bt.grid(row=15, column=7)

# Cleanup the project folder
for file_name in listdir("./RUI3-Modular"):
    if file_name.startswith('RAK'):
        os.remove("./RUI3-Modular/" + file_name)

# Add common AT commands
at_query_bt = tk.Button(text="?", background="#1E90FF",
                        command=lambda: at_command_selected(0))
at_query_bt.grid(row=0, column=21, sticky='nsew')
at_boot_bt = tk.Button(text="BOOT", background="#1E90FF",
                       command=lambda: at_command_selected(1))
at_boot_bt.grid(row=1, column=21, sticky='nsew')
at_z_bt = tk.Button(text="Z\nReset", background="#1E90FF",
                    command=lambda: at_command_selected(2))
at_z_bt.grid(row=2, column=21, sticky='nsew')
at_bat_bt = tk.Button(text="BAT", background="#1E90FF",
                      command=lambda: at_command_selected(3))
at_bat_bt.grid(row=3, column=21, sticky='nsew')
at_ver_bt = tk.Button(text="VER", background="#1E90FF",
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

# Setup the callback when the window close button is pushed
main_window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the configuration check after the main window is openend
main_window.after(250, check_config)

# Set the Window icon
main_window.iconbitmap(ico_file)

# Start the main window loop
main_window.mainloop()
