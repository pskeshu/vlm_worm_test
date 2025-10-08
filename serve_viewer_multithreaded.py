#!/usr/bin/env python3
"""
Multithreaded HTTP server for embryo viewer.
Handles multiple concurrent users better than basic http.server.
"""

import http.server
import socketserver
import threading

PORT = 8000

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """HTTP server that uses threading to handle multiple requests"""
    allow_reuse_address = True
    daemon_threads = True

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler with better logging"""

    def log_message(self, format, *args):
        """Override to add timestamp and color"""
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    handler = MyHTTPRequestHandler

    with ThreadedHTTPServer(("", PORT), handler) as httpd:
        print("=" * 60)
        print("🔬 C. elegans Embryo Viewer - HTTP Server")
        print("=" * 60)
        print(f"\nServer running on port {PORT}")
        print(f"\n📱 Access the viewer at:")
        print(f"   http://localhost:{PORT}/embryo_viewer_light.html")
        print(f"\n🌐 Or from other devices on your network:")
        print(f"   http://YOUR_IP_ADDRESS:{PORT}/embryo_viewer_light.html")
        print(f"\n💡 This server supports multiple concurrent users")
        print(f"\n⏹  Press Ctrl+C to stop the server\n")
        print("=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down server...")
            httpd.shutdown()
            print("✓ Server stopped\n")
