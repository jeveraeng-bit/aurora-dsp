"""
Servidor local ultraligero para previsualizar la tienda web de Aurora DSP.
Ejecuta: python web/serve.py
"""
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"=======================================================")
        print(f"  AURORA DSP - TIENDA WEB DE PLUGINS & SINTETIZADORES")
        print(f"  Desarrollado por Juan Esteban Vera (UAN)")
        print(f"=======================================================")
        print(f"  Servidor corriendo en: {url}")
        print(f"  Abriendo navegador automáticamente...")
        print(f"  Presiona Ctrl + C para detener.")
        print(f"=======================================================")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
            sys.exit(0)

if __name__ == "__main__":
    run()
