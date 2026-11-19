import socket
import sys
import textwrap
import time

import pytest

from fm27facegen.forge import ForgeManager, api_enabled, api_state, find_launcher


def test_find_launcher_and_api_flag(tmp_path):
    assert find_launcher(tmp_path) is None
    (tmp_path / "webui").mkdir()
    (tmp_path / "webui" / "webui-user.bat").write_text("@echo off\nset COMMANDLINE_ARGS=\ncall webui.bat\n")
    assert find_launcher(tmp_path) == tmp_path / "webui" / "webui-user.bat"
    assert api_enabled(tmp_path) is False
    (tmp_path / "webui" / "webui-user.bat").write_text("set COMMANDLINE_ARGS=--xformers --api\n")
    assert api_enabled(tmp_path) is True
    (tmp_path / "run.bat").write_text("call environment.bat\n")
    assert find_launcher(tmp_path) == tmp_path / "run.bat"  # One-Click-Paket bevorzugt


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="nachgebautes Forge als Shell-Skript")
def test_start_wait_and_stop_fake_forge(tmp_path):
    port = _free_port()
    server = tmp_path / "server.py"
    server.write_text(textwrap.dedent(f"""
        import time, json
        from http.server import BaseHTTPRequestHandler, HTTPServer
        time.sleep(2)  # Forge braucht etwas zum Starten
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                d = json.dumps({{"sd_model_checkpoint": "RealVisXL"}}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(d))); self.end_headers()
                self.wfile.write(d)
            def log_message(self, *a): pass
        HTTPServer(("127.0.0.1", {port}), H).serve_forever()
    """))
    (tmp_path / "webui.sh").write_text(f'echo "Forge startet"\nexec "{sys.executable}" "{server}"\n')
    url = f"http://127.0.0.1:{port}"
    fm = ForgeManager(tmp_path / "forge.log")
    assert api_state(url) == "down"
    fm.start(tmp_path)
    ticks = []
    assert fm.wait_ready(url, timeout=30, interval=0.5, on_tick=ticks.append) == "ready"
    assert ticks and fm.state == "ready" and "Forge startet" in (tmp_path / "forge.log").read_text()
    fm.stop()
    time.sleep(0.5)
    assert api_state(url) == "down"  # samt Unterprozess beendet


def test_stop_does_nothing_if_not_started_by_us(tmp_path):
    fm = ForgeManager(tmp_path / "forge.log")
    fm.stop()  # darf nicht abstürzen
    assert fm.state == "idle"


def test_update_notify_rules():
    from fm27facegen.update import parse_version, should_notify
    assert parse_version("v1.7.2") == (1, 7, 2)
    assert should_notify("1.7.0", "1.7.1")
    assert not should_notify("1.7.1", "1.7.1") and not should_notify("1.7.1", "1.7.0")
    # 1.7.1 ausgeblendet -> kein Hinweis für 1.7.1, aber wieder für 1.7.2
    assert not should_notify("1.7.0", "1.7.1", skipped="1.7.1")
    assert should_notify("1.7.0", "1.7.2", skipped="1.7.1")
    assert should_notify("1.7.0", "1.10.0")  # numerisch, nicht alphabetisch
    assert not should_notify("1.7.0", "kaputt")
