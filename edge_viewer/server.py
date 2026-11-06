import http.server
import socketserver
import os
import json
import urllib.parse
import time
import random

PORT = 8080
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class EdgeViewerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/file":
            file_rel = query.get("path", [""])[0]
            safe_path = os.path.abspath(os.path.join(BASE_DIR, file_rel))
            if not safe_path.startswith(BASE_DIR) or not os.path.isfile(safe_path):
                self.send_error(404, "File not found or access denied")
                return

            content = ""
            for encoding in ["utf-8", "latin-1"]:
                try:
                    with open(safe_path, "r", encoding=encoding, errors="replace") as f:
                        content = f.read()
                    break
                except Exception:
                    continue

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"path": file_rel, "content": content}).encode("utf-8"))
            return

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status = {
                "system": "Edge Computing RPL-UDP Simulation",
                "gateway": {"ip": "fd00::1", "port": 5678, "status": "ONLINE"},
                "server": {"ip": "127.0.0.1", "port": 8080, "protocol": "TCP", "status": "ONLINE"},
                "rpl_root": {"id": 1, "prefix": "fd00::/64", "status": "DAG_ROOT_ACTIVE"}
            }
            self.wfile.write(json.dumps(status).encode("utf-8"))
            return

        return super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), EdgeViewerHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
