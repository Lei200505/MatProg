import csv
import networkx as nx
import pandas as pd
import pickle
import time
import math

#Adatok betöltése
# Gráf betöltése
def graf_betoltes(fajl):
    with open(fajl, "rb") as f:
        data = pickle.load(f)
    return nx.node_link_graph(data)
# Megállók betöltése
def stops(graph: nx.multidigraph):
    stops_dict = {}
    for node in graph.nodes():
        stops_dict[node] = graph.nodes()[node]["stop_name"]
    return stops_dict
#Járatszamok betöltése
def routes(fajl):
    r_dict = {}
    r = pd.read_csv(fajl, encoding="utf-8", low_memory=False)
    for _, row in r.iterrows():
        r_dict[row["route_id"]] = row["route_short_name"]
    return r_dict
    

#Algoritmus
def dijkstra(graph, graph_night, start, end, start_time):
    # Ha este 10 után indulunk csak az este 22:00-05:00 közötti járatokat nézzük
    #return-ben utolsó szám -1 ha a start vagy end nincs a gráfban, -2 ha nincs út a kettő között,
    # 0 ha van út és nappali, 1 ha van út és éjszakai
    tipus = 0
    if 79200 < start_time < 86400 or start_time < 3 * 3600:
        tipus = 1
        graph = graph_night
    
    if start not in graph.nodes() or end not in graph.nodes(): 
        tipus = -1
        return ([], {}, tipus)
    
    #Algoritmus inicializálása
    vege = False
    
    not_visited = set(graph.nodes()) - {start}
    visited = set([start]) 
    K = {start: start_time}
    
    
    #[elindulási csúcs, aktuális csúcs, None (key), járat száma, járat típusa, (indulási idő, utazási idő)]
    p = {start: [start, start, None, None, None, (start_time, 0)]} 
    
    
    
    #Algoritmus futtatása (amíg elérjük a célt vagy nincs több hely ahova el tudnánk menni)
    while len(visited) > 0 and not vege:
        u = min(visited, key=lambda x: K[x])
        
        # Ha kikerül a végállomás leállunk
        #esetleg breakelni ha még egy iterációt megy
        if u == end:
            vege = True
        visited.remove(u)
        
        # Mivel minden u-v csúcspárra, annyi él van köztük, mint ahány járat megy köztük,
        #így járatonként (data) kell végigiterálni a csúcspárokon/éleken
        for _, v, data in graph.out_edges(u, data=True):
            #Emellett minden párosított megálló-járat párra az élen van az összes indulás ideje
            #Ezeken végig kell iterálni, úgy hogy mindig csak a legelső elérhető járatra szeretnénk felszállni
            for dep_time, duration in data["departures"]:
                # Átszállás és járat esetén:
                if dep_time > K[u] or (dep_time == K[u] and p[u][3] == data["route_id"]):
                    if v in visited and K[v] > dep_time + duration:
                        K[v] = dep_time + duration
                        p[v] = [u, v, None, data["route_id"], data["route_type"], (dep_time, duration)]
                    elif v in not_visited:
                        K[v] = dep_time + duration
                        visited.add(v)
                        not_visited = not_visited - {v}
                        p[v] = [u, v, None, data["route_id"], data["route_type"], (dep_time, duration)]
            
                # Séta esetén:
                elif data["route_type"] == "TRANSFER":
                    if v in visited and K[v] > K[u] + duration:
                        K[v] = K[u] + duration
                        p[v] = [u, v, None, "TRANSFER", "TRANSFER", (K[u], duration)]
                    elif v in not_visited:
                        K[v] = K[u] + duration
                        visited.add(v)
                        not_visited = not_visited - {v}
                        p[v] = [u, v, None, "TRANSFER", "TRANSFER", (K[u], duration)]

    #balint: ezt en irtam bele, hogy ideiglenesen tudjam tesztelni graph_viz.py-t. amikor az egesz script egy fajl lesz mar nem kell
    #with open(r"C:\Users\Lenovo\Desktop\matprogcsom\grafepites\p.txt", "w") as f:
    #    f.write(str(p))
    #path = reconstruct_path(p, start, end)
    #with open(r"C:\Users\Lenovo\Desktop\matprogcsom\grafepites\path.txt", "w") as f:
    #    f.write(str(path))
    
    if not vege:
        tipus = -2
        return ([p[start]], p, tipus)
    else:
        return (reconstruct_path(p, start, end), p, tipus)
    
# Legrövidebb út rekonstruálása a szülőkkel
def reconstruct_path(p, start, end):
    if len(p) == 1:
        return p
    
    # parent szerint visszafejtjük az utat a végétől, amíg elérünk a kiindulási pontba
    path = []
    current = end
    while current != start:
        path.append(p[current])
        current = p[current][0]
    path.append(p[start])
    return path[::-1]

