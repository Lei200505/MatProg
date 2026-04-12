import dijkstra
from itertools import combinations
import graph_viz


source_night = "night_budapest.pkl"
G_night = dijkstra.graf_betoltes(source_night)
routes_dict = dijkstra.routes("./budapest_data/routes.txt")


source = "budapest.pkl"
G = dijkstra.graf_betoltes(source)
def stop_dict_maker(graph):
    stops_dict = {}
    for node in graph.nodes():
        stops_dict[node] = graph.nodes()[node]["stop_name"]
    return stops_dict
stops_dict = stop_dict_maker(G)
stop_list = list(stops_dict.keys())

t = 23*3600 + 57 * 60



"""

path, fenyo = dijkstra.dijkstra(G_night, stop_list[0], '19785', t)
halozat_rajz = graph_viz.GraphViz(G_night, r"./budapest_data")
halozat_rajz.fenyo_viz(fenyo, stop_list[0], '061379', path)

node = '19784'

for u, v, data in G_night.out_edges(node, data=True):
    print(u, "->", v, data)



hiba_parok = ['061379', '118757', '19784274', '19785275', '19785', '19784']
for hibas in hiba_parok:
    try:
        if hibas in G_night.nodes():
            path, fenyo = dijkstra.dijkstra(G_night, stop_list[0], hibas, t)
            halozat_rajz = graph_viz.GraphViz(G_night, r"./budapest_data")
            halozat_rajz.fenyo_viz(fenyo, stop_list[0], hibas, path)
        else:
            print("nincs benne")
            print(hibas)
    except Exception as e:
        print(f"Hiba {e}")
"""


print("Kezdődhet")
hiba_parok = []
szazas = 1
futas = 0
for allomas in stop_list:
    try:
        path = dijkstra.dijkstra(G_night, allomas, stop_list[0], t)
        dijkstra.pretty_path(path[0], stops_dict=stops_dict, routes_dict=routes_dict)
        
        futas += 1
        if futas % 100 == 0:
            print(f"{futas*szazas} siker")
            futas = 0
            szazas += 1
    except Exception as e:
        hiba_parok.append(allomas)
        print(allomas)

print(hiba_parok)