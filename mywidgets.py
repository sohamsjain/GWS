from typing import List, Optional
from tkinter import ttk
from tkinter import *
from symbols import *
import pandas as pd
import numpy as np
from colors import *
from pandastable import Table
from pandastable.config import apply_options
from datetime import *
from queue import Queue
from typing import Optional


lengthOfStatuses = 10
PENDING, ENTRY, STOPLOSS, TARGET, MISSED, FAILED, HARDEXIT, CANCELLED, REJECTED, MARGIN = range(lengthOfStatuses)

statuses: List[str] = ["PENDING", "ENTRY", "STOPLOSS", "TARGET", "MISSED", "FAILED", "HARDEXIT", "CANCELLED",
                       "REJECTED", "MARGIN"]


class Xone:
    attrs = ['symbol', 'entry', 'stoploss', 'target', 'size', 'status', 'entryhit']

    def __init__(self, symbol, entry, stoploss, target=None, state=None, entryhit=0, size=0):
        if entry == stoploss:
            raise ValueError("Entry Cannot be equal to Stoploss")

        self.symbol: str = symbol
        self.entry: float = entry
        self.stoploss: float = stoploss
        self.rpu: float = abs(entry - stoploss)
        self.islong: bool = entry > stoploss
        self.target: float = target or (entry + (2 * self.rpu) if self.islong else entry - (2 * self.rpu))
        self.state: int = state or PENDING
        self.status: str = statuses[self.state]
        self.entryhit: int = entryhit or 0
        self.nextstate: Optional[int] = None
        self.size: int = size or 0

    def setstate(self, state):
        self.state = state
        self.status = statuses[self.state]

    def setsize(self, size):
        self.size = size

    def getvalues(self):
        return {k: v for k, v in self.__dict__.items() if k in Xone.attrs}


orders = ['Symbol', 'Action', 'Type', 'Details', 'Size', 'Fill Px', 'Sbmt']
ordersdf = pd.DataFrame(np.random.randn(700, 7), columns=orders)

xoneattr = ['symbol', 'entry', 'stoploss', 'target', 'size', 'status', 'entryhit']
xonedf = pd.DataFrame(np.random.randn(700, 7), columns=xoneattr)

emptydf = pd.DataFrame(columns=xoneattr)

pads = dict(ipadx=5, ipady=5, padx=5, pady=5)
acton = ["Self", "Futures", "Call", "Put"]
attached = dict()


