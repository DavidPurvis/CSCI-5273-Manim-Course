"""A small local web server with the Range support video seeking needs. It only listens on this Mac."""
import errno
import json
import mimetypes
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

PORT = 5273
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
TYPES = {".md": "text/plain; charset=utf-8", ".canvas": "application/json; charset=utf-8", ".vtt": "text/vtt", ".mp4": "video/mp4", ".json": "application/json", ".js": "text/javascript", ".css": "text/css",
         ".html": "text/html; charset=utf-8", ".jpg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf", ".svg": "image/svg+xml"}


def make_handler(mounts, on_post=None):
    """mounts maps a URL prefix to a folder; the longest matching prefix wins."""
    order = sorted(mounts, key=len, reverse=True)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def locate(self):
            url = unquote(urlparse(self.path).path)
            for prefix in order:
                if url.startswith(prefix):
                    root = Path(mounts[prefix]).resolve()
                    target = (root / url[len(prefix):].lstrip("/")).resolve()
                    if not target.is_relative_to(root):
                        return None
                    target = (target / "index.html").resolve() if target.is_dir() else target
                    return target if target.is_relative_to(root) else None
            return None

        def fail(self, code):
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_HEAD(self):
            self.do_GET(body=False)

        def do_GET(self, body=True):
            path = self.locate()
            if path is None or not path.is_file():
                return self.fail(404)
            size = path.stat().st_size
            start, end, status = 0, size - 1, 200
            m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:
                    start = max(size - int(m.group(2)), 0)
                end = min(end, size - 1)
                if start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                status = 206
            self.send_response(status)
            self.send_header("Content-Type", TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", "no-cache")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if not body:
                return
            try:
                with path.open("rb") as f:
                    f.seek(start)
                    left = end - start + 1
                    while left > 0:
                        chunk = f.read(min(1 << 20, left))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def allowed_writer(self):
            """Only this server's own pages may write. A JSON content type also forces a browser
            preflight on any other site, and this server answers no preflight."""
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            content = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            return (host.rsplit(":", 1)[0] in LOCAL_HOSTS and content == "application/json"
                    and (origin is None or origin == f"http://{host}"))

        def do_POST(self):
            if on_post is None:
                return self.fail(404)
            if not self.allowed_writer():
                return self.fail(403)
            try:
                data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                reply = json.dumps(on_post(urlparse(self.path).path, data)).encode()
            except (ValueError, KeyError, TypeError, AttributeError):
                return self.fail(400)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

    return Handler


def create_server(mounts, on_post=None, port=PORT):
    """Bind loopback; let the OS choose a free port if the preferred one is busy."""
    handler = make_handler(mounts, on_post)
    try:
        return ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE or port == 0:
            raise
        return ThreadingHTTPServer(("127.0.0.1", 0), handler)


def serve(mounts, start="/", on_post=None, port=PORT, open_browser=True):
    server = create_server(mounts, on_post, port)
    url = f"http://127.0.0.1:{server.server_port}{start}"
    print(f"Open {url}\nPress Control-C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
