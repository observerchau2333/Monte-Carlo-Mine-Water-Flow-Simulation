import networkx as nx
import matplotlib.pyplot as plt
import random
import math
import csv
from pathlib import Path

# =========================
# Parameters
# =========================

ALPHA = 10.0          # water-height sensitivity
SOURCE = 0            # source node
RANDOM_SEED = None    # set an integer such as 42 for repeatable runs

A = 1.0               # water inflow rate (m^3/s)
DT = 1.0              # timestep

N_DROPS = 1000        # droplets per timestep
STEPS = 100           
SNAPSHOT_INTERVAL = 10

TUNNEL_WIDTH = 2.0
SHOW_PLOT = False

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def edge_key(u, v):
    return tuple(sorted((u, v)))


def edge_label(key):
    return f"{key[0]}-{key[1]}"


# =========================
# Build Mine Network
# =========================

G = nx.Graph()

edges = [
    (0, 1, 10),
    (1, 2, 8),
    (1, 3, 12),
    (2, 4, 6),
    (3, 4, 7),
    (4, 5, 5),
]

EDGE_KEYS = [edge_key(u, v) for u, v, _ in edges]

for u, v, length in edges:
    G.add_edge(
        u,
        v,
        length=length,
        height=0.0
    )

# =========================
# Water Drop Simulation
# =========================


def get_heights():
    return {
        key: G[key[0]][key[1]]["height"]
        for key in EDGE_KEYS
    }


def print_heights(title, heights):
    print(f"\n{title}\n")

    for key in EDGE_KEYS:
        print(f"{key[0]} <-> {key[1]} : {heights[key]:.6f}")


def save_history_csv(history, output_path):
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["step", *[edge_label(key) for key in EDGE_KEYS]])

        for step, heights in history:
            writer.writerow([step, *[heights[key] for key in EDGE_KEYS]])


def draw_final_network(output_path):
    pos = nx.spring_layout(G, seed=42)
    heights = get_heights()
    max_height = max(heights.values()) or 1.0

    edge_colors = [
        heights[edge_key(u, v)]
        for u, v in G.edges()
    ]
    edge_widths = [
        1.0 + 5.0 * heights[edge_key(u, v)] / max_height
        for u, v in G.edges()
    ]
    edge_labels = {
        (u, v): f"{G[u][v]['height']:.2f}"
        for u, v in G.edges()
    }

    plt.figure(figsize=(8, 5))
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=700,
        edge_color=edge_colors,
        edge_cmap=plt.cm.Blues,
        width=edge_widths
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels
    )
    plt.title("Mine Water Monte Carlo Simulation - Final Heights")
    plt.savefig(output_path, dpi=200)

    if SHOW_PLOT:
        plt.show()

    plt.close()


def draw_height_history(history, output_path):
    plt.figure(figsize=(9, 5))

    steps = [step for step, _ in history]

    for key in EDGE_KEYS:
        values = [heights[key] for _, heights in history]
        plt.plot(steps, values, marker="o", label=edge_label(key))

    plt.xlabel("Step")
    plt.ylabel("Water height (m)")
    plt.title("Water Height Change During Simulation")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")

    if SHOW_PLOT:
        plt.show()

    plt.close()


def choose_next_node(current, previous, used_edges):

    neighbors = list(G.neighbors(current))

    # no backtracking and no repeatedly walking the same tunnel
    candidates = []

    for n in neighbors:
        if n == previous:
            continue
        if edge_key(current, n) in used_edges:
            continue
        candidates.append(n)

    # dead end
    if len(candidates) == 0:
        return None

    weights = []

    for n in candidates:

        h = G[current][n]["height"]

        w = math.exp(-ALPHA * h)

        weights.append(w)

    total = sum(weights)

    probs = [w / total for w in weights]

    next_node = random.choices(
        candidates,
        probs
    )[0]

    return next_node


def simulate_drop(volume):

    current = SOURCE
    previous = None

    path = []
    used_edges = set()

    total_length = 0.0

    while True:

        nxt = choose_next_node(
            current,
            previous,
            used_edges
        )

        if nxt is None:
            break

        edge = G[current][nxt]
        used_edges.add(edge_key(current, nxt))

        path.append((current, nxt))

        total_length += edge["length"]

        previous = current
        current = nxt

    # isolated source
    if total_length == 0:
        return

    dh = volume / (
        total_length * TUNNEL_WIDTH
    )

    for u, v in path:
        G[u][v]["height"] += dh


# =========================
# Main Simulation
# =========================

if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

drop_volume = A * DT / N_DROPS
history = [(0, get_heights())]

for step in range(1, STEPS + 1):

    for _ in range(N_DROPS):

        simulate_drop(drop_volume)

    if step % SNAPSHOT_INTERVAL == 0 or step == STEPS:
        history.append((step, get_heights()))

# =========================
# Results and Outputs
# =========================

for step, heights in history:
    print_heights(f"Water Heights at Step {step}:", heights)

final_network_path = OUTPUT_DIR / "mine_water_final_network.png"
history_plot_path = OUTPUT_DIR / "water_height_history.png"
history_csv_path = OUTPUT_DIR / "water_height_history.csv"

draw_final_network(final_network_path)
draw_height_history(history, history_plot_path)
save_history_csv(history, history_csv_path)

print("\nSaved outputs:\n")
print(final_network_path)
print(history_plot_path)
print(history_csv_path)
