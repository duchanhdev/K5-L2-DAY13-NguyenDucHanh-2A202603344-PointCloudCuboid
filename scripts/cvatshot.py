"""Điều khiển CVAT 3D qua CDP (Chrome thật cổng 9222) và chụp ảnh bằng ImageGrab."""
import json
import subprocess
import sys
import time

from PIL import Image, ImageGrab

sys.path.insert(0, "scripts")
from cdp import Cdp, page_ws  # noqa: E402

DPR = 1.25  # devicePixelRatio cua may


def find_window(title_part="Computer Vision Annotation Tool"):
    """Tra ve hwnd cua cua so Chrome dang hien CVAT."""
    ps = r"""
Add-Type @"
using System;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;
public class WF{
 [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb,IntPtr l);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetWindowTextW(IntPtr h,StringBuilder s,int n);
 [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h,out R r);
 [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h,int c);
 public struct R{public int L,T,Ri,B;}
 public delegate bool EnumWindowsProc(IntPtr h,IntPtr l);
 public static List<string> List(){var a=new List<string>();EnumWindows((h,l)=>{if(IsWindowVisible(h)){var sb=new StringBuilder(300);GetWindowTextW(h,sb,300);var t=sb.ToString();if(t.Trim().Length>0){R r;GetWindowRect(h,out r);a.Add(h.ToInt64()+"|"+t+"|"+r.L+","+r.T+","+(r.Ri-r.L)+"x"+(r.B-r.T));}}return true;},IntPtr.Zero);return a;}
 public static void Focus(long hw){var h=new IntPtr(hw);ShowWindow(h,3);SetForegroundWindow(h);}
}
"@
[WF]::List()
"""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60
    ).stdout
    best = None
    for line in out.splitlines():
        if title_part in line:
            hwnd, title, rect = line.split("|", 2)
            x, y, wh = rect.split(",")
            w, h = wh.split("x")
            if best is None or int(w) * int(h) > best[3] * best[4]:
                best = (int(hwnd), title, int(x), int(y), int(w), int(h))
    return best


def focus_chrome():
    w = find_window()
    if not w:
        raise SystemExit("khong tim thay cua so Chrome CVAT")
    hwnd, title, x, y, ww, hh = w
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Add-Type -Namespace W -Name F -MemberDefinition '[DllImport(\"user32.dll\")] "
            f"public static extern bool SetForegroundWindow(IntPtr h);"
            f"[DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr h,int c);';"
            f"[W.F]::ShowWindow([IntPtr]{hwnd},3);[W.F]::SetForegroundWindow([IntPtr]{hwnd})",
        ],
        capture_output=True,
        timeout=30,
    )
    return w


def grab_screen():
    return ImageGrab.grab(all_screens=True)


def canvas_rects(cdp):
    return json.loads(
        cdp.eval(
            "JSON.stringify(Array.from(document.querySelectorAll('canvas')).map(c=>{"
            "const r=c.getBoundingClientRect();"
            "return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}))"
        )
    )


def grab_canvas(cdp, index=0, path=None, pad=0):
    """Chup vung canvas theo toa do hien thi tren man hinh (dung cho WebGL)."""
    r = canvas_rects(cdp)[index]
    x0 = int((r["x"] - pad) * DPR)
    y0 = int((r["y"] - pad) * DPR)
    x1 = int((r["x"] + r["w"] + pad) * DPR)
    y1 = int((r["y"] + r["h"] + pad) * DPR)
    im = grab_screen().crop((x0, y0, x1, y1))
    if path:
        im.save(path)
    return im


def grab_page(cdp, path=None):
    im = grab_screen()
    if path:
        im.save(path)
    return im