class Spawn(LabelFrame):

    def __init__(self, master, **kw):

        self.params = dict()
        for k, v in kw.items():
            self.params[k] = v

        super(Spawn, self).__init__(master, self.params)
        self.nextwidget = dict()
        self.required = list()

        self.heading = MyLabel(self, text="New Xone", font=25)
        self.heading.grid(row=0, column=0, columnspan=2, sticky="", ipadx=15, pady=15)

        self.symbol = MyLabel(self, text="Symbol")
        self.symbol.grid(row=1, column=0, **pads)

        self.entry = MyLabel(self, text="Entry")
        self.entry.grid(row=2, column=0, **pads)

        self.stoploss = MyLabel(self, text="Stoploss")
        self.stoploss.grid(row=3, column=0, **pads)

        self.target = MyLabel(self, text="Target")
        self.target.grid(row=4, column=0, **pads)

        self.acton = MyLabel(self, text="Act On")
        self.acton.grid(row=5, column=0, **pads)

        self.symbol_txt_var = StringVar()
        self.symbol_combo = Symbolbox(self, textvariable=self.symbol_txt_var)
        self.symbol_combo.grid(row=1, column=1, **pads)
        self.symbol_combo.bind("<Return>", self.focusnext)
        self.symbol_combo.bind("<Tab>", self.focusnext)
        self.required.append(self.symbol_combo)

        self.entry_field = Pricebox(self)
        self.entry_field.grid(row=2, column=1, **pads)
        self.entry_field.bind("<Return>", self.focusnext)
        self.entry_field.bind("<Tab>", self.focusnext)
        self.nextwidget[self.symbol_combo] = self.entry_field
        self.required.append(self.entry_field)

        self.stoploss_field = Pricebox(self)
        self.stoploss_field.grid(row=3, column=1, **pads)
        self.stoploss_field.bind("<Return>", self.focusnext)
        self.stoploss_field.bind("<Tab>", self.focusnext)
        self.nextwidget[self.entry_field] = self.stoploss_field
        self.required.append(self.stoploss_field)

        self.target_field = Pricebox(self)
        self.target_field.grid(row=4, column=1, **pads)
        self.target_field.bind("<Return>", self.focusnext)
        self.target_field.bind("<Tab>", self.focusnext)
        self.nextwidget[self.stoploss_field] = self.target_field

        self.acton_field = ActOnbox(self)
        self.acton_field.grid(row=5, column=1, **pads)
        self.acton_field.bind("<Return>", self.focusnext)
        self.acton_field.bind("<Tab>", self.focusnext)
        self.nextwidget[self.target_field] = self.acton_field

        self.spawn_button = Button(self, text="Spawn", bg=brown, fg=black, command=self.insert, bd=0,
                                   activebackground=grey, width=27, activeforeground=black)
        self.spawn_button.grid(row=6, column=0, columnspan=2, sticky=E, **pads)

        self.spawning_q: Optional[Queue] = None

    def set_spawning_q(self, cb):
        if isinstance(cb, Queue):
            self.spawning_q = cb

    def focusnext(self, event):
        try:
            widget = event.widget
            next = self.nextwidget[widget]
            widget.background_normal()
            next.focus_set()
        except KeyError as ke:
            self.spawn_button.focus_set()
            self.insert()

    def insert(self):
        global emptydf
        something_missing = False
        for widget in self.required:
            if widget.get() == "":
                something_missing = True
                widget.background_issue()
        if something_missing:
            return
        sym = self.symbol_combo.get()
        e = float(self.entry_field.get())
        s = float(self.stoploss_field.get())
        if e == s:
            self.stoploss_field.delete(0, END)
            self.stoploss_field.background_issue()
            return
        t = self.target_field.get()
        if t:
            t = float(t)
            if e > s and t < e:
                self.target_field.delete(0, END)
                self.target_field.insert(0, e + abs(e - s))
                self.target_field.background_issue()
                return
            elif e < s and t > e:
                self.target_field.delete(0, END)
                self.target_field.insert(0, e - abs(e - s))
                self.target_field.background_issue()
                return
        message = dict(symbol=sym, entry=e, stoploss=s, target=t)
        if self.spawning_q:
            self.spawning_q.put(message)
        self.clear_subs()

        #     if mypendingdf.empty:
        #         mypendingdf = pd.DataFrame([[sym, e, s, t, "", "", ""]], columns=xoneattr)
        #     else:
        #         mypendingdf = mypendingdf.append(pd.DataFrame([[sym, e, s, t, "", "", ""]], columns=xoneattr),
        #                                          ignore_index=True)
        #     table = attached[5]
        #     table.model.df = mypendingdf
        #     table.redraw()
        #     self.clear_subs()
        #     return
        # if mypendingdf.empty:
        #     mypendingdf = pd.DataFrame([[sym, e, s, "", "", "", ""]], columns=xoneattr)
        # else:
        #     mypendingdf = mypendingdf.append(pd.DataFrame([[sym, e, s, "", "", "", ""]], columns=xoneattr),
        #                                      ignore_index=True)
        # table = attached[5]
        # table.model.df = mypendingdf
        # table.redraw()
        # self.clear_subs()

    def clear_subs(self):
        self.symbol_combo.delete(0, END)
        self.entry_field.delete(0, END)
        self.stoploss_field.delete(0, END)
        self.target_field.delete(0, END)
        self.acton_field.delete(0, END)


class Symbolbox(ttk.Combobox):

    def __init__(self, master, **kw):

        self.params = dict()
        for k, v in kw.items():
            self.params[k] = v

        super(Symbolbox, self).__init__(master, **self.params)
        self.mystyle = ttk.Style()

        self.mystyle.theme_create('symbol', parent='alt',
                                  settings=dict(
                                      TCombobox=dict(
                                          configure=dict(
                                              selectbackground=grey,
                                              selectforeground=black,
                                              fieldbackground=black,
                                              background=black,
                                              foreground=grey,
                                              arrowcolor=grey,
                                              insertcolor=grey,
                                              borderwidthd=0)),
                                      ComboboxPopdownFrame=dict(
                                          configure=dict(
                                              highlightthickness=1,
                                              highlightbackground=black,
                                              relief='groove'))))

        self.mystyle.theme_use('symbol')
        self['values'] = symbols
        self.bind('<KeyRelease>', self.checkkey)
        self.master.option_add('*TCombobox*Listbox.background', black)
        self.master.option_add('*TCombobox*Listbox.foreground', grey)
        self.master.option_add('*TCombobox*Listbox.selectBackground', grey)
        self.master.option_add('*TCombobox*Listbox.selectForeground', black)

    def checkkey(self, event):

        value = self.get()
        if not value == '':
            data = []
            for item in self['values']:
                if value.lower() in item.lower():
                    data.append(item)
            if not data:
                self.delete(len(self.get()) - 1, END)
                return
            self['values'] = data
            return
        self['values'] = symbols

    def background_issue(self):
        self.mystyle.configure('TCombobox', fieldbackground=brown)
        self.after(5000, self.background_normal)

    def background_normal(self):
        self.select_clear()
        self.mystyle.configure('TCombobox', fieldbackground=black)

    def focus(self, event):
        self.focus_set()


