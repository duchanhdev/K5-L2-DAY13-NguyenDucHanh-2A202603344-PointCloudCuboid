"""Doc noi dung canvas WebGL cua CVAT bang readPixels.

`canvas.toDataURL()` tra ve mau den voi context `preserveDrawingBuffer:false`,
nhung `gl.readPixels()` trong mot khung hinh (requestAnimationFrame) van
doc duoc buffer that. Ham nay dung de lay khung 3D va khung Top/Side/Front.
"""

import base64
import io
import json
import zlib

READ = """
new Promise(res => {
  const c = document.querySelectorAll('canvas')[%d];
  if (!c) { res('null'); return; }
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const w = c.width, h = c.height;
      const buf = new Uint8Array(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, buf);
      let bin = '';
      const CH = 8192;
      for (let i = 0; i < buf.length; i += CH) {
        bin += String.fromCharCode.apply(null, buf.subarray(i, i + CH));
      }
      res(JSON.stringify({ w: w, h: h, b64: btoa(bin) }));
    });
  });
})
"""


def _png(width, height, rgba):
    """Dong goi pixel RGBA (thu tu duoi len tren) thanh PNG."""
    raw = bytearray()
    for y in range(height - 1, -1, -1):
        raw.append(0)
        row = rgba[y * width * 4 : (y + 1) * width * 4]
        raw.extend(row)

    def chunk(tag, data):
        out = bytearray()
        out += len(data).to_bytes(4, "big")
        out += tag + data
        out += (zlib.crc32(tag + data) & 0xFFFFFFFF).to_bytes(4, "big")
        return bytes(out)

    ihdr = width.to_bytes(4, "big") + height.to_bytes(4, "big")
    ihdr += bytes([8, 6, 0, 0, 0])
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


def read_canvas(cdp, index=0):
    """Tra ve PIL Image cua canvas, hoac None neu khong doc duoc."""
    from PIL import Image

    res = cdp.eval(READ % index)
    if not res or res == "null":
        return None
    data = json.loads(res)
    rgba = base64.b64decode(data["b64"])
    png = _png(data["w"], data["h"], rgba)
    return Image.open(io.BytesIO(png)).convert("RGB")
