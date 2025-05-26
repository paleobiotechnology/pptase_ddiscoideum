# ╭──────────────────────────────────────────────────────────────────────────────╮
# │                             2a_parse_eic_data.py                             │
# │ Extracts EICs from mzML files based on metabolite list and exports to CSV.  │
# ╰──────────────────────────────────────────────────────────────────────────────╯

"""
- Reads a list of metabolites with mode-specific target m/z values
- Loads mzML files from positive and negative mode folders
- Extracts intensity values for each feature at every RT across scans
- Outputs a long-format DataFrame [File, RT, feature, mz, mode, Intensity]

Requirements:
- pyOpenMS
- pandas, openpyxl (for reading .xlsx)
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
import os
import glob
import pandas as pd
from pyopenms import MSExperiment, MzMLFile
from collections import defaultdict

# ─────────────────────────────
# Helper function to detect mode from file name
# ─────────────────────────────
def detect_mode(file_name):
    name_lower = file_name.lower()
    if 'pos' in name_lower:
        return 'pos'
    elif 'neg' in name_lower:
        return 'neg'
    else:
        return 'unknown'

# ─────────────────────────────
# Process a single mzML file
# ─────────────────────────────
def process_file_to_df(input_file, eic_search_df, ppm_tolerance=10):
    mode = detect_mode(input_file)
    df_mode = eic_search_df[eic_search_df['mode'] == mode]
    if df_mode.empty:
        return pd.DataFrame(columns=["File", "RT", "feature", "mz", "mode", "Intensity"])
    
    masses = df_mode["mz"].tolist()
    features = df_mode["feature"].tolist()
    mass_to_features = defaultdict(list)
    for m, f in zip(masses, features):
        mass_to_features[m].append(f)
    
    exp = MSExperiment()
    MzMLFile().load(input_file, exp)
    
    results = []
    for spec in exp:
        rt = spec.getRT()
        for mass, feat_list in mass_to_features.items():
            window = (mass * ppm_tolerance) / 1e6
            index = spec.findHighestInWindow(mass, window, window)
            intensity = spec[index].getIntensity() if index != -1 else 0.0
            for feat in feat_list:
                results.append({
                    "File": os.path.basename(input_file),
                    "RT": rt,
                    "feature": feat,
                    "mz": mass,
                    "mode": mode,
                    "Intensity": intensity
                })
    
    return pd.DataFrame(results)

# ─────────────────────────────
# Main execution
# ─────────────────────────────
def main():
    # Load input metabolite table (.xlsx)
    metabolites_xlsx = "/path/to/04_bioassays/02_data/tables/metabolites.xlsx"
    # Expects columns: ['name', 'positive_ion', 'negative_ion']
    df = pd.read_excel(metabolites_xlsx)
    
    # Create search table for EIC extraction
    df_pos = df[['name', 'positive_ion']].rename(columns={'name': 'feature', 'positive_ion': 'mz'})
    df_pos['mode'] = 'pos'
    df_neg = df[['name', 'negative_ion']].rename(columns={'name': 'feature', 'negative_ion': 'mz'})
    df_neg['mode'] = 'neg'
    eic_search_df = pd.concat([df_pos, df_neg], ignore_index=True)[['feature', 'mode', 'mz']]
    
    # Define path and collect input files
    base_dir = "/path/to/04_bioassays/02_data/mzML"
    pos_files = glob.glob(os.path.join(base_dir, "pos", "*.mzML"))
    neg_files = glob.glob(os.path.join(base_dir, "neg", "*.mzML"))
    all_files = pos_files + neg_files
    
    print(f"Found {len(pos_files)} positive-mode mzML files.")
    print(f"Found {len(neg_files)} negative-mode mzML files.")
    
    # Process each file
    all_dfs = []
    for mzml_path in all_files:
        df_res = process_file_to_df(mzml_path, eic_search_df, ppm_tolerance=15)
        if not df_res.empty:
            all_dfs.append(df_res)
    
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
    else:
        final_df = pd.DataFrame(columns=["File", "RT", "feature", "mz", "mode", "Intensity"])
    
    # Save to CSV
    output_csv = os.path.join(base_dir, "02_data", "tables", "eic_data.csv")
    final_df.to_csv(output_csv, index=False)
    print(f"Saved combined EIC results to: {output_csv}")

# ─────────────────────────────
# Run as script
# ─────────────────────────────
if __name__ == "__main__":
    main()
