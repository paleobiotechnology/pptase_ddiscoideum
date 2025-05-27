# Image analysis

This folder contains automated pipelines for segmentation and quantification of cellular phenotypes in *Dictyostelium discoideum*, including macropinocytosis, chemotaxis, growth, and migration.

Segmentation was performed using Cellpose models and quantification was carried out using custom Python scripts. For experiments involving cell tracking (e.g., chemotaxis and migration), tracking was performed externally using the TrackMate plugin in Fiji/ImageJ. Corresponding `trackmate_settings.xml` files are included for reproducibility.

---

## General structure

Each subfolder corresponds to one experimental assay and contains:

- `01_scripts/`  
  Core scripts for Cellpose segmentation (`1_cellpose.py`), data preparation or quantification (`2_quantification.py` or `2_preprocessing.ipynb`), and downstream analysis (`3_data_analysis.ipynb`).


- `02_data/`  
  Metadata or results, including measurement tables or TrackMate configuration files.

Assays:
- `01_macropinocytosis_quantification/`  
  Measures fluid uptake via high-throughput analysis of fluorescence stacks.
- `02_chemotaxis_towards_cAMP/`  
  Quantifies directional migration in response to cAMP gradients.
- `03_axenic_xenic_growth/`, `06_growth_at_28C/`  
  Assess growth under different nutritional or temperature conditions.
- `04_axenic_migration/`  
  Tracks cell movement under axenic conditions (HL5 medium).
- `05_pufa_feeding/`  
  Evaluates phenotypic rescue by fatty acid supplementation.
