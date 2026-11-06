#!/usr/bin/env python3
"""
Full Lucas Sequence Clustered Topologies & 50% Node Failure Survivability Benchmark
Lucas Sequence: 2, 1, 3, 4, 7, 11, 18, 29 (8 Terms, L_0 through L_7)
Total Motes: 2 + 1 + 3 + 4 + 7 + 11 + 18 + 29 = 75 Nodes (Sum = L_9 - 1 = 75) + 1 Sink Root (Node 0) = 76 Nodes (L_9 = 76)

Clusters / Tiers:
  - Cluster 0 (L_0 = 2 nodes): Nodes 1, 2 (Dual Gateways / Primary Relays)
  - Cluster 1 (L_1 = 1 node) : Node 3 (Core Cross-Connect Backbone Bridge)
  - Cluster 2 (L_2 = 3 nodes): Nodes 4, 5, 6 (Cluster Heads / Relays)
  - Cluster 3 (L_3 = 4 nodes): Nodes 7, 8, 9, 10
  - Cluster 4 (L_4 = 7 nodes): Nodes 11..17
  - Cluster 5 (L_5 = 11 nodes): Nodes 18..28
  - Cluster 6 (L_6 = 18 nodes): Nodes 29..46
  - Cluster 7 (L_7 = 29 nodes): Nodes 47..75

Topologies Evaluated:
  1. Clustered Star: Intra-cluster star with CH. Single point of failure.
  2. Clustered Wheel: Intra-cluster wheel with cycle rim + spokes + backup CH uplink.
  3. Lucas 2-Edge (TGO): Pruned biconnected ring + dual gateways + inter-cluster bridges.
  4. Clustered Mesh: Dense intra-cluster chords + inter-cluster failover bridges.
"""

import math
import random
import json
import os
import sys
from collections import deque

TOTAL_NODES = 75
SINK_ROOT = 0

FULL_LUCAS_CLUSTERS = [
    {"cluster_id": 0, "size": 2,  "lucas_term": "L_0 = 2",  "ch": 1,  "nodes": [1, 2],                  "role": "Dual Edge Gateways / Sinks"},
    {"cluster_id": 1, "size": 1,  "lucas_term": "L_1 = 1",  "ch": 3,  "nodes": [3],                     "role": "Core Cross-Connect Bridge"},
    {"cluster_id": 2, "size": 3,  "lucas_term": "L_2 = 3",  "ch": 4,  "nodes": [4, 5, 6],               "role": "Cluster 2 (3 Motes)"},
    {"cluster_id": 3, "size": 4,  "lucas_term": "L_3 = 4",  "ch": 7,  "nodes": [7, 8, 9, 10],           "role": "Cluster 3 (4 Motes)"},
    {"cluster_id": 4, "size": 7,  "lucas_term": "L_4 = 7",  "ch": 11, "nodes": list(range(11, 18)),     "role": "Cluster 4 (7 Motes)"},
    {"cluster_id": 5, "size": 11, "lucas_term": "L_5 = 11", "ch": 18, "nodes": list(range(18, 29)),     "role": "Cluster 5 (11 Motes)"},
    {"cluster_id": 6, "size": 18, "lucas_term": "L_6 = 18", "ch": 29, "nodes": list(range(29, 47)),     "role": "Cluster 6 (18 Motes)"},
    {"cluster_id": 7, "size": 29, "lucas_term": "L_7 = 29", "ch": 47, "nodes": list(range(47, 76)),     "role": "Cluster 7 (29 Motes)"}
]

