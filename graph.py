import numpy as np
import networkx as nx
import pandas as pd
from scipy.spatial import cKDTree
import pickle
import json
import os

class Graph:
    def __init__(self, source_folder):
        self.output_folder = source_folder
        #a grafepitesre az alabbi negy fajlra van szuksegunk amelyet pandas dataframe formatumban fogunk tarolni
        #stop_times-ban konkret viszonlatonkent (pl 8:15-kor Orsrol indulu M2) a megallo szekvencia
        #stops ban minden megallo egyeni azonositoja, koordinitai
        #a tripsben talalhatoak a viszonylatok altalanos osszegyujtese, azaz honnan hova megy es mikor
        #a routesban talalhatoak a kulonbozo jaratok kulonbozo iranyai
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
        #az alabbi metodus ellistat ad amelybol a networkx sajat beepitett graf adatstrukturajat fel tudjuk epiteni

        #a stop_times standard GTFS file
        #fo informacioja egy konkret viszonylatazonosito (pl: 10:00:00-kor, Puskas fele indulu 75-os trolinak van egy egyedi azonositoja)
        #megallok egy szekvenciaja, azaz elso megallo: jaszai mari ter, masodik megallo: radnoti miklos utca, stb.
        #a megallokat technikai azonositokkal melyet self.stops-ban tudunk majd elerni, nevere visszavaltani, illetve azzal meghivni
        stop_times_sorted = self.stop_times.sort_values(["trip_id", "stop_sequence"])

        for trip_id, group in stop_times_sorted.groupby("trip_id"):

            stops_list = list(group['stop_id'])
            arr_times = list(self.time_from_str(group["arrival_time"]))
            dep_times = list(self.time_from_str(group["departure_time"]))


            for i in range(len(stops_list)-1):
                edge = {
                    "from_stop": stops_list[i],
                    "to_stop": stops_list[i+1],
                    "departure_time": dep_times[i],
                    "arrival_time": arr_times[i+1],
                    "trip_id": trip_id
                }
                edges.append(edge)

        #most benne van: kiindulo megallo, erkezo megallo, erkezes ideje, indulas ideje, illetve a viszonylatszam
        edges_df = pd.DataFrame(edges)


        #a viszonylatszamokhoz kiirjuk a jaratszamot is
        #pl: 12356ABC egy 7.00-kor indulo hetes busz, ehhez kiirjuk a hetesbusz jaratkodjat
        edges_df = edges_df.merge(
            self.trips[["trip_id", "route_id"]],
            on="trip_id",
            how="left"
        )

        #bekerul meg az adott el tipusa is, hogy visszakovethetobb legyen, illetve vizualizacional is benne legyen
        #route_type = 0: villamos
        #route_type = 1: metro
        #route_type = 3: busz
        #route_type = 11: troli
        #route_type = 109: hev
        edges_df = edges_df.merge(
            self.routes[["route_id", "route_type"]],
            on="route_id",
            how="left"
        )

        #most pedig egy olyan tomb kell nekunk, amiben benne vannak a konkret elek, jaratonkent egy:
        #1 rekord igy fog kinezni:
        #kiindulo megallo, erkezesi megallo (konkret uv el), indulasi ido, erkezesi ido parok a nap folyaman, / jaratszam
        #Szentlelek ter - Florian ter, 237-es busz, [(7:00, 7:05 viszonylat_id), (7:20, 7:25, viszonlat_id),...]
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
    def transfer_edges(self, max_transfer_dist = 200, max_walking_speed = 1.5):
        #stops tarolja minden megallo (csucs) szelessegi es hosszusagi koordinatait
        #ezeket egy numpy tombbe, majd ckdtreeben fogjuk tarolni
        coords = self.stops[["stop_lat", "stop_lon"]].to_numpy()
        #a ckdtree egy scipy.spatial-beli osztaly, ami nagyon gyorsan lehetove teszi az adott tavolsagra levo pontok elereset
        #eloszor for ciklusos implementacio volt, es az 45 percig futottatta az O(n^2) csucsparra
        tree = cKDTree(coords)

        stop_ids = self.stops["stop_id"].to_numpy()

        #ezzel a becslessel fogjuk gombi koordinatak/meterek kozott atvaltani
        meters_per_degree = 111000 #ez becsles, wiki: lat: 110.6 km/deg, lon: 111.3 km/deg
        radius_deg = max_transfer_dist / meters_per_degree

        #a ckdtree.query_ball_point egy B(x, r) gombot ad meg a mar atvaltott tavolsag szerint
        #alapertelmezve legfeljebb 200m-es atszallasokat engedelyezunk
        #korabban kiprobualtunk 100m-t de akkor viszonylag trivialis atszallasok (pl Jaszai troli megallo - Jaszai 4-6 megallo) kimaradtak
        #minden koordinataparra (csucs a grafban) megadjuk azon koordinataparokat (csucsokat a grafban), amelyek <=200m-re vannak
        neighbors_list = tree.query_ball_point(coords, radius_deg)
        edges = []

        #eleket epitunk a kozeli pontok kozott
        for i, neighbors in enumerate(neighbors_list):
            #kidobjuk onmagat
            neighbors = [j for j in neighbors if j != i]

            #van olyan pont, amelynek nincsenek szomszedjai
            #ez viszonylag ritka, altalaban iranyonkent 1-1 csucs van kulon
            #ez alol kivetelt kepeznek pl. a rackevei hev megallo, ahol bar 1 megallo van mindket iranynak, megis fel van veve ket csucs
            #ezeket a pontokat skippeljuk
            if neighbors == []:
                continue
            
            
            #kiszamoljuk a tavolasagot, majd az el koltsege az tavolsag / walking_speed ami 1.5m/s alapbol
            #az atszallasi eleket kulon "TRANSFER" attributummal jeloljuk
            #a departure times mindossze 0, ezt a dijkstranak majd kulon kell keznie
            #azaz a transfer edgeket MINDIG lehet hasznalni majd
            dists = np.linalg.norm(coords[neighbors] - coords[i], axis=1) * meters_per_degree
            travel_times = (dists / max_walking_speed).astype(int)
            #egyebkent az adatstruktura a fenti kulonbsegeken kivul megegyezik a sima elekkel
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
        #mivel vannak parhuzamos elek: 7-es es 8-as busznak is van keleti-huszar utca ele
        #ezert nx.MultiDiGraph kell
        G = nx.MultiDiGraph()
        for row in edgelist.itertuples(index = False):
            #rendezzunk az indulasi idoket departure time szerint
            dep_list = sorted([(int(dep), int(arr - dep)) for dep, arr, _ in row.departures], key=lambda x: x[0])
            #ezek utan egy el ugy nez ki, hogy:
            #melyik csucsbol -> melyikbe
            #key az csak technikai, hogy ne zavarja ossze a networkx-et, enelkul nehany elet egymasba nyomott
            #route_id: hanyas jarat, pl 7es busz vagy H6 hev
            #route_type: busz/metro/vili/troli/hev
            #departures: lista az indulo jaratokrol: [(mikor indul, mennyi ido aterni), (10:10:12, 60), (11:10:12, 60),...]
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
            
            if all(data["route_type"]=="TRANSFER" for u, v, data in edges):
                remove.append(node)

        G.remove_nodes_from(remove)
        return G
    
    #elmentjuk a grafot egy .pkl-be
    #eredileg json-be akartunk menteni, de teszteles utan akar 3x gyorsitast kaptunk
    #ehhez kell os es pickle package
    #ebbol utana with open(path, "r", utf-8) as f: data = pickle.load(f)-el visszanyerheto
    #majd nx objektum: G=nx.node_link_graph(data)-val nx grafot lehet visszakapni
    def save_graph(self, out_loc=None, fname = "budapest.pkl"):

        if out_loc is None:
            out_loc = self.output_folder

        path = os.path.join(out_loc, fname)

        edges = self.edge_list()
        G = self.graph(edges)

        data = nx.node_link_data(G)


        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        print("File saved successfully at:", path)

        with open(os.path.join(out_loc, "budapest.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)



source = "./budapest_data"
out_loc = "."
g = Graph(source)

g.save_graph(out_loc)