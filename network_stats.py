import collections
import itertools
import json
import os.path
import csv
from typing import Callable
from collections import Counter

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from gerrychain.graph import Graph
from networkx.readwrite import json_graph
import us
from tqdm.auto import tqdm

GEOGRAPHIES = {
    "county": {"graph": "cnty", "shapefile": "county20"},
    "tract":  {"graph": "t", "shapefile": "tract"},
    "block":  {"graph": "b", "shapefile": "tabblock20"},
    "blockgroup": {"graph": "bg", "shapefile": "bg"},
    "vtd": {"graph": "vtd", "shapefile": "vtd20"}
}

def import_graph(geog: str, state: us.states.State, path = None):
    if path is not None:
        f = open(path)
    else:
        f = open(f'./data/{geog}_graphs/{GEOGRAPHIES[geog]["graph"]}_{state.abbr.lower()}.json')

    j = json.load(f)
    G = json_graph.adjacency_graph(j)

    G.graph['geog'] = geog
    G.graph['state_abbrev'] = state.abbr.lower()

    return G

def generate_degree_histogram(G: nx.Graph, figwidth=15):
    geog, state_abbrev = [G.graph['geog'], G.graph['state_abbrev']]

    degree_sequence = sorted([d for n, d in G.degree()], reverse=True) 

    degreeCount = collections.Counter(degree_sequence)
    deg, cnt = zip(*degreeCount.items())

    fig, ax = plt.subplots()
    plt.bar(deg, cnt, width=0.80, color='b')

    plt.title(f"{state_abbrev.upper()} {geog.title()} Degree Histogram")
    plt.ylabel("Count")
    plt.xlabel("Degree")
    ax.set_xticks([d for d in deg])
    ax.set_xticklabels(deg, rotation=-80)

    # draw graph in inset
    plt.axes([0.4, 0.4, 0.5, 0.5])
    fig.set_figwidth(figwidth)
    plt.axis('off')


    os.makedirs("output/histograms/degree/", exist_ok=True)    
    plt.savefig(f'./output/histograms/degree/{state_abbrev}_{geog}.png')
    plt.close()

def generate_clustering_scatter(G: nx.Graph):
    geog, state_abbrev = [G.graph['geog'], G.graph['state_abbrev']]

    degree_sequence = sorted([d for n, d in G.degree()], reverse=True) 
    clustering_by_deg = [(G.degree[n], c*(G.degree[n]-1)/2) for n, c in nx.clustering(G).items()]
    x_vals = [x[0] for x in clustering_by_deg]
    y_vals = [x[1] for x in clustering_by_deg]

    degreeCount = collections.Counter(degree_sequence)
    deg, _ = zip(*degreeCount.items())

    fig, ax = plt.subplots()
    plt.scatter(x_vals, y_vals, s =10)

    plt.title(f"{state_abbrev.upper()} {geog.title()} Clustering By Degree")
    plt.ylabel("Clustering Coefficient")
    plt.xlabel("Degree")
    ax.set_xticks([d for d in deg])
    ax.set_xticklabels(deg)

    # draw graph in inset
    plt.axes([0.4, 0.4, 0.5, 0.5])
    fig.set_figwidth(15)
    plt.axis('off')
        
    os.makedirs("output/scatters/clustering/", exist_ok = True)
    plt.savefig(f'./output/scatters/clustering/{state_abbrev}_{geog}.png')
    plt.close()

def n_common_neighbors(G: nx.Graph, n1, n2):
    return len(set(G.neighbors(n1)).intersection(G.neighbors(n2)))

def is_windowpaneish(G: nx.Graph, node):
    if G.degree[node] != 4:
        return False
    elif nx.clustering(G, node) != 0:
        return False
    else:
        nbhd  = G.neighbors(node)
        pairs = set(itertools.combinations(nbhd, 2))
        trim  = [n_common_neighbors(G, *ns) for ns in pairs]

        return sum(1 for x in trim if x > 1) >= 4

