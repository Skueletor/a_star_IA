from flask import Flask, request, jsonify
from flask_cors import CORS
import osmnx as ox
import networkx as nx
import heapq

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir peticiones desde el frontend en Vue

# --- Cargar y limpiar el grafo ---
place_name = "Santa Cruz de la Sierra, Bolivia"
G = ox.graph_from_place(place_name, network_type="drive")

for edge in G.edges:
    maxspeed = 40
    if "maxspeed" in G.edges[edge]:
        maxspeed_val = G.edges[edge]["maxspeed"]
        if isinstance(maxspeed_val, list):
            speeds = [int(speed) for speed in maxspeed_val if str(speed).isdigit()]
            if speeds:
                maxspeed = min(speeds)
        elif isinstance(maxspeed_val, str):
            try:
                maxspeed = int(maxspeed_val)
            except:
                maxspeed = 40
    G.edges[edge]["maxspeed"] = maxspeed
    G.edges[edge]["weight"] = G.edges[edge]["length"] / maxspeed

# --- Funciones para calcular rutas ---
def reset_nodes():
    for node in G.nodes:
        G.nodes[node]["visited"] = False
        G.nodes[node]["distance"] = float("inf")
        G.nodes[node]["previous"] = None
        G.nodes[node]["g_score"] = float("inf")
        G.nodes[node]["f_score"] = float("inf")

def dijkstra(orig, dest):
    reset_nodes()
    G.nodes[orig]["distance"] = 0
    pq = [(0, orig)]
    while pq:
        dist, node = heapq.heappop(pq)
        if node == dest:
            return
        if G.nodes[node]["visited"]:
            continue
        G.nodes[node]["visited"] = True
        for u, v, key in G.out_edges(node, keys=True):
            neighbor = v
            weight = G.edges[(u, v, key)]["weight"]
            if G.nodes[neighbor]["distance"] > G.nodes[node]["distance"] + weight:
                G.nodes[neighbor]["distance"] = G.nodes[node]["distance"] + weight
                G.nodes[neighbor]["previous"] = node
                heapq.heappush(pq, (G.nodes[neighbor]["distance"], neighbor))
    return

def distance(node1, node2):
    x1, y1 = G.nodes[node1]["x"], G.nodes[node1]["y"]
    x2, y2 = G.nodes[node2]["x"], G.nodes[node2]["y"]
    return ((x2 - x1)**2 + (y2 - y1)**2)**0.5

def a_star(orig, dest):
    reset_nodes()
    G.nodes[orig]["g_score"] = 0
    G.nodes[orig]["f_score"] = distance(orig, dest)
    pq = [(G.nodes[orig]["f_score"], orig)]
    while pq:
        _, node = heapq.heappop(pq)
        if node == dest:
            return
        for u, v, key in G.out_edges(node, keys=True):
            neighbor = v
            tentative_g_score = G.nodes[node]["g_score"] + distance(node, neighbor)
            if tentative_g_score < G.nodes[neighbor]["g_score"]:
                G.nodes[neighbor]["previous"] = node
                G.nodes[neighbor]["g_score"] = tentative_g_score
                G.nodes[neighbor]["f_score"] = tentative_g_score + distance(neighbor, dest)
                heapq.heappush(pq, (G.nodes[neighbor]["f_score"], neighbor))
    return

def reconstruct_path(orig, dest):
    path = []
    current = dest
    while current is not None:
        path.append(current)
        if current == orig:
            break
        current = G.nodes[current]["previous"]
    path.reverse()
    return path

# --- Endpoint que recibe los puntos de inicio y destino ---
@app.route('/route', methods=['GET'])
def get_route():
    # Parámetros: algorithm (a_star), start_lat, start_lon, end_lat, end_lon
    algorithm = request.args.get('algorithm', 'a_star')
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
    except (TypeError, ValueError):
        return jsonify({"error": "Coordenadas inválidas o faltantes"}), 400

    orig = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    dest = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    # Ejecutar el algoritmo seleccionado
    if algorithm == 'dijkstra':
        dijkstra(orig, dest)
    else:
        a_star(orig, dest)

    # Reconstruir la ruta
    path = reconstruct_path(orig, dest)
    route = [{"x": G.nodes[node]["x"], "y": G.nodes[node]["y"]} for node in path]
    return jsonify({"route": route})

if __name__ == '__main__':
    app.run(debug=True)
