#!/usr/bin/env python3
"""Minimal HTTP wrapper around decide_request (standard library only).

Run:
    python3 examples/serve_decision.py
    curl -s localhost:8092/decide -H 'content-type: application/json' \
         -d '{"text":"delete /tmp/report.txt"}'
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from gama_decision import decide_request


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if self.path != "/decide":
            self._json(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("content-length", 0) or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            text = str(payload.get("text", ""))
        except (ValueError, TypeError):
            self._json(400, {"ok": False, "error": "invalid json"})
            return
        if not text:
            self._json(400, {"ok": False, "error": "missing text"})
            return
        self._json(200, decide_request(text))


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8092), Handler).serve_forever()
