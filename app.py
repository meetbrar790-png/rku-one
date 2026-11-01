import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class RKUHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"RKU ONE Backend Ready")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), RKUHandler)
    server.serve_forever()
