#!/usr/bin/env python3
"""Send a precise CI-only click to the QEMU USB tablet via local QMP."""
import argparse
import json
from pathlib import Path
import socket
import time

def command(s, stream, payload):
    s.sendall((json.dumps(payload) + "\r\n").encode())
    while True:
        reply = stream.readline()
        if not reply:
            raise ConnectionError("QMP connection closed")
        result = json.loads(reply)
        if "error" in result:
            raise RuntimeError(str(result["error"]))
        if "return" in result:
            return result["return"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--socket", default="machines/cachyos-dailylive/skaldr-ci-qmp.sock")
    for key in ("x", "y", "width", "height"):
        p.add_argument("--" + key, required=True, type=int)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if min(a.width, a.height) < 2 or not (0 <= a.x < a.width and 0 <= a.y < a.height):
        p.error("Click must be inside the screenshot")
    ax = round(a.x * 32767 / (a.width - 1))
    ay = round(a.y * 32767 / (a.height - 1))
    events = [{"type":"abs","data":{"axis":"x","value":ax}},
              {"type":"abs","data":{"axis":"y","value":ay}}]
    if a.dry_run:
        print(json.dumps({"x": ax, "y": ay, "events": events}))
        return
    path = Path(a.socket)
    until = time.monotonic() + 20
    while not path.exists() and time.monotonic() < until:
        time.sleep(0.25)
    if not path.exists():
        raise FileNotFoundError(str(path))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(12)
        s.connect(str(path))
        with s.makefile("r", encoding="utf-8") as stream:
            banner = json.loads(stream.readline())
            if "QMP" not in banner:
                raise RuntimeError("Invalid QMP handshake")
            command(s, stream, {"execute": "qmp_capabilities"})
            command(s, stream, {"execute": "input-send-event", "arguments": {"events": events}})
            time.sleep(0.3)
            for pressed in (True, False):
                command(s, stream, {"execute":"input-send-event", "arguments":{
                    "events":[{"type":"btn","data":{"button":"left","down":pressed}}]}})
                time.sleep(0.15)
    print(f"QMP click at ({a.x},{a.y}); normalized ({ax},{ay})")

if __name__ == "__main__":
    main()
