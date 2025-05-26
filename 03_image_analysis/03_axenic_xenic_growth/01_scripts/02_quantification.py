# ╭────────────────────────────────────────────────────────────────────────────╮
# │                        02_quantification.py                                 │
# │ Measures cell properties from Cellpose masks using scikit-image.           │
# │ Extracts features and saves results to CSV.                                │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Scans for Cellpose mask images (.tif)
- Measures labeled region properties using scikit-image
- Saves output as CSV table

Requirements:
- tifffile
- scikit-image
- pandas
- tqdm
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import time
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from tifffile import imread
from skimage.measure import label, regionprops
from skimage.segmentation import clear_border

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────
root_dir = Path("/path/to/03_axenic_xenic_growth/02_data/img/cp")
output_csv = Path("/path/to/03_axenic_xenic_growth/02_data/tables/cell_analysis_results.csv")

# ─────────────────────────────
# Collect input files
# ─────────────────────────────
input_files = [str(p) for p in root_dir.rglob("*.tif")]

# ─────────────────────────────
# Measure cell properties
# ─────────────────────────────
data_list = []

for file_path in tqdm(input_files, desc="Processing images"):
    img = imread(file_path)
    cleaned_img = clear_border(img)
    labeled_img = label(cleaned_img)
    props = regionprops(labeled_img)

    for prop in props:
        cell_data = {
            "filename": file_path,
            "cell_label": prop.label,
        }

        # Extract scalar properties; count 'coords' manually
        for attr in dir(prop):
            if attr.startswith("_"):
                continue
            if attr in ["image", "filled_image", "coords"]:
                continue
            value = getattr(prop, attr, None)
            if isinstance(value, (int, float, np.integer, np.floating)):
                cell_data[attr] = value

        cell_data["coords_count"] = len(prop.coords)
        data_list.append(cell_data)

# ─────────────────────────────
# Export results
# ─────────────────────────────
results_df = pd.DataFrame(data_list)
results_df.to_csv(output_csv, index=False)
print(f"Saved results to: {output_csv}")
