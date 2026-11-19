import base64
import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image

from fm27facegen.backends import BackendSettings, StableDiffusionWebUIBackend
from fm27facegen.prompts import FaceOptions, build_prompt


class SlowForge(BaseHTTPRequestHandler):
    started = 0.0

    def _json(self, data):
        d = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/sdapi/v1/progress"):
            elapsed = time.time() - SlowForge.started
            self._json({"progress": min(elapsed / 2.0, 0.95) if SlowForge.started else 0})
        else:
            self._json({"sd_model_checkpoint": "RealVisXL_V5.0"})

    def do_POST(self):  # noqa: N802
        self.rfile.read(int(self.headers["Content-Length"]))
        SlowForge.started = time.time()
        time.sleep(2.0)  # Bild wird "berechnet"
        buf = io.BytesIO()
        Image.new("RGB", (64, 64)).save(buf, "PNG")
        self._json({"images": [base64.b64encode(buf.getvalue()).decode()]})

    def log_message(self, *a):
        pass


def test_real_progress_from_webui():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), SlowForge)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        b = StableDiffusionWebUIBackend(BackendSettings(sd_url=f"http://127.0.0.1:{srv.server_port}"))
        seen = []
        b.progress_cb = seen.append
        b.generate(build_prompt(FaceOptions(), seed=1))
        assert len(seen) >= 2 and seen == sorted(seen) and 0 < seen[0] < seen[-1] <= 1
    finally:
        srv.shutdown()
