"""Drive the real Chrome (CDP port 9222) to log in to CVAT and capture canvases."""
import json
import time

import requests
import websocket

BASE = "http://localhost:9222"


def page_ws(url_part="localhost:8080"):
    tabs = requests.get(f"{BASE}/json/list", timeout=10).json()
    for t in tabs:
        if t.get("type") == "page" and url_part in t.get("url", ""):
            return t["webSocketDebuggerUrl"], t
    raise SystemExit("khong tim thay tab CVAT")


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(
            ws_url, timeout=60, max_size=200 * 1024 * 1024, suppress_origin=True
        )
        self.i = 0

    def send(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def eval(self, expr, await_promise=True):
        r = self.send(
            "Runtime.evaluate",
            expression=expr,
            awaitPromise=await_promise,
            returnByValue=True,
        )
        res = r.get("result", {})
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:500])
        return res.get("value")

    def close(self):
        self.ws.close()


def main():
    ws, tab = page_ws()
    print("tab:", tab["url"])
    cdp = Cdp(ws)
    try:
        cdp.eval("localStorage.getItem('lang')")
        print("title:", cdp.eval("document.title"))
        print("url:", cdp.eval("location.href"))
    finally:
        cdp.close()


if __name__ == "__main__":
    main()
