"""Chup anh CVAT that cho bai lab Day 13.

CVAT ve point cloud bang WebGL. Anh chup truc tiep tu he thong (WebGL/
`Page.captureScreenshot`) ra mau den, nen dung `gl.readPixels()` trong
mot khung hinh de doc dung buffer that cua khung 3D, roi dong goi thanh PNG.

Dieu khien CVAT qua CDP (Chrome that o cong 9222):
  - doi frame: ghi vao o `spinbutton` cua thanh cong cu
  - chon cuboid: bam vao dong trong bang Objects
  - xoay/pan/zoom goc nhin: keo chuot tren khung 3D (mouse wheel de zoom)
"""

import base64
import io
import json
import os
import sys
import time

sys.path.insert(0, "scripts")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from canvasread import _png  # noqa: E402
from cdp import Cdp, page_ws  # noqa: E402

OUT = os.path.join("report", "individual", "images")

# Toa do khung 3D trong trang (CSS px), lay lai dong de khong phu thuoc layout.
CANVAS3D = {"x": 52, "y": 104, "w": 863, "h": 452}


def canvas_rect(cdp, index=0):
    return json.loads(
        cdp.eval(
            "JSON.stringify((()=>{const c=document.querySelectorAll('canvas')[%d];"
            "const r=c.getBoundingClientRect();"
            "return {x:r.left,y:r.top,w:r.width,h:r.height};})())" % index
        )
    )


READ_PX = """
new Promise(res => {
  const c = document.querySelectorAll('canvas')[%d];
  if (!c) { res('null'); return; }
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const w = c.width, h = c.height;
      const buf = new Uint8Array(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, buf);
      let bin = ''; const CH = 8192;
      for (let i = 0; i < buf.length; i += CH) {
        bin += String.fromCharCode.apply(null, buf.subarray(i, i + CH));
      }
      res(JSON.stringify({w: w, h: h, b64: btoa(bin)}));
    });
  });
})
"""


def grab3d(cdp, index=0, boost=2.2):
    """Doc buffer that cua canvas WebGL va tra ve PIL Image."""
    res = cdp.eval(READ_PX % index)
    if not res or res == "null":
        return None
    d = json.loads(res)
    rgba = base64.b64decode(d["b64"])
    im = Image.open(io.BytesIO(_png(d["w"], d["h"], rgba))).convert("RGB")
    if boost and boost != 1.0:
        im = im.point(lambda v: min(255, int(v * boost)))
    return im


# ---------------------------------------------------------------- dieu khien


def _key(cdp, code, vk, mods=0):
    for t in ("rawKeyDown", "keyUp"):
        cdp.send(
            "Input.dispatchKeyEvent",
            type=t,
            code=code,
            key=code,
            windowsVirtualKeyCode=vk,
            nativeVirtualKeyCode=vk,
            modifiers=mods,
        )
    time.sleep(0.08)


def tilt(cdp, up=True, times=1):
    """shift+ArrowUp/Down: nghieng goc nhin (TILT)."""
    code = "ArrowUp" if up else "ArrowDown"
    for _ in range(times):
        _key(cdp, code, 38, mods=8)
        time.sleep(0.15)


def drag(cdp, x0, y0, x1, y1, steps=12):
    """Keo chuot tren khung 3D de xoay / day goc nhin."""
    cdp.send(
        "Input.dispatchMouseEvent",
        type="mousePressed",
        x=int(x0),
        y=int(y0),
        button="left",
        buttons=1,
        clickCount=1,
    )
    for i in range(1, steps + 1):
        cdp.send(
            "Input.dispatchMouseEvent",
            type="mouseMoved",
            x=int(x0 + (x1 - x0) * i / steps),
            y=int(y0 + (y1 - y0) * i / steps),
            button="left",
            buttons=1,
        )
        time.sleep(0.04)
    cdp.send(
        "Input.dispatchMouseEvent",
        type="mouseReleased",
        x=int(x1),
        y=int(y1),
        button="left",
        buttons=0,
        clickCount=1,
    )
    time.sleep(0.6)


