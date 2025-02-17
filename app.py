from flask import Flask, request, jsonify
from flask_cors import CORS
import osmnx as ox
import networkx as nx
import heapq

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir peticiones desde el frontend

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

# --- Funciones para calcular rutas con A* y almacenar bordes explorados ---
def reset_nodes():
    for node in G.nodes:
        G.nodes[node]["visited"] = False
        G.nodes[node]["distance"] = float("inf")
        G.nodes[node]["previous"] = None
        G.nodes[node]["g_score"] = float("inf")
        G.nodes[node]["f_score"] = float("inf")

def distance(node1, node2):
    x1, y1 = G.nodes[node1]["x"], G.nodes[node1]["y"]
    x2, y2 = G.nodes[node2]["x"], G.nodes[node2]["y"]
    return abs(x2 - x1) + abs(y2 - y1)

def a_star(orig, dest):
    reset_nodes()
    visited_edges = []  # Almacena los bordes explorados en el transcurso de la búsqueda
    G.nodes[orig]["g_score"] = 0
    G.nodes[orig]["f_score"] = distance(orig, dest)
    pq = [(G.nodes[orig]["f_score"], orig)]
    while pq:
        _, node = heapq.heappop(pq)
        if node == dest:
            return visited_edges
        for u, v, key in G.out_edges(node, keys=True):
            neighbor = v
            tentative_g_score = G.nodes[node]["g_score"] + distance(node, neighbor)
            if tentative_g_score < G.nodes[neighbor]["g_score"]:
                G.nodes[neighbor]["previous"] = node
                G.nodes[neighbor]["g_score"] = tentative_g_score
                G.nodes[neighbor]["f_score"] = tentative_g_score + distance(neighbor, dest)
                heapq.heappush(pq, (G.nodes[neighbor]["f_score"], neighbor))
                visited_edges.append((node, neighbor))
    return visited_edges

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
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
    except (TypeError, ValueError):
        return jsonify({"error": "Coordenadas inválidas o faltantes"}), 400

    # Encontrar los nodos más cercanos a las coordenadas dadas
    orig = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    dest = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    # Ejecutar A* y almacenar los bordes explorados
    visited_edges = a_star(orig, dest)
    # Reconstruir el camino óptimo
    optimal_path = reconstruct_path(orig, dest)

    # Convertir el camino óptimo a coordenadas
    optimal_coords = [{"x": G.nodes[node]["x"], "y": G.nodes[node]["y"]} for node in optimal_path]

    # Convertir cada borde visitado a coordenadas
    visited_coords = []
    for (u, v) in visited_edges:
        visited_coords.append({
            "from": {"x": G.nodes[u]["x"], "y": G.nodes[u]["y"]},
            "to": {"x": G.nodes[v]["x"], "y": G.nodes[v]["y"]}
        })

    return jsonify({"optimal": optimal_coords, "visited": visited_coords})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')