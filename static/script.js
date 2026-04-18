(() => {
  const lunarCanvas = document.getElementById('lunarCanvas');
  const pieCanvas = document.getElementById('pieChartCanvas');
  const decisionEl = document.getElementById('decision');
  const safeEl = document.getElementById('safePct');
  const divertEl = document.getElementById('divertPct');
  const abortEl = document.getElementById('abortPct');

  const lctx = lunarCanvas.getContext('2d');
  const pctx = pieCanvas.getContext('2d');

  const img = new Image();
  img.src = '/static/moon_surface_image.jpg';
  img.onload = drawLunarImage;

  function drawLunarImage() {
    const cw = lunarCanvas.width = lunarCanvas.clientWidth;
    const ch = lunarCanvas.height = lunarCanvas.clientHeight;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const scale = Math.min(cw / iw, ch / ih);
    const sw = iw * scale, sh = ih * scale;
    const sx = (cw - sw) / 2, sy = (ch - sh) / 2;

    lctx.fillStyle = "#000";
    lctx.fillRect(0, 0, cw, ch);
    lctx.drawImage(img, 0, 0, iw, ih, sx, sy, sw, sh);
  }

  function drawPieChart(data) {
    const w = pieCanvas.width = pieCanvas.clientWidth;
    const h = pieCanvas.height = pieCanvas.clientHeight;
    const cx = w / 2, cy = h / 2, r = Math.min(w, h) * 0.4;

    const slices = [
      { frac: data.safe_frac || 0, color: "#00ff66" },
      { frac: data.divert_frac || 0, color: "#ffcc00" },
      { frac: data.abort_frac || 0, color: "#ff4444" },
    ];

    pctx.clearRect(0, 0, w, h);
    let start = -Math.PI / 2;
    slices.forEach(s => {
      const angle = s.frac * 2 * Math.PI;
      pctx.beginPath();
      pctx.moveTo(cx, cy);
      pctx.arc(cx, cy, r, start, start + angle);
      pctx.closePath();
      pctx.fillStyle = s.color;
      pctx.fill();
      start += angle;
    });

    // Pie outline
    pctx.beginPath();
    pctx.arc(cx, cy, r, 0, Math.PI * 2);
    pctx.strokeStyle = "#fff";
    pctx.lineWidth = 2;
    pctx.stroke();
  }

  function updateInfo(data) {
    const safe = Math.round((data.safe_frac || 0) * 100);
    const divert = Math.round((data.divert_frac || 0) * 100);
    const abort = Math.round((data.abort_frac || 0) * 100);

    // ✅ fixed interpolation
    safeEl.textContent = `${safe}%`;
    divertEl.textContent = `${divert}%`;
    abortEl.textContent = `${abort}%`;

    let decision = "SAFE";
    if (abort > 30) decision = "ABORT";
    else if (divert + abort > 50) decision = "DIVERT";

    // ✅ fixed interpolation
    decisionEl.textContent = `Decision: ${decision}`;
  }

  // --- CLICK HANDLER ---
  lunarCanvas.addEventListener('click', async (e) => {
    const rect = lunarCanvas.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * img.naturalWidth);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * img.naturalHeight);

    // Click marker
    lctx.beginPath();
    lctx.arc(e.offsetX, e.offsetY, 6, 0, 2 * Math.PI);
    lctx.strokeStyle = '#00ffff';
    lctx.lineWidth = 2;
    lctx.stroke();

    try {
      const res = await fetch('/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, radius: 40 })
      });

      const data = await res.json();

      if (data.safe_frac !== undefined) {
        drawPieChart(data);
        updateInfo(data);
      } else {
        console.error('Bad response:', data);
      }
    } catch (err) {
      console.error('Error contacting server:', err);
    }
  });

  // Default chart
  drawPieChart({ safe_frac: 0.33, divert_frac: 0.33, abort_frac: 0.34 });
  updateInfo({ safe_frac: 0.33, divert_frac: 0.33, abort_frac: 0.34 });

  window.addEventListener('resize', drawLunarImage);
})();
