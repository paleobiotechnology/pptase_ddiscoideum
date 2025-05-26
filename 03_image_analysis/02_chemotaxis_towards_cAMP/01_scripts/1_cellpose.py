# ╭────────────────────────────────────────────────────────────────────────────╮
# │ 2_cellpose_crop_detection.py                                               │
# │ Runs Cellpose on cropped brightfield images and saves masks + crops        │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Recursively scans a directory for TIFF images
- Crops a defined region from the center of each image
- Runs Cellpose segmentation on the cropped region
- Saves Cellpose masks and cropped images to parallel output directories

Requirements:
- cellpose
- tifffile
- tqdm
- matplotlib
- scikit-image
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import time
import math
import shutil
import numpy as np
from tqdm import tqdm
import tifffile as tiff
from cellpose import models
from skimage import io

# ─────────────────────────────
# Scan for TIFF files
# ─────────────────────────────
root_dir = '/path/to/03_image_analysis/02_chemotaxis_towards_cAMP'
input_files = []

for dirpath, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.tif'):
            input_files.append(os.path.join(dirpath, file))

input_files.sort()

# Define output paths
output_files_cp = [s.replace("/bf/", "/cp/").replace(".tif", "_cp.tif") for s in input_files]
output_files_bf_crop = [s.replace("/bf/", "/bf_crop/").replace(".tif", "_bf_crop.tif") for s in input_files]

# ─────────────────────────────
# Define crop dimensions
# ─────────────────────────────
crop_width = 1250
crop_height = 2800

# ─────────────────────────────
# Prepare output directories
# ─────────────────────────────
unique_directories = set(os.path.dirname(path) for path in (output_files_bf_crop + output_files_cp))

for directory in unique_directories:
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        print(f"Cleaned directory: {directory}")
    else:
        os.makedirs(directory)
        print(f"Created directory: {directory}")

# ─────────────────────────────
# Run Cellpose on cropped images
# ─────────────────────────────
start_time = time.time()
input_files_selected = input_files
total_iterations = len(input_files_selected)

progress_bar = tqdm(total=total_iterations, desc='Processing', unit='image', dynamic_ncols=True)
model = models.Cellpose(gpu=True, model_type='cyto2')

for i, image_path in enumerate(input_files_selected):
    try:
        img = io.imread(image_path)
        height, width = img.shape[:2]

        # Center crop
        start_y = height // 2 - crop_height // 2
        start_x = width // 2 - crop_width // 2
        center_crop = img[start_y:start_y+crop_height, start_x:start_x+crop_width]

        # Cellpose parameters
        cellprob_threshold = 0.0
        flow_threshold = 0.9
        diameter = 20

        masks, _, _, _ = model.eval(
            center_crop,
            diameter=diameter,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold
        )

        tiff.imwrite(output_files_cp[i], masks.astype('uint16'))
        tiff.imwrite(output_files_bf_crop[i], center_crop.astype('uint16'))

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

    progress_bar.update(1)

    # Progress timing
    elapsed_time = time.time() - start_time
    remaining_time = (elapsed_time / (i + 1)) * (total_iterations - i - 1)

    e_h, e_r = divmod(elapsed_time, 3600)
    e_m, e_s = divmod(e_r, 60)
    r_h, r_r = divmod(remaining_time, 3600)
    r_m, r_s = divmod(r_r, 60)

    progress_bar.set_description(
        f"Elapsed: {int(e_h)}h {int(e_m)}m {int(e_s)}s | "
        f"Remaining: {int(r_h)}h {int(r_m)}m {int(r_s)}s"
    )

progress_bar.close()

# Final timing
total_time = time.time() - start_time
t_h, t_r = divmod(total_time, 3600)
t_m, t_s = divmod(t_r, 60)
print(f"Total time taken: {int(t_h)}h {int(t_m)}m {int(t_s)}s")
