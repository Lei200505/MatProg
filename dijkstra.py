import csv
import networkx as nx
import pickle
import time
import math

#Adatok betöltése
# Gráf betöltése
def graf_betoltes(fajl, fajl_nighttime, t):
    #Amennyiben este 10 után indulunk csak az este 22:00-05:00 közötti járatokat nézzük
    #Így könnyebb a napváltást implementálni az algoritmusban
    
    if 79200 < t <  86400:
        fajl = fajl_nighttime
    with open(fajl, "rb") as f:
        data = pickle.load(f)
    return nx.node_link_graph(data)
# Megállók betöltése
def stops(graph: nx.multidigraph):
    stops_dict = {}
    for node in graph.nodes():
        stops_dict[node] = G.nodes()[node]["stop_name"]
    return stops_dict


#Járatszamok betöltése
def routes(fajl):
    r_dict = {}
    with open(fajl, "r", encoding="utf-8") as f:
        for line in f:
            r_id, r_name = line.strip().split(": ")
            r_dict[r_id] = r_name
    return r_dict



#Algoritmus
def dijkstra(graph, start, end, start_time):
    #Inicializáció
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
        for u, v, data in graph.out_edges(u, data=True):
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
        raise ValueError("Nincs út")
    else:
        return (reconstruct_path(p, start, end), p)
# Legrövidebb út rekonstruálása a szülőkkel
def reconstruct_path(p, start, end):
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
def pretty_path(p, stops_dict, routes_dict):
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
    start_1 = time.time()
    source = "budapest.pkl"
    source_night = "night_budapest.pkl"
    G = graf_betoltes(source, source_night, time.time())
    end_1 = time.time()

    start_2 = time.time()
    stops_dict = stops(G)
    #print(G.edges("009459", data=True))
    #print(G.edges("004952", data=True))
    routes_dict = {}
    with open("./budapest_data/routes.txt", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        for line in reader:
            routes_dict[line['route_id']] = line['route_short_name']
    end_2 = time.time()

    start_3 = time.time()
    print("Start benne van:", '006390' in G.nodes())
    print("End benne van:", '009684' in G.nodes())
        
        
    path = dijkstra(G, '006390', '009684', 8*3600)
    end_3 = time.time()

    start_4 = time.time()
    #kb 0.001 mp futásidő
    print(pretty_path(path[0], stops_dict=stops_dict, routes_dict=routes_dict))
    end_4 = time.time()

    print(f"Gráf betöltése: {end_1-start_1}")
    print(f"Egyéb betöltés: {end_2 - start_2}")
    print(f"Dijkstra: {end_3-start_3}")
    print(f"Kiírás: {end_4-start_4}")
    print(f"Egész algoritmus futásideje: {end_4-start_1} mp")
