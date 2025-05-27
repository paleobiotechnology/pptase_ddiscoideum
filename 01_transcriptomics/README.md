# Transcriptomic analysis

Analysis of gene expression differences and Gene Ontology enrichment between wild-type and disfp⁻ *Dictyostelium discoideum* across developmental stages.

---

## Folder structure

- `01_scripts/Analysis and visualization.ipynb`  
  R notebook for PCA, GO enrichment, and network visualization

- `02_data/tables/annotation/`  
  - `genes/` – DictyBase gene annotations  
  - `TopGO/` – GO term definitions and mappings

- `02_data/tables/diffAbs/`  
  Differential expression results per stage (`veg`, `agg`, `fbs`)

- `02_data/tables/GO/`  
  GO term descriptions and ontology file (`go-basic.obo`)

---

## Data processing

Raw reads were processed externally using the nf-core RNA-seq pipeline (v3.12.0), which includes quality control (FastQC), trimming (Trim Galore), alignment to the *D. discoideum* genome (STAR), and gene-level quantification (Salmon).  
Differential expression analysis was performed with the nf-core differentialabundance pipeline (v1.2.0) using DESeq2.

The resulting tables of differential gene expression serve as input for the R notebook in this folder.

---
