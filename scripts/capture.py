"""Chup anh that cua CVAT 3D bang cach chup man hinh that.

CVAT ve point cloud bang WebGL voi `preserveDrawingBuffer: false` nen
`Page.captureScreenshot` / `canvas.toDataURL()` deu ra mau den. Chi chup
duoc cua so that tren man hinh (PIL.ImageGrab).

Toa do: `phys = offset + css * dpr`, trong do `offset` do bang thuc do
(vi tri cua so tren man hinh) duoc do lai bang mot marker mau tim tinh
mot lan truoc khi chup.
"""

import ctypes
import ctypes.wintypes as wt
import sys
import time

from PIL import ImageGrab

sys.path.insert(0, "scripts")
from cdp import Cdp  # noqa: E402

user32 = ctypes.windll.user32

VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002


def focus(hwnd):
    """Dua cua so len truoc; phai 'alt' trick vi SetForegroundWindow bi chan."""
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    user32.ShowWindow(hwnd, 3)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)


MARKER = """(() => {
  let d = document.getElementById('__cal');
  if (!d) { d = document.createElement('div'); d.id = '__cal'; document.body.appendChild(d); }
  d.style.cssText = 'position:fixed;left:0px;top:0px;width:8px;height:8px;' +
    'background:rgb(255,0,255);z-index:2147483647;pointer-events:none;';
  return JSON.stringify({dpr: window.devicePixelRatio});
})()"""

CLEAR = """(() => { const d = document.getElementById('__cal'); if (d) d.remove(); return 'ok'; })()"""


def calibrate(cdp, hwnd):
    """Do mapping toa do CSS -> pixel vat ly bang marker 8x8 o goc trang.

    Marker duoc dat bang `position: fixed` o toa do CSS (0,0) cua trang, nen
    pixel vat ly cua no cho biet goc dich cua khung nhin theo CSS.
    """
    focus(hwnd)
    cdp.send("Page.bringToFront")
    time.sleep(0.8)
    import json

    info = json.loads(cdp.eval(MARKER))
    time.sleep(0.8)
    im = ImageGrab.grab(all_screens=True).convert("RGB")
    px = im.load()
    xs, ys = [], []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]
            if r > 190 and b > 190 and g < 70:
                xs.append(x)
                ys.append(y)
    cdp.eval(CLEAR)
    if not xs:
        raise SystemExit("khong tim thay marker khi do toa do")
    dpr = info["dpr"]
    return {
        "off_x": min(xs),
        "off_y": min(ys),
        "dpr": dpr,
        "marker": (min(xs), min(ys), max(xs), max(ys)),
    }


def css_to_phys(cal, x, y, w, h):
    d = cal["dpr"]
    ox, oy = cal["off_x"], cal["off_y"]
    return (
        int(round(ox + x * d)),
        int(round(oy + y * d)),
        int(round(w * d)),
        int(round(h * d)),
    )


def shot_css(cdp, cal, index=0, path=None, pad=0, rect=None):
    """Chup vung canvas theo toa do CSS cua trang."""
    if rect is None:
        import json

        rect = json.loads(
            cdp.eval(
                "JSON.stringify((()=>{const c=document.querySelectorAll('canvas')[%d];"
                "const r=c.getBoundingClientRect();"
                "return {x:r.left,y:r.top,w:r.width,h:r.height};})())" % index
            )
        )
    x, y, w, h = css_to_phys(
        cal, rect["x"] - pad, rect["y"] - pad, rect["w"] + 2 * pad, rect["h"] + 2 * pad
    )
    im = ImageGrab.grab(all_screens=True).crop((x, y, x + w, y + h))
    if path:
        im.save(path)
    return im


def shot_screen_rect(cdp, cal, x, y, w, h, path=None):
    """Chup mot vung toa do CSS bat ky (khong phai canvas)."""
    px_, py_, pw, ph = css_to_phys(cal, x, y, w, h)
    im = ImageGrab.grab(all_screens=True).crop((px_, py_, px_ + pw, py_ + ph))
    if path:
        im.save(path)
    return im
