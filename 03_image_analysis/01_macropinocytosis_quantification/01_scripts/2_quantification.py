# ╭──────────────────────────────────────────────────────────────────────────────╮
# │ 2_quantification.py                                                         │
# │ Quantifies macropinocytosis from Cellpose masks and fluorescence stacks    │
# ╰──────────────────────────────────────────────────────────────────────────────╯

"""
- Performs background subtraction and max projection on fluorescence stacks
- Computes binary macropinocytosis masks and region properties
- Saves related intermediate images
- Outputs single-cell metrics to a timestamped CSV file

Requirements:
- numpy, pandas
- scikit-image
- tqdm
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import numpy as np
import pandas as pd
import concurrent.futures
from tqdm import tqdm
from datetime import datetime
from skimage.io import imread, imsave
from skimage.measure import label, regionprops
from skimage.restoration import rolling_ball
from skimage.filters import gaussian

# ─────────────────────────────
# Helper functions
# ─────────────────────────────
def iterative_background_subtraction_stack(image_stack, num_iterations=1, ball_radius=15, gaussian_sigma=2):
    """
    Apply iterative background subtraction to each image in a stack.
    """
    processed_stack = []
    for image in image_stack:
        processed_img = image.copy()
        for _ in range(num_iterations):
            background = rolling_ball(processed_img, radius=ball_radius)
            smoothed = gaussian(background, sigma=gaussian_sigma)
            processed_img = np.clip(processed_img - smoothed, 0, None)
        processed_stack.append(processed_img)
    return np.array(processed_stack)


def analyze_image(bf_img_path, cp_img_path, fl_img_path, root_dir):
    """
    Analyze image triplet and extract single-cell features.
    """
    cp_img = imread(cp_img_path)
    fl_stack = imread(fl_img_path)
    fl_img = np.amax(fl_stack, axis=0)
    bs_stack = iterative_background_subtraction_stack(fl_stack)
    fm_img = np.amax(bs_stack, axis=0)

    threshold = 400
    bn_img = (fm_img > threshold).astype(np.uint8)

    base = os.path.splitext(os.path.basename(fl_img_path))[0]
    imsave(os.path.join(root_dir, 'fl', f'{base}_merged.tif'), fl_img)
    imsave(os.path.join(root_dir, 'bn', f'{base}_binary.tif'), bn_img * 255)

    for i, img in enumerate(bs_stack):
        imsave(os.path.join(root_dir, 'fl_stack_bs', f'{base}_bs_{i:03d}.tif'), img)

    labeled = label(cp_img)
    props = ['perimeter', 'eccentricity', 'max_intensity', 'mean_intensity',
             'min_intensity', 'major_axis_length', 'minor_axis_length']
    
    records = []
    for region in regionprops(labeled, intensity_image=fm_img):
        cell_data = {
            'datafile': base.replace("_fl_stack", ""),
            'id': region.label,
            'cell_area': region.area,
            'mpc_area': np.sum(bn_img[tuple(region.coords.T)])
        }
        for prop in props:
            cell_data[prop] = getattr(region, prop)
        records.append(cell_data)

    return pd.DataFrame(records)

# ─────────────────────────────
# Main workflow
# ─────────────────────────────
def main():
    root_dir = 'path/to/03_image_analysis/01_macropinocytosis_quantification'
    for sub in ['fl', 'bn', 'fl_stack_bs']:
        os.makedirs(os.path.join(root_dir, sub), exist_ok=True)

    # Collect all .tif files recursively
    input_files = []
    for dirpath, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.tif'):
                input_files.append(os.path.join(dirpath, file))

    bf_files = sorted([f for f in input_files if "_bf_fp.tif" in f])
    cp_files = sorted([f for f in input_files if "_cp.tif" in f])
    fl_files = sorted([f for f in input_files if "_fl_stack.tif" in f])

    # For testing:
    # bf_files, cp_files, fl_files = bf_files[:2], cp_files[:2], fl_files[:2]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(analyze_image, bf, cp, fl, root_dir)
            for bf, cp, fl in zip(bf_files, cp_files, fl_files)
        ]
        results = [
            future.result() for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Processing Images"
            )
        ]

    final_df = pd.concat(results, ignore_index=True)
    tables_dir = os.path.join(os.path.dirname(root_dir), 'tables')
    os.makedirs(tables_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(tables_dir, f'mpc_quantification_{timestamp}.csv')
    final_df.to_csv(file_path, index=False)

    print(f'Data saved to {file_path}')


if __name__ == '__main__':
    main()
