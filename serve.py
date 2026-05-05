import os, http.server, socketserver

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servidor en http://localhost:{PORT}")
    httpd.serve_forever()
