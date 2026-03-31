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
