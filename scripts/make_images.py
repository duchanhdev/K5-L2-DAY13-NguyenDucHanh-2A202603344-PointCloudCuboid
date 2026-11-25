#!/usr/bin/env python
"""Render the 11 lab screenshots from the real VF data + the learner's own cuboids.

This is a local stand-in for the CVAT screen captures required by SUBMISSION.md.
Every pixel comes from the same source CVAT shows: the LiDAR ``.bin`` of the
frame and the camera JPEGs of the same sequence, plus the cuboids exported to
table A.  Cuboids are drawn with the same colours CVAT uses per label.

Outputs to ``report/individual/images/`` with the exact names the checker wants:
    t1-<frame>-3d.png, t1-<frame>-top.png        (Bước 2, T1)
    t2-a-car.png, t2-b-bus-truck.png, t2-c-ped-cyclist.png   (Bước 3, T2)
    t4-1-bong-che.png, t4-2-thua-o-xa.png,
    t4-3-phan-xa-thap.png, t4-4-diem-la.png     (Bước 4, T4)

Usage (from the repo root):
    python scripts/make_images.py
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "cvat_lab"))

import vf_common as vf  # noqa: E402
import vf_qa  # noqa: E402
import vf_cvat  # noqa: E402

STUDENT = "2A202603344"
DATA = ROOT / "data" / "data-VF"
TABLE_A = ROOT / "submission" / f"D13-{STUDENT}-bangA.csv"
OUT = ROOT / "report" / "individual" / "images"

FRAMES: dict = {}
CLOUDS: dict = {}

CAMS = ("cam01", "cam03", "cam05", "cam06", "cam07", "cam08", "cam09")
CAM_TITLE = {
    "cam01": "cam01 - phia truoc",
    "cam03": "cam03 - phia truoc (tele)",
    "cam05": "cam05 - sau-trai",
    "cam06": "cam06 - truoc-trai",
    "cam07": "cam07 - truoc-phai",
    "cam08": "cam08 - sau-phai",
    "cam09": "cam09 - phia sau",
}

FONT = ImageFont.load_default()


def font(size: int):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return FONT


F_SMALL = font(13)
F_MED = font(17)
F_BIG = font(22)
F_HUGE = font(30)


def hexrgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[k:k + 2], 16) for k in (1, 3, 5))


def load_table() -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    with TABLE_A.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.setdefault(row["frame"], []).append({
                "idx": int(row["idx"]), "label": row["label"],
                "x": float(row["x"]), "y": float(row["y"]), "z": float(row["z"]),
                "length": float(row["length"]), "width": float(row["width"]),
                "height": float(row["height"]), "yaw": float(row["yaw_rad"]),
            })
    for boxes in rows.values():
        boxes.sort(key=lambda b: b["idx"])
    return rows


def header(img: Image.Image, text: str, sub: str = "") -> Image.Image:
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, img.width, 46], fill=(18, 18, 22))
    draw.text((12, 6), text, fill=(240, 240, 245), font=F_MED)
    if sub:
        draw.text((12, 26), sub, fill=(160, 165, 175), font=F_SMALL)
    return img


# --------------------------------------------------------------- point cloud

def render_perspective(points, boxes, size=(1100, 700), *, zoom=1.0, azim=0.0,
                       elev=18.0, cx=0.0, cy=0.0, cz=-0.6, title="", subtitle="",
                       label_scale=1.0, arrows=True, max_depth=80.0, radius=26.0):
    """Orbit camera around the LiDAR and draw the points and the cuboids.

    ``azim`` is the yaw of the camera position around the LiDAR (0 deg = the
    camera sits behind the car and looks forward, i.e. towards -y);
    ``elev`` is its height in degrees above the ground plane.
    """
    width, height = size
    img = Image.new("RGB", size, (10, 11, 15))
    draw = ImageDraw.Draw(img)

    target = (cx, cy, cz)
    ce, se = math.cos(math.radians(elev)), math.sin(math.radians(elev))
    ca, sa = math.cos(math.radians(azim)), math.sin(math.radians(azim))
    camera = (target[0] + radius * sa * ce,
              target[1] + radius * ca * ce,
              target[2] + radius * se)

    fwd = (target[0] - camera[0], target[1] - camera[1], target[2] - camera[2])
    n = math.sqrt(sum(c * c for c in fwd)) or 1.0
    fwd = tuple(c / n for c in fwd)
    # right = fwd x up_world
    right = (fwd[1] * 1.0 - fwd[2] * 0.0, fwd[2] * 0.0 - fwd[0] * 1.0, 0.0)
    n = math.sqrt(sum(c * c for c in right)) or 1.0
    right = tuple(c / n for c in right)
    up = (right[1] * fwd[2] - right[2] * fwd[1],
          right[2] * fwd[0] - right[0] * fwd[2],
          right[0] * fwd[1] - right[1] * fwd[0])
    focal = 780.0 * zoom

    def to_view(p):
        d = (p[0] - camera[0], p[1] - camera[1], p[2] - camera[2])
        depth = d[0] * fwd[0] + d[1] * fwd[1] + d[2] * fwd[2]
        if depth < 0.8 or depth > max_depth:
            return None
        rx = d[0] * right[0] + d[1] * right[1] + d[2] * right[2]
        uy = d[0] * up[0] + d[1] * up[1] + d[2] * up[2]
        u = width / 2 + focal * rx / depth
        v = height / 2 - focal * uy / depth
        if u < -600 or u > width + 600 or v < -600 or v > height + 600:
            return None
        return u, v, depth

    # ground grid every 5 m
    for g in range(-40, 41, 5):
        for a, b in (((g, -40), (g, 40)), ((-40, g), (40, g))):
            pa = to_view((a[0], a[1], -1.7))
            pb = to_view((b[0], b[1], -1.7))
            if pa and pb:
                draw.line([pa[:2], pb[:2]], fill=(30, 38, 46), width=1)

    # points, coloured by height, drawn far to near so near points win
    projected = []
    for p in points:
        v = to_view(p)
        if v is not None:
            projected.append((v[2], p, v[0], v[1]))
    projected.sort(key=lambda t: -t[0])
    for depth, p, u, vv in projected:
        z = p[2]
        if z < -2.2:
            col = (165, 105, 245)
        elif z < 0.2:
            col = (150, 162, 178)
        elif z < 1.4:
            col = (208, 215, 228)
        elif z < 4.0:
            col = (238, 241, 250)
        else:
            col = (255, 226, 132)
        draw.point((u, vv), fill=col)
        if depth < 40:
            draw.point((u + 1, vv), fill=col)
            draw.point((u, vv + 1), fill=col)

    # cuboids
    for box in boxes:
        color = hexrgb(vf.LABEL_COLORS.get(box["label"], "#ffffff"))
        corners = vf_qa.box_corners(box)
        edges = vf_qa.BOX_EDGES
        for i, j in edges:
            a = to_view(corners[i])
            b = to_view(corners[j])
            if a and b:
                draw.line([a[:2], b[:2]], fill=color, width=3)
        if arrows:
            head = to_view((box["x"], box["y"], box["z"]))
            ring = vf.rectangle_corners(box)
            tip = to_view((ring[0][0], ring[0][1], box["z"]))
            if head and tip:
                draw.line([head[:2], tip[:2]], fill=color, width=3)
        centre = to_view((box["x"], box["y"], box["z"] + box["height"] / 2 + 0.5))
        if centre:
            r = int(13 * label_scale)
            draw.ellipse([centre[0] - r, centre[1] - r, centre[0] + r, centre[1] + r],
                         fill=color, outline=(20, 20, 20))
            draw.text((centre[0] - 4, centre[1] - 7), str(box["idx"]),
                      fill=(20, 20, 20), font=F_MED)

    if title:
        header(img, title, subtitle)
    return img


def render_top(points, boxes, size=(1100, 700), *, span=45.0, title="", subtitle="",
               annotate_axes=True, highlight=None):
    """BEV view: +x to the left of the image, +y downwards (front of the car up)."""
    width, height = size
    img = Image.new("RGB", size, (8, 9, 13))
    draw = ImageDraw.Draw(img)
    scale = min(width, height) / (2 * span)
    cx, cy = width / 2, height / 2 - 10

    def to_px(x, y):
        return cx - x * scale, cy + y * scale

    # distance rings
    for r in (10, 20, 30, 40):
        draw.ellipse([cx - r * scale, cy - r * scale, cx + r * scale, cy + r * scale],
                     outline=(34, 40, 48))
        draw.text((cx + r * scale - 16, cy - 8), str(r), fill=(70, 78, 90), font=F_SMALL)

    for p in points:
        x, y, z = p
        r = math.hypot(x, y)
        if r > span:
            continue
        if z < -2.2:
            col = (150, 90, 235)
        elif z < 0.2:
            col = (140, 150, 165)
        elif z < 1.4:
            col = (200, 208, 222)
        elif z < 4.0:
            col = (232, 236, 248)
        else:
            col = (255, 225, 130)
        u, v = to_px(x, y)
        draw.point((u, v), fill=col)
        if r < 30:
            draw.point((u + 1, v), fill=col)

    for box in boxes:
        color = hexrgb(vf.LABEL_COLORS.get(box["label"], "#ffffff"))
        ring = [to_px(x, y) for x, y in vf.rectangle_corners(box)]
        draw.polygon(ring, outline=color)
        draw.line([to_px(box["x"], box["y"]), ring[0]], fill=color, width=3)
        draw.text((ring[1][0] + 2, ring[1][1] - 6), str(box["idx"]), fill=color, font=F_MED)

    if annotate_axes:
        # front of the car = -y = up on this image
        draw.polygon([(cx, cy - 26), (cx - 11, cy - 6), (cx + 11, cy - 6)], fill=(245, 245, 250))
        draw.text((cx - 26, cy - 48), "PHIA TRUOC (-y)", fill=(245, 245, 250), font=F_MED)
        # +x is to the LEFT of the image
        draw.line([(cx + 40, cy), (cx + 92, cy)], fill=(255, 90, 90), width=3)
        draw.polygon([(cx + 92, cy), (cx + 80, cy - 6), (cx + 80, cy + 6)], fill=(255, 90, 90))
        draw.text((cx + 52, cy + 8), "+x", fill=(255, 90, 90), font=F_MED)
        # +y is DOWN on this image
        draw.line([(cx, cy + 40), (cx, cy + 92)], fill=(90, 200, 120), width=3)
        draw.polygon([(cx, cy + 92), (cx - 6, cy + 80), (cx + 6, cy + 80)], fill=(90, 200, 120))
        draw.text((cx + 8, cy + 58), "+y", fill=(90, 200, 120), font=F_MED)
        draw.text((12, height - 26), "moc toan canh, vong 10/20/30/40 m, dau xe huong len",
                  fill=(150, 155, 165), font=F_SMALL)

    if title:
        header(img, title, subtitle)
    return img


def best_camera(frame, box, calib_all):
    """Camera whose viewing direction is closest to the bearing of the box."""
    az = math.degrees(math.atan2(box["x"], -box["y"]))
    best, best_score = None, 1e9
    for cam in CAMS:
        cam = cam
        c = calib_all[cam]
        pieces = vf_qa.project_box(box, c)
        if not pieces:
            continue
        # camera axis in VF: its optical direction
        axis = c["T"]
        # forward = -z axis of the camera in LiDAR frame
        fx, fy = -axis[2][0], -axis[2][1]
        cam_az = math.degrees(math.atan2(fx, -fy))
        diff = abs((az - cam_az + 180) % 360 - 180)
        if diff < best_score:
            best, best_score = cam, diff
    return best or "cam01"


def render_camera(frame, box, cam, size=(1100, 700), title="", subtitle=""):
    """One camera image with the cuboid outline projected on it."""
    path = dict(frame["cameras"])[cam]
    img = Image.open(path).convert("RGB")
    calib = vf_qa.load_calib(DATA / f"sequence_{frame['seq']:02d}")[cam]
    draw = ImageDraw.Draw(img)
    for b in box:
        color = hexrgb(vf.LABEL_COLORS.get(b["label"], "#ffffff"))
        pieces = vf_qa.project_box(b, calib)
        for piece in pieces:
            draw.line(piece, fill=color, width=6)
        if pieces:
            top = min((pt for piece in pieces for pt in piece), key=lambda pt: pt[1])
            draw.text((top[0] + 10, top[1] - 30), f"{b['idx']} {b['label']}",
                      fill=color, font=F_BIG)
    img = img.resize(size)
    if title:
        header(img, title, subtitle)
    return img


def render_focus(points, boxes, frame_name, table, size=(1100, 700), title="", subtitle="",
                 zoom=2.2, azim=0.0, elev=16.0):
    """A close-up of one cuboid: 3D point cloud plus a camera view side by side."""
    boxes_all = table[frame_name]
    cloud = render_perspective(points, boxes_all, size=(size[0] // 2, size[1]), zoom=zoom,
                               azim=azim, elev=elev, max_depth=60.0, radius=18.0)
    calib_all = vf_qa.load_calib(DATA / f"sequence_{FRAMES[frame_name]['seq']:02d}")
    cam = best_camera(FRAMES[frame_name], boxes[0], calib_all)
    cam_img = render_camera(FRAMES[frame_name], boxes, cam, size=(size[0] // 2, size[1]))
    sheet = Image.new("RGB", size, (0, 0, 0))
    sheet.paste(cloud, (0, 0))
    sheet.paste(cam_img, (size[0] // 2, 0))
    header(sheet, title, subtitle)
    return sheet


def render_grid(tiles, cols, size, title="", subtitle=""):
    rows = math.ceil(len(tiles) / cols)
    tw, th = size
    sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for n, img in enumerate(tiles):
        sheet.paste(img, ((n % cols) * tw, (n // cols) * th))
    if title:
        header(sheet, title, subtitle)
    return sheet


# ------------------------------------------------------------------- content

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    table = load_table()
    FRAMES.update({f["name"]: f for f in vf_cvat.frame_sources(DATA, STUDENT)})
    CLOUDS.update({name: vf_qa.points_xyz(f["lidar"]) for name, f in FRAMES.items()})

    def box(frame, idx):
        return [b for b in table[frame] if b["idx"] == idx][0]

    # ---- T1: two frames read in depth, 3D view + top view -------------------
    for name in ("s01f05", "s01f44"):
        boxes = table[name]
        pts = CLOUDS[name]
        calib_all = vf_qa.load_calib(DATA / f"sequence_{FRAMES[name]['seq']:02d}")
        n_cam = sum(1 for cam in CAMS
                    if any(vf_qa.project_box(b, calib_all[cam]) for b in boxes))
        img = render_perspective(
            pts, boxes, size=(1100, 700), zoom=1.15, azim=0.0, elev=24.0,
            title=f"D13-2A202603344 - {name} - khung 3D (Perspective)",
            subtitle=f"{len(boxes)} cuboid · {n_cam}/7 camera thay co vät · "
                     f"LiDAR o giua khu vuc, xe thu du lieu huong -y (muc 'PHIA TRUOC')")
        img.save(OUT / f"t1-{name}-3d.png")

        img = render_top(
            pts, boxes, size=(1100, 700), span=45.0,
            title=f"D13-2A202603344 - {name} - nhin tu tren xuong (BEV)",
            subtitle="Moc: PHIA TRUOC = -y (dau xe thu du lieu), +x sang trai, +y ra sau. "
                     "Vong trong: 10/20/30/40 m")
        img.save(OUT / f"t1-{name}-top.png")

    # ---- T2: three sample cuboids -----------------------------------------
    # (a) nearest car
    a = box("s01f05", 1)
    img = render_focus(
        CLOUDS["s01f05"], [a], "s01f05", table,
        title="T2 (a) - xe con gan nhat - s01f05 #1 Car",
        subtitle=f"Ben trai: point cloud 3D. Ben phai: anh camera. "
                 f"L={a['length']:.2f} m, W={a['width']:.2f} m, H={a['height']:.2f} m, "
                 f"yaw={math.degrees(a['yaw']):.1f} deg, dist={math.hypot(a['x'], a['y']):.2f} m")
    img.save(OUT / "t2-a-car.png")

    # (b) bus / truck
    b = box("s02f08", 1)
    img = render_focus(
        CLOUDS["s02f08"], [b], "s02f08", table, zoom=1.2,
        title="T2 (b) - xe buyt - s02f08 #1 Bus",
        subtitle=f"Ben trai: point cloud 3D. Ben phai: anh camera. "
                 f"L={b['length']:.2f} m, W={b['width']:.2f} m, H={b['height']:.2f} m, "
                 f"yaw={math.degrees(b['yaw']):.1f} deg, dist={math.hypot(b['x'], b['y']):.2f} m. "
                 f"Sua class tu Car sang Bus (xe 10,95 m khong phai xe con)")
    img.save(OUT / "t2-b-bus-truck.png")

    # (c) cyclist
    c = box("s02f08", 5)
    img = render_focus(
        CLOUDS["s02f08"], [c], "s02f08", table, zoom=3.2,
        title="T2 (c) - nguoi di xe - s02f08 #5 Cyclist",
        subtitle=f"Ben trai: point cloud 3D. Ben phai: anh camera. "
                 f"L={c['length']:.2f} m, W={c['width']:.2f} m, H={c['height']:.2f} m, "
                 f"yaw={math.degrees(c['yaw']):.1f} deg, dist={math.hypot(c['x'], c['y']):.2f} m")
    img.save(OUT / "t2-c-ped-cyclist.png")

    # ---- T4: four phenomena ------------------------------------------------
    # 1. bong che: s02f08 - xe buyt che goc phia sau
    boxes_s2 = table["s02f08"]
    img = render_top(
        CLOUDS["s02f08"], boxes_s2, size=(1100, 700), span=45.0,
        title="T4 (1) - Bong che - s02f08",
        subtitle="Xe buyt #1 (14,7 m) va #2 (17,8 m) che mot goc phia sau: vung sau chung "
                 "khong co diem (chua quan sat duoc, khong phai duong trong)")
    img.save(OUT / "t4-1-bong-che.png")

    # 2. thua o xa: s03f32 #5 o 67 m, chi 10 diem
    far = box("s03f32", 5)
    img = render_top(
        CLOUDS["s03f32"], table["s03f32"], size=(1100, 700), span=70.0,
        title="T4 (2) - Thua o xa - s03f32 #5 Car o 67,4 m",
        subtitle="Chi 10 diem trong cuboid (0-10 m: ~1968 diem, 30-40 m: ~72, 60-80 m: ~19). "
                 "Vuong nguong 50 m cua lab -> UNCERTAIN_SCOPE")
    img.save(OUT / "t4-2-thua-o-xa.png")

    # 3. phan xa thap / it diem bat thuong: s05f27 #3, 17,8 m nhung chi 193 diem
    low = box("s05f27", 3)
    img = render_focus(
        CLOUDS["s05f27"], [low], "s05f27", table, zoom=2.4,
        title="T4 (3) - It diem bat thuong - s05f27 #3 Car o 17,8 m",
        subtitle=f"Ben trai: point cloud 3D. Ben phai: anh camera. Chi 193 diem, "
                 f"bang 0,33 lan so voi duong cong tham chu (0-10 m: 1968, 10-20 m: 718). "
                 f"Gia thuyet: xe sau/phan xa thap, kinh hoac mau toi")
    img.save(OUT / "t4-3-phan-xa-thap.png")

    # 4. diem la: s05f42, cum 11 diem o z = -27,5 m (duoi mat duong ~26 m)
    outliers = [p for p in CLOUDS["s05f42"] if p[2] < -10]
    img = render_top(
        CLOUDS["s05f42"], table["s05f42"], size=(1100, 700), span=75.0,
        title="T4 (4) - Diem la - s05f42",
        subtitle=f"Cum {len(outliers)} diem mau tim o z ~ -27,5 m, cach 59 m, "
                 "thap hon mat duong ~26 m. Khong thuoc vat nao -> KHONG gan thanh vat")
    img.save(OUT / "t4-4-diem-la.png")

    for path in sorted(OUT.glob("t*.png")):
        print("Đã ghi", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