class ActOnbox(ttk.Combobox):

    def __init__(self, master, **kw):

        self.params = dict()
        for k, v in kw.items():
            self.params[k] = v

        super(ActOnbox, self).__init__(master, **self.params)
        self.mystyle = ttk.Style()

        self.mystyle.theme_create('acton', parent='alt',
                                  settings=dict(
                                      TCombobox=dict(
                                          configure=dict(
                                              selectbackground=grey,
                                              selectforeground=black,
                                              fieldbackground=black,
                                              background=black,
                                              foreground=grey,
                                              arrowcolor=grey,
                                              insertcolor=grey,
                                              borderwidthd=0)),
                                      ComboboxPopdownFrame=dict(
                                          configure=dict(
                                              highlightthickness=1,
                                              highlightbackground=black,
                                              relief='groove'))))

        self.mystyle.theme_use('acton')
        self['values'] = acton
        self.bind('<KeyRelease>', self.checkkey)
        self.master.option_add('*TCombobox*Listbox.background', black)
        self.master.option_add('*TCombobox*Listbox.foreground', grey)
        self.master.option_add('*TCombobox*Listbox.selectBackground', grey)
        self.master.option_add('*TCombobox*Listbox.selectForeground', black)

    def checkkey(self, event):

        value = self.get()
        if not value == '':
            data = []
            for item in self['values']:
                if value.lower() in item.lower():
                    data.append(item)
            if not data:
                self.delete(len(self.get()) - 1, END)
                return
            self['values'] = data
            return
        self['values'] = acton

    def background_issue(self):
        self.mystyle.configure('TCombobox', fieldbackground=brown)
        self.after(5000, self.background_normal)

    def background_normal(self):
        self.select_clear()
        self.mystyle.configure('TCombobox', fieldbackground=black)


class Pricebox(Spinbox):

    def __init__(self, master, **kw):
        self.params = dict(background=black, foreground=black, fg=grey, bd=1, buttonbackground=black,
                           selectbackground=grey, selectforeground=black, relief='sunken', insertbackground=grey)
        for k, v in kw.items():
            self.params[k] = v
        self.int_var = ()
        super(Pricebox, self).__init__(master, from_=0.0, to=999999999.0, increment=0.05, textvariable=self.int_var,
                                       command=lambda: self.icursor(END), **self.params)
        self.delete(0, END)
        self.bind('<KeyRelease>', self.checkkey)

    def checkkey(self, event):
        value = self.get()
        if not value == '':
            try:
                float(value)
            except:
                self.delete(len(value) - 1, END)
                return

    def background_issue(self):
        self.configure(background=brown)
        self.after(5000, self.background_normal)

    def background_normal(self):
        self.selection_clear()
        self.configure(background=black)


class MyLabel(Label):

    def __init__(self, master, **kw):
        self.params = dict(anchor=E, width=5, background=black, fg=grey)
        for k, v in kw.items():
            self.params[k] = v
        super(MyLabel, self).__init__(master, **self.params)


options = {'align': 'w',
           'cellbackgr': black,
           'cellwidth': 80,
           'colheadercolor': black,
           'floatprecision': 2,
           'font': 'Arial',
           'fontsize': 12,
           'fontstyle': '',
           'grid_color': grey,
           'linewidth': 1,
           'rowheight': 22,
           'rowselectedcolor': brown,
           'textcolor': grey}


