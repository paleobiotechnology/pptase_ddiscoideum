# ╭────────────────────────────────────────────────────────────────────────────╮
# │                        01_cellpose.py                                      │
# │ Batch segmentation of TIFF images using Cellpose (cyto3 model).            │
# │ Scans input folders, prepares output dirs, and runs inference.             │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Batch segmentation of TIFF images using Cellpose (cyto3 model)
- Scans input directory, creates output folders, cleans them, and runs segmentation
- Saves predicted masks as uint16 TIFF files

Requirements:
- cellpose
- tifffile
- tqdm
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import time
import shutil
from tqdm import tqdm
from pathlib import Path
import tifffile as tiff
from cellpose import models, io

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────
root_dir = Path("/path/to/03_image_analysis/04_axenic_migration/img")
model_type = "cyto3"
diameter = 70
cellprob_threshold = 0.0
flow_threshold = 0.4

# ─────────────────────────────
# Scan for input and generate output paths
# ─────────────────────────────
input_files = sorted([
    str(Path(dirpath) / file)
    for dirpath, _, files in os.walk(root_dir)
    for file in files if file.endswith(".tif")
])

output_files = [
    f.replace("/bf/", "/cp/").replace(".tif", "_cp.tif")
    for f in input_files
]

# ─────────────────────────────
# Clean or create output directories
# ─────────────────────────────
unique_directories = set(os.path.dirname(p) for p in output_files)
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
                print(f"Failed to delete {file_path}. Reason: {e}")
        print(f"Cleaned directory: {directory}")
    else:
        os.makedirs(directory)
        print(f"Created directory: {directory}")

# ─────────────────────────────
# Run Cellpose segmentation
# ─────────────────────────────
start_time = time.time()

model = models.Cellpose(gpu=False, model_type=model_type)
progress_bar = tqdm(total=len(input_files), desc='Processing', unit='image', dynamic_ncols=True)

for i, image_path in enumerate(input_files):
    try:
        img = io.imread(image_path)
        masks, _, _, _ = model.eval(
            img,
            diameter=diameter,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold
        )
        tiff.imwrite(output_files[i], masks.astype("uint16"))
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
    
    progress_bar.update(1)
    
    elapsed_time = time.time() - start_time
    remaining_time = (elapsed_time / (i + 1)) * (len(input_files) - (i + 1))
    elapsed_h, rem_e = divmod(elapsed_time, 3600)
    elapsed_m, elapsed_s = divmod(rem_e, 60)
    rem_h, rem_r = divmod(remaining_time, 3600)
    rem_m, rem_s = divmod(rem_r, 60)
    time_info = f"Elapsed: {int(elapsed_h)}h {int(elapsed_m)}m {int(elapsed_s)}s | Remaining: {int(rem_h)}h {int(rem_m)}m {int(rem_s)}s"
    progress_bar.set_description(time_info)

progress_bar.close()

total_time = time.time() - start_time
total_h, total_r = divmod(total_time, 3600)
total_m, total_s = divmod(total_r, 60)
print(f"Total time taken: {int(total_h)}h {int(total_m)}m {int(total_s)}s")
