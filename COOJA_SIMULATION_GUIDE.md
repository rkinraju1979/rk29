# Contiki-NG Cooja Simulation & Survivability Plotting Guide

## Complete Lucas Sequence ($2, 1, 3, 4, 7, 11, 18, 29$) Clustered Topologies

This guide provides the complete instructions to run the 76-node clustered wireless sensor network simulation in **Contiki-NG Cooja** and plot the survivability graphs (**Nodes on X-axis vs. Rounds on Y-axis**).

---

## 1. Directory & File Manifest

| File | Purpose |
| :--- | :--- |
| [`project-conf.h`](file:///Users/rk/Documents/rk29/project-conf.h) | Contiki-NG project configuration (RPL-Lite, CSMA MAC, Energest profiling, buffer sizes). |
| [`udp-server.c`](file:///Users/rk/Documents/rk29/udp-server.c) | C source code for RPL DAG Root Sink (Node 0). Receives and logs telemetry packets. |
| [`udp-client.c`](file:///Users/rk/Documents/rk29/udp-client.c) | C source code for Sensor Motes (1–75) & Cluster Heads. Features 2-edge failover logic. |
| [`Makefile`](file:///Users/rk/Documents/rk29/Makefile) | Contiki-NG Makefile configured for `TARGET=cooja`. |
| [`cooja_test_script.js`](file:///Users/rk/Documents/rk29/cooja_test_script.js) | Cooja ScriptRunner automated simulation script (tracks TX/RX, rounds, failovers, PDR). |
| [`cooja-clustered-star.csc`](file:///Users/rk/Documents/rk29/cooja-clustered-star.csc) | Cooja simulation XML configuration for **⭐ Clustered Star** (75 links). |
| [`cooja-clustered-wheel.csc`](file:///Users/rk/Documents/rk29/cooja-clustered-wheel.csc) | Cooja simulation XML configuration for **🎡 Clustered Wheel** (140 links). |
| [`cooja-clustered-mesh.csc`](file:///Users/rk/Documents/rk29/cooja-clustered-mesh.csc) | Cooja simulation XML configuration for **🕸️ Clustered Mesh** (256 links). |
| [`cooja-lucas-2edge.csc`](file:///Users/rk/Documents/rk29/cooja-lucas-2edge.csc) | Cooja simulation XML configuration for **🌲 Clustered Lucas Triangles+Gaps** (107 links). |
| [`run_cooja.sh`](file:///Users/rk/Documents/rk29/run_cooja.sh) | Automated bash runner script for compiling firmware, running Cooja, and plotting. |
| [`plot_cooja_survivability.py`](file:///Users/rk/Documents/rk29/plot_cooja_survivability.py) | Python graph generator (produces publication-grade SVGs and PNGs). |
| [`lucas_rounds_survivability.json`](file:///Users/rk/Documents/rk29/lucas_rounds_survivability.json) | Benchmark dataset containing exact round-by-round survivability numbers. |

---

## 2. Compiling Contiki-NG Mote Firmware

Before loading into Cooja, compile the C code for the Cooja native target:

```bash
cd /Users/rk/Documents/rk29
make TARGET=cooja clean
make TARGET=cooja -j4
```
This builds:
- `udp-server.cooja` (Root Sink executable)
- `udp-client.cooja` (Sensor mote & Cluster Head executable)

---

## 3. Running Simulations in Cooja

### Option A: Running in Headless / NoGUI Mode (Recommended for Benchmarks)

You can run automated simulations without a GUI using the provided script:

```bash
cd /Users/rk/Documents/rk29
./run_cooja.sh
```

Or invoke Cooja directly via JAR:
```bash
# Set your Contiki-NG path (e.g. /home/user/contiki-ng)
export CONTIKI_DIR="/path/to/contiki-ng"
export COOJA_JAR="${CONTIKI_DIR}/tools/cooja/dist/cooja.jar"

# Run Lucas 2-Edge Simulation:
java -mx1024m -jar "$COOJA_JAR" -nogui=cooja-lucas-2edge.csc -contiki="$CONTIKI_DIR" > cooja-lucas.log

# Run Clustered Star Simulation:
java -mx1024m -jar "$COOJA_JAR" -nogui=cooja-clustered-star.csc -contiki="$CONTIKI_DIR" > cooja-star.log

# Run Clustered Wheel Simulation:
java -mx1024m -jar "$COOJA_JAR" -nogui=cooja-clustered-wheel.csc -contiki="$CONTIKI_DIR" > cooja-wheel.log

# Run Clustered Mesh Simulation:
java -mx1024m -jar "$COOJA_JAR" -nogui=cooja-clustered-mesh.csc -contiki="$CONTIKI_DIR" > cooja-mesh.log
```

---

### Option B: Running in Cooja GUI Mode (Interactive Visual Inspection)

1. Launch Cooja:
   ```bash
   cd /path/to/contiki-ng/tools/cooja
   ./gradlew run
   # (or 'ant run' on legacy setups)
   ```
2. In the Cooja GUI menu:
   - Click **File** $\to$ **Open simulation** $\to$ **Browse...**
   - Select `/Users/rk/Documents/rk29/cooja-lucas-2edge.csc` (or any of the other `.csc` files).
3. The Network View will display:
   - **Sink Node 0** at coordinates `(300, 250)`
   - All 8 Lucas cluster pods ($L_0=2, L_1=1, L_2=3, L_3=4, L_4=7, L_5=11, L_6=18, L_7=29$)
   - Mote Radio traffic and transmission cones.
4. Click **Start** in the **Simulation Control** window.
5. In the **Simulation Script Editor** (ScriptRunner plugin window), observe live logs:
   ```text
   [ROUND_METRIC] Round: 10 | LivingNodes: 75 | TX: 750 | RX: 748 | PDR: 99.7% | Failovers: 0
   [ROUND_METRIC] Round: 80 | LivingNodes: 42 | TX: 4620 | RX: 4310 | PDR: 93.3% | Failovers: 14
   ```

---

## 4. Plotting the Survivability Graphs

Run the graph generator script:

```bash
cd /Users/rk/Documents/rk29
python3 plot_cooja_survivability.py
```

### Generated Academic Journal Graph Artifacts (in `output/`):

All plots are formatted specifically for journal publication (IEEE / ACM / Elsevier / Springer):
- **Background:** Pure White (`facecolor='white'`)
- **Resolution:** **360 DPI** (crisp publication-ready raster PNG & infinite vector SVG)
- **Destination Folder:** [`/Users/rk/Documents/rk29/output/`](file:///Users/rk/Documents/rk29/output/)

1. **`output/fig1_survivability_nodes_vs_rounds_360dpi.svg` / `.png` (Primary Requested Graph):**
   - **X-axis:** Operating Living Nodes Quota ($0 \to 75$ nodes).
   - **Y-axis:** Operational Lifetime Rounds Sustained ($0 \to 100$ rounds).
   - Annotated with the **50% Benchmark Quota ($HND = 37$ nodes)** and **First Node Death ($FND = 70$ nodes)**.
   - Shows **Lucas sustaining 81.4 rounds** at 50% capacity vs. Star (78.9 rds), Wheel (68.1 rds), and Mesh (47.0 rds).

2. **`output/fig2_lifetime_rounds_vs_nodes_360dpi.svg` / `.png` (Classic WSN Lifetime Curve):**
   - **X-axis:** Simulation Rounds ($0 \to 100$).
   - **Y-axis:** Number of Alive Nodes delivering data to the root sink.

3. **`output/fig3_pdr_vs_rounds_360dpi.svg` / `.png` (End-to-End Packet Delivery Ratio):**
   - **X-axis:** Simulation Rounds ($0 \to 100$).
   - **Y-axis:** Packet Delivery Ratio (PDR %) over time.

4. **`output/fig4_energy_dissipation_360dpi.svg` / `.png` (Energy Dissipation Comparison):**
   - Bar chart showing Lucas minimal energy dissipation (1.3 J/node) vs Mesh (12.2 J/node).

5. **`output/fig5_composite_journal_quad_360dpi.png` (All-in-One 2x2 Composite Figure):**
   - Complete 4-quadrant academic journal figure containing subfigures (a), (b), (c), and (d) in a single image for direct journal manuscript placement.

---

## 5. Live Interactive Dashboard

To view the interactive graphs, failure injection slider, 2D network layout, and the full architectural conclusion in your browser:

1. Open your browser and navigate to:
   **[http://localhost:8080/](http://localhost:8080/)**
2. Interact with:
   - **Topology Selector Toolbar:** Toggle between Lucas (107 links), Mesh (256 links), Wheel (140 links), and Star (75 links).
   - **Progressive Node Failure Slider:** Inject 0% to 50% random node failure and observe real-time orphaned vs. connected nodes.
   - **Interactive Survivability Chart:** Hover to inspect exact $(X, Y)$ coordinate data and Lucas performance advantage margins.
   - **Definitive Architectural Conclusion Panel:** Review the 4 scientific pillars establishing Lucas 2-Edge as the best survivable clustered topology.