class Activity(ttk.Notebook):

    def __init__(self, master, **kw):
        self.params = dict()
        for k, v in kw.items():
            self.params[k] = v
        super(Activity, self).__init__(master, **self.params)
        self.mystyle = ttk.Style()

        self.mystyle.configure("TNotebook", background=black, tabmargins=[1, 1, 0, 0])
        self.mystyle.map("TNotebook.Tab", background=[("selected", brown)], foreground=[("selected", black)],
                         expand=[("selected", [5, 0, 5, 0])])
        self.mystyle.configure("TNotebook.Tab", background=black, foreground=grey, padding=[17, 5],
                               highlightcolor=brown,
                               focuscolor=brown)
        self.orders_tab = Frame(self, background=black)
        self.trades_tab = Frame(self, background=black)
        self.positions_tab = Frame(self, background=black)
        self.add(self.orders_tab, text="Orders")
        self.add(self.trades_tab, text="Trades")
        self.add(self.positions_tab, text="Positions")
        self.ordersdf = DTable(self.orders_tab)
        self.ordersdf.model.df = ordersdf
        self.ordersdf.show()


class Xones(ttk.Notebook):

    def __init__(self, master, **kw):
        self.params = dict()
        for k, v in kw.items():
            self.params[k] = v
        super(Xones, self).__init__(master, **self.params)
        self.mystyle = ttk.Style()

        self.mystyle.configure("TNotebook", background=black, tabmargins=[1, 1, 0, 0])
        self.mystyle.map("TNotebook.Tab", background=[("selected", brown)], foreground=[("selected", black)],
                         expand=[("selected", [5, 0, 5, 0])])
        self.mystyle.configure("TNotebook.Tab", background=black, foreground=grey, padding=[17, 5],
                               focuscolor=brown)
        self.pending_tab = Frame(self, background=black)
        self.open_tab = Frame(self, background=black)
        self.closed_tab = Frame(self, background=black)
        self.add(self.pending_tab, text="Pending")
        self.add(self.open_tab, text="Open")
        self.add(self.closed_tab, text="Closed")
        self.pending = DTable(self.pending_tab)
        self.open = DTable(self.open_tab)
        self.closed = DTable(self.closed_tab)
        self.pending.model.df = emptydf
        self.open.model.df = emptydf
        self.closed.model.df = emptydf
        self.pending.show()
        self.open.show()
        self.closed.show()

    def refresh(self, dict_of_df):
        for xtype , xdf in dict_of_df.items():
            table: Table = self.__getattribute__(xtype)
            table.model.df = xdf
            table.redraw()


class DTable(Table):
    def __init__(self, master):
        super(DTable, self).__init__(master)
        self.mystyle = ttk.Style()
        self.mystyle.configure("Vertical.TScrollbar", troughcolor='black', background='black', bordercolor="black")
        self.mystyle.configure("Horizontal.TScrollbar", troughcolor='black', background='black', bordercolor="black")
        apply_options(options, self)


class BotBubble:
    def __init__(self, master, message=""):
        self.master = master
        self.frame = Frame(master, bg=brown)
        self.i = self.master.create_window(60, 600, window=self.frame)
        Label(self.frame, text=datetime.now().strftime("%Y-%m-%d %H:%m"), font=("Helvetica", 7), bg=brown).grid(row=1,
                                                                                                                column=0,
                                                                                                                sticky="w",
                                                                                                                padx=3)
        Label(self.frame, text=message, font=("Helvetica", 9), bg=brown).grid(row=0, column=0, sticky="w")
        self.master.master.update_idletasks()
        self.master.create_polygon(self.draw_triangle(self.i), fill=brown, outline="grey")

    def draw_triangle(self, widget):
        x1, y1, x2, y2 = self.master.bbox(widget)
        return x1, y2 - 5, x1 - 15, y2 + 10, x1, y2


class Raven(LabelFrame):
    def __init__(self, master, **kw):
        super(Raven, self).__init__(master, **kw)
        self.canvas = Canvas(self, width=200, height=200, scrollregion=(0, 0, 500, 500), bg=black,
                             highlightbackground=black)
        self.canvas.pack(fill=BOTH, expand=True)
        self.bubbles = list()
        self.textfield = Text(self, bg=black, fg=grey, height=2, width=30)
        self.textfield.pack(side=LEFT, anchor=S, fill=X)
        self.textfield.bind("<Control-Return>", self.send_message)

    def send_message(self, event):
        msg = self.textfield.get("0.0", END)
        self.textfield.delete("0.0", END)
        if msg:
            if self.bubbles:
                self.canvas.move(ALL, 0, -100)
            a = BotBubble(self.canvas, message=msg)
            self.bubbles.append(a)

    def post_message(self, msg):
        if msg:
            if self.bubbles:
                self.canvas.move(ALL, 0, -100)
            a = BotBubble(self.canvas, message=msg)
            self.bubbles.append(a)
