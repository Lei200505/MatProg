import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from unidecode import unidecode
import dijkstra
import graph_viz
import csv
import sys
import os

#a vegso produktum egy .exe file lesz
#ehhez a .pkl grafokat es a gfts adatbazist be kell csomagulununk
#pyinstallerel csinaljuk az .exe-t, ehhez kell ennek a tmp mappaja, a  .meipass
def exe_path(rel_path):
    try:
        path = sys._MEIPASS
    except AttributeError:
        path = os.path.abspath(".")
    return os.path.join(path, rel_path)

source = exe_path("budapest.pkl")
source_night = exe_path("night_budapest.pkl")
G = dijkstra.graf_betoltes(source)
stops_dict = dijkstra.stops(G)
stop_list = list(stops_dict.values())
G_night = dijkstra.graf_betoltes(source_night)
stops_dict_night = dijkstra.stops(G_night)
routes_dict = dijkstra.routes(exe_path("budapest_data/routes.txt"))

halozat_rajz = graph_viz.GraphViz(G, exe_path("budapest_data"))
halozat_rajz_night = graph_viz.GraphViz(G_night, exe_path("budapest_data"))

root = tk.Tk()
root.title("Utazástervező")
root.iconbitmap(exe_path("busicon.ico"))
root.minsize(300,200)

#grid átméretezhetősége
for i in range(6):
    root.grid_rowconfigure(i, weight=1)
for i in range(4):
    root.grid_columnconfigure(i, weight=1)

frobool = False
tobool = False

#a tervezés gomb feloldása, miután kezdő-és végpont ki lett választva
def enable(*args):
    if frobool and tobool:
        terv.config(state="normal")
    else:
        terv.config(state="disabled")

#a lista szűrése a keresőmezőbe beírt szöveg alapján (kezdőpont)
def update_fro(data):
    frolist.delete(0, tk.END)
    for i in data:
        frolist.insert(tk.END, i)

#a lista szűrése a keresőmezőbe beírt szöveg alapján (végpont)
def update_to(data):
    tolist.delete(0, tk.END)
    for i in data:
        tolist.insert(tk.END, i)

#a keresőmező kitöltése a megállóra kattintás után (kezdőpont)
def filloutfro(event):
    global frobool
    fro.delete(0, tk.END)
    if frolist.curselection():
        index = frolist.curselection()[0]
        fro.insert(0, frolist.get(index))
        frobool = True
    enable(event)

#a keresőmező kitöltése a megállóra kattintás után (végpont)
def filloutto(event):
    global tobool
    to.delete(0, tk.END)
    if tolist.curselection():
        index = tolist.curselection()[0]
        to.insert(0, tolist.get(index))
        tobool = True
    enable(event)

#a lista szűrése a keresőmezőbe beírt szöveg alapján (kezdőpont)
def filterfro(event):
    global frobool
    frobool = False
    inp = fro.get()
    if inp == "":
        data = stop_list
    else:
        data = []
        for i in stop_list:
            if unidecode(inp).lower() in unidecode(i).lower():
                data.append(i)
    update_fro(data)
    enable(event)

#a lista szűrése a keresőmezőbe beírt szöveg alapján (végpont)
def filterto(event):
    global tobool
    tobool = False
    inp = to.get()
    if inp == "":
        data = stop_list
    else:
        data = []
        for i in stop_list:
            if unidecode(inp).lower() in unidecode(i).lower():
                data.append(i)
    update_to(data)
    enable(event)

def graph_ui():
    #graphout = tk.Toplevel(root)
    #graphout.title("Térkép")
    #ax.clear()
    halozat_rajz.viz()
    #canvas = FigureCanvasTkAgg(fig, master = graphout)
    #canvas.draw()
    #canvas.get_tk_widget().pack()

def night_graph_ui():
    #nightgraphout = tk.Toplevel(root)
    #nightgraphout.title("Térkép (éjszakai)")
    halozat_rajz_night.viz()
    #canvas = FigureCanvasTkAgg(fig, master = nightgraphout)
    #canvas.get_tk_widget().pack()

