document.addEventListener("DOMContentLoaded", function () {
  const backButton = document.querySelector("[data-history-back='true']");
  if (backButton) {
    backButton.addEventListener("click", function (event) {
      event.preventDefault();
      const fallbackUrl =
        backButton.getAttribute("data-fallback-url") ||
        backButton.getAttribute("href") ||
        "/";

      if (window.history.length > 1) {
        window.history.back();
        return;
      }

      window.location.href = fallbackUrl;
    });
  }

  const avatar = document.querySelector(".seller-profile__avatar");
  if (!avatar) {
    return;
  }

  const colorDistance = (r1, g1, b1, r2, g2, b2) => {
    const dr = r1 - r2;
    const dg = g1 - g2;
    const db = b1 - b2;
    return Math.sqrt(dr * dr + dg * dg + db * db);
  };

  const autoCropAvatar = (img) => {
    if (img.dataset.autocropped === "1") {
      return;
    }
    if (!img.naturalWidth || !img.naturalHeight) {
      return;
    }

    const maxSample = 512;
    const ratio = Math.min(1, maxSample / Math.max(img.naturalWidth, img.naturalHeight));
    const sw = Math.max(1, Math.round(img.naturalWidth * ratio));
    const sh = Math.max(1, Math.round(img.naturalHeight * ratio));

    const sampleCanvas = document.createElement("canvas");
    sampleCanvas.width = sw;
    sampleCanvas.height = sh;
    const sctx = sampleCanvas.getContext("2d", { willReadFrequently: true });
    if (!sctx) {
      return;
    }

    sctx.drawImage(img, 0, 0, sw, sh);
    const data = sctx.getImageData(0, 0, sw, sh).data;

    const cornerPoints = [
      [0, 0],
      [sw - 1, 0],
      [0, sh - 1],
      [sw - 1, sh - 1],
      [Math.floor(sw / 2), 0],
      [Math.floor(sw / 2), sh - 1],
      [0, Math.floor(sh / 2)],
      [sw - 1, Math.floor(sh / 2)],
    ];

    let bgR = 0;
    let bgG = 0;
    let bgB = 0;
    let bgCount = 0;

    cornerPoints.forEach(([x, y]) => {
      const idx = (y * sw + x) * 4;
      const a = data[idx + 3];
      if (a > 200) {
        bgR += data[idx];
        bgG += data[idx + 1];
        bgB += data[idx + 2];
        bgCount += 1;
      }
    });

    if (!bgCount) {
      bgR = 255;
      bgG = 255;
      bgB = 255;
      bgCount = 1;
    }

    bgR /= bgCount;
    bgG /= bgCount;
    bgB /= bgCount;

    let minX = sw;
    let minY = sh;
    let maxX = -1;
    let maxY = -1;

    for (let y = 0; y < sh; y += 1) {
      for (let x = 0; x < sw; x += 1) {
        const idx = (y * sw + x) * 4;
        const r = data[idx];
        const g = data[idx + 1];
        const b = data[idx + 2];
        const a = data[idx + 3];

        if (a < 20) {
          continue;
        }

        const dist = colorDistance(r, g, b, bgR, bgG, bgB);
        const isContent = dist > 28 || a < 245;
        if (!isContent) {
          continue;
        }

        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
      }
    }

    if (maxX < 0 || maxY < 0) {
      return;
    }

    const bboxW = maxX - minX + 1;
    const bboxH = maxY - minY + 1;
    const coverRatio = (bboxW * bboxH) / (sw * sh);

    // Si ya ocupa casi todo el lienzo, no recortar.
    if (coverRatio > 0.93) {
      return;
    }

    const padX = Math.round(bboxW * 0.06);
    const padY = Math.round(bboxH * 0.06);

    minX = Math.max(0, minX - padX);
    minY = Math.max(0, minY - padY);
    maxX = Math.min(sw - 1, maxX + padX);
    maxY = Math.min(sh - 1, maxY + padY);

    const cropX = Math.round(minX / ratio);
    const cropY = Math.round(minY / ratio);
    const cropW = Math.max(1, Math.round((maxX - minX + 1) / ratio));
    const cropH = Math.max(1, Math.round((maxY - minY + 1) / ratio));

    const outCanvas = document.createElement("canvas");
    outCanvas.width = cropW;
    outCanvas.height = cropH;
    const octx = outCanvas.getContext("2d");
    if (!octx) {
      return;
    }

    octx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);
    img.dataset.autocropped = "1";
    img.src = outCanvas.toDataURL("image/png");
  };

  if (avatar.complete) {
    autoCropAvatar(avatar);
  } else {
    avatar.addEventListener("load", function () {
      autoCropAvatar(avatar);
    });
  }
});
