import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import os

class GraphViz:
    def __init__(self, G: nx.MultiDiGraph, source_folder : str):
        self.stops = pd.read_csv(os.path.join(source_folder, "stops.txt"), encoding="UTF-8", low_memory=False)
        self.routes = pd.read_csv(os.path.join(source_folder, "routes.txt"), encoding="UTF-8", low_memory=False)
        self.G = G
    
    def viz(self):
        pos = {row["stop_id"]: (row["stop_lon"], row["stop_lat"]) for _, row in self.stops.iterrows()}
        plt.figure(figsize=(12,12))

        bus_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_type"]==3]
        tram_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_type"]==0]
        metro_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_type"]==1]
        trolley_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_type"]==11]
        hev_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_type"]==109]
        transfer_edges = [(u,v) for u, v, d in self.G.edges(data=True) if d["route_id"] == "TRANSFER"]

        nx.draw_networkx_edges(self.G, pos, edgelist=bus_edges, edge_color = "blue", arrows = False, alpha=0.3)
        nx.draw_networkx_edges(self.G, pos, edgelist=tram_edges, edge_color = "yellow", arrows = False, alpha=0.3)
        nx.draw_networkx_edges(self.G, pos, edgelist=metro_edges, edge_color = "black", arrows = False, alpha=0.6)
        nx.draw_networkx_edges(self.G, pos, edgelist=trolley_edges, edge_color = "red", arrows = False, alpha=0.3)
        nx.draw_networkx_edges(self.G, pos, edgelist=hev_edges, edge_color = "green", arrows = False, alpha=0.3)
        nx.draw_networkx_edges(self.G, pos, edgelist=transfer_edges, edge_color = "gray", arrows = False, alpha=0.3)

        nx.draw_networkx_nodes(self.G, pos, node_size=2, node_color="#444444")
        plt.axis("off")
        plt.show()


source = r"C:\Users\Lenovo\Desktop\matprogcsom\budapest data"
with open(f"{source}/night_budapest.pkl", "rb") as f:
    data = pickle.load(f)

G = nx.node_link_graph(data)

h  = GraphViz(G, source_folder=source)
h.viz()

        
        
        