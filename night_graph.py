import numpy as np
import networkx as nx
import pandas as pd
import pickle
from scipy.spatial import cKDTree
import json
import os

class Graph:
    def __init__(self, source_folder):
        self.output_folder = source_folder
        self.stop_times = pd.read_csv(f"{source_folder}/stop_times.txt", encoding="UTF-8", low_memory=False)
        self.stops = pd.read_csv(f"{source_folder}/stops.txt", encoding="UTF-8", low_memory=False)
        self.trips = pd.read_csv(f"{source_folder}/trips.txt", encoding="UTF-8", low_memory=False)
        self.routes = pd.read_csv(f"{source_folder}/routes.txt", encoding="UTF-8", low_memory=False)

    def time_from_str(self, times: list):
        out = []
        for t in times:
            h, m, s = map(int, t.split(":"))
            out.append(3600 * h + 60 * m + s)
        return out

    def edge_list(self):
        edges = []
        stop_times_sorted = self.stop_times.sort_values(["trip_id", "stop_sequence"])

        for trip_id, group in stop_times_sorted.groupby("trip_id"):

            stops_list = list(group['stop_id'])
            arr_times = list(self.time_from_str(group["arrival_time"]))
            dep_times = list(self.time_from_str(group["departure_time"]))

            #az ejszakai jaratok modellezesere csak az este 22:00 es reggel 5:00 kozotti jaratok kerulnek bele
            for i in range(len(stops_list)-1):
                if dep_times[i] <= 18000 or dep_times[i] >= 79200:
                    edge = {
                        "from_stop": stops_list[i],
                        "to_stop": stops_list[i+1],
                        "departure_time": dep_times[i],
                        "arrival_time": arr_times[i+1],
                        "trip_id": trip_id
                    }
                    edges.append(edge)
                else:
                    continue

        edges_df = pd.DataFrame(edges)


        edges_df = edges_df.merge(
            self.trips[["trip_id", "route_id"]],
            on="trip_id",
            how="left"
        )

        edges_df = edges_df.merge(
            self.routes[["route_id", "route_type"]],
            on="route_id",
            how="left"
        )

        edges_collapsed = (
            edges_df
            .groupby(["from_stop", "to_stop", "route_id", "route_type"])
            .apply(lambda group: list(zip(group["departure_time"], group["arrival_time"], group["trip_id"])))
            .reset_index(name="departures")
        )


        transfer_edges = self.transfer_edges()
        if transfer_edges:
            edges_collapsed = pd.concat(
                [edges_collapsed, pd.DataFrame(transfer_edges)],
                ignore_index=True
            )
        
        return edges_collapsed


    # https://en.wikipedia.org/wiki/Geographic_coordinate_system
    #az ejszakai menetrendet kicsit mas parameterekkel allitjuk be:
    #mivel az ejszakai buszhalozat kevesbe jol lefedett, ezert messzebbre leszunk hajlandoak elmenni gyalog
    #de lassabban is, hogy ne preferalja a vegigsetalast
    def transfer_edges(self, max_transfer_dist = 1250, max_walking_speed = 1):
        coords = self.stops[["stop_lat", "stop_lon"]].to_numpy()
        tree = cKDTree(coords)

        stop_ids = self.stops["stop_id"].to_numpy()

        meters_per_degree = 111000 #ez becsles, wiki: lat: 110.6 km/deg, lon: 111.3 km/deg
        radius_deg = max_transfer_dist / meters_per_degree

        neighbors_list = tree.query_ball_point(coords, radius_deg)
        edges = []

        for i, neighbors in enumerate(neighbors_list):
            neighbors = [j for j in neighbors if j != i]

            if neighbors == []:
                continue
            
        
            dists = np.linalg.norm(coords[neighbors] - coords[i], axis=1) * meters_per_degree
            travel_times = (dists / max_walking_speed).astype(int)
            edges.extend([
                {"from_stop": stop_ids[i],
                 "to_stop": stop_ids[j],
                 "route_id": "TRANSFER",
                 "route_type": "TRANSFER",
                 "departures": [(0, t, "TRANSFER")],}
                for j, t in zip(neighbors, travel_times)
            ])
        
        return edges
        
    def graph(self, edgelist):
        G = nx.MultiDiGraph()
        for row in edgelist.itertuples(index = False):
            dep_list = sorted([(int(dep), int(arr - dep)) for dep, arr, _ in row.departures], key=lambda x: x[0])

            #hogy folytatolagosan modellezzunk, minden 0:00 es 5:00 kozotti indulashoz hozzaadunk 1 napot
            for departure in dep_list:
                dep = departure[0]
                cost = departure[1]
                if dep >=0 and dep <= 18000:
                    dep_list.append((dep + 86400, cost))

            dep_list = sorted(dep_list, key= lambda x: x[0])

            G.add_edge(
                row.from_stop,
                row.to_stop,
                key=row.route_id,
                route_id=row.route_id,
                route_type=row.route_type,
                departures=dep_list
            )
        stop_name_map = dict(zip(self.stops["stop_id"], self.stops["stop_name"]))
        nx.set_node_attributes(G, stop_name_map, name="stop_name")

        remove = []
        for node in G.nodes():
            edges = list(G.out_edges(node, data=True))

            if len(edges) ==0:
                remove.append(node)
                continue
            
            #if all(data["route_type"]=="TRANSFER" for u, v, data in edges):
            #    remove.append(node)

        G.remove_nodes_from(remove)
        return G
    
    def save_graph(self, out_loc=None, fname = "night_budapest.pkl"):

        if out_loc is None:
            out_loc = self.output_folder

        path = os.path.join(out_loc, fname)

        edges = self.edge_list()
        G = self.graph(edges)

        data = nx.node_link_data(G)

        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        print("File saved successfully at:", path)

        with open(os.path.join(out_loc, "night_budapest.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)


source = "budapest_data"
out_loc = "."
graph = Graph(source)
graph.save_graph(out_loc)