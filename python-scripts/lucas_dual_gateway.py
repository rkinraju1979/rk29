"""
Dual-Edge Python Gateway for Lucas Sequence 2-Edge Survivable Networks
Binds to both Edge Gateway 1 (fd00::1:5678) and Edge Gateway 2 (fd00::2:5678)
Provides hot-standby 2-edge fault tolerance and forwards telemetry to the Edge Server.
"""

import sys
import time
import socket
import threading

BUFSIZE = 1024

class LucasDualEdgeGateway:
    def __init__(self, gw1_ip="fd00::1", gw2_ip="fd00::2", port=5678, server_ip="127.0.0.1", server_port=8080):
        self.gw1_ip = gw1_ip
        self.gw2_ip = gw2_ip
        self.port = port
        self.server_ip = server_ip
        self.server_port = server_port
        self.total_packets = 0
        self.gw1_packets = 0
        self.gw2_packets = 0
        self.start_time = None
        self.tcp_sock = None
        self.lock = threading.Lock()

    def connect_upstream_server(self):
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.connect((self.server_ip, self.server_port))
            print(f"[GATEWAY] Connected to Edge Server at {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"[GATEWAY] Notice: Upstream server not reached ({e}). Running in local telemetry mode.")
            self.tcp_sock = None

    def listen_gateway(self, gw_ip, gw_id):
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
                s.bind((gw_ip, self.port))
                print(f"[GATEWAY {gw_id}] IPv6 UDP Gateway ready on [{gw_ip}]:{self.port}")
                while True:
                    data, addr = s.recvfrom(BUFSIZE)
                    with self.lock:
                        if self.start_time is None:
                            self.start_time = time.time()
                        self.total_packets += 1
                        if gw_id == 1:
                            self.gw1_packets += 1
                        else:
                            self.gw2_packets += 1

                        elapsed = time.time() - self.start_time
                        print(f"[GW-{gw_id}] Received from {addr}: {data.decode('utf-8', errors='ignore')} | "
                              f"Total: {self.total_packets} (GW1: {self.gw1_packets}, GW2: {self.gw2_packets}) | Time: {elapsed:.2f}s")

                        if self.tcp_sock:
                            try:
                                self.tcp_sock.sendall(data)
                            except Exception:
                                pass
        except Exception as e:
            print(f"[GATEWAY {gw_id}] Interface [{gw_ip}] note: {e}")

    def run(self):
        print("=== LUCAS SEQUENCE 2-EDGE SURVIVABLE GATEWAY INITIALIZING ===")
        print(f"Dual Edge Gateways: L0=2 -> GW1=[{self.gw1_ip}], GW2=[{self.gw2_ip}]")
        self.connect_upstream_server()

        t1 = threading.Thread(target=self.listen_gateway, args=(self.gw1_ip, 1), daemon=True)
        t2 = threading.Thread(target=self.listen_gateway, args=(self.gw2_ip, 2), daemon=True)
        t1.start()
        t2.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[GATEWAY] Shutting down.")

if __name__ == "__main__":
    gw = LucasDualEdgeGateway()
    gw.run()
