# Lunar Landing Analysis

A Flask-based web application that analyzes digital elevation models (DEM) of the lunar surface using Computer Vision and Data Science techniques to calculate terrain risks and predict safe landing zones in real-time. 

This interactive tool is designed to assess the safety of lunar landing zones by processing high-resolution topographical data. It calculates a weighted risk score based on slope proxy, terrain roughness, and the presence of craters, boulders, or shadows, providing an instant statistical probability of a safe landing.

---

## Features

* **Interactive Lunar Map:** Users can click anywhere on the rendered lunar surface canvas to scan a specific radius.
* **Topographical Image Processing:** Utilizes OpenCV, SciPy, and Rasterio to process DEM data.
* **Real-time Risk Calculation:** Evaluates localized terrain gradients and anomalies instantly.
* **Dynamic Data Visualization:** Renders an interactive pie chart displaying the exact percentages for Safe, Divert, and Abort landing recommendations.

---

## Tech Stack

* **Backend:** Python, Flask
* **Data Science & Vision:** NumPy, OpenCV (`cv2`), SciPy (`scipy.ndimage`), Rasterio
* **Frontend:** Vanilla JavaScript, HTML5 Canvas, CSS3

---

## How It Works

The backend analyzes the terrain data using five distinct indicators, combining them into a final weighted risk score:

1. **Slope Proxy (40% weight):** Calculates gradient magnitude using Sobel operators.
2. **Roughness (25% weight):** Determines local standard deviation using uniform filters.
3. **Boulder Indicator (15% weight):** Identifies local maxima above a 70th percentile threshold.
4. **Crater Indicator (20% weight):** Identifies local minima below a 30th percentile threshold.
5. **Shadow Indicator (5% weight):** Calculates the normalized low-intensity fraction.

Based on the aggregated risk score within the scanned radius, pixels are classified into three categories: Safe (< 0.20), Divert (0.20 - 0.40), and Abort (>= 0.40).

---

## Project Structure

```text
lunar-landing-analysis/
│
├── app.py                      # Main Flask application and image processing logic
├── requirements.txt            # Python dependencies
├── lunar_map_safe.tif          # High-resolution Lunar DEM file (Requires manual download)
│
├── static/
│   ├── style.css               # Frontend styling
│   ├── script.js               # Canvas interaction, API calls, and chart rendering
│   └── moon_surface_image.jpg  # Generated normalized grayscale image
│
└── templates/
    └── index.html              # Main frontend interface
