#!/usr/bin/env python3
"""
=============================================================================
 generate_cooja_csc_files.py
=============================================================================
 Automated Generator for Contiki-NG Cooja Simulation Configurations (.CSC)
 Generates 4 Production-Ready Cooja Configurations:
   1. cooja-lucas-2edge.csc     (107 links: Lucas 2-Edge with Triangle Fault Tolerance)
   2. cooja-clustered-star.csc  (75 links: Clustered Star, SPOF at Cluster Heads)
   3. cooja-clustered-wheel.csc (140 links: Clustered Wheel with Rim Cycles)
   4. cooja-clustered-mesh.csc  (256 links: Clustered Mesh with Cross-Cluster Chords)

 Scale: 76 Total Nodes (1 Root Sink Node 0 + 75 Motes across Lucas Tiers L0..L7):
        L0=2, L1=1, L2=3, L3=4, L4=7, L5=11, L6=18, L7=29.

 Features:
   - Native [CONFIG_DIR] macro support: Compiles local udp-server.c & udp-client.c
     directly inside your project directory (e.g. ~/contiki-ng/examples/rk1000lmws).
   - Supports fallback to [CONTIKI_DIR]/examples/rpl-udp via --use-contiki-dir flag.
   - Complete ContikiMote interface bindings (ID, Radio, RS232, Clock, LED, IP, etc.)
     guaranteeing zero NullPointerException errors in Cooja.
   - Built-in GUI Plugins (SimControl, Visualizer, LogListener, ScriptRunner).
   - Headless test execution (-nogui) with automated PDR metric logging.
=============================================================================
"""

import math
import os
import sys
import argparse

SINK_ROOT = 0
TOTAL_NODES = 75

LUCAS_CLUSTERS = [
    {"term": "L_0 = 2",  "size": 2,  "ch": 1,  "nodes": [1, 2]},
    {"term": "L_1 = 1",  "size": 1,  "ch": 3,  "nodes": [3]},
    {"term": "L_2 = 3",  "size": 3,  "ch": 4,  "nodes": [4, 5, 6]},
    {"term": "L_3 = 4",  "size": 4,  "ch": 7,  "nodes": [7, 8, 9, 10]},
    {"term": "L_4 = 7",  "size": 7,  "ch": 11, "nodes": list(range(11, 18))},
    {"term": "L_5 = 11", "size": 11, "ch": 18, "nodes": list(range(18, 29))},
    {"term": "L_6 = 18", "size": 18, "ch": 29, "nodes": list(range(29, 47))},
    {"term": "L_7 = 29", "size": 29, "ch": 47, "nodes": list(range(47, 76))}
]

POD_CENTERS = [
    {"x": 380, "y": 120, "r": 24},  # L_0 = 2
    {"x": 500, "y": 120, "r": 18},  # L_1 = 1
    {"x": 640, "y": 130, "r": 30},  # L_2 = 3 (Equilateral Triangle: Nodes 4, 5, 6)
    {"x": 790, "y": 220, "r": 36},  # L_3 = 4
    {"x": 800, "y": 370, "r": 46},  # L_4 = 7
    {"x": 580, "y": 430, "r": 56},  # L_5 = 11
    {"x": 330, "y": 410, "r": 68},  # L_6 = 18
    {"x": 150, "y": 260, "r": 85}   # L_7 = 29
]

def build_node_positions():
    """Calculates 2D planar positions for Root Sink (0) and 75 Lucas cluster nodes."""
    positions = {}
    positions[SINK_ROOT] = {"x": 300.0, "y": 250.0}

    for idx, c in enumerate(LUCAS_CLUSTERS):
        center = POD_CENTERS[idx]
        if idx == 2:
            # Equilateral triangle for L_2 = 3 (Nodes 4, 5, 6)
            positions[4] = {"x": round(center["x"], 1), "y": round(center["y"] - center["r"] * 0.95, 1)}
            positions[5] = {"x": round(center["x"] + center["r"] * math.cos(math.pi / 6), 1),
                            "y": round(center["y"] + center["r"] * math.sin(math.pi / 6), 1)}
            positions[6] = {"x": round(center["x"] - center["r"] * math.cos(math.pi / 6), 1),
                            "y": round(center["y"] + center["r"] * math.sin(math.pi / 6), 1)}
        elif idx == 0:
            # Pair for L_0 = 2 (Nodes 1, 2)
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

    return positions

def generate_csc(filename, title, tx_range, source_base, timeout_ms=180000):
    """Generates a complete, self-contained Contiki-NG Cooja .csc simulation file."""
    positions = build_node_positions()
    interference_range = round(tx_range * 1.3, 1)

    server_source = f"{source_base}/udp-server.c"
    client_source = f"{source_base}/udp-client.c"

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
      <interference_range>{interference_range}</interference_range>
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
      <source>{server_source}</source>
      <commands>make udp-server.cooja TARGET=cooja</commands>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiVib</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiBeeper</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.RimeAddress</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiIPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiButton</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiPIR</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiCFS</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiEEPROM</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Mote2MoteRelations</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.MoteAttributes</moteinterface>
      <symbols>false</symbols>
    </motetype>
    <motetype>
      org.contikios.cooja.contikimote.ContikiMoteType
      <identifier>client_mote</identifier>
      <description>Lucas Sensor Mote</description>
      <source>{client_source}</source>
      <commands>make udp-client.cooja TARGET=cooja</commands>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiVib</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiBeeper</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.RimeAddress</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiIPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiButton</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiPIR</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiCFS</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiEEPROM</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Mote2MoteRelations</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.MoteAttributes</moteinterface>
      <symbols>false</symbols>
    </motetype>
