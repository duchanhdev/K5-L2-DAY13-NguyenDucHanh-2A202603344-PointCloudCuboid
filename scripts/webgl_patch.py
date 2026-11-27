"""Patch WebGL de capture duoc kiem 3D cua CVAT.

CVAT tao context WebGL voi `preserveDrawingBuffer: false`, nen
`canvas.toDataURL()` va `Page.captureScreenshot` deu ra mau den.
Ep `getContext` ve `preserveDrawingBuffer: true` truoc khi trang tai
trang, roi reload: bui 3D ve lai giup va duoc chup nguyen ban.
"""

PATCH = r"""
(() => {
  const orig = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) {
    if (String(type).indexOf('webgl') === 0) {
      attrs = Object.assign({}, attrs || {}, { preserveDrawingBuffer: true });
    }
    return orig.call(this, type, attrs);
  };
})();
"""
