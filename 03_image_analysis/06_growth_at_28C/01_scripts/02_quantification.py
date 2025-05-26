# ╭────────────────────────────────────────────────────────────────────────────╮
# │                        02_quantification.py                                │
# │ Measure properties of Cellpose masks and save per-cell statistics.         │
# │ Uses skimage, tifffile, and parallel processing.                           │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Loads all .tif masks from Cellpose output directory
- Measures region properties using skimage
- Supports parallel processing with multiple CPU cores
- Saves per-cell data as a CSV

Requirements:
- tifffile
- scikit-image
- pandas
- tqdm
"""

# Load libraries
import os
import pandas as pd
from tqdm import tqdm
from tifffile import imread
from skimage.measure import label, regionprops
from skimage.segmentation import clear_border
import concurrent.futures
from pathlib import Path

# User-configurable settings
root_dir = Path("/path/to/03_image_analysis/06_growth_at_28/02_data/img/cp")
output_path = Path("/path/to/03_image_analysis/06_growth_at_28/02_data/tables/quant_cells.csv")
num_cpus = 4  # Set to None to use all available CPUs

# Scan for all .tif files
input_files = sorted([str(p) for p in root_dir.rglob("*.tif")])

# Function to measure properties from a single file
def process_file(file_path):
    img = imread(file_path)
    cleaned_img = clear_border(img)
    labeled_img = label(cleaned_img)
    props = regionprops(labeled_img)

    file_data = []
    for prop in props:
        cell_data = {'filename': file_path, 'cell_label': prop.label}
        for prop_name in prop:
            if prop_name not in ['image', 'filled_image', 'coords']:
                cell_data[prop_name] = getattr(prop, prop_name)
            elif prop_name == 'coords':
                cell_data['coords_count'] = len(prop.coords)
        file_data.append(cell_data)
    
    return file_data

# Main routine
def main(input_files, output_path, num_cpus=None):
    data_list = []
    num_workers = num_cpus if num_cpus is not None else None

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(tqdm(
            executor.map(process_file, input_files),
            total=len(input_files),
            desc="Processing Files"
        ))

    for file_data in results:
        data_list.extend(file_data)

    results_df = pd.DataFrame(data_list)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)

# Run script
if __name__ == "__main__":
    main(input_files, output_path, num_cpus)