def is_half_wheely(G: nx.Graph, node):
    return (nx.triangles(G, node) >= 10 and G.degree[node] >= 10)

def list_nodes(G: nx.Graph, property_fn):
    return list(filter(lambda node: property_fn(G, node), G.nodes()))

def generate_csv(G: nx.Graph, property_fn):
    nodes = list_nodes(G, property_fn)
    geoids = [G.nodes[n]["GEOID20"] for n in nodes]
    geog, state = [G.graph["geog"], us.states.lookup(G.graph["state_abbrev"])]

    os.makedirs("output/csvs", exist_ok=True)

    with open(f"output/csvs/{property_fn.__name__}/{state.abbr.lower()}_{geog}.csv") as file:
        w = csv.writer(file)
        w.writerows([[g] for g in geoids])

def generate_shp(G: nx.Graph, property_fn):
    nodes = list_nodes(G, property_fn)
    degrees = [G.degree[node] for node in nodes]
    geoids = [G.nodes[n]["GEOID20"] for n in nodes]
    pd.DataFrame.from_dict(geoids)
    geog, state = [G.graph["geog"], us.states.lookup(G.graph["state_abbrev"])]
    gdf   = gpd.GeoDataFrame.from_file(f"./data/{geog}_shapefiles/tl_2020_{state.fips}_{GEOGRAPHIES[geog]['shapefile']}/tl_2020_{state.fips}_{GEOGRAPHIES[geog]['shapefile']}.shp")

    if "GEOID20" in gdf.columns:
        output_gdf = gdf[gdf["GEOID20"].isin(geoids)].copy()
    else:
        output_gdf = gdf[gdf["GEOID"].isin(geoids)].copy()

    output_gdf["degree"] = degrees

    os.makedirs(f"output/shapefiles/{property_fn.__name__}/{state.abbr.lower()}_{geog}/", exist_ok=True)
    output_gdf.to_file(f"output/shapefiles/{property_fn.__name__}/{state.abbr.lower()}_{geog}/{state.abbr.lower()}_{geog}.shp")

def l_infty_ball(G, c):
    eg = nx.ego_graph(G, c, radius=2)
    ball = eg.__class__()
    ball.add_nodes_from(eg)
    ball.add_edges_from(eg.edges)

    for n in list(ball.nodes()):
        if ball.degree(n) == 1 and n != c:
            ball.remove_node(n)
    
    nx.set_node_attributes(ball, dict(zip(ball, [n == c for n in list(ball.nodes())])), "center")

    return ball

def ball_iso_types(G):
    iso_classes = []
    # lens = []
    # balls = [l_infty_ball(G, n) for n in tqdm(list(G.nodes()))]

    # for ball in tqdm(balls):
    #     lens.append(len(ball.nodes()))

    # print(Counter(lens))

    for n in tqdm(list(G.nodes())):
        ball = l_infty_ball(G, n)

        # print(f"check iso with {len(iso_classes)} balls")
        if len(ball.nodes()) == 15:
            for idx, c in enumerate(iso_classes):
                # print(idx)

                if nx.vf2pp_is_isomorphic(c, ball, node_label="center"):
                    nx.set_node_attributes(G, {n: idx}, "nbhd_type")
                    break
            else:
                # print("no match, adding...")
                iso_classes.append(ball)
                nx.set_node_attributes(G, {n: len(iso_classes)-1}, "nbhd_type")
    
    G.graph["ball_iso_classes"] = iso_classes
    return G       

def apply_to_all(fn: Callable[[nx.Graph], None], property_fn, states: list[us.states.State], geogs: list[str]):
    for state in states:
        for geog in geogs:
            if os.path.isfile(f"./data/{geog}_graphs/{GEOGRAPHIES[geog]['graph']}_{state.abbr.lower()}.json"):
                print(f"{state.abbr} {geog}s")
                G = import_graph(geog, state)
                fn(G, property_fn)
                del G
            else:
                print(f"No graph for {state.name} {geog}s, skipping")