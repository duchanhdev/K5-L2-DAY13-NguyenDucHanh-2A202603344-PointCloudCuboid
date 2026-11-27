"""Driver: dieu khien CVAT 3D (Chrome that qua CDP 9222) va chup anh bang ImageGrab.

Vi sao dung ImageGrab chu khong dung Page.captureScreenshot:
CVAT ve point cloud bang WebGL; Chrome compositor khong dua lop WebGL vao
Page.captureScreenshot (anh ra den), nhung cua so that van hien day du.
ImageGrab chup man hinh that nen thay point cloud.
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys
import time

from PIL import Image, ImageGrab

sys.path.insert(0, "scripts")
from cdp import Cdp, page_ws  # noqa: E402

user32 = ctypes.windll.user32

KEYS = {
    "TILT_UP": ("ArrowUp", 8),
    "TILT_DOWN": ("ArrowDown", 8),
    "ROTATE_LEFT": ("ArrowLeft", 8),
    "ROTATE_RIGHT": ("ArrowRight", 8),
    "MOVE_UP": ("u", 1),
    "MOVE_DOWN": ("o", 1),
    "MOVE_LEFT": ("j", 1),
    "MOVE_RIGHT": ("l", 1),
    "ZOOM_IN": ("i", 1),
    "ZOOM_OUT": ("k", 1),
}


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wt.LONG),
        ("top", wt.LONG),
        ("right", wt.LONG),
        ("bottom", wt.LONG),
    ]


def _enum_windows():
    out = []
    EnumProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        out.append((hwnd, buf.value))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return out


def find_chrome_hwnd():
    for hwnd, title in _enum_windows():
        if "Computer Vision Annotation Tool" in title:
            return hwnd
    return None


def focus_chrome():
    hwnd = find_chrome_hwnd()
    if hwnd is None:
        raise SystemExit("khong tim thay cua so Chrome CVAT")
    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)


def client_origin(hwnd):
    """Goc toa do cua vung noi dung trong cua so theo pixel man hinh."""
    r = RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    p = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(p))
    return p.x, p.y, r.right - r.left, r.bottom - r.top


def key(cdp, code, mods=0, vk=0):
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
    time.sleep(0.12)


def action(cdp, name, times=1, pause=0.2):
    code, mods = KEYS[name]
    vk = ord(code.upper()) if len(code) == 1 else 0
    for _ in range(times):
        key(cdp, code, mods, vk)
        time.sleep(pause)


def canvas_rects(cdp):
    return json.loads(
        cdp.eval(
            "JSON.stringify(Array.from(document.querySelectorAll('canvas')).map(c=>{"
            "const r=c.getBoundingClientRect();"
            "return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}))"
        )
    )


def viewport(cdp):
    return json.loads(
        cdp.eval(
            "JSON.stringify({w:window.innerWidth,h:window.innerHeight,"
            "dpr:window.devicePixelRatio})"
        )
    )


def screen_scale():
    """Ti le giua pixel thuc cua man hinh va toa do logic cua Windows."""
    logical_w = user32.GetSystemMetrics(0)
    phys_w = ImageGrab.grab(all_screens=True).size[0]
    return phys_w / logical_w


def shot_region(cdp, index=0, path=None, pad=0, hwnd=None):
    """Chup vung canvas theo toa do CSS, chuyen sang pixel man hinh that."""
    hwnd = hwnd or find_chrome_hwnd()
    ox, oy, cw, ch = client_origin(hwnd)
    k = screen_scale()
    r = canvas_rects(cdp)[index]
    box = (
        int((ox + (r["x"] - pad)) * k),
        int((oy + (r["y"] - pad)) * k),
        int((ox + (r["x"] + r["w"] + pad)) * k),
        int((oy + (r["y"] + r["h"] + pad)) * k),
    )
    im = ImageGrab.grab(all_screens=True).crop(box)
    if path:
        im.save(path)
    return im


def shot_page(path=None, hwnd=None):
    hwnd = hwnd or find_chrome_hwnd()
    ox, oy, cw, ch = client_origin(hwnd)
    k = screen_scale()
    im = ImageGrab.grab(all_screens=True).crop(
        (int(ox * k), int(oy * k), int((ox + cw) * k), int((oy + ch) * k))
    )
    if path:
        im.save(path)
    return im


def set_frame(cdp, index):
    cdp.eval(
        """(()=>{const i=document.querySelector('input[role=spinbutton][aria-valuemax]');
        if(!i) return 'none';
        const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
        set.call(i, '%d');
        i.dispatchEvent(new Event('input',{bubbles:true}));
        i.dispatchEvent(new Event('change',{bubbles:true}));
        i.blur();
        return i.value;})()"""
        % index
    )
    time.sleep(2.5)


def select_object(cdp, idx):
    """Chon cuboid theo so thu tu trong bang Objects (1-based)."""
    cdp.eval(
        """(()=>{const o=document.querySelectorAll('[role=option]')[%d];
        if(o){o.click();return 'ok'}return 'none'})()"""
        % (idx - 1)
    )
    time.sleep(1.2)


def double_click_3d(cdp, index=0, fx=0.5, fy=0.5):
    """Nhay doi trong khung 3D (dung de reset goc nhin)."""
    r = canvas_rects(cdp)[index]
    cx = r["x"] + int(r["w"] * fx)
    cy = r["y"] + int(r["h"] * fy)
    for _ in range(2):
        cdp.send(
            "Input.dispatchMouseEvent",
            type="mousePressed",
            x=cx,
            y=cy,
            button="left",
            clickCount=1,
        )
        cdp.send(
            "Input.dispatchMouseEvent",
            type="mouseReleased",
            x=cx,
            y=cy,
            button="left",
            clickCount=1,
        )
        time.sleep(0.08)
    time.sleep(1.2)
