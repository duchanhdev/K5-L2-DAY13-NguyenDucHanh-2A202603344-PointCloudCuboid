"""Kiểm tra nội dung các canvas WebGL trong trang CVAT (qua CDP port 9222)."""
import json
import sys

from cdp import Cdp, page_ws

EXPR = """
(async () => {
  const cs = Array.from(document.querySelectorAll('canvas'));
  const out = [];
  for (let i = 0; i < cs.length; i++) {
    const c = cs[i];
    const r = c.getBoundingClientRect();
    let stat = 'ERR';
    try {
      const d = await new Promise((res) => requestAnimationFrame(() => {
        try { res(c.toDataURL('image/png')); } catch (e) { res('ERR:' + e.message); }
      }));
      if (d.startsWith('data:')) {
        const img = new Image(); img.src = d; await img.decode();
        const t = document.createElement('canvas');
        t.width = img.width; t.height = img.height;
        const g = t.getContext('2d'); g.drawImage(img, 0, 0);
        const px = g.getImageData(0, 0, t.width, t.height).data;
        let sum = 0, mx = 0, bright = 0, sat = 0;
        for (let k = 0; k < px.length; k += 4) {
          const rr = px[k], gg = px[k + 1], bb = px[k + 2];
          const v = (rr + gg + bb) / 3; sum += v;
          if (v > mx) mx = v;
          if (v > 60) bright++;
          const hi = Math.max(rr, gg, bb), lo = Math.min(rr, gg, bb);
          if (hi > 60 && hi - lo > 50) sat++;
        }
        const n = px.length / 4;
        stat = `${img.width}x${img.height} mean=${(sum/n).toFixed(1)} max=${mx} bright=${bright} sat=${sat}`;
      }
    } catch (e) { stat = 'EX:' + e.message; }
    out.push(`${i}: ${stat} @(${Math.round(r.x)},${Math.round(r.y)}) ${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  return out.join('\\n');
})()
"""


def main():
    ws, tab = page_ws()
    cdp = Cdp(ws)
    try:
        print(cdp.eval(EXPR))
    finally:
        cdp.close()


if __name__ == "__main__":
    main()
