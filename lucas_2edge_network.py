"""
Lucas Sequence 2-Edge Survivable Network Topology Generator
Generates a 17-node, 5-tier network where node counts per tier follow Lucas numbers:
L_0 = 2 (Dual Edge Gateways / Sinks)
L_1 = 1 (Central Backbone Bridge)
L_2 = 3 (Cluster Head Routers)
L_3 = 4 (Distribution Relays)
L_4 = 7 (Leaf Sensor Motes)
Total = 17 nodes.

Every node has degree >= 2 and 2 edge-disjoint paths to the edge gateways,
guaranteeing 2-edge survivability (k=2 edge-connected).
"""

import math
import json

LUCAS_TIERS = [
    {"tier": 0, "name": "Dual Edge Gateways (E1, E2)", "count": 2, "nodes": [1, 2]},
    {"tier": 1, "name": "Core Backbone Bridge (B1)", "count": 1, "nodes": [3]},
    {"tier": 2, "name": "Cluster Head Routers (C1..C3)", "count": 3, "nodes": [4, 5, 6]},
    {"tier": 3, "name": "Distribution Relays (D1..D4)", "count": 4, "nodes": [7, 8, 9, 10]},
    {"tier": 4, "name": "Leaf Sensor Motes (S1..S7)", "count": 7, "nodes": [11, 12, 13, 14, 15, 16, 17]}
]

# Generate coordinates (x, y) in concentric rings / hierarchical tiers
def generate_positions():
    positions = {}
    
    # Tier 0: Dual Edge Gateways (x: 100, 300; y: 40)
    positions[1] = {"x": 140.0, "y": 40.0, "tier": 0, "role": "Edge Gateway 1 (fd00::1)"}
    positions[2] = {"x": 260.0, "y": 40.0, "tier": 0, "role": "Edge Gateway 2 (fd00::2)"}

    # Tier 1: Core Backbone Bridge (Center: x: 200, y: 100)
    positions[3] = {"x": 200.0, "y": 100.0, "tier": 1, "role": "Core Backbone Bridge"}

    # Tier 2: 3 Cluster Heads (y: 170)
    positions[4] = {"x": 100.0, "y": 170.0, "tier": 2, "role": "Cluster Head 1"}
    positions[5] = {"x": 200.0, "y": 170.0, "tier": 2, "role": "Cluster Head 2"}
    positions[6] = {"x": 300.0, "y": 170.0, "tier": 2, "role": "Cluster Head 3"}

    # Tier 3: 4 Distribution Relays (y: 250)
    positions[7] = {"x": 70.0,  "y": 250.0, "tier": 3, "role": "Distribution Relay 1"}
    positions[8] = {"x": 150.0, "y": 250.0, "tier": 3, "role": "Distribution Relay 2"}
    positions[9] = {"x": 250.0, "y": 250.0, "tier": 3, "role": "Distribution Relay 3"}
    positions[10] = {"x": 330.0, "y": 250.0, "tier": 3, "role": "Distribution Relay 4"}

    # Tier 4: 7 Leaf Sensor Motes (y: 330)
    for i in range(7):
        node_id = 11 + i
        x_pos = 40.0 + i * 53.3
        positions[node_id] = {"x": round(x_pos, 1), "y": 330.0, "tier": 4, "role": f"Sensor Mote {i+1}"}

    return positions

# Define links guaranteeing 2-edge connectivity (no single edge cut disconnects any node)
def generate_2edge_topology():
    edges = [
        # Inter-gateway tie-line (direct edge redundancy between dual roots)
        (1, 2),
        
        # Tier 0 to Tier 1: Core Bridge connected to both E1 and E2
        (1, 3), (2, 3),

        # Tier 1 to Tier 2:
        (1, 4), (3, 4),        # C1 connected to E1 and B1
        (3, 5), (1, 5), (2, 5), # C2 connected to B1, E1, E2
        (2, 6), (3, 6),        # C3 connected to E2 and B1
        (4, 5), (5, 6),        # Cross-tier ring links between cluster heads

        # Tier 2 to Tier 3:
        (4, 7), (4, 8),
        (5, 8), (5, 9),
        (6, 9), (6, 10),
        (7, 8), (8, 9), (9, 10), # Lateral ring links for 2-edge redundancy

        # Tier 3 to Tier 4 (Each of the 7 sensor motes connects to >= 2 distribution relays):
        (7, 11), (8, 11),
        (7, 12), (8, 12),
        (8, 13), (9, 13),
        (8, 14), (9, 14),
        (9, 15), (10, 15),
        (9, 16), (10, 16),
        (10, 17), (7, 17),      # Outer wrap-around link providing complete 2-edge biconnectivity
        (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17) # Adjacent mesh links
    ]
    # Remove duplicates and sort
    clean_edges = sorted(list(set((min(u, v), max(u, v)) for u, v in edges)))
    return clean_edges

def verify_2edge_survivability(nodes, edges):
    """
    Verifies that removing any single edge keeps all nodes connected to at least one edge gateway (1 or 2).
    """
    adj = {n: set() for n in nodes}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    print(f"Total Nodes: {len(nodes)} (Lucas sequence: 2 + 1 + 3 + 4 + 7 = 17)")
    print(f"Total Edges: {len(edges)}")
    
    # Check node degrees
    min_degree = min(len(adj[n]) for n in nodes)
    print(f"Minimum Node Degree: {min_degree} (Required >= 2 for 2-edge survivability: {'PASS' if min_degree >= 2 else 'FAIL'})")

    # Simulate removal of every edge
    all_survived = True
    for cut_edge in edges:
        # Build graph without cut_edge
        cut_adj = {n: set() for n in nodes}
        for u, v in edges:
            if (u, v) == cut_edge or (v, u) == cut_edge:
                continue
            cut_adj[u].add(v)
            cut_adj[v].add(u)

        # BFS from Dual Edge Gateways (nodes 1 and 2)
        visited = set()
        queue = [1, 2]
        visited.add(1)
        visited.add(2)
        
        while queue:
            curr = queue.pop(0)
            for neighbor in cut_adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(visited) != len(nodes):
            unreachable = set(nodes) - visited
            print(f"FAIL: Cutting edge {cut_edge} disconnected nodes: {unreachable}")
            all_survived = False
            break

    if all_survived:
        print(">>> 2-EDGE SURVIVABILITY VERIFIED: 100% of single edge failures survive with alternative paths to Edge Gateways!")

    return all_survived

if __name__ == "__main__":
    nodes = list(range(1, 18))
    edges = generate_2edge_topology()
    verify_2edge_survivability(nodes, edges)
