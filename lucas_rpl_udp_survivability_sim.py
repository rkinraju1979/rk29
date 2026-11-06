#!/usr/bin/env python3
"""
RPL-UDP Packet Delivery & Survivability Simulator for Lucas Topologies
Simulates RPL Rank calculation (MRHOF Objective Function), parent selection,
local repair failover, and UDP Packet Delivery Ratio (PDR) under 1-Edge, 2-Edge,
and 3-Edge failures in Star, Wheel, and Mesh topologies.
"""

import sys
import random
import math
from collections import deque
from lucas_topology_survivability import (
    NUM_NODES, ROOT_ID, CLIENT_IDS,
    get_star_edges, get_wheel_edges, get_mesh_edges
)

class RPLNode:
    def __init__(self, node_id, is_root=False):
        self.id = node_id
        self.is_root = is_root
        self.rank = 256 if is_root else 65535  # RFC 6550: Root default rank 256
        self.preferred_parent = None
        self.alternate_parents = []
        self.neighbors = set()

class RPLSimulation:
    def __init__(self, topology_name, edges):
        self.name = topology_name
        self.edges = set(edges)
        self.active_edges = set(edges)
        self.nodes = {i: RPLNode(i, is_root=(i == ROOT_ID)) for i in range(1, NUM_NODES + 1)}
        self._build_neighbors()
        self.build_dodag()

    def _build_neighbors(self):
        for n in self.nodes.values():
            n.neighbors.clear()
        for u, v in self.active_edges:
            self.nodes[u].neighbors.add(v)
            self.nodes[v].neighbors.add(u)

    def build_dodag(self):
        """
        Simulates RPL DODAG formation via DIO multicasts with MRHOF ETX metric.
        Root starts at Rank 256. Each hop adds step_of_rank = 256.
        """
        for n in self.nodes.values():
            if not n.is_root:
                n.rank = 65535
                n.preferred_parent = None
                n.alternate_parents = []

        queue = deque([ROOT_ID])
        visited_depth = {ROOT_ID: 0}

        while queue:
            curr_id = queue.popleft()
            curr_node = self.nodes[curr_id]

            for neighbor_id in curr_node.neighbors:
                if neighbor_id not in visited_depth:
                    visited_depth[neighbor_id] = visited_depth[curr_id] + 1
                    queue.append(neighbor_id)

                nb_node = self.nodes[neighbor_id]
                # If neighbor has lower rank, it's a potential parent
                if curr_node.rank < nb_node.rank:
                    new_rank = curr_node.rank + 256  # Step of rank = 256
                    if new_rank < nb_node.rank:
                        nb_node.rank = new_rank
                        nb_node.preferred_parent = curr_id
                    elif new_rank == nb_node.rank and curr_id != nb_node.preferred_parent:
                        if curr_id not in nb_node.alternate_parents:
                            nb_node.alternate_parents.append(curr_id)

    def route_packet(self, src_id, max_hops=20):
        """
        Attempts to route a UDP telemetry packet from src_id to ROOT_ID (1)
        using RPL preferred and alternate parents.
        Returns: (success: bool, hops: int, path: list)
        """
        if src_id == ROOT_ID:
            return True, 0, [ROOT_ID]

        curr = src_id
        path = [curr]
        visited = {curr}

        for _ in range(max_hops):
            node = self.nodes[curr]
            parent = node.preferred_parent

            # Verify parent link is still active
            edge = (min(curr, parent), max(curr, parent)) if parent else None
            if parent and edge in self.active_edges:
                next_hop = parent
            else:
                # RPL Local Repair: search alternate parents with active link
                next_hop = None
                for alt in node.alternate_parents:
                    alt_edge = (min(curr, alt), max(curr, alt))
                    if alt_edge in self.active_edges:
                        next_hop = alt
                        break

                # If no alternate parent, check any neighbor with lower rank
                if not next_hop:
                    for nb in node.neighbors:
                        if self.nodes[nb].rank < node.rank and nb not in visited:
                            next_hop = nb
                            break

            if not next_hop:
                return False, len(path), path  # Link broken, packet dropped

            path.append(next_hop)
            if next_hop == ROOT_ID:
                return True, len(path) - 1, path

            visited.add(next_hop)
            curr = next_hop

        return False, len(path), path

    def cut_edges(self, edges_to_cut):
        for e in edges_to_cut:
            clean_e = (min(e[0], e[1]), max(e[0], e[1]))
            if clean_e in self.active_edges:
                self.active_edges.remove(clean_e)
        self._build_neighbors()
        self.build_dodag()

    def restore_all(self):
        self.active_edges = set(self.edges)
        self._build_neighbors()
        self.build_dodag()

    def run_udp_round(self, packets_per_node=10):
        """
        Sends UDP CBR telemetry from all 17 client motes to the Root.
        Returns PDR and average hop count.
        """
        total_tx = 0
        total_rx = 0
        total_hops = 0

        for client_id in CLIENT_IDS:
            for _ in range(packets_per_node):
                total_tx += 1
                success, hops, _ = self.route_packet(client_id)
                if success:
                    total_rx += 1
                    total_hops += hops

        pdr = (total_rx / total_tx) * 100.0 if total_tx > 0 else 0.0
        avg_hops = (total_hops / total_rx) if total_rx > 0 else 0.0
        return pdr, avg_hops, total_rx, total_tx

def test_topology_survivability():
    topos = [
        ("Lucas Star", get_star_edges()),
        ("Lucas Wheel", get_wheel_edges()),
        ("Lucas Mesh", get_mesh_edges())
    ]

    print("=" * 70)
    print(" RPL-UDP SURVIVABILITY SIMULATION UNDER 1, 2, AND 3 EDGE CUTS")
    print("=" * 70)

    for name, edges in topos:
        sim = RPLSimulation(name, edges)
        pdr_base, hops_base, _, _ = sim.run_udp_round()

        print(f"\n--- {name.upper()} (Total Links: {len(edges)}) ---")
        print(f"  [Baseline] 0 Cuts -> PDR: {pdr_base:.1f}% | Avg Hops: {hops_base:.2f}")

        for k in [1, 2, 3]:
            # Run 50 random cut trials for each k
            pdr_trials = []
            hops_trials = []
            num_trials = 50

            edge_list = list(edges)
            for _ in range(num_trials):
                sim.restore_all()
                chosen_cuts = random.sample(edge_list, k)
                sim.cut_edges(chosen_cuts)
                pdr, hops, _, _ = sim.run_udp_round(packets_per_node=5)
                pdr_trials.append(pdr)
                if hops > 0:
                    hops_trials.append(hops)

            avg_pdr = sum(pdr_trials) / len(pdr_trials)
            avg_h = sum(hops_trials) / len(hops_trials) if hops_trials else 0.0

            verdict = "100% SURVIVES" if avg_pdr == 100.0 else f"{avg_pdr:.1f}% PDR"
            print(f"  [{k}-Edge Failure] Average PDR across {num_trials} trials: {avg_pdr:.1f}% | Avg Hops: {avg_h:.2f} -> {verdict}")

if __name__ == "__main__":
    test_topology_survivability()
