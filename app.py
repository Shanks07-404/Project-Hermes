from flask import Flask, render_template, request, jsonify
import numpy as np
import cv2
import rasterio
from scipy.ndimage import uniform_filter, maximum_filter, minimum_filter
import os

app = Flask(__name__)

DEM_PATH = "lunar_map_safe.tif"
IMG_PATH = "static/moon_surface_image.jpg"

if not os.path.exists('static'):
    os.makedirs('static')

try:
    print(f"--> Loading DEM file: {DEM_PATH}")
    with rasterio.open(DEM_PATH) as dataset:
        elevation_map = dataset.read(1).astype(np.float32)

    if np.isnan(elevation_map).any():
        print("--> Found 'No Data' (NaN) values. Cleaning map...")
        median_val = np.nanmedian(elevation_map)
        elevation_map = np.nan_to_num(elevation_map, nan=median_val)
        print("--> Map cleaning complete.")

    low = np.percentile(elevation_map, 2)
    high = np.percentile(elevation_map, 98)
    if high == low:
        high = low + 1

    norm_map = (elevation_map - low) / (high - low)
    norm_map = np.clip(norm_map * 255, 0, 255)
    img_gray = norm_map.astype(np.uint8)

    cv2.imwrite(IMG_PATH, img_gray)
    print(f"--> Successfully created '{IMG_PATH}' from clean DEM data.")

except FileNotFoundError:
    raise FileNotFoundError(f"Could not find '{DEM_PATH}'. Make sure your lunar_map.tif file is in the same folder as app.py")
except Exception as e:
    raise RuntimeError(f"An error occurred while processing the DEM file: {e}")

if img_gray is None:
    raise FileNotFoundError(f"Could not find '{IMG_PATH}'. Make sure file exists in static/")

img = img_gray.astype(np.float32)
H, W = img.shape

# 1) Slope proxy: gradient magnitude (Sobel)
gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
grad = np.sqrt(gx**2 + gy**2).astype(np.float32)

gmin, gmax = np.percentile(grad, [1, 99])
s_norm = np.clip((grad - gmin) / (gmax - gmin + 1e-9), 0.0, 1.0)

# 2) Roughness: local standard deviation using uniform_filter
mean = uniform_filter(img, size=9)
mean_sq = uniform_filter(img * img, size=9)
std = np.sqrt(np.maximum(mean_sq - mean * mean, 0.0))
rmin, rmax = np.percentile(std, [1, 99])
r_norm = np.clip((std - rmin) / (rmax - rmin + 1e-9), 0.0, 1.0)

# 3) Boulder indicator: local maxima above threshold
local_max = maximum_filter(img, size=7)
boulder = ((img == local_max) & (img > np.percentile(img, 70))).astype(np.float32)

# 4) Crater indicator: local minima below threshold
local_min = minimum_filter(img, size=9)
crater = ((img == local_min) & (img < np.percentile(img, 30))).astype(np.float32)

# 5) Shadow indicator: normalized low-intensity fraction
p80 = np.percentile(img, 80)
p5  = np.percentile(img, 5)
shadow_norm = np.clip((p80 - img) / (p80 - p5 + 1e-9), 0.0, 1.0)

# --- Adjusted Risk Weights ---
W_SLOPE = 0.40    
W_ROUGH = 0.25    
W_BOUL  = 0.15    
W_CRAT  = 0.20    
W_SHAD  = 0.05    

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    """
    POST JSON: {"x": int, "y": int, "radius": int}
    Coordinates are in image pixel space (0..W-1, 0..H-1).
    Returns safe/divert/abort counts and fractions.
    """
    data = request.get_json(force=True)
    x = int(round(data.get("x", 0)))
    y = int(round(data.get("y", 0)))
    radius = int(round(data.get("radius", 40)))

    # clamp center
    x = max(0, min(W - 1, x))
    y = max(0, min(H - 1, y))
    radius = max(1, min(max(W, H), radius))

    # bounding box crop
    x0 = max(0, x - radius)
    x1 = min(W, x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(H, y + radius + 1)

    yy, xx = np.mgrid[y0:y1, x0:x1]
    mask = ((xx - x) ** 2 + (yy - y) ** 2) <= radius * radius
    total_pixels = float(mask.sum())
    if total_pixels == 0:
        return jsonify({"error": "empty_mask", "safe_frac": 0.0, "divert_frac": 0.0, "abort_frac": 0.0})

    # slice maps
    s = s_norm[y0:y1, x0:x1]
    r = r_norm[y0:y1, x0:x1]
    b = boulder[y0:y1, x0:x1]
    c = crater[y0:y1, x0:x1]
    sh = shadow_norm[y0:y1, x0:x1]

    risk = (W_SLOPE * s + W_ROUGH * r + W_BOUL * b + W_CRAT * c + W_SHAD * sh)

    # --- Refined Classification Thresholds ---
    # 0..0.20 -> safe; 0.20..0.40 -> divert; >=0.40 -> abort
    masked_risk = risk[mask]

    safe_cnt = int(np.sum(masked_risk < 0.20))
    divert_cnt = int(np.sum((masked_risk >= 0.20) & (masked_risk < 0.40)))
    abort_cnt = int(np.sum(masked_risk >= 0.40))

    resp = {
        "safe": safe_cnt,
        "divert": divert_cnt,
        "abort": abort_cnt,
        "safe_frac": float(round(safe_cnt / total_pixels, 4)),
        "divert_frac": float(round(divert_cnt / total_pixels, 4)),
        "abort_frac": float(round(abort_cnt / total_pixels, 4)),
        "center_slope": float(round(float(s[y - y0, x - x0]), 4)),
        "center_roughness": float(round(float(r[y - y0, x - x0]), 4)),
        "img_w": W,
        "img_h": H
    }
    return jsonify(resp)

if __name__ == "__main__":
    app.run(debug=True)
