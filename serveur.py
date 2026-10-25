import http.server
import socketserver
import urllib.request
import urllib.error
import ssl
import os

PORT = int(os.environ.get("PORT", 10000))

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-MAL-CLIENT-ID')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def handle_mal_request(self):
        if self.path.startswith('/api/'):
            url = "https://api.myanimelist.net/v2/" + self.path[5:]
        elif self.path.startswith('/oauth/'):
            url = "https://myanimelist.net/v1/oauth2/" + self.path[7:]
        else:
            self.send_error(404)
            return

        req = urllib.request.Request(url, method=self.command)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        for k, v in self.headers.items():
            if k.lower() not in ['host', 'connection', 'content-length', 'origin', 'referer', 'accept-encoding', 'user-agent']:
                req.add_header(k, v)
        
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            req.data = self.rfile.read(content_length)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                self.send_response(response.status)
                self.send_cors_headers()
                for k, v in response.getheaders():
                    if k.lower() not in ['transfer-encoding', 'connection', 'www-authenticate']:
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_cors_headers()
            for k, v in e.headers.items():
                if k.lower() not in ['transfer-encoding', 'connection', 'www-authenticate']:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path.startswith('/api/') or self.path.startswith('/oauth/'):
            self.handle_mal_request()
        else:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b"Serveur actif")

    def do_POST(self): self.handle_mal_request()
    def do_PATCH(self): self.handle_mal_request()
    def do_PUT(self): self.handle_mal_request()
    def do_DELETE(self): self.handle_mal_request()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
    httpd.serve_forever()
