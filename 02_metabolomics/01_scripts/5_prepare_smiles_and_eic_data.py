# ╭────────────────────────────────────────────────────────────────────────────╮
# │            5_prepare_smiles_and_eic_data.py                                │
# │ Draws SMILES as SVGs and extracts EIC (Extracted Ion Chromatograms)        │
# │ from mzML files for selected features.                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯

"""
- Draws molecular structures as SVG files from SIRIUS-generated SMILES.
- Extracts EICs from mzML files for selected features using pyOpenMS.

Requirements:
- RDKit
- pyOpenMS
- tqdm
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import glob
import shutil
import warnings
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from pyopenms import MSExperiment, MzMLFile
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────
wd = "/path/to/02_metabolomics"
os.chdir(wd)

# ─────────────────────────────
# Draw SMILES as SVG files
# ─────────────────────────────

# Load SIRIUS feature table
csv_input = os.path.join("03_analysis", "tables", "featureTable.csv")
df = pd.read_csv(csv_input)

# Filter for features with valid SMILES
df_smiles = df[df["sirius_smiles"].notna()]

# Output directory for SVGs
svg_dir = os.path.join("03_analysis", "formulas", "light_white-background")
os.makedirs(svg_dir, exist_ok=True)

def save_mol_as_svg(smiles, file_path):
    """Draw molecule as SVG from SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        warnings.warn(f"Invalid SMILES string, skipping: {file_path}")
        return
    drawer = rdMolDraw2D.MolDraw2DSVG(300, 300)
    drawer.drawOptions().addAtomIndices = False
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText().replace('<?xml version="1.0"?>', '')
    with open(file_path, 'w') as f:
        f.write(svg)

# Draw and save SVGs
for _, row in df_smiles.iterrows():
    file_path = os.path.join(svg_dir, f"{row['feature']}.svg")
    save_mol_as_svg(row['sirius_smiles'], file_path)

# ─────────────────────────────
# Extract EIC data from mzML files
# ─────────────────────────────

def detect_mode(file_name):
    """Detect ionization mode from file name."""
    name = file_name.lower()
    return 'pos' if 'pos' in name else 'neg' if 'neg' in name else 'unknown'

def process_file(input_file, eic_df):
    """Extract EICs for features in one mzML file."""
    mode = detect_mode(input_file)
    mode_df = eic_df[eic_df['mode'] == mode]
    masses = mode_df['mz'].tolist()
    ids = mode_df['feature'].tolist()
    ppm_tol = 10

    mass_to_ids = defaultdict(list)
    for mass, fid in zip(masses, ids):
        mass_to_ids[mass].append(fid)

    exp = MSExperiment()
    MzMLFile().load(input_file, exp)
    mass_data = {fid: [] for fid_list in mass_to_ids.values() for fid in fid_list}

    for spec in exp:
        rt = spec.getRT()
        for mass, fid_list in mass_to_ids.items():
            ppm = (mass * ppm_tol) / 1e6
            idx = spec.findHighestInWindow(mass, ppm, ppm)
            intensity = spec[idx].getIntensity() if idx != -1 else 0
            for fid in fid_list:
                mass_data[fid].append((rt, intensity, os.path.basename(input_file)))

    return mass_data

def save_mass_data(data, output_dir, fid):
    """Save EIC data to CSV."""
    df = pd.DataFrame(data, columns=['RT', 'Intensity', 'File'])
    df.to_csv(os.path.join(output_dir, f"{fid}.csv"), index=False)

def extract_eic(wd, xic_dir, eic_df, sample_names, chunk_size=1000):
    """Main pipeline to extract EICs across mzML files."""
    modes = ['pos', 'neg']
    mzml_files = [f for mode in modes 
                  for f in glob.glob(os.path.join(wd, "03_data", "mzML", "02_split", mode, "*.mzML"))]
    mzml_files = [f for f in mzml_files if any(s in os.path.basename(f) for s in sample_names)]

    total = len(eic_df)
    with tqdm(total=total, desc="Extracting EICs", unit="feature") as pbar:
        for start in range(0, total, chunk_size):
            chunk = eic_df.iloc[start:start + chunk_size]
            chunk_data = {}

            with ProcessPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(process_file, f, chunk): f for f in mzml_files}
                for future in as_completed(futures):
                    result = future.result()
                    for fid, data in result.items():
                        chunk_data.setdefault(fid, []).extend(data)

            for fid, data in chunk_data.items():
                save_mass_data(data, xic_dir, fid)
            pbar.update(len(chunk))

# ─────────────────────────────
# Prepare directories and input
# ─────────────────────────────

xic_dir = os.path.join("03_analysis", "eic")
shutil.rmtree(xic_dir, ignore_errors=True)
os.makedirs(xic_dir, exist_ok=True)

# Load feature table
ft_path = os.path.join("03_analysis", "tables", "featureTable_final.csv")
ft = pd.read_csv(ft_path)

# Load sample metadata
md_path = os.path.join("02_data", "tables", "samplelist.xlsx")
md = pd.read_excel(md_path)
sample_names = md[md['type'].isin(['sample', 'control'])]['name'].tolist()

# Filter features of interest
eic_df = ft[
    (~ft['change_veg'].isin(["none", "na"])) |
    (~ft['change_stv'].isin(["none", "na"])) |
    (~ft['change_fbs'].isin(["none", "na"])) |
    ft["sirius_molecularFormula"].notna() |
    (ft["msms"] == True)
]

# ─────────────────────────────
# Run extraction
# ─────────────────────────────

extract_eic(wd, xic_dir, eic_df, sample_names)
