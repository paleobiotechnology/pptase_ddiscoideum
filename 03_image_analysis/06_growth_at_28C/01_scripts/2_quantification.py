# ╭────────────────────────────────────────────────────────────────────────────╮
# │                      02_quantification.py                                  │
# │ Measures cell properties from TIFF masks created by Cellpose.              │
# │ Loads images, extracts regionprops, and writes output as CSV.             │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Loads segmented TIFF masks and extracts region properties using skimage
- Supports parallel processing using ProcessPoolExecutor
- Saves result table as CSV

Requirements:
- tifffile
- skimage
- tqdm
- pandas
"""

# Load libraries
import os
import time
import shutil
import math
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from tifffile import imread
from skimage.measure import label, regionprops
from skimage.segmentation import clear_border
import concurrent.futures

# User-configurable settings
root_dir = Path("/path/to/03_image_analysis/06_growth_at_28C/02_data/img/cp")
output_csv = Path("/path/to/03_image_analysis/06_growth_at_28C/02_data/tables/cell_analysis.csv")
num_cpus = 4  # Number of CPU cores to use

# Scan for all .tif files
input_files = sorted([str(p) for p in root_dir.rglob("*.tif")])
print(f"Found {len(input_files)} input files.")

# Function to process a single file and return cell properties
def process_file(file_path):
    img = imread(file_path)
    cleaned = clear_border(img)
    labeled = label(cleaned)
    props = regionprops(labeled)

    file_data = []
    for prop in props:
        entry = {'filename': file_path, 'cell_label': prop.label}
        for attr in prop:
            if attr not in ['image', 'filled_image', 'coords']:
                entry[attr] = getattr(prop, attr)
            elif attr == 'coords':
                entry['coords_count'] = len(prop.coords)
        file_data.append(entry)
    
    return file_data

# Main function to run quantification
def main(input_files, output_path, num_workers=None):
    all_data = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(tqdm(executor.map(process_file, input_files), total=len(input_files), desc="Processing"))

    for result in results:
        all_data.extend(result)

    df = pd.DataFrame(all_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved results to {output_path}")

# Run
main(input_files, output_csv, num_cpus)