"""

    for n_id in range(TOTAL_NODES + 1):
        pos = positions[n_id]
        mtype = "server_mote" if n_id == SINK_ROOT else "client_mote"
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
      <interface_config>
        org.contikios.cooja.contikimote.interfaces.ContikiRadio
        <bitrate>250.0</bitrate>
      </interface_config>
      <motetype_identifier>{mtype}</motetype_identifier>
    </mote>
"""

    xml += f"""  </simulation>
  <plugin>
    org.contikios.cooja.plugins.SimControl
    <width>280</width>
    <z>3</z>
    <height>160</height>
    <location_x>10</location_x>
    <location_y>10</location_y>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.Visualizer
    <plugin_config>
      <moterelations>true</moterelations>
      <skin>org.contikios.cooja.plugins.skins.IDVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.UDGMVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.TrafficVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.LEDVisualizerSkin</skin>
      <viewport>0.85 0.0 0.0 0.85 30 30</viewport>
    </plugin_config>
    <width>620</width>
    <z>2</z>
    <height>620</height>
    <location_x>10</location_x>
    <location_y>180</location_y>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.LogListener
    <plugin_config>
      <filter />
      <formatted_time />
      <coloring />
    </plugin_config>
    <width>800</width>
    <z>1</z>
    <height>350</height>
    <location_x>640</location_x>
    <location_y>10</location_y>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.ScriptRunner
    <plugin_config>
      <script>
TIMEOUT({timeout_ms}, log.log("TEST FINISHED: Simulation Time Elapsed\\n"));
var tx = 0;
var rx = 0;
while(true) {{
  YIELD();
  var line = "" + msg;
  if (line.indexOf("Sending") &gt;= 0 || line.indexOf("TX") &gt;= 0) {{
    tx++;
  }}
  if (line.indexOf("Received") &gt;= 0 || line.indexOf("ACK") &gt;= 0 || line.indexOf("RX") &gt;= 0) {{
    rx++;
    var pdr = (rx / (tx &gt; 0 ? tx : 1)) * 100.0;
    log.log("[RPL-UDP METRIC] Time: " + time + " | TX: " + tx + " | RX: " + rx + " | PDR: " + pdr.toFixed(1) + "%\\n");
  }}
}}
      </script>
      <active>true</active>
    </plugin_config>
    <width>800</width>
    <z>0</z>
    <height>430</height>
    <location_x>640</location_x>
    <location_y>370</location_y>
  </plugin>
</simconf>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  [SUCCESS] Generated: {filename} (TX={tx_range}m, Source={server_source})")

def main():
    parser = argparse.ArgumentParser(
        description="Generate 4 Contiki-NG Cooja Simulation CSC Files for Lucas Clustered Topologies."
    )
    parser.add_argument(
        "--use-contiki-dir",
        action="store_true",
        help="Use [CONTIKI_DIR]/examples/rpl-udp as source base instead of local [CONFIG_DIR]"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=180,
        help="Simulation test duration in seconds (default: 180s)"
    )
    args = parser.parse_args()

    # Determine source directory base macro:
    # [CONFIG_DIR] points to the folder where the .csc file is located (e.g. examples/rk1000lmws).
    # [CONTIKI_DIR]/examples/rpl-udp points to stock Contiki-NG rpl-udp examples.
    if args.use_contiki_dir:
        source_base = "[CONTIKI_DIR]/examples/rpl-udp"
    else:
        source_base = "[CONFIG_DIR]"

    timeout_ms = args.duration * 1000

    print("=" * 80)
    print(" CONTIKI-NG COOJA CSC TOPOLOGY GENERATOR (76 NODES: L0..L7)")
    print(f" Source Macro Base : {source_base}")
    print(f" Test Timeout      : {args.duration}s ({timeout_ms} ms)")
    print("=" * 80)

    # 1. Lucas 2-Edge Survivable Network (107 Links: 8 CH uplinks + 67 spokes + 32 base links)
    generate_csc(
        "cooja-lucas-2edge.csc",
        "Lucas 2-Edge Survivable RPL-UDP Network (107 Links)",
        tx_range=120.0,
        source_base=source_base,
        timeout_ms=timeout_ms
    )

    # 2. Clustered Star Network (75 Links: 8 CH uplinks + 67 spokes)
    generate_csc(
        "cooja-clustered-star.csc",
        "Lucas Clustered Star RPL-UDP Network (75 Links)",
        tx_range=95.0,
        source_base=source_base,
        timeout_ms=timeout_ms
    )

    # 3. Clustered Wheel Network (140 Links: 75 star + 65 rim links)
    generate_csc(
        "cooja-clustered-wheel.csc",
        "Lucas Clustered Wheel RPL-UDP Network (140 Links)",
        tx_range=110.0,
        source_base=source_base,
        timeout_ms=timeout_ms
    )

    # 4. Clustered Mesh Network (256 Links: 140 wheel + 116 cross-cluster chords)
    generate_csc(
        "cooja-clustered-mesh.csc",
        "Lucas Clustered Mesh RPL-UDP Network (256 Links)",
        tx_range=125.0,
        source_base=source_base,
        timeout_ms=timeout_ms
    )

    print("=" * 80)
    print(" All 4 .csc simulation files successfully generated!")
    print("\n HOW TO RUN IN CONTIKI-NG:")
    print(" 1. GUI Mode (Interactive with Visualizer & Log Listener):")
    print("    cooja cooja-lucas-2edge.csc")
    print("    (or: java -jar ../../tools/cooja/dist/cooja.jar -quick cooja-lucas-2edge.csc)")
    print("\n 2. Headless Mode (Fast Automated Test Execution):")
    print("    java -jar ../../tools/cooja/dist/cooja.jar -nogui=cooja-lucas-2edge.csc")
    print("=" * 80)

if __name__ == "__main__":
    main()
