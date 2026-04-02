import numpy as np
import networkx as nx
import json
import time
import heapq


# Gráf betöltése
def graf_betoltes(fajl):
    start = time.time()
    with open(fajl, "r", encoding="UTF-8") as f:
        data = json.load(f)
    end = time.time()
    print("A gráf betöltése:", end - start, "másodperc")
    return nx.node_link_graph(data)




#implementálni éjfélt
def dijkstra(graph, start, end, start_time):
    #Inicializáció
    vege = False
    
    not_visited = set(graph.nodes()) - {start}
    visited = set([start])
    #esetleg heapq is jo lehet 
    K = {start: start_time}
    
    
    #[elindulasi csucs, aktualis csucs, erkezes ideje, jarat szama, jarat tipusa, (indulasi ido, utazasi ido)]
    p = {start: [start, start, None, None, None, (start_time, 0)]} 
    
    
    
    #Algoritmus futtatása
    while len(visited) > 0 and not vege:
        u = min(visited, key=lambda x: K[x])
        if u == end:
            vege = True
        visited.remove(u)
        
        
        for u, v, key, data in G.out_edges(u, keys=True, data=True):
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
    return reconstruct_path(p, start, end)
    
def reconstruct_path(p, start, end):
    path = []
    current = end
    while current != start:
        path.append(p[current])
        current = p[current][0]
    path.append(p[start])
    return path[::-1]

def kiiras(p):
    for step in p:
        print(f"Indulás: {step[5][0]} - {step[3]} ({step[4]}) - Érkezés: {step[5][0] + step[5][1]} - {step[1]}")


G = graf_betoltes("budapest.json")
path = dijkstra(G, 'F01163', 'F02112', 43200)
kiiras(path)



