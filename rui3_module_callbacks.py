import tkinter as tk
from tkinter import scrolledtext
import tkinter.ttk as ttk
from tkinter import messagebox
import os
from os import listdir
import shutil
import glob
import time

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

# Flag for debug on/off
debug_on = True

# Flag for autoconfig DR on/off
auto_dr_on = True

# Callback for Slot selection
# Saves selected slot in "selected_slot"
# Closes the selection window
# var slot - selected slot name

def init_buttons(window):
	global rak1901_bt
	global rak1902_bt
	global rak1903_bt
	global rak1904_bt
	global rak1905_bt
	global rak1906_bt
	global rak1921_bt
	global rak12002_bt
	global rak12003_bt
	global rak12008_bt
	global rak12010_bt
	global rak12014_bt
	global rak12019_bt
	global rak12027_bt
	global rak12037_bt
	global rak12039_bt
	global rak12040_bt
	global rak12047_bt
	global rak12500_bt
	global rak13011_bt
	global rak3372_bt
	global rak4631_bt
	global rak11722_bt
	global main_window
	global module_label

	main_window = window
	
	use_row = 2
	use_column = 0

	# Add the module buttons column 1
	rak1901_bt = tk.Button(text="RAK1901\nT&H",
						background="#FA8072", command=rak1901_cb)
	rak1901_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1902_bt = tk.Button(text="RAK1902\nBaro",
						background="#FA8072", command=rak1902_cb)
	rak1902_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1903_bt = tk.Button(text="RAK1903\nLight",
						background="#FA8072", command=rak1903_cb)
	rak1903_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1904_bt = tk.Button(text="RAK1904\nAcc",
						background="#FA8072", command=rak1904_cb)
	rak1904_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1905_bt = tk.Button(text="RAK1905\n9DOF",
						background="#FA8072", command=rak1905_cb)
	rak1905_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1906_bt = tk.Button(text="RAK1906\nEnv",
						background="#FA8072", command=rak1906_cb)
	rak1906_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak1921_bt = tk.Button(text="RAK1921\nOLED",
						background="#FA8072", command=rak1921_cb)
	rak1921_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')

	use_row = 2
	use_column = use_column + 1

	# Add the module buttons column 2
	rak12002_bt = tk.Button(text="RAK12002\nRTC",
							background="#FA8072", command=rak12002_cb)
	rak12002_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12003_bt = tk.Button(text="RAK12003\nFIR",
							background="#FA8072", command=rak12003_cb)
	rak12003_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12008_bt = tk.Button(text="RAK12008\nCO2",
							background="#FA8072", command=rak12008_cb)
	rak12008_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12010_bt = tk.Button(text="RAK12010\nLight",
							background="#FA8072", command=rak12010_cb)
	rak12010_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12014_bt = tk.Button(text="RAK12014\nToF",
							background="#FA8072", command=rak12014_cb)
	rak12014_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12019_bt = tk.Button(text="RAK12019\nUV",
							background="#FA8072", command=rak12019_cb)
	rak12019_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak12027_bt = tk.Button(text="RAK12027\nQuake",
							background="#FA8072", command=rak12027_cb)
	rak12027_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')

	use_row = 2
	use_column = use_column + 1

	# Add the module buttons column 3
	rak12037_bt = tk.Button(text="RAK12037\nCO2",
							background="#FA8072", command=rak12037_cb)
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
	rak12047_bt = tk.Button(text="RAK12047\nVOC",
							background="#FA8072", command=rak12047_cb)
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
	rak3372_bt = tk.Button(
	text="RAK3372", background="#FA8072", command=rak3372_cb)
	rak3372_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak4631_bt = tk.Button(
	text="RAK4631", background="#FA8072", command=rak4631_cb)
	rak4631_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	use_row = use_row + 1
	rak11722_bt = tk.Button(
	text="RAK11722", background="#FA8072", command=rak11722_cb)
	rak11722_bt.grid(row=use_row, column=use_column, padx=5, pady=5, sticky='nsew')
	# rak11722_bt["state"] = "disable"
	
	# Add a status row at the bottom
	module_label = tk.Label(text="Core: ???")
	module_label.grid(row=15, column=0)
	
	return


def get_selected_board():
	global selected_board
	return selected_board

def slot_selected_cb(slot):
	global get_slot_window
	global selected_slot
	selected_slot = slot
	print("Selected Slot " + slot + " for module")
	get_slot_window.destroy()
	return

def is_RAK3372():
	global rak3372
	return rak3372


def is_RAK4631():
	global rak4631
	return rak4631


def is_RAK11722():
	global rak11722
	return rak11722