def wheel(cdp, x, y, delta):
    cdp.send(
        "Input.dispatchMouseEvent",
        type="mouseWheel",
        x=int(x),
        y=int(y),
        deltaX=0,
        deltaY=delta,
        pointerType="mouse",
    )
    time.sleep(0.25)


def double_click(cdp, x, y):
    for _ in range(2):
        cdp.send(
            "Input.dispatchMouseEvent",
            type="mousePressed",
            x=int(x),
            y=int(y),
            button="left",
            clickCount=1,
        )
        cdp.send(
            "Input.dispatchMouseEvent",
            type="mouseReleased",
            x=int(x),
            y=int(y),
            button="left",
            clickCount=1,
        )
        time.sleep(0.06)
    time.sleep(0.5)


def set_frame(cdp, index):
    cdp.eval(
        """(()=>{const i=document.querySelector('input[role=spinbutton][aria-valuemax]');
        if(!i) return 'none';
        const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
        set.call(i,'%d');
        i.dispatchEvent(new Event('input',{bubbles:true}));
        i.dispatchEvent(new Event('change',{bubbles:true}));
        i.blur();
        return i.value;})()"""
        % index
    )
    time.sleep(3.0)


def select_object(cdp, idx):
    """Chon cuboid theo thu tu dong trong bang Objects (1-based)."""
    cdp.eval(
        """(()=>{const o=document.querySelectorAll('[role=option]')[%d];
        if(o){o.click();return 'ok';} return 'none';})()"""
        % (idx - 1)
    )
    time.sleep(1.5)


def objects_text(cdp):
    return cdp.eval(
        "JSON.stringify(Array.from(document.querySelectorAll('[role=option]')).map(o=>o.textContent))"
    )


# ---------------------------------------------------------------- ghi anh


def save(im, name):
    path = os.path.join(OUT, name)
    im.save(path)
    print("  ->", path, im.size)
    return path


def annotate_top(im, note=None):
    """Ve moc 'PHIA TRUOC', '+x', '+y' tren anh nhin tu tren xuong."""
    im = im.copy()
    d = ImageDraw.Draw(im)
    w, h = im.size
    try:
        f = ImageFont.truetype("arialbd.ttf", max(16, h // 22))
    except Exception:
        f = ImageFont.load_default()

    # Goc toa do: theo bao cao, nhin tu tren xuong: phia truoc o tren,
    # +x sang trai, +y xuong duoi.
    cx, cy = w // 2, h // 2
    r = min(w, h) // 4

    d.text((cx - 70, cy - r - 34), "PHIA TRUOC (-y)", fill=(255, 235, 0), font=f)
    d.line([(cx, cy - r - 14), (cx, cy - r - 44)], fill=(255, 235, 0), width=4)
    d.polygon(
        [(cx, cy - r - 46), (cx - 12, cy - r - 30), (cx + 12, cy - r - 30)],
        fill=(255, 235, 0),
    )

    d.text((cx - r - 118, cy + 12), "+x", fill=(0, 255, 120), font=f)
    d.line([(cx - r - 20, cy + 24), (cx - r - 96, cy + 24)], fill=(0, 255, 120), width=4)
    d.polygon(
        [(cx - r - 100, cy + 24), (cx - r - 82, cy + 12), (cx - r - 82, cy + 36)],
        fill=(0, 255, 120),
    )

    d.text((cx + r + 14, cy + 12), "+y", fill=(120, 180, 255), font=f)
    d.line([(cx + r + 18, cy + 24), (cx + r + 62, cy + 24)], fill=(120, 180, 255), width=4)
    d.polygon(
        [(cx + r + 66, cy + 24), (cx + r + 48, cy + 12), (cx + r + 48, cy + 36)],
        fill=(120, 180, 255),
    )

    d.ellipse(
        [cx - 9, cy - 9, cx + 9, cy + 9], outline=(255, 255, 255), width=3
    )
    if note:
        d.text((12, 10), note, fill=(255, 255, 255), font=f)
    return im
