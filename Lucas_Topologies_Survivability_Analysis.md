# Lucas Sequence Topology Suite: Star, Wheel, and Mesh
## 1-Edge, 2-Edge, and 3-Edge Survivability Analysis for RPL-UDP in Contiki-NG / Cooja

### 1. Mathematical Sequence & Tier Formulation
The classical **Lucas sequence** is defined by initial terms $L_0 = 2, L_1 = 1$ and the recurrence relation:
$$L_n = L_{n-1} + L_{n-2} \quad \text{for } n \ge 2$$
producing the sequence:
$$\mathbf{2, 1, 3, 4, 7, 11, 18, 29, 47, 76, \dots}$$

Our topology suite deploys an **18-node network** corresponding to the 6th Lucas number:
$$N = L_6 = 18$$
consisting of **1 central RPL DODAG Root / Server (Node 1)** and **17 client motes (Nodes 2..18)**. The 17 client motes partition into consecutive Lucas terms:
$$17 = \sum_{i=0}^4 L_i = L_0 + L_1 + L_2 + L_3 + L_4 = 2 + 1 + 3 + 4 + 7$$

| Tier Index | Lucas Term | Count | Assigned Motes | Functional Role |
| :--- | :---: | :---: | :---: | :--- |
| **Root Gateway** | — | 1 | Node 1 | RPL DODAG Root / UDP Gateway Server (`fd00::1`) |
| **Tier 0** | $L_0 = 2$ | 2 | Nodes 2, 3 | Dual Edge Relays / Sub-Gateways |
| **Tier 1** | $L_1 = 1$ | 1 | Node 4 | Core Backbone Cross-Connect Bridge |
| **Tier 2** | $L_2 = 3$ | 3 | Nodes 5, 6, 7 | Cluster Head Routers |
| **Tier 3** | $L_3 = 4$ | 4 | Nodes 8, 9, 10, 11 | Distribution Relays |
| **Tier 4** | $L_4 = 7$ | 7 | Nodes 12..18 | Leaf Sensor Motes (Multi-Homed) |

---

### 2. Evaluated Topologies & Graph Properties

#### 2.1 Lucas Star Topology ($S_{18}$)
- **Structure:** Central Root 1 connected directly to 17 motes via radial spoke links.
- **Total Edges:** $|E| = 17$
- **Degrees:** $\delta(G) = 1$ (all leaf motes have degree 1), $\Delta(G) = 17$ (Root 1)
- **Edge Connectivity:** $\lambda(G) = 1$
- **1-Edge Survivability:** **0.00%** (Cutting any spoke isolates that client node)
- **2-Edge Survivability:** **0.00%** (Isolates 2 client nodes)
- **3-Edge Survivability:** **0.00%** (Isolates 3 client nodes)
- **Verdict:** **0-Edge Survivable** (Single Point of Failure vulnerability).

#### 2.2 Lucas Wheel Topology ($W_{18}$)
- **Structure:** Central Root 1 connected to 17 rim nodes ($C_{17}$ cycle rim) via 17 radial spokes.
- **Total Edges:** $|E| = 34$ ($17 \text{ spokes} + 17 \text{ rim edges}$)
- **Degrees:** $\delta(G) = 3$ (every rim node has 1 spoke + 2 adjacent rim links), $\Delta(G) = 17$
- **Edge Connectivity:** $\lambda(G) = 3$
- **1-Edge Survivability:** **100.00%** (All 34 single-edge cuts maintain 100% reachability to Root 1)
- **2-Edge Survivability:** **100.00%** (All 561 2-edge cuts maintain 100% reachability to Root 1)
- **3-Edge Survivability:** **99.72%** (5,967 of 5,984 3-edge cuts maintain reachability; cutting the 3 incident edges of any rim node isolates it)
- **Verdict:** **2-Edge Survivable** (Guaranteed against any 1 or 2 arbitrary edge failures; fails on 3-edge worst case).

#### 2.3 Lucas Mesh Topology with Chordal Interconnects
- **Structure:** Lucas Wheel augmented with Lucas-interval chords skipping $L_2 = 3$ nodes and $L_3 = 4$ nodes along the rim.
- **Total Edges:** $|E| = 68$
- **Degrees:** $\delta(G) = 7$ (every client node has degree $\ge 7$), $\Delta(G) = 17$
- **Edge Connectivity:** $\lambda(G) \ge 4$
- **1-Edge Survivability:** **100.00%** (68 / 68 cuts survive)
- **2-Edge Survivability:** **100.00%** (2,278 / 2,278 cuts survive)
- **3-Edge Survivability:** **100.00%** (50,116 / 50,116 cuts survive, **zero network partitioning**)
- **Verdict:** **3-Edge Survivable** (100% guaranteed survivability under any 1, 2, or 3 arbitrary edge cuts).

---

### 3. Comprehensive Combinatorial Survivability Scoreboard

| Topology | Edges $|E|$ | Min Deg $\delta$ | Edge Conn $\lambda$ | 1-Edge Survivability | 2-Edge Survivability | 3-Edge Survivability | Survivability Guarantee |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Lucas Star** | 17 | 1 | 1 | **0.00%** (0 / 17) | **0.00%** (0 / 136) | **0.00%** (0 / 680) | **0-Edge Critical** |
| **Lucas Wheel** | 34 | 3 | 3 | **100.00%** (34 / 34) | **100.00%** (561 / 561) | **99.72%** (5,967 / 5,984) | **2-Edge Survivable** |
| **Lucas Mesh** | 68 | 7 | $\ge 4$ | **100.00%** (68 / 68) | **100.00%** (2,278 / 2,278) | **100.00%** (50,116 / 50,116) | **3-Edge Survivable** |

---

### 4. Cooja Simulation Files (.CSC)

The following simulation configurations are ready for execution in Contiki-NG / Cooja:
- `lucas-star.csc`: Star topology XML for Cooja with UDGM radio medium ($R_{tx} = 85.0\text{ m}$).
- `lucas-wheel.csc`: Wheel topology XML with circular ring layout ($R = 80.0\text{ m}$, $R_{tx} = 85.0\text{ m}$).
- `lucas-mesh.csc`: 4-connected Mesh topology XML with Lucas chordal interconnects ($R_{tx} = 120.0\text{ m}$).
- `lucas_edge_fault_test.js`: Cooja JavaScript test script for headless automated fault injection and PDR logging.

#### Compiling and Running in Cooja:
```bash
# 1. Compile firmware in the rpl-udp directory:
make udp-server.cooja TARGET=cooja
make udp-client.cooja TARGET=cooja

# 2. Run in Cooja GUI:
cd ~/contiki-ng/tools/cooja
./gradlew run --args='--gui /Users/rk/Documents/rk29/lucas-wheel.csc'

# Or run Lucas Mesh:
./gradlew run --args='--gui /Users/rk/Documents/rk29/lucas-mesh.csc'

# 3. Headless automated execution:
./gradlew run --args='--nogui=/Users/rk/Documents/rk29/lucas-wheel.csc -contiki=/Users/rk/contiki-ng'
```

---

### 5. Interactive Web Dashboard
Run the built-in web viewer to visualize the topologies and interactively inject 1-edge, 2-edge, and 3-edge cuts:
```bash
python3 /Users/rk/Documents/rk29/edge_viewer/server.py
```
Then navigate to `http://localhost:8080` in your web browser.
