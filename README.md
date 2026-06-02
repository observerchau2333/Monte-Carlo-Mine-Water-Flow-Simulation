# Monte-Carlo Mine Water Flow Simulation

中文版本: [README.zh-CN.md](README.zh-CN.md)

This project uses a Monte Carlo method to simulate how water spreads through a mine tunnel network after water enters from a source node at a constant rate.

The model treats the mine as an undirected graph:

- nodes represent tunnel junctions or endpoints;
- edges represent mine tunnels;
- each edge has a length and an accumulated water height;
- water enters from a fixed source node at a constant inflow rate.

The core idea is to split the incoming water into many small water drops. Each drop moves through the network randomly, but the randomness is biased by the current water height of each candidate tunnel. Tunnels with lower water height are more likely to be chosen, so the flow tends to spread toward lower accumulated regions.

## Problem Background

In a mine water inrush problem, water may enter the tunnel system from one location and then expand through the connected underground network. A full physical simulation may require solving fluid dynamics equations, tunnel geometry, slopes, hydraulic resistance, and boundary conditions.

This project uses a simpler network-based approximation. It focuses on the cumulative distribution of water height in each tunnel rather than detailed velocity fields. The simulation is useful for exploring questions such as:

- Which tunnels are likely to accumulate more water?
- How does the water distribution evolve over time?
- How does local height feedback affect global spreading?
- What happens when water avoids already-filled regions?

## Model Assumptions

The current implementation makes the following simplifying assumptions:

- The water source has a constant inflow rate `A`, measured in cubic meters per second.
- All tunnels have the same width, `TUNNEL_WIDTH`.
- The mine network is represented by a graph.
- Each water drop does not move backward to the node it just came from.
- Each water drop does not repeatedly walk through the same tunnel in one trip, which prevents infinite loops in cyclic networks.
- When a drop reaches a dead end or has no valid next tunnel, it stops.
- The drop volume is distributed as a height increment over every tunnel in its traveled path.

## Algorithm

For each simulation step:

1. Compute the volume of one water drop:

   $$V_{\text{drop}} = \frac{A \Delta t}{N_{\text{drops}}}$$

2. Release `N_DROPS` water drops from the source node.

3. For each drop, repeat the following until it stops:

   - find all neighboring tunnels that are valid next choices;
   - remove the previous node to prevent immediate backtracking;
   - remove tunnels already used by this drop to avoid loops;
   - calculate the selection weight of each candidate tunnel:

     $$w_i = e^{-\alpha h_i}$$

     where `h_i` is the current water height of candidate tunnel `i`.

   - normalize the weights into probabilities;
   - randomly choose the next tunnel according to those probabilities;
   - add the tunnel length to the total traveled length.

4. When the drop stops, update all tunnels in its path:

   $$\Delta h = \frac{V_{\text{drop}}}{L_{\text{path}} W}$$

   Then every tunnel in the path receives the height increment $\Delta h$.

5. Save intermediate snapshots every `SNAPSHOT_INTERVAL` steps.

## Height-Biased Random Choice

The probability rule is the main feedback mechanism:

$$
P_i =
\frac{e^{-\alpha h_i}}
{\sum_{j \in C} e^{-\alpha h_j}}
$$

where:

- `P_i` is the probability of choosing tunnel `i`;
- `h_i` is the current water height of tunnel `i`;
- `alpha` controls how strongly water avoids higher tunnels.
- `C` is the set of valid candidate tunnels from the current node.

When `alpha` is small, the water chooses paths more randomly.

When `alpha` is large, the water strongly prefers tunnels with lower current water height. This creates a balancing effect: high-water tunnels become less attractive, and low-water tunnels receive more future drops.

## Outputs

After running the simulation, the program writes outputs to:

```text
outputs/
```

The generated files are:

- `mine_water_final_network.png`: final network graph with edge color and width representing water height;
- `water_height_history.png`: line chart showing how each tunnel's water height changes over time;
- `water_height_history.csv`: CSV table of intermediate water-height snapshots.

The terminal also prints water heights at step `0`, every `SNAPSHOT_INTERVAL`, and the final step.

## Important Parameters

The main parameters are defined near the top of `simulation.py`:

```python
ALPHA = 10.0
SOURCE = 0
RANDOM_SEED = None
A = 1.0
DT = 1.0
N_DROPS = 1000
STEPS = 100
SNAPSHOT_INTERVAL = 10
TUNNEL_WIDTH = 2.0
SHOW_PLOT = False
```

Useful adjustments:

- Increase `STEPS` to simulate a longer time.
- Increase `N_DROPS` for smoother Monte Carlo results.
- Decrease `N_DROPS` to make random variation more visible.
- Increase `ALPHA` to make water avoid high-water tunnels more strongly.
- Set `RANDOM_SEED = 42` or another integer to make runs repeatable.
- Set `SHOW_PLOT = True` if you want matplotlib windows to pop up during local execution.

## Generalization

Although this project is written as a mine water flow simulation, the same algorithm can be generalized to other network propagation problems.

The broader pattern is:

```text
many small particles / agents move through a network
their path choices depend on existing accumulated quantities
after each trip, the traveled path receives an increment
future agents react to the updated network state
```

Examples:

- Crowd evacuation: people move through corridors, and crowded corridors become less attractive.
- Traffic assignment: vehicles choose roads, and congested roads become less likely to be selected.
- Information diffusion: messages spread through a social network, and overloaded or saturated channels receive fewer future messages.
- Heat accumulation: heat packets travel through a connected structure, and hotter edges become less favorable paths.
- Sediment or pollutant transport: particles move through river channels, and local concentration changes future path probabilities.
- Network load balancing: computational tasks move through a server network, avoiding already loaded links.
- Disease exposure accumulation: simulated exposure particles move through contact networks, with already exposed paths receiving different probabilities.
- Capital or resource allocation: small units of resource move through a supply network, avoiding saturated routes and accumulating on selected paths.

In these cases, the "water height" variable can be replaced by another cumulative quantity, such as congestion, load, temperature, concentration, risk, or demand.

## Limitations

This model is intentionally simple. It does not currently include:

- tunnel slope or gravity direction;
- hydraulic pressure;
- flow velocity;
- water conservation at every intermediate node;
- tunnel capacity limits;
- drainage or outflow;
- time-dependent source rates;
- different tunnel widths;
- physical resistance or friction.

These can be added later if the goal is to move from an exploratory network model toward a more physically realistic hydraulic model.