#Az út összehúzása járatok szerint
#p[i] =[elindulasi csúcs, aktuáli csúcs, None (key), járat szama, járat típusa, (indulási idő, utazási idő)]
def pretty_path(p, stops_dict, stops_dict_night, routes_dict, tipus):
    if tipus == -1:
        return f"A start vagy end nincs a gráfban"
    if tipus == -2:
        return f"Nincs út a két megálló között"
    if len(p) == 1:
        return f"Ugyanaz a két megálló"
    if tipus == 1:
        stops_dict = stops_dict_night
    
    #Inicializálás
    #[elindulási csúcs, [köztes megállók], leszállási csúcs, járat száma, járat típusa, [elindulási idő, köztes megallók érkezési ideje, érkezési idő]]
    pretty = [ [p[1][0], [], p[1][1], p[1][3], p[1][4], [p[1][-1][0], p[1][-1][0]+p[1][-1][1]] ] ]
    
    #Végigiterálunk az éleken
    for i in range(2, len(p)):
        # Ha az előző élen ugyanazzal a járművel mentünk, akkor úgy vesszük, hogy ezek egy járathoz tartoznak
        if p[i][3] == p[i-1][3]:
            pretty[-1][1].append(p[i][0]) #él kezdőállomását hozzáadjuk a köztes megállókhoz 
            pretty[-1][2] = p[i][1] #a végállomást a járathoz átállítjuk az új él végpontjába
            pretty[-1][-1][-1] = p[i][-1][0] # Indulási idejét az élnek kicseréljük a menetrendben az eddigi végére
            pretty[-1][-1].append(p[i][-1][0]+p[i][-1][1]) #és a beérkezést a végére rakjuk
        # Különben új járatra szállunk
        else:
            pretty.append([p[i][0], [], p[i][1], p[i][3], p[i][4], [p[i][-1][0], p[i][-1][0]+p[i][-1][1]]])

    
    #Kiíratás
    output = f""
    
    output += f"Teljes idő: {math.ceil((pretty[-1][-1][-1] - pretty[0][-1][0])/60)} perc\n"
    output += f"  Indulás: {pretty_time(pretty[0][-1][0])}\n"
    output += f"  Érkezés: {pretty_time(pretty[-1][-1][-1])} \n\n"
    
    
    for jarat in pretty:
        # Séta esetén
        if jarat[3] == "TRANSFER":
            output += f"Séta {stops_dict[jarat[2]]} megállóig [{math.ceil((jarat[-1][-1] - jarat[-1][0])/60)} perc] "
            output += f"Érkezés : {pretty_time(jarat[-1][-1])}\n"
        
        # Járattípusok szerint
        else:
            output += f"{routes_dict[jarat[3]]} {transport_conversion(jarat[4])} : {stops_dict[jarat[0]]} megállótól "
            output += f"{stops_dict[jarat[2]]} megállóig  [{math.ceil((jarat[-1][-1] - jarat[-1][0])/60)} perc]\n"
            
            output += f"\t -{stops_dict[jarat[0]]} - {pretty_time(jarat[-1][0])}\n"
            for megallo in range(len(jarat[1])):
                output += f"\t -{stops_dict[jarat[1][megallo]]} - {pretty_time(jarat[-1][megallo+1])}\n"
            output += f"\t -{stops_dict[jarat[2]]} - {pretty_time(jarat[-1][-1])}\n"
    return output
def pretty_time(t):
    if t > 86400:
        t = t - 86400
        h = t // 3600
        m = (t % 3600) // 60
        s = t % 60
        if s != 0:
            return f"{h:02d}:{m:02d}:{s:02d} (+1)"  
        else:
            return f"{h:02d}:{m:02d} (+1)"

    h = t // 3600
    m = (t % 3600) // 60
    s = t % 60
    if s != 0:
        return f"{h:02d}:{m:02d}:{s:02d}"  
    else:
        return f"{h:02d}:{m:02d}"
def transport_conversion(id):
    if id == 3:
        return "busz"
    if id == 0:
        return "villamos"
    if id == 11:
        return "trolibusz"
    if id == 109:
        return "hév"
    if id == 1:
        return "metró"


if __name__ == "__main__":
    print("Teszt fut")
    source = "budapest.pkl"
    source_night = "night_budapest.pkl"
    G = graf_betoltes(source)
    stops_dict = stops(G)
    G_night = graf_betoltes(source_night)
    stops_dict_night = stops(G_night)
    routes_dict = routes("./budapest_data/routes.txt")

    s = '098527'
    v = 'F00147'
    t = 23*3600 + 57 * 60
    path = dijkstra(G, G_night, s, v, t)
    print(pretty_path(path[0], stops_dict=stops_dict, stops_dict_night=stops_dict_night, routes_dict=routes_dict, tipus=path[2]))

    #kb 0.001 mp futásidő