# Slot selection window
# Setup of pop-up window with a list of Sensor Slots
# var module - which module the selection is used for
def ask_slot(module):
	global main_window
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
	for file_name in listdir("./RUI3-Modular"):
		print("Found file " + file_name)
		if file_name.startswith(source_name):
			print ("Delete " + file_name)
			os.remove("./RUI3-Modular/" + file_name)

	# fileList = glob.glob("./RUI3-Modular/"+source_name+"*")
	# # Iterate over the list of filepaths & remove each file.
	# for filePath in fileList:
	#	 try:
	#		 os.remove(filePath)
	#	 except:
	#		 print("Error while deleting file : ", filePath)
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

# Clean up the build folders
# The result is shown in the result button result_bt


def clean_build():
	if os.path.exists("./RUI3-Modular/build"):
		shutil.rmtree("./RUI3-Modular/build")
	if os.path.exists("./RUI3-Modular/cache"):
		shutil.rmtree("./RUI3-Modular/cache")
	if os.path.exists("./RUI3-Modular/flash-files"):
		shutil.rmtree("./RUI3-Modular/flash-files")
	return

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
	global rak1905
	global rak1904_bt
	global rak1904_slot

	header_name = "RAK1904_acc_S_"
	if (rak1904):
		rak1904 = remove_source(rak1904_bt, "RAK1904")
		rak1904_bt.config(text="RAK1904\nAcc")
	else:
		if (rak1905):
			messagebox.showerror("ERROR", "RAK1904 and RAK1905 cannot be used together")
			return
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
	global rak1904
	global rak1905
	global rak1905_bt
	global rak1905_slot
	header_name = "RAK1905_9dof_S_"

	if (rak1905):
		rak1905 = remove_source(rak1905_bt, "RAK1905")
		rak1905_bt.config(text="RAK1905\n9DOF")
	else:
		if (rak1904):
			messagebox.showerror("ERROR", "RAK1904 and RAK1905 cannot be used together")
			return
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
	global selected_board
	if (selected_board == "rak_rui:stm32:WisDuoRAK3172EvaluationBoard"):
		messagebox.showerror(
			"ERROR", "RAK3372 does not support RAK12500 (yet)")
		rak12500 = False
		rak12500_bt.config(background="#FA8072")
		try:
			os.remove("./RUI3-Modular/rak12500_gnss.cpp")
		except:
			print("Could not delete RAK12500 files")
		return
	if (rak12500):
		print("Remove RAK12500")
		rak12500 = remove_source(rak12500_bt, "RAK12500")
	else:
		print("Add RAK12500")
		rak12500 = enable_source(rak12500_bt, "RAK12500_gnss.cpp")
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
	global rak12500
	global module_label
	
	if not (selected_board == rak3372_board):
		clean_build()
		if (rak12500):
			rak12500 = remove_source(rak12500_bt, "RAK12500")
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
		clean_build()
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
		clean_build()
	selected_board = rak11722_board
	rak3372 = False
	rak4631 = False
	rak11722 = True
	rak3372_bt.config(background="#FA8072")
	rak4631_bt.config(background="#FA8072")
	rak11722_bt.config(background="#00FF00")
	module_label.config(text="RAK11722")
	return

def get_debug():
	global debug_on
	return debug_on

def set_debug(new_level):
	global debug_on
	debug_on = new_level
	return

def get_auto_dr():
	global aut0_dr_on
	return auto_dr_on


def set_auto_dr(new_level):
	global auto_dr_on
	auto_dr_on = new_level
	return

# Parse configuration line
# Enables the module that is found in the line
# var check_line - a single line of the configuration file
def get_last_config(check_line, main_window):
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
    global auto_dr_on

    if check_line == 'debug_off':
        print("Debug is off")
        debug_on = False
    if check_line == 'auto_dr_off':
        print("Auto DR is off")
        auto_dr_on = False
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
    elif check_line == "RAK12039":
        rak12039 = enable_source(rak12039_bt, "RAK12039_pm.cpp")
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

# Saves the currently selected modules into configuration file
def save_config(debug_on):
    global rak1901
    global rak1902
    global rak1903
    global rak1904
    global rak1905
    global rak1906
    global rak1921
    global rak12002
    global rak12003
    global rak12008
    global rak12010
    global rak12014
    global rak12019
    global rak12027
    global rak12037
    global rak12039
    global rak12040
    global rak12047
    global rak12500
    global rak13011
    global rak3372
    global rak4631
    global rak11722
    global auto_dr_on

    print("Saving config")

    # Remove saved config
    if os.path.exists("./.config"):
        os.remove("./.config")
    # Save current config
    f = open('./.config', 'w')
    if not debug_on:
        f.write("debug_off\n")
    if not auto_dr_on:
        f.write("auto_dr_off\n")
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
    return
