# Metabolomics analysis

This folder contains scripts, data tables, and workflows for untargeted LC-HRMS/MS-based metabolomics in wild-type and disfp⁻ *Dictyostelium discoideum* across developmental stages.  
The analysis includes differential abundance, classification of absent features in the disfp⁻ mutant, and structural annotation of compounds. Additional *pks* gene knockout mutants were used to link selected features to individual *pks* genes.

---

## Folder structure

- `00_env/metabolomics-env.yaml`  
  Conda environment definition for all Python-based analysis scripts.

- `01_scripts/`  
  - `1_data_preparation.py`  
    Converts Thermo `.raw` files to `.mzML` using ThermoRawFileParser and splits them by ionization mode.
  - `2_mzmine_processing.py`  
    Modifies and executes MZmine 4 batch files in headless mode for feature detection and alignment.
  - `3_sirius_annotation.py`  
    Runs SIRIUS in headless mode for formula prediction, Zodiac scoring, fingerprinting, and structure search.
  - `4_data_analysis.ipynb`  
    Downstream feature-based analysis, chemical class assignment, and visual summaries.
  - `5_prepare_smiles_and_eic_data.py`  
    Draws molecular structures (SMILES) as SVGs and extracts EICs for selected features using pyOpenMS.
  - `6a–6e_Visualization_*.ipynb`  
    Final visualizations: overview, differential abundance, absence features, molecular networks, and dashboards.

- `02_data/tables/`  
  Sample metadata (`samplelist.xlsx`, `grouplist.xlsx`) used throughout the analysis.

- `04_results/tables/`  
  Final annotated feature table used in the manuscript and supplementary files.

---

## Data processing

Raw LC-MS files were converted to `.mzML` format and split by ionization mode before feature detection with MZmine 4.  
MS/MS spectra were annotated using SIRIUS (including Zodiac and CANOPUS modules), and compound classification was performed with NPClassifier and ClassyFire.

---

## GNPS Feature-Based Molecular Networks

The corresponding Feature-Based Molecular Networks created on GNPS can be found at:

- **Negative ion mode**: [https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=fbd0b9d4a0494beca59ef300ccd62acc](https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=fbd0b9d4a0494beca59ef300ccd62acc)  
- **Positive ion mode**: [https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=199d1b73ab7a4722a96c3fef3eae1c11](https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=199d1b73ab7a4722a96c3fef3eae1c11)  
- **Merged ion modes**: [https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=e8e61c044d3f490f8a803e0b9dc73970](https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=e8e61c044d3f490f8a803e0b9dc73970)

---

## Data availability

The raw LC-MS data have been deposited in the MassIVE repository:  
[https://doi.org/10.25345/C5JQ0T72R](https://doi.org/10.25345/C5JQ0T72R)
