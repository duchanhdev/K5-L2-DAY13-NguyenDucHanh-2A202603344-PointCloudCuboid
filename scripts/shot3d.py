"""Chụp vùng khung 3D của CVAT bằng CDP (Chrome thật, cổng 9222)."""
import base64
import io
import sys
import time

from PIL import Image

from cdp import Cdp, page_ws


def grab(cdp, clip=None, path=None):
    params = {"format": "png", "captureBeyondViewport": False}
    if clip:
        params["clip"] = {**clip, "scale": clip.get("scale", 1)}
    res = cdp.send("Page.captureScreenshot", **params)
    raw = base64.b64decode(res["data"])
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if path:
        im.save(path)
    return im


def canvas_rects(cdp):
    return cdp.eval(
        "JSON.stringify(Array.from(document.querySelectorAll('canvas')).map(c=>{"
        "const r=c.getBoundingClientRect();"
        "return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}))"
    )


def main():
    ws, tab = page_ws()
    cdp = Cdp(ws)
    try:
        rects = json.loads(canvas_rects(cdp))
        print("rects:", rects)
        r = rects[0]
        im = grab(cdp, {"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"], "scale": 1},
                  r"work\shot\cdp_real3d.png")
        print("saved", im.size)
    finally:
        cdp.close()


if __name__ == "__main__":
    import json  # noqa: E402
    main()
