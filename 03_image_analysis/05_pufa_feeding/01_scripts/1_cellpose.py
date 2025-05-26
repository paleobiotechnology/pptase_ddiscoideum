# ╭────────────────────────────────────────────────────────────────────────────╮
# │                        01_cellpose.py                                      │
# │ Batch segmentation of TIFF images using Cellpose (cyto3 model).            │
# │ Scans input folders, prepares output dirs, and runs inference.             │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Batch segmentation of TIFF images using Cellpose (cyto3 model)
- Cleans or creates corresponding output directories
- Saves predicted masks as uint16 TIFF files

Requirements:
- cellpose
- tifffile
- tqdm
"""

# Load libraries
import os
import time
import shutil
from pathlib import Path
from tqdm import tqdm
import tifffile as tiff
from cellpose import models, io

# User-configurable settings
root_dir = Path("/path/to/03_image_analysis/05_pufa_feeding/02_data/img/input")
model_type = "cyto3"
diameter = 22
cellprob_threshold = 0.0
flow_threshold = 0.4
use_gpu = True

# Scan for .tif files
input_files = sorted([str(p) for p in root_dir.rglob("*.tif")])

# Generate output paths by replacing 'input' with 'cp' and adding suffix
output_files = [
    s.replace("/input/", "/cp/").replace(".tif", "_cp.tif")
    for s in input_files
]

# Prepare and clean output directories
for directory in {os.path.dirname(p) for p in output_files}:
    if os.path.exists(directory):
        for file in os.listdir(directory):
            try:
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
        print(f"Cleaned directory: {directory}")
    else:
        os.makedirs(directory)
        print(f"Created directory: {directory}")

# Initialize Cellpose model
start_time = time.time()
model = models.Cellpose(gpu=use_gpu, model_type=model_type)
progress = tqdm(total=len(input_files), desc="Processing", unit="image", dynamic_ncols=True)

# Run segmentation
for i, image_path in enumerate(input_files):
    try:
        img = io.imread(image_path)
        masks, *_ = model.eval(
            img,
            diameter=diameter,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold
        )
        tiff.imwrite(output_files[i], masks.astype("uint16"))
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
    
    progress.update(1)

    elapsed = time.time() - start_time
    eta = (elapsed / (i + 1)) * (len(input_files) - i - 1)
    eh, em = divmod(elapsed, 60)
    rh, rm = divmod(eta, 60)
    progress.set_description(f"Elapsed: {int(eh)}m {int(em)}s | Remaining: {int(rh)}m {int(rm)}s")

progress.close()

# Print total time
total = time.time() - start_time
th, tr = divmod(total, 3600)
tm, ts = divmod(tr, 60)
print(f"Total time taken: {int(th)}h {int(tm)}m {int(ts)}s")
