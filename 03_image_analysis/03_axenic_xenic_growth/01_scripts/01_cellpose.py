# ╭────────────────────────────────────────────────────────────────────────────╮
# │                        01_cellpose.py                                      │
# │ Batch segmentation of TIFF images using Cellpose (cyto2 model).            │
# │ Scans input folders, prepares output dirs, and runs inference.             │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Batch segmentation of brightfield TIFF images using Cellpose (cyto2 model)
- Cleans or creates corresponding output directories
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
from pathlib import Path
from tqdm import tqdm
import tifffile as tiff
from cellpose import models, io

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────
root_dir = Path("/path/to/03_axenic_xenic_growth/02_data/img/bf")
model_type = "cyto2"
diameter = 70
cellprob_threshold = 0.0
flow_threshold = 0.4

# ─────────────────────────────
# Prepare input and output paths
# ─────────────────────────────
input_files = [str(p) for p in root_dir.rglob("*.tif")]
output_files = [p.replace("/bf/", "/cp/").replace(".tif", "_cp.tif") for p in input_files]

# ─────────────────────────────
# Clean or create output directories
# ─────────────────────────────
unique_dirs = set(os.path.dirname(p) for p in output_files)
for directory in unique_dirs:
    Path(directory).mkdir(parents=True, exist_ok=True)
    for item in Path(directory).iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"Failed to delete {item}: {e}")
    print(f"Prepared directory: {directory}")

# ─────────────────────────────
# Run Cellpose batch segmentation
# ─────────────────────────────
start_time = time.time()

model = models.Cellpose(gpu=True, model_type=model_type)
progress_bar = tqdm(total=len(input_files), desc="Starting...", unit="image", dynamic_ncols=True)

for i, image_path in enumerate(input_files):
    try:
        img = io.imread(image_path)
        masks, _, _, _ = model.eval(
            img,
            diameter=diameter,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold,
        )
        tiff.imwrite(output_files[i], masks.astype("uint16"))
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
    
    progress_bar.update(1)

    # Update time estimate
    elapsed = time.time() - start_time
    remaining = (elapsed / (i + 1)) * (len(input_files) - i - 1)

    elapsed_mins, elapsed_secs = divmod(elapsed, 60)
    elapsed_hrs, elapsed_mins = divmod(elapsed_mins, 60)
    remaining_mins, remaining_secs = divmod(remaining, 60)
    remaining_hrs, remaining_mins = divmod(remaining_mins, 60)

    progress_bar.set_description(
        f"Elapsed: {int(elapsed_hrs)}h {int(elapsed_mins)}m {int(elapsed_secs)}s | "
        f"ETA: {int(remaining_hrs)}h {int(remaining_mins)}m {int(remaining_secs)}s"
    )

progress_bar.close()

# ─────────────────────────────
# Final summary
# ─────────────────────────────
total_time = time.time() - start_time
total_mins, total_secs = divmod(total_time, 60)
total_hrs, total_mins = divmod(total_mins, 60)
print(f"Total time: {int(total_hrs)}h {int(total_mins)}m {int(total_secs)}s")
