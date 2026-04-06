import numpy as np
import networkx as nx
import pickle
import time
import math

#Adatok betöltése
# Gráf betöltése
def graf_betoltes(fajl, fajl_nighttime, t):
    #Amennyiben este 10 után indulunk csak az este 22:00-05:00 közötti járatokat nézzük
    #Így könnyebb a napváltást implementálni az algoritmusban
    
    
    #start = time.time() <-- más a függvény futása mint ez
    if 79200 < t <  86400:
        fajl = fajl_nighttime
    with open(fajl, "rb") as f:
        data = pickle.load(f)
    #end = time.time()
    #print("A gráf betöltése:", end - start, "másodperc")
    return nx.node_link_graph(data)
# Megállók betöltése
def stops(fajl):
    stops_dict = {}
    with open(fajl, "r", encoding="utf-8") as f:
        for line in f:
            stop_id, name = line.strip().split(": ")
            stops_dict[stop_id] = name
    return stops_dict


#Algoritmus
def dijkstra(graph, start, end, start_time):
    #alg_start = time.time()
    #Inicializáció
    vege = False
    
    not_visited = set(graph.nodes()) - {start}
    visited = set([start])
    #esetleg heapq is jo lehet 
    K = {start: start_time}
    
    
    #[elindulasi csucs, aktualis csucs, None (key), jarat szama, jarat tipusa, (indulasi ido, utazasi ido)]
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
        for u, v, data in G.out_edges(u, data=True):
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
    #alg_end = time.time()
    #print(f"Az algoritmus futásideje: {alg_end - alg_start}")
    return (reconstruct_path(p, start, end), p)
# Legrövidebb út rekonstruálása a szülőkkel
def reconstruct_path(p, start, end):
    path = []
    current = end
    while current != start:
        path.append(p[current])
        current = p[current][0]
    path.append(p[start])
    return path[::-1]


#Az út összehúzása járatok szerint
#p[i] =[elindulasi csúcs, aktuáli csúcs, None (key), járat szama, járat típusa, (indulási idő, utazási idő)]
def pretty_path(p):
    #Inicializálás
    #[elindulási csúcs, [köztes megállók], leszállási csúcs, járat száma, járat típusa, [elindulási idő, köztes megallók érkezési ideje, érkezési idő]]
    pretty = [ [p[1][0], [], p[1][1], p[1][3], p[1][4], [p[1][-1][0], p[1][-1][0]+p[1][-1][1]] ] ]
    for i in range(2, len(p)):
        if p[i][3] == p[i-1][3]:
            pretty[-1][1].append(p[i][0])
            pretty[-1][2] = p[i][1]
            pretty[-1][-1][-1] = p[i][-1][0]
            pretty[-1][-1].append(p[i][-1][0]+p[i][-1][1])
        else:
            pretty.append([p[i][0], [], p[i][1], p[i][3], p[i][4], [p[i][-1][0], p[i][-1][0]+p[i][-1][1]]])

    
    #Kiíratás
    for jarat in pretty:
        if jarat[3] == "TRANSFER":
            print(f"Séta {id_to_name(stops_dict,jarat[2])} megállóig [{math.ceil((jarat[-1][-1] - jarat[-1][0])/60)} perc]")
        #járattípusok szerint
        else:
            print(f"{id_to_name(routes_dict, jarat[3])} {transport_conversion(jarat[4])} : {id_to_name(stops_dict, jarat[0])} megállótól {id_to_name(stops_dict, jarat[2])} megállóig  [{math.ceil((jarat[-1][-1] - jarat[-1][0])/60)} perc]")
def pretty_time(t):
    h = t // 3600
    m = (t % 3600) // 60
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:02d}"     
def id_to_name(di, id):
    return di[id]
#Járatszamok betöltése
def routes(fajl):
    r_dict = {}
    with open(fajl, "r", encoding="utf-8") as f:
        for line in f:
            r_id, r_name = line.strip().split(": ")
            r_dict[r_id] = r_name
    return r_dict
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


#Nem kell
#def kiiras(p):
#    for step in p:
#        print(f"Indulás-Érkezés: {pretty_time(step[5][0])}-{pretty_time(step[5][0] + step[5][1])}, "
#              f"járat:{step[3]} (járattípus: {step[4]}) - {step[1]}")


start_0 = time.time()
start_1 = time.time()
source = "budapest.pkl"
source_night = "night_budapest.pkl"
G = graf_betoltes(source, source_night, time.time())
end_1 = time.time()
print(f"Gráf betöltése: {end_1-start_1}")

start_2 = time.time()
stops_dict = stops("stops_out.txt")
routes_dict = routes("./routes_out.txt")
end_2 = time.time()
print(f"Egyéb betöltés: {end_2 - start_2}")


start_3 = time.time()
path = dijkstra(G, '008280', '009684', 8*3600)
end_3 = time.time()
print(f"Dijkstra: {end_3-start_3}")

start_4 = time.time()
#kb 0.001 mp futásidő
pretty_path(path[0])
end_4 = time.time()
print(f"Kiírás: {end_4-start_4}")

end_0 = time.time()
print(f"Egész algoritmus futásideje: {end_0-start_0} mp")
print(f"Összeg: {end_1-start_1 + end_2-start_2+end_3-start_3+end_4-start_4} mp")