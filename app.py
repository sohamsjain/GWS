from tkinter import *
from tkinter import ttk
from symbols import *
from mywidgets import *

pads = dict(ipadx=5, ipady=5, padx=5, pady=5)
theme = dict(bg='black', fg='grey')


class App(Tk):
    def __init__(self):
        super().__init__()
        self.resizable(0, 0)
        self.configure(background='black')
        self.title("Grid Work Station")
        self.spawn = Spawn(self, text="Spawn", **theme, highlightbackground='black')
        self.xones = Xones(self)
        self.activity = Activity(self)
        self.raven = Raven(self, text="Raven", **theme)

        self.spawn.grid(column=0, row=0, columnspan=1, sticky="NEWS", **pads)
        self.activity.grid(column=1, row=0, columnspan=5, sticky="NEWS", padx=5, pady=12)
        self.xones.grid(column=0, row=1, columnspan=5, sticky="NEWS", padx=5, pady=12)
        self.raven.grid(column=6, row=0, rowspan=2, sticky="NEWS", padx=5, pady=5)

        self.bind("<Control-n>", self.spawn.symbol_combo.focus)
