
This repository contains scripts, meta data tables, and environments used in the study:  
**"Global analysis of polyketide synthase functions in social amoeba"**  
by Guenther et al., 2025 (submitted).

The study investigates the physiological, transcriptomic, and metabolomic consequences of a phosphopantetheinyl transferase (DiSfp) knockout in *Dictyostelium discoideum*, revealing the essential role of polyketide synthases (PKSs) in amoeba development and metabolism.

This repository accompanies a research manuscript currently under review and may be updated prior to final publication.

---

## Overview

- `00_env/`  
  Environment files for reproducibility of R analyses.

- `01_transcriptomics/`  
  Analysis of RNA-seq data across developmental stages. Includes differential gene expression and GO term enrichment.

- `02_metabolomics/`  
  Untargeted LC-MS/MS processing using MZmine, SIRIUS, and GNPS. Includes annotation workflows and network visualization.

- `03_image_analysis/`  
  Automated image analysis pipelines (Cellpose + quantification) for macropinocytosis, chemotaxis, and growth assays.

- `04_bioassays/`  
  Additional bioassays (spore viability, development, metabolite EIC analysis).

---

## How to use

Each subfolder contains its own `README.md` with usage notes, environment specifications, and documentation of the analysis workflow.  
These materials are intended to support reproducibility and provide insight into the data processing steps used in the study.

---

## Citation

If you use these materials, please cite the corresponding publication.
