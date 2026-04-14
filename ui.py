import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from unidecode import unidecode
import dijkstra
import graph_viz
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

#Gráfok és megállók betöltése
source = exe_path("budapest.pkl")
source_night = exe_path("night_budapest.pkl")
G = dijkstra.graf_betoltes(source)
stops_dict = dijkstra.stops(G)
stop_list = list(stops_dict.values())
G_night = dijkstra.graf_betoltes(source_night)
stops_dict_night = dijkstra.stops(G_night)
routes_dict = dijkstra.routes(exe_path("budapest_data/routes.txt"))

#Gráfok vizualizációjához szükséges objektumok létrehozása
halozat_rajz = graph_viz.GraphViz(G, exe_path("budapest_data"))
halozat_rajz_night = graph_viz.GraphViz(G_night, exe_path("budapest_data"))

root = tk.Tk()
root.title("Utazástervező")
root.iconbitmap(exe_path("busicon.ico"))
root.minsize(300,200)

#Grid átméretezhetősége
for i in range(6):
    root.grid_rowconfigure(i, weight=1)
for i in range(4):
    root.grid_columnconfigure(i, weight=1)

frobool = False
tobool = False

#Tervezés gomb feloldása, miután kezdő-és végpont ki lett választva
def enable(*args):
    if frobool and tobool:
        terv.config(state="normal")
    else:
        terv.config(state="disabled")

#Lista szűrése a keresőmezőbe beírt szöveg alapján (kezdőpont)
def update_fro(data):
    frolist.delete(0, tk.END)
    for i in data:
        frolist.insert(tk.END, i)

#Lista szűrése a keresőmezőbe beírt szöveg alapján (végpont)
def update_to(data):
    tolist.delete(0, tk.END)
    for i in data:
        tolist.insert(tk.END, i)

#Keresőmező kitöltése a megállóra kattintás után (kezdőpont)
def filloutfro(event):
    global frobool
    fro.delete(0, tk.END)
    if frolist.curselection():
        index = frolist.curselection()[0]
        fro.insert(0, frolist.get(index))
        frobool = True
    enable(event)

#Keresőmező kitöltése a megállóra kattintás után (végpont)
def filloutto(event):
    global tobool
    to.delete(0, tk.END)
    if tolist.curselection():
        index = tolist.curselection()[0]
        to.insert(0, tolist.get(index))
        tobool = True
    enable(event)

#Lista szűrése a keresőmezőbe beírt szöveg alapján (kezdőpont)
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

#Lista szűrése a keresőmezőbe beírt szöveg alapján (végpont)
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

#Egész gráfok (nappali és éjszakai)
def graph_ui():
    halozat_rajz.viz()
def night_graph_ui():
    halozat_rajz_night.viz()

#Gomb megnyomására véghezvitt függvény (Dijkstra)
def endpoints():
    origin = [key for key, val in stops_dict.items() if val == fro.get()][0] #kezdőpont
    destination = [key for key, val in stops_dict.items() if val == to.get()][0] #végpont
    seconds = 3600*int(hr.get()) + 60*int(min.get()) #beállított kezdési időpont átszámolva másodpercre
    
    path = dijkstra.dijkstra(graph=G, graph_night=G_night, start=origin, end=destination, start_time=seconds) #útvonaltervezés
    out = dijkstra.pretty_path(path[0], stops_dict=stops_dict, stops_dict_night=stops_dict_night,
                               routes_dict=routes_dict, tipus=path[2]) # útvonal szöveges megjelenítése

    #Útvonal megjelenítése új ablakban
    labelout = tk.Toplevel(root)
    labelout.title("Útvonal")
    
    header = tk.Label(labelout, text="Tervezett útvonal", 
                  font=("Courier", 16, "bold"), bg="purple", fg="white")
    header.pack(fill="x", pady=(0,10))
    
    #Szöveges útvonal megjelenítése görgethető textboxban
    textbox = tk.Text(labelout, font=("Courier", 12), fg="purple", 
                  bg="white", padx=10, pady=10, wrap="word", width=60, height=20)
    textbox.insert("1.0", out)
    textbox.config(state="disabled")
    textbox.pack(padx=10, pady=10)
    
    #útvonal vizuális megjelenítése matplotlib segítségével 
    #Először az animáció új ablakban, majd a gráf végső állapota egy statikus képként
    fig, ax=halozat_rajz.fenyo_viz(path[1], origin, destination, path[0])
    canvas = FigureCanvasTkAgg(fig, master = labelout)
    canvas.draw()
    canvas.get_tk_widget().pack()


