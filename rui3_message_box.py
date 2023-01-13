import tkinter as tk

class rui3_message(tk.Toplevel):
    def __init__(self, title, message):
        super().__init__()
        self.details_expanded = False
        self.title(title)
        self.geometry(
            "{}x75+{}+{}".format(self.master.winfo_width(), self.master.winfo_x(), self.master.winfo_y()))
        self.configure(bg="#FA8072")
        self.resizable(False, False)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        tk.Label(self, text=message).grid(row=0, column=0,
                                          columnspan=3, pady=(7, 7), padx=(7, 7), sticky="ew")
        tk.Button(self, text="OK", command=self.destroy).grid(
            row=1, column=1, sticky="ew")

