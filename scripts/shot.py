"""Tien ich chup man hinh that cua CVAT 3D (Windows).

Ly do phai chup man hinh that: CVAT ve point cloud bang WebGL voi
`preserveDrawingBuffer: false`, nen `Page.captureScreenshot` va
`canvas.toDataURL()` deu ra mau den. Anh cua cua so that tren man hinh
thi co duoc bui mau.

Quy uoc toa do:
  - CSS px (trong trang) -> px vat ly tren man hinh: `phys = css * dpr`
  - `dpr` lay tu `window.devicePixelRatio`.
  - Goc toa do man hinh cua cua so lay bang ClientToScreen (process phai
    DPI-aware, vi du chay voi `-X utf8` va goi SetProcessDpiAwareness truoc).
"""

import ctypes
import ctypes.wintypes as wt
import sys
import time

from PIL import ImageGrab

sys.path.insert(0, "scripts")

user32 = ctypes.windll.user32
try:  # phai dat TRUOC khi goi bat ky ham nao cua user32
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wt.LONG),
        ("top", wt.LONG),
        ("right", wt.LONG),
        ("bottom", wt.LONG),
    ]


def window_rects():
    """Danh sach (hwnd, tieu de) cua cac cua so dang thay."""
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


def find_cvat_window(pid=None):
    """Tim cua so Chrome dang mo CVAT; uu tien cua so cua process duoc chon."""
    cands = []
    for hwnd, title in window_rects():
        if "Computer Vision Annotation Tool" not in title:
            continue
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if pid is not None and p.value != pid:
            continue
        cands.append((hwnd, title, p.value))
    if not cands:
        raise SystemExit("khong tim thay cua so CVAT")
    return cands


def focus(hwnd):
    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.2)


def client_origin(hwnd):
    """Goc toa do va kich thuoc vung noi dung, tinh theo pixel vat ly."""
    r = RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    p = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(p))
    return p.x, p.y, r.right - r.left, r.bottom - r.top


def grab_screen():
    return ImageGrab.grab(all_screens=True)