#UI elemek létrehozása

#----------------------------Megállók kiválasztása-----------------------------
#Kezdőpont kiválasztása
lbl1 = tk.Label(root, width=30, text="Honnan szeretnél utazni?", font=("Courier", 18), bg="purple", fg="white") #címke a kezdőpont kiválasztásához
lbl1.grid(row=0, column=0, sticky="nsew")
fro = tk.Entry(root, width=30, font=("Courier", 18), fg="purple") #keresőmező a kezdőpont kiválasztásához
fro.grid(row=1, column=0, sticky="nsew")
frolist = tk.Listbox(root, width=30, font=("Courier", 18), fg="purple", exportselection=False) #listbox a megállók listájához
frolist.grid(row=2, column=0, sticky="nsew")
#Végpont kiválasztása
lbl2 = tk.Label(root, width=30, text="Hova szeretnél utazni?", font=("Courier", 18), bg="purple", fg="white") #címke a végpont kiválasztásához
lbl2.grid(row=0, column=1, columnspan=2, sticky="nsew")
to = tk.Entry(root, width=30, font=("Courier", 18), fg="purple") #keresőmező a végpont kiválasztásához
to.grid(row=1, column=1, columnspan=2, sticky="nsew")
tolist = tk.Listbox(root, width=30, font=("Courier", 18), fg="purple", exportselection=False) #listbox a megállók listájához
tolist.grid(row=2, column=1, columnspan=2, sticky="nsew")

#----------------------------Kezdési időpont kiválasztása-----------------------------
lbl3 = tk.Label(root, width=30, text="Kezdő időpont:", font=("Courier", 18), bg="purple", fg="white")
lbl3.grid(row=3, column=0, sticky="nsew")
#órák legördülő menüből
hr = tk.StringVar(root) #a legördülő menü értékét tároló változó
hr.set("12")
hours = [f"{i:02d}" for i in range(24)]
hoursopt = ttk.Combobox(root, values=hours, textvariable=hr, state="readonly") 
hoursopt.configure(width=4, font=("Courier", 18), background = "white", foreground="purple", justify="center")
hoursopt.grid(row=3, column=1, sticky="nsew")
#percek legördülő menüből
min = tk.StringVar(root)
min.set("00")
mins = [f"{i:02d}" for i in range(60)]
minsopt = ttk.Combobox(root, values=mins, textvariable=min, state="readonly")
minsopt.configure(width=4, font=("Courier", 18), background = "white", foreground="purple", justify="center")
minsopt.grid(row=3, column=2, sticky="nsew")

#--------------------Egyéb gombok-----------------------
#Tervezés gomb, ami a Dijkstra algoritmust futtatja a megadott paraméterekkel
terv = tk.Button(root, width=60, text="Tervezés", font=("Courier", 18), bg="purple", fg="white", command=endpoints, state="disabled")
terv.grid(row=4, column=0, columnspan=3, sticky="nsew")

#Az egész gráf megjelenítése gombok
btn_graph = tk.Button(root, width=30, text="Térkép", font=("Courier", 18), bg="purple", fg="white", command=graph_ui)
btn_graph.grid(row=5, column=0, columnspan=1, sticky="nsew")
btn_night_graph = tk.Button(root, width=30, text="Térkép (éjszakai)", font=("Courier", 18), bg="purple", fg="white", command=night_graph_ui)
btn_night_graph.grid(row=5, column=1, columnspan=2, sticky="nsew")


#--------------------Megálló lista-------------------
#megállók listájának feltöltése
update_fro(stop_list)
update_to(stop_list)

#listában szereplő megállóra való kattintás után kitölti a keresőmezőt
frolist.bind("<<ListboxSelect>>", filloutfro)
tolist.bind("<<ListboxSelect>>", filloutto)

#keresőmezőbe gépelés után leszűri a megállók listáját
fro.bind("<KeyRelease>", filterfro)
to.bind("<KeyRelease>", filterto)


root.mainloop()