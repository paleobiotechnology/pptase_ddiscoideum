# ╭──────────────────────────────────────────────────────────────────────────────╮
# │ 1_cellpose.py                                                               │
# │ Performs batch segmentation using Cellpose (cyto2) on TIFF brightfield data │
# ╰──────────────────────────────────────────────────────────────────────────────╯

"""
- Recursively scans a directory for .tif files
- Uses Cellpose (cyto2 model) to segment cells in each image
- Saves segmentation masks as .tif files in a parallel output directory
- Reports progress and estimated runtime with tqdm

Requirements:
- cellpose (with GPU support if available)
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
import tifffile as tiff
from cellpose import models, io

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────
root_dir = 'path/to/03_image_analysis/01_macropinocytosis_quantification'

# ─────────────────────────────
# Scan for .tif files and define output paths
# ─────────────────────────────
input_files = []
for dirpath, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.tif'):
            input_files.append(os.path.join(dirpath, file))

output_files = [
    path.replace("/bf_fp/", "/cp/").replace(".tif", "_cp.tif")
    for path in input_files
]

# ─────────────────────────────
# Prepare output directories
# ─────────────────────────────
unique_dirs = set(os.path.dirname(p) for p in output_files)

for directory in unique_dirs:
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
# Run Cellpose on all images
# ─────────────────────────────
start_time = time.time()
input_files_selected = input_files
total = len(input_files_selected)

progress_bar = tqdm(total=total, desc='Processing', unit='image', dynamic_ncols=True)
model = models.Cellpose(gpu=True, model_type='cyto2')

for i, image_path in enumerate(input_files_selected):
    try:
        cellprob_threshold = 0.8
        flow_threshold = 0.7
        diameter = 60

        img = io.imread(image_path)
        masks, _, _, _ = model.eval(
            img,
            diameter=diameter,
            cellprob_threshold=cellprob_threshold,
            flow_threshold=flow_threshold
        )

        tiff.imwrite(output_files[i], masks.astype('uint16'))

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

    progress_bar.update(1)

    elapsed = time.time() - start_time
    remaining = (elapsed / (i + 1)) * (total - i - 1)

    e_h, e_r = divmod(elapsed, 3600)
    e_m, e_s = divmod(e_r, 60)
    r_h, r_r = divmod(remaining, 3600)
    r_m, r_s = divmod(r_r, 60)

    progress_bar.set_description(
        f"Elapsed: {int(e_h)}h {int(e_m)}m {int(e_s)}s | "
        f"Remaining: {int(r_h)}h {int(r_m)}m {int(r_s)}s"
    )

progress_bar.close()
total_time = time.time() - start_time
t_h, t_r = divmod(total_time, 3600)
t_m, t_s = divmod(t_r, 60)

print(f"Total time taken: {int(t_h)}h {int(t_m)}m {int(t_s)}s")
