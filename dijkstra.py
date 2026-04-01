import numpy as np
import networkx as nx
import json
import time

start = time.time()

with open("budapest.json", "r", encoding="UTF-8") as f:
    data = json.load(f)

G = nx.node_link_graph(data)

end = time.time()
print("A gráf betöltése:", end - start, "másodperc")


start = time.time()
def dijkstra(graph, start, end, start_time):
    jelen = start_time
    bekerult = 0
    kikerult = 0
    
    
    non_visited = G.nodes()
    visited = set([start])
    K = {start: start_time}
    while visited:
        u = min(visited, key=lambda x: K[x])
        if u == end:
            kikerult = 1
        visited.remove(u)
        
        
        for u, v, key, data in G.out_edges(u, keys=True, data=True):
            print(f"u: {u}, v: {v}, key: {key}, data: {data}")
            #for dep_time, duration in data["departures"]:
                #if dep_time >= jelen:
                #   print(f"Jelen: {jelen}, u: {u}, v: {v}, dep_time: {dep_time}, duration: {duration}")
                #   break
    
    
dijkstra(G, 'F03971', '008280', 6000)
end = time.time()
print("Dijkstra algoritmus futtatása:", end - start, "másodperc")


print("-"*50)
print("-"*50)




start = time.time()
nx.dijkstra_path(G, 'F04023', 'F04365')
end = time.time()
print("Dijkstra algoritmus futtatása 2:", end - start, "másodperc")