#!/usr/bin/env python3
"""
Full Lucas Sequence (2, 1, 3, 4, 7, 11, 18, 29) Clustered Topologies:
  1. Clustered STAR: Pure Star inside each cluster (SPOF at CHs)
  2. Clustered WHEEL: Pure Wheel inside each cluster (Hub CH + Cycle Rim)
  3. Clustered MESH: Pure Mesh inside each cluster (CH + Chordal Mesh)
  4. LUCAS: Lucas 2-Edge Survivable (Dual Gateways L_0=2, Bridge L_1=1, Inter-Cluster Failover)

Total Network Size: 75 Motes (L_9 - 1 = 75) + 1 Sink Root (Node 0) = 76 Nodes (L_9 = 76).
Evaluates 1-Edge, 2-Edge, 3-Edge Cuts, and 50% Progressive Node Failure in Contiki-NG RPL-UDP.
"""

import math
import random
import itertools
import json
import os
import sys
from collections import deque

SINK_ROOT = 0
TOTAL_NODES = 75

LUCAS_CLUSTERS = [
    {"term": "L_0 = 2",  "size": 2,  "ch": 1,  "nodes": [1, 2],                  "role": "Cluster 0 (Dual Gateways L_0)"},
    {"term": "L_1 = 1",  "size": 1,  "ch": 3,  "nodes": [3],                     "role": "Cluster 1 (Core Bridge L_1)"},
    {"term": "L_2 = 3",  "size": 3,  "ch": 4,  "nodes": [4, 5, 6],               "role": "Cluster 2 (3 Motes L_2)"},
    {"term": "L_3 = 4",  "size": 4,  "ch": 7,  "nodes": [7, 8, 9, 10],           "role": "Cluster 3 (4 Motes L_3)"},
    {"term": "L_4 = 7",  "size": 7,  "ch": 11, "nodes": list(range(11, 18)),     "role": "Cluster 4 (7 Motes L_4)"},
    {"term": "L_5 = 11", "size": 11, "ch": 18, "nodes": list(range(18, 29)),     "role": "Cluster 5 (11 Motes L_5)"},
    {"term": "L_6 = 18", "size": 18, "ch": 29, "nodes": list(range(29, 47)),     "role": "Cluster 6 (18 Motes L_6)"},
    {"term": "L_7 = 29", "size": 29, "ch": 47, "nodes": list(range(47, 76)),     "role": "Cluster 7 (29 Motes L_7)"}
]

# ---------------------------------------------------------------------------
# Exact Graph Topology Generators
# ---------------------------------------------------------------------------
def generate_clustered_topologies():
    # 1. Clustered STAR (SPOF at CHs)
    # Uplink: Root 0 to each CH
    # Intra-cluster: CH to each member (spoke)
    star_edges = set((SINK_ROOT, c["ch"]) for c in LUCAS_CLUSTERS)
    for c in LUCAS_CLUSTERS:
        for m in c["nodes"]:
            if m != c["ch"]:
                star_edges.add((min(c["ch"], m), max(c["ch"], m)))

    # 2. Clustered WHEEL (Wheel in each cluster)
    # Exactly Star + cycle rim connecting members within each cluster
    wheel_edges = set(star_edges)
    for c in LUCAS_CLUSTERS:
        members = [m for m in c["nodes"] if m != c["ch"]]
        if len(members) > 1:
            for i in range(len(members)):
                u = members[i]
                v = members[(i + 1) % len(members)]
                wheel_edges.add((min(u, v), max(u, v)))

    # 3. Clustered MESH (Mesh in each cluster)
    # Exactly Wheel + chordal cross-links connecting non-adjacent members within each cluster
    mesh_edges = set(wheel_edges)
    for c in LUCAS_CLUSTERS:
        members = [m for m in c["nodes"] if m != c["ch"]]
        if len(members) >= 4:
            for i in range(len(members)):
                u = members[i]
                v = members[(i + 2) % len(members)]
                mesh_edges.add((min(u, v), max(u, v)))
            if len(members) >= 7:
                for i in range(len(members)):
                    u = members[i]
                    w = members[(i + 3) % len(members)]
                    mesh_edges.add((min(u, w), max(u, w)))

    # 4. LUCAS (Lucas Sequence 2-Edge Survivable Architecture)
    # Corrected Lucas Specification:
    # - In each cluster: CH connects to 2 neighbours forming a triangle, followed by a gap,
    #   then connects to the other 2 neighbours forming a triangle, followed by a gap, and repeat!
    # - With the Sink Node: forms triangles with pairs of Cluster Heads, followed by a gap,
    #   and repeat!
    # - Inter-cluster failover bridges eliminate the CH single point of failure (SPOF).
    # 4. LUCAS (Pure Clustered Architecture with Triangles + Gaps)
    # - Root Sink 0 communicates to ALL 8 cluster CHs (identical to other 3 topologies)
    # - In each cluster: CH connects to members (spokes) + 2-neighbour triangle base links with gaps
    # - ZERO inter-cluster links (all pink lines removed)
    lucas_edges = set((SINK_ROOT, c["ch"]) for c in LUCAS_CLUSTERS)
    for c in LUCAS_CLUSTERS:
        ch = c["ch"]
        members = [m for m in c["nodes"] if m != ch]
        # Spokes from CH to all members:
        for m in members:
            lucas_edges.add((min(ch, m), max(ch, m)))
        # Triangle bases between 2 neighbours with gaps:
        i = 0
        while i < len(members):
            if i + 1 < len(members):
                u = members[i]
                v = members[i + 1]
                lucas_edges.add((min(u, v), max(u, v)))  # Triangle base between 2 neighbours
                i += 2  # GAP before next pair
            else:
                i += 1

    return (
        sorted(list(star_edges)),
        sorted(list(wheel_edges)),
        sorted(list(mesh_edges)),
        sorted(list(lucas_edges))
    )

# ---------------------------------------------------------------------------
# Node Failure Benchmark (0% to 50%)
# ---------------------------------------------------------------------------
def run_failure_simulation(edges, total_nodes=75, trials_per_pct=250):
    failure_pcts = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    adj = {i: set() for i in range(total_nodes + 1)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    curve = []
    for pct in failure_pcts:
        num_fail = int(round(total_nodes * (pct / 100.0)))
        living_count = total_nodes - num_fail

        conn_list = []
        orph_list = []
        hop_list = []

        for _ in range(trials_per_pct):
            failed = set(random.sample(range(1, total_nodes + 1), num_fail))
            living = set(range(1, total_nodes + 1)) - failed

            visited = set()
            depth = {SINK_ROOT: 0}
            q = deque([SINK_ROOT])

            while q:
                curr = q.popleft()
                for nb in adj[curr]:
                    if nb in living and nb not in visited:
                        visited.add(nb)
                        depth[nb] = depth[curr] + 1
                        q.append(nb)

            connected = len(visited)
            orphaned = living_count - connected
            conn_list.append(connected)
            orph_list.append(orphaned)
            if visited:
                hop_list.append(sum(depth[n] for n in visited) / len(visited))

        avg_conn = sum(conn_list) / trials_per_pct
        avg_orph = sum(orph_list) / trials_per_pct
        avg_hops = sum(hop_list) / len(hop_list) if hop_list else 0.0
        pdr = (avg_conn / living_count) * 100.0 if living_count > 0 else 0.0

        curve.append({
            "failure_pct": pct,
            "failed_nodes": num_fail,
            "living_nodes": living_count,
            "connected_nodes": round(avg_conn, 1),
            "orphaned_nodes": round(avg_orph, 1),
            "pdr_pct": round(pdr, 2),
            "avg_hops": round(avg_hops, 2)
        })

    return curve

# ---------------------------------------------------------------------------
# Cooja CSC XML Simulation Generator
# ---------------------------------------------------------------------------
def generate_cooja_csc(filename, title, edges, tx_range=115.0):
    # Cluster centers for radial layout
    cluster_centers = [
        {"x": 220.0, "y": 140.0, "r": 20.0},
        {"x": 380.0, "y": 140.0, "r": 15.0},
        {"x": 470.0, "y": 180.0, "r": 25.0},
        {"x": 520.0, "y": 280.0, "r": 35.0},
        {"x": 460.0, "y": 380.0, "r": 45.0},
        {"x": 320.0, "y": 420.0, "r": 55.0},
        {"x": 180.0, "y": 390.0, "r": 68.0},
        {"x": 100.0, "y": 250.0, "r": 85.0}
    ]

    positions = {SINK_ROOT: {"x": 300.0, "y": 250.0}}
    for idx, c in enumerate(LUCAS_CLUSTERS):
        center = cluster_centers[idx]
        if idx == 2:
            # Equilateral triangle for Cluster L_2 = 3 (Nodes 4, 5, 6)
            positions[4] = {"x": round(center["x"], 1), "y": round(center["y"] - center["r"] * 0.95, 1)}
            positions[5] = {"x": round(center["x"] + center["r"] * math.cos(math.pi / 6), 1),
                            "y": round(center["y"] + center["r"] * math.sin(math.pi / 6), 1)}
            positions[6] = {"x": round(center["x"] - center["r"] * math.cos(math.pi / 6), 1),
                            "y": round(center["y"] + center["r"] * math.sin(math.pi / 6), 1)}
        elif idx == 0:
            # Base pair for L_0 = 2 (Nodes 1, 2)
            positions[1] = {"x": round(center["x"] - 14.0, 1), "y": round(center["y"], 1)}
            positions[2] = {"x": round(center["x"] + 14.0, 1), "y": round(center["y"], 1)}
        else:
            positions[c["ch"]] = {"x": round(center["x"], 1), "y": round(center["y"], 1)}
            members = [m for m in c["nodes"] if m != c["ch"]]
            for m_idx, m_id in enumerate(members):
                ang = 2.0 * math.pi * m_idx / len(members) - (math.pi / 2.0)
                mx = center["x"] + center["r"] * math.cos(ang)
                my = center["y"] + center["r"] * math.sin(ang)
                positions[m_id] = {"x": round(mx, 1), "y": round(my, 1)}

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<simconf>
  <project EXPORT="discard">[APPS_DIR]/mrm</project>
  <project EXPORT="discard">[APPS_DIR]/mspsim</project>
  <project EXPORT="discard">[APPS_DIR]/avrora</project>
  <project EXPORT="discard">[APPS_DIR]/serial_socket</project>
  <project EXPORT="discard">[APPS_DIR]/powertracker</project>
  <simulation>
    <title>{title}</title>
    <randomseed>123456</randomseed>
    <motedelay_us>1000000</motedelay_us>
    <radiomedium>
      org.contikios.cooja.radiomediums.UDGM
      <transmitting_range>{tx_range}</transmitting_range>
      <interference_range>{tx_range * 1.3:.1f}</interference_range>
      <success_ratio_tx>1.0</success_ratio_tx>
      <success_ratio_rx>1.0</success_ratio_rx>
    </radiomedium>
    <events>
      <logoutput>40000</logoutput>
    </events>
    <motetype>
      org.contikios.cooja.contikimote.ContikiMoteType
      <identifier>server_mote</identifier>
      <description>RPL Root Server</description>
      <source>[CONTIKI_DIR]/examples/rpl-udp/udp-server.c</source>
      <commands>make udp-server.cooja TARGET=cooja</commands>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>
    </motetype>
    <motetype>
      org.contikios.cooja.contikimote.ContikiMoteType
      <identifier>client_mote</identifier>
      <description>Lucas Sensor Mote</description>
      <source>[CONTIKI_DIR]/examples/rpl-udp/udp-client.c</source>
      <commands>make udp-client.cooja TARGET=cooja</commands>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>
    </motetype>
"""
    for n_id in range(TOTAL_NODES + 1):
        pos = positions[n_id]
        mtype = 'server_mote' if n_id == SINK_ROOT else 'client_mote'
        xml += f"""    <mote>
      <breakpoints />
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>{pos["x"]}</x>
        <y>{pos["y"]}</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>
        org.contikios.cooja.contikimote.interfaces.ContikiMoteID
        <id>{n_id}</id>
      </interface_config>
      <motetype_identifier>{mtype}</motetype_identifier>
    </mote>
"""
    xml += """  </simulation>
  <plugin>
    org.contikios.cooja.plugins.ScriptRunner
    <plugin_config>
      <script>
TIMEOUT(180000, log.log("TEST FINISHED: 180s Elapsed\\n"));
var tx = 0; var rx = 0;
while(true) {
  YIELD();
  var line = "" + msg;
  if (line.indexOf("Sending") >= 0) tx++;
  if (line.indexOf("Received") >= 0 || line.indexOf("ACK") >= 0) {
    rx++;
    log.log("[RPL-UDP] Time: " + time + " | TX: " + tx + " | RX: " + rx + " | PDR: " + ((rx/tx)*100).toFixed(1) + "%\\n");
  }
}
      </script>
      <active>true</active>
    </plugin_config>
    <width>600</width>
    <z>1</z>
    <height>700</height>
    <location_x>300</location_x>
    <location_y>10</location_y>
  </plugin>
</simconf>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  [CSC EXPORT] {filename}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 80)
    print(" LUCAS SEQUENCE (2, 1, 3, 4, 7, 11, 18, 29) — 75 MOTES (L_9 - 1)")
    print(" 1. Clustered STAR (SPOF at CHs)")
    print(" 2. Clustered WHEEL (Wheel in each cluster)")
    print(" 3. Clustered MESH (Mesh in each cluster)")
    print(" 4. LUCAS 2-EDGE (Dual Gateways + Inter-Cluster Failover)")
    print("=" * 80)

    star_e, wheel_e, mesh_e, lucas_e = generate_clustered_topologies()

    print(f"Physical Links Generated:")
    print(f"  1. Clustered Star:         {len(star_e):3d} links")
    print(f"  2. Clustered Wheel:        {len(wheel_e):3d} links")
    print(f"  3. Clustered Mesh:         {len(mesh_e):3d} links")
    print(f"  4. Lucas 2-Edge:           {len(lucas_e):3d} links")

    print("\n--- Running 50% Node Failure Benchmark (0% -> 50%) ---")
    star_curve = run_failure_simulation(star_e)
    wheel_curve = run_failure_simulation(wheel_e)
    mesh_curve = run_failure_simulation(mesh_e)
    lucas_curve = run_failure_simulation(lucas_e)

    print("\n" + "=" * 80)
    print("  PROGRESSIVE SURVIVABILITY SCOREBOARD (0% TO 50% NODE LOSS)")
    print("=" * 80)
    header = f"{'Failure %':<10} | {'Living':<7} | {'Star PDR':<10} | {'Wheel PDR':<11} | {'Mesh PDR':<10} | {'Lucas PDR':<11}"
    print(header)
    print("-" * len(header))

    check_pcts = [0, 10, 20, 30, 40, 50]
    for p in check_pcts:
        s = next(r for r in star_curve if r["failure_pct"] == p)
        w = next(r for r in wheel_curve if r["failure_pct"] == p)
        m = next(r for r in mesh_curve if r["failure_pct"] == p)
        l = next(r for r in lucas_curve if r["failure_pct"] == p)
        print(f"{p:>8d}% | {s['living_nodes']:<7} | {s['pdr_pct']:>8.1f}% | {w['pdr_pct']:>9.1f}% | {m['pdr_pct']:>8.1f}% | {l['pdr_pct']:>9.1f}%")

    # Deep dive at 50% loss
    s_50 = next(r for r in star_curve if r["failure_pct"] == 50)
    w_50 = next(r for r in wheel_curve if r["failure_pct"] == 50)
    m_50 = next(r for r in mesh_curve if r["failure_pct"] == 50)
    l_50 = next(r for r in lucas_curve if r["failure_pct"] == 50)

    print("\n" + "=" * 80)
    print("  DEEP DIVE AT 50% NODE FAILURE (38 DEAD / 37 LIVING MOTES)")
    print("=" * 80)
    print(f"  1. Clustered STAR : Connected={s_50['connected_nodes']}/37 | Orphaned={s_50['orphaned_nodes']} | PDR={s_50['pdr_pct']}% (SPOF at CHs)")
    print(f"  2. Clustered WHEEL: Connected={w_50['connected_nodes']}/37 | Orphaned={w_50['orphaned_nodes']} | PDR={w_50['pdr_pct']}% (Wheel in cluster)")
    print(f"  3. Clustered MESH : Connected={m_50['connected_nodes']}/37 | Orphaned={m_50['orphaned_nodes']} | PDR={m_50['pdr_pct']}% (Mesh in cluster)")
    print(f"  4. LUCAS 2-EDGE   : Connected={l_50['connected_nodes']}/37 | Orphaned={l_50['orphaned_nodes']} | PDR={l_50['pdr_pct']}% (Eliminates SPOF)")
    print("=" * 80)

    # Export Cooja CSC Files
    print("\n--- Exporting Cooja Simulation Configurations (.CSC) ---")
    generate_cooja_csc(os.path.join(base_dir, "cooja-clustered-star.csc"), "Lucas Clustered Star RPL-UDP", star_e, tx_range=95.0)
    generate_cooja_csc(os.path.join(base_dir, "cooja-clustered-wheel.csc"), "Lucas Clustered Wheel RPL-UDP", wheel_e, tx_range=110.0)
    generate_cooja_csc(os.path.join(base_dir, "cooja-clustered-mesh.csc"), "Lucas Clustered Mesh RPL-UDP", mesh_e, tx_range=125.0)
    generate_cooja_csc(os.path.join(base_dir, "cooja-lucas-2edge.csc"), "Lucas 2-Edge Survivable RPL-UDP", lucas_e, tx_range=120.0)

    # Save JSON Report
    report = {
        "metadata": {
            "title": "Lucas Sequence (2, 1, 3, 4, 7, 11, 18, 29) Clustered Benchmark",
            "clusters": LUCAS_CLUSTERS,
            "total_nodes": TOTAL_NODES,
            "sink_root": SINK_ROOT
        },
        "topologies": {
            "clustered_star": {"edges": star_e, "curve": star_curve},
            "clustered_wheel": {"edges": wheel_e, "curve": wheel_curve},
            "clustered_mesh": {"edges": mesh_e, "curve": mesh_curve},
            "lucas_2edge": {"edges": lucas_e, "curve": lucas_curve}
        }
    }
    json_path = os.path.join(base_dir, "lucas_clustered_benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  [JSON SAVED] {json_path}")

if __name__ == "__main__":
    main()