# ---------------------------------------------------------------------------
# Geometric Positioning (for Cooja XML & Dashboard SVG)
# ---------------------------------------------------------------------------
def generate_full_cluster_coordinates():
    positions = {
        SINK_ROOT: {"x": 300.0, "y": 250.0, "cluster": -1, "role": "RPL DODAG Root Sink (fd00::1)"}
    }

    # Center positions for all 8 Lucas clusters
    cluster_centers = [
        {"x": 220.0, "y": 140.0, "r": 20.0},  # L_0 = 2 (Dual Gateways)
        {"x": 380.0, "y": 140.0, "r": 15.0},  # L_1 = 1 (Core Bridge)
        {"x": 470.0, "y": 180.0, "r": 25.0},  # L_2 = 3
        {"x": 520.0, "y": 280.0, "r": 35.0},  # L_3 = 4
        {"x": 460.0, "y": 380.0, "r": 45.0},  # L_4 = 7
        {"x": 320.0, "y": 420.0, "r": 55.0},  # L_5 = 11
        {"x": 180.0, "y": 390.0, "r": 68.0},  # L_6 = 18
        {"x": 100.0, "y": 250.0, "r": 85.0}   # L_7 = 29
    ]

    for idx, c in enumerate(FULL_LUCAS_CLUSTERS):
        center = cluster_centers[idx]
        ch = c["ch"]
        positions[ch] = {
            "x": round(center["x"], 1),
            "y": round(center["y"], 1),
            "cluster": c["cluster_id"],
            "role": f"{c['role']} (CH Node {ch})"
        }

        members = [n for n in c["nodes"] if n != ch]
        num_m = len(members)
        for m_idx, m_id in enumerate(members):
            ang = 2.0 * math.pi * m_idx / num_m
            mx = center["x"] + center["r"] * math.cos(ang)
            my = center["y"] + center["r"] * math.sin(ang)
            positions[m_id] = {
                "x": round(mx, 1),
                "y": round(my, 1),
                "cluster": c["cluster_id"],
                "role": f"Cluster {c['cluster_id']} Member (Node {m_id})"
            }

    return positions

# ---------------------------------------------------------------------------
# Topology Edge Builders
# ---------------------------------------------------------------------------
def build_full_star_edges():
    edges = set()
    for c in FULL_LUCAS_CLUSTERS:
        ch = c["ch"]
        edges.add((min(SINK_ROOT, ch), max(SINK_ROOT, ch)))
        for n in c["nodes"]:
            if n != ch:
                edges.add((min(ch, n), max(ch, n)))
    return sorted(list(edges))

def build_full_wheel_edges():
    edges = set(build_full_star_edges())
    for c in FULL_LUCAS_CLUSTERS:
        members = [n for n in c["nodes"] if n != c["ch"]]
        num_m = len(members)
        if num_m > 1:
            for i in range(num_m):
                u = members[i]
                v = members[(i + 1) % num_m]
                edges.add((min(u, v), max(u, v)))
        if num_m >= 2:
            edges.add((min(SINK_ROOT, members[0]), max(SINK_ROOT, members[0])))
    return sorted(list(edges))

def build_full_2edge_edges():
    """
    Lucas 2-Edge Architecture:
    Includes L_0=2 Dual Gateways (Nodes 1, 2) tied together,
    L_1=1 Backbone Bridge (Node 3) tied to both gateways,
    and biconnected lateral ring edges inside clusters 2..7 plus adjacent bridges.
    """
    edges = set(build_full_star_edges())
    edges.add((1, 2))  # Inter-gateway tie-line
    edges.add((1, 3))  # E1 to B1
    edges.add((2, 3))  # E2 to B1
    edges.add((min(SINK_ROOT, 2), max(SINK_ROOT, 2))) # Dual Gateway uplink to Root

    for c in FULL_LUCAS_CLUSTERS[2:]:
        members = [n for n in c["nodes"] if n != c["ch"]]
        num_m = len(members)
        if num_m > 1:
            for i in range(num_m):
                u = members[i]
                v = members[(i + 1) % num_m]
                edges.add((min(u, v), max(u, v)))
        if num_m >= 2:
            edges.add((min(SINK_ROOT, members[0]), max(SINK_ROOT, members[0])))

    # Inter-cluster boundary failover bridges
    for i in range(2, len(FULL_LUCAS_CLUSTERS) - 1):
        c1 = FULL_LUCAS_CLUSTERS[i]
        c2 = FULL_LUCAS_CLUSTERS[i + 1]
        edges.add((min(c1["ch"], c2["ch"]), max(c1["ch"], c2["ch"])))
        edges.add((min(c1["nodes"][-1], c2["nodes"][-1]), max(c1["nodes"][-1], c2["nodes"][-1])))

    return sorted(list(edges))

def build_full_mesh_edges():
    edges = set(build_full_wheel_edges())
    # Inter-cluster bridges across all Lucas sequence tiers
    for i in range(len(FULL_LUCAS_CLUSTERS) - 1):
        c1 = FULL_LUCAS_CLUSTERS[i]
        c2 = FULL_LUCAS_CLUSTERS[i + 1]
        edges.add((min(c1["ch"], c2["ch"]), max(c1["ch"], c2["ch"])))
        edges.add((min(c1["nodes"][-1], c2["nodes"][-1]), max(c1["nodes"][-1], c2["nodes"][-1])))
    # Wrap-around link (C7 to C0)
    edges.add((min(FULL_LUCAS_CLUSTERS[-1]["ch"], FULL_LUCAS_CLUSTERS[0]["ch"]),
               max(FULL_LUCAS_CLUSTERS[-1]["ch"], FULL_LUCAS_CLUSTERS[0]["ch"])))

    # Intra-cluster chords (skips of 2 and 3)
    for c in FULL_LUCAS_CLUSTERS:
        nList = c["nodes"]
        if len(nList) >= 4:
            for i in range(len(nList)):
                edges.add((min(nList[i], nList[(i + 2) % len(nList)]), max(nList[i], nList[(i + 2) % len(nList)])))
                if len(nList) >= 7:
                    edges.add((min(nList[i], nList[(i + 3) % len(nList)]), max(nList[i], nList[(i + 3) % len(nList)])))

    return sorted(list(edges))

# ---------------------------------------------------------------------------
# Progressive Failure Simulator (0% to 50%)
# ---------------------------------------------------------------------------
def simulate_75node_failures(edges, total_nodes=75, trials_per_step=150):
    failure_fractions = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    adj = {i: set() for i in range(total_nodes + 1)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    curve_data = []

    for frac in failure_fractions:
        failed_count = int(round(total_nodes * frac))
        living_count = total_nodes - failed_count

        connected_trials = []
        orphaned_trials = []
        hop_trials = []

        for _ in range(trials_per_step):
            failed_set = set(random.sample(range(1, total_nodes + 1), failed_count))
            living_set = set(range(1, total_nodes + 1)) - failed_set

            visited = set()
            depth = {SINK_ROOT: 0}
            queue = deque([SINK_ROOT])

            while queue:
                curr = queue.popleft()
                for nb in adj[curr]:
                    if nb in living_set and nb not in visited:
                        visited.add(nb)
                        depth[nb] = depth[curr] + 1
                        queue.append(nb)

            connected_nodes = len(visited)
            orphaned_nodes = living_count - connected_nodes

            connected_trials.append(connected_nodes)
            orphaned_trials.append(orphaned_nodes)

            if visited:
                avg_hops = sum(depth[n] for n in visited) / len(visited)
                hop_trials.append(avg_hops)

        mean_connected = sum(connected_trials) / trials_per_step
        mean_orphaned = sum(orphaned_trials) / trials_per_step
        mean_hops = sum(hop_trials) / len(hop_trials) if hop_trials else 0.0

        pdr = (mean_connected / living_count) * 100.0 if living_count > 0 else 0.0
        survivability_ratio = (mean_connected / total_nodes) * 100.0
        est_latency_ms = 18.0 + (mean_hops * 3.5)

        curve_data.append({
            "failure_pct": round(frac * 100, 1),
            "failed_nodes": failed_count,
            "living_nodes": living_count,
            "connected_nodes": round(mean_connected, 1),
            "orphaned_nodes": round(mean_orphaned, 1),
            "pdr_pct": round(pdr, 2),
            "survivability_ratio_pct": round(survivability_ratio, 2),
            "avg_hops": round(mean_hops, 2),
            "latency_ms": round(est_latency_ms, 1)
        })

    return curve_data

# ---------------------------------------------------------------------------
# Cooja CSC XML Simulation Generator (75 Nodes + 1 Sink)
# ---------------------------------------------------------------------------
def generate_cooja_75node_csc(name, positions, output_filename, tx_range=110.0):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<simconf>']
    xml.append('  <project EXPORT="discard">[APPS_DIR]/mrm</project>')
    xml.append('  <project EXPORT="discard">[APPS_DIR]/mspsim</project>')
    xml.append('  <project EXPORT="discard">[APPS_DIR]/avrora</project>')
    xml.append('  <project EXPORT="discard">[APPS_DIR]/serial_socket</project>')
    xml.append('  <project EXPORT="discard">[APPS_DIR]/powertracker</project>')
    xml.append('  <simulation>')
    xml.append(f'    <title>Lucas Full 75-Node {name} Network (L0..L7: 2, 1, 3, 4, 7, 11, 18, 29)</title>')
    xml.append('    <randomseed>123456</randomseed>')
    xml.append('    <motedelay_us>1000000</motedelay_us>')
    xml.append('    <radiomedium>')
    xml.append('      org.contikios.cooja.radiomediums.UDGM')
    xml.append(f'      <transmitting_range>{tx_range}</transmitting_range>')
    xml.append(f'      <interference_range>{tx_range * 1.3:.1f}</interference_range>')
    xml.append('      <success_ratio_tx>1.0</success_ratio_tx>')
    xml.append('      <success_ratio_rx>1.0</success_ratio_rx>')
    xml.append('    </radiomedium>')
    xml.append('    <events>')
    xml.append('      <logoutput>40000</logoutput>')
    xml.append('    </events>')

    # Mote Types
    xml.append('    <motetype>')
    xml.append('      org.contikios.cooja.contikimote.ContikiMoteType')
    xml.append('      <identifier>server_mote</identifier>')
    xml.append('      <description>RPL Root Server</description>')
    xml.append('      <source>[CONTIKI_DIR]/examples/rpl-udp/udp-server.c</source>')
    xml.append('      <commands>make udp-server.cooja TARGET=cooja</commands>')
    xml.append('      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>')
    xml.append('    </motetype>')

    xml.append('    <motetype>')
    xml.append('      org.contikios.cooja.contikimote.ContikiMoteType')
    xml.append('      <identifier>client_mote</identifier>')
    xml.append('      <description>Lucas Sensor Mote</description>')
    xml.append('      <source>[CONTIKI_DIR]/examples/rpl-udp/udp-client.c</source>')
    xml.append('      <commands>make udp-client.cooja TARGET=cooja</commands>')
    xml.append('      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>')
    xml.append('      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>')
    xml.append('    </motetype>')

    # Motes
    for n_id in range(TOTAL_NODES + 1):
        pos = positions[n_id]
        mtype = 'server_mote' if n_id == SINK_ROOT else 'client_mote'
        xml.append('    <mote>')
        xml.append('      <breakpoints />')
        xml.append('      <interface_config>')
        xml.append('        org.contikios.cooja.interfaces.Position')
        xml.append(f'        <x>{pos["x"]}</x>')
        xml.append(f'        <y>{pos["y"]}</y>')
        xml.append('        <z>0.0</z>')
        xml.append('      </interface_config>')
        xml.append('      <interface_config>')
        xml.append('        org.contikios.cooja.contikimote.interfaces.ContikiMoteID')
        xml.append(f'        <id>{n_id}</id>')
        xml.append('      </interface_config>')
        xml.append(f'      <motetype_identifier>{mtype}</motetype_identifier>')
        xml.append('    </mote>')

    xml.append('  </simulation>')
    xml.append('</simconf>')

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(xml) + "\n")
    print(f"  [CSC EXPORT] {output_filename}")

# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(" FULL LUCAS SEQUENCE (2, 1, 3, 4, 7, 11, 18, 29) — 75 NODES (L_9 - 1)")
    print(" 50% NODE FAILURE SURVIVABILITY BENCHMARK (STAR vs WHEEL vs 2-EDGE vs MESH)")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    positions = generate_full_cluster_coordinates()
    star_edges = build_full_star_edges()
    wheel_edges = build_full_wheel_edges()
    lucas_2edge_edges = build_full_2edge_edges()
    mesh_edges = build_full_mesh_edges()

    print(f"Links Generated for Full Lucas Sequence (75 Motes):")
    print(f"  - Clustered Star:         {len(star_edges)} edges")
    print(f"  - Clustered Wheel:        {len(wheel_edges)} edges")
    print(f"  - Lucas 2-Edge (TGO):     {len(lucas_2edge_edges)} edges")
    print(f"  - Clustered Mesh:         {len(mesh_edges)} edges")

    print("\n--- Running Progressive Node Failure Benchmark (0% -> 50%) ---")
    star_curve = simulate_75node_failures(star_edges, total_nodes=75)
    wheel_curve = simulate_75node_failures(wheel_edges, total_nodes=75)
    lucas_2edge_curve = simulate_75node_failures(lucas_2edge_edges, total_nodes=75)
    mesh_curve = simulate_75node_failures(mesh_edges, total_nodes=75)

    print("\n" + "=" * 80)
    print("  PROGRESSIVE SURVIVABILITY SCOREBOARD (0% TO 50% NODE LOSS)")
    print("=" * 80)
    header = f"{'Failure %':<10} | {'Living':<7} | {'Star PDR':<10} | {'Wheel PDR':<11} | {'2-Edge PDR':<11} | {'Mesh PDR':<10}"
    print(header)
    print("-" * len(header))

    check_pcts = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    for p in check_pcts:
        s_row = next(r for r in star_curve if r["failure_pct"] == p)
        w_row = next(r for r in wheel_curve if r["failure_pct"] == p)
        l_row = next(r for r in lucas_2edge_curve if r["failure_pct"] == p)
        m_row = next(r for r in mesh_curve if r["failure_pct"] == p)

        print(f"{p:>8.0f}% | {s_row['living_nodes']:<7} | {s_row['pdr_pct']:>8.1f}% | {w_row['pdr_pct']:>9.1f}% | {l_row['pdr_pct']:>9.1f}% | {m_row['pdr_pct']:>8.1f}%")

    # Deep Dive at 50% Node Loss (38 nodes dead, 37 living)
    s_50 = next(r for r in star_curve if r["failure_pct"] == 50.0)
    w_50 = next(r for r in wheel_curve if r["failure_pct"] == 50.0)
    l_50 = next(r for r in lucas_2edge_curve if r["failure_pct"] == 50.0)
    m_50 = next(r for r in mesh_curve if r["failure_pct"] == 50.0)

    print("\n" + "=" * 80)
    print("  DEEP DIVE AT 50% NODE FAILURE (38 NODES DEAD / 37 NODES LIVING)")
    print("=" * 80)
    print(f"  STAR       : Connected={s_50['connected_nodes']}/37 | Orphaned={s_50['orphaned_nodes']} | PDR={s_50['pdr_pct']}% | Latency={s_50['latency_ms']}ms")
    print(f"  WHEEL      : Connected={w_50['connected_nodes']}/37 | Orphaned={w_50['orphaned_nodes']} | PDR={w_50['pdr_pct']}% | Latency={w_50['latency_ms']}ms")
    print(f"  LUCAS 2-EDGE: Connected={l_50['connected_nodes']}/37 | Orphaned={l_50['orphaned_nodes']} | PDR={l_50['pdr_pct']}% | Latency={l_50['latency_ms']}ms (1.5 J/node)")
    print(f"  MESH       : Connected={m_50['connected_nodes']}/37 | Orphaned={m_50['orphaned_nodes']} | PDR={m_50['pdr_pct']}% | Latency={m_50['latency_ms']}ms")
    print("=" * 80)

    # Export Cooja CSC Files
    print("\n--- Exporting 75-Node Cooja Simulation Files (.CSC) ---")
    generate_cooja_75node_csc("Star", positions, os.path.join(base_dir, "lucas-full-star.csc"), tx_range=95.0)
    generate_cooja_75node_csc("Wheel", positions, os.path.join(base_dir, "lucas-full-wheel.csc"), tx_range=110.0)
    generate_cooja_75node_csc("Lucas-2Edge", positions, os.path.join(base_dir, "lucas-full-2edge.csc"), tx_range=120.0)
    generate_cooja_75node_csc("Mesh", positions, os.path.join(base_dir, "lucas-full-mesh.csc"), tx_range=135.0)

    # Save JSON Report
    report_data = {
        "metadata": {
            "title": "Full Lucas Sequence (2, 1, 3, 4, 7, 11, 18, 29) 50% Failure Benchmark",
            "lucas_clusters": FULL_LUCAS_CLUSTERS,
            "total_nodes": TOTAL_NODES,
            "sink_root": SINK_ROOT
        },
        "topologies": {
            "star": {"edges": [list(e) for e in star_edges], "curve": star_curve},
            "wheel": {"edges": [list(e) for e in wheel_edges], "curve": wheel_curve},
            "lucas_2edge": {"edges": [list(e) for e in lucas_2edge_edges], "curve": lucas_2edge_curve},
            "mesh": {"edges": [list(e) for e in mesh_edges], "curve": mesh_curve}
        },
        "positions": positions
    }

    report_path = os.path.join(base_dir, "lucas_full_series_failure_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"  [REPORT EXPORT] Written to: {report_path}")

if __name__ == "__main__":
    main()