#a gomb megnyomására véghezvitt függvény (Dijkstra)
def endpoints():
    origin = [key for key, val in stops_dict.items() if val == fro.get()][0]
    destination = [key for key, val in stops_dict.items() if val == to.get()][0]
    seconds = 3600*int(hr.get()) + 60*int(min.get())
    
    path = dijkstra.dijkstra(graph=G, graph_night=G_night, start=origin, end=destination, start_time=seconds)
    out = dijkstra.pretty_path(path[0], stops_dict=stops_dict, stops_dict_night=stops_dict_night, routes_dict=routes_dict, tipus=path[2])

    labelout = tk.Toplevel(root)
    labelout.title("Útvonal")
    
    header = tk.Label(labelout, text="Tervezett útvonal", 
                  font=("Courier", 16, "bold"), bg="purple", fg="white")
    header.pack(fill="x", pady=(0,10))
    textbox = tk.Text(labelout, font=("Courier", 12), fg="purple", 
                  bg="white", padx=10, pady=10, wrap="word", width=60, height=20)
    textbox.insert("1.0", out)
    textbox.config(state="disabled")
    textbox.pack(padx=10, pady=10)
    
    #plotout = tk.Toplevel(root)
    #plotout.title("Térkép")
    #ax.clear()
    halozat_rajz.fenyo_viz(path[1], origin, destination, path[0])
    #canvas = FigureCanvasTkAgg(fig, master = plotout)
    #canvas.draw()
    #canvas.get_tk_widget().pack()

lbl1 = tk.Label(root, width=30, text="Honnan szeretnél utazni?", font=("Courier", 18), bg="purple", fg="white")
lbl1.grid(row=0, column=0, sticky="nsew")

fro = tk.Entry(root, width=30, font=("Courier", 18), fg="purple")
fro.grid(row=1, column=0, sticky="nsew")

frolist = tk.Listbox(root, width=30, font=("Courier", 18), fg="purple", exportselection=False)
frolist.grid(row=2, column=0, sticky="nsew")

lbl2 = tk.Label(root, width=30, text="Hova szeretnél utazni?", font=("Courier", 18), bg="purple", fg="white")
lbl2.grid(row=0, column=1, columnspan=2, sticky="nsew")

to = tk.Entry(root, width=30, font=("Courier", 18), fg="purple")
to.grid(row=1, column=1, columnspan=2, sticky="nsew")

tolist = tk.Listbox(root, width=30, font=("Courier", 18), fg="purple", exportselection=False)
tolist.grid(row=2, column=1, columnspan=2, sticky="nsew")

lbl3 = tk.Label(root, width=30, text="Kezdő időpont:", font=("Courier", 18), bg="purple", fg="white")
lbl3.grid(row=3, column=0, sticky="nsew")

hr = tk.StringVar(root)
hr.set("00")
hours = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
hoursopt = ttk.Combobox(root, values=hours, textvariable=hr, state="readonly")
hoursopt.configure(width=4, font=("Courier", 18), background = "white", foreground="purple", justify="center")
hoursopt.grid(row=3, column=1, sticky="nsew")

min = tk.StringVar(root)
min.set("00")
mins = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59']
minsopt = ttk.Combobox(root, values=mins, textvariable=min, state="readonly")
minsopt.configure(width=4, font=("Courier", 18), background = "white", foreground="purple", justify="center")
minsopt.grid(row=3, column=2, sticky="nsew")

terv = tk.Button(root, width=60, text="Tervezés", font=("Courier", 18), bg="purple", fg="white", command=endpoints, state="disabled")
terv.grid(row=4, column=0, columnspan=3, sticky="nsew")

btn_graph = tk.Button(root, width=30, text="Térkép", font=("Courier", 18), bg="purple", fg="white", command=graph_ui)
btn_graph.grid(row=5, column=0, columnspan=1, sticky="nsew")
#
btn_night_graph = tk.Button(root, width=30, text="Térkép (éjszakai)", font=("Courier", 18), bg="purple", fg="white", command=night_graph_ui)
btn_night_graph.grid(row=5, column=1, columnspan=2, sticky="nsew")
update_fro(stop_list)
update_to(stop_list)

#a listában szereplő megállóra való kattintás után kitölti a keresőmezőt
frolist.bind("<<ListboxSelect>>", filloutfro)
tolist.bind("<<ListboxSelect>>", filloutto)

#a keresőmezőbe gépelés után leszűri a megállók listáját
fro.bind("<KeyRelease>", filterfro)
to.bind("<KeyRelease>", filterto)

root.mainloop()