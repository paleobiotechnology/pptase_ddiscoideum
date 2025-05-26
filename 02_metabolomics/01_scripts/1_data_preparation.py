# ╭───────────────────────────────────────────────────────────────────────────╮
# │               01_data_preparation.py                                      │
# │ Converts Thermo .raw files to .mzML using ThermoRawFileParser, and splits │
# │ mzML files into positive/negative mode using pyOpenMS.                    │
# ╰───────────────────────────────────────────────────────────────────────────╯

"""
- Converts Thermo .raw files to .mzML using ThermoRawFileParser (via mono)
- Splits each mzML into positive/negative ionization mode using pyOpenMS

Requirements:
- mono installed in a Conda environment
- pyOpenMS installed
- ThermoRawFileParser executable
"""

# ─────────────────────────────
# Load libraries
# ─────────────────────────────
from pathlib import Path
import os
import IPython
import glob
import concurrent.futures
import pyopenms as oms

# ─────────────────────────────
# USER-CONFIGURABLE SETTINGS
# ─────────────────────────────

# Path to the ThermoRawFileParser executable (absolute or relative)
thermo_parser_path = "/path/to/ThermoRawFileParser/ThermoRawFileParser.exe"

# Name of the conda environment that includes 'mono' and dependencies
conda_env_name = "metabolomics-env"

# Set the working directory
wd = "/path/to/02_metabolomics/"
os.chdir(wd)

# ─────────────────────────────
# List input raw files
# ─────────────────────────────

# Define the input folder containing the raw files
input_raw_folder = os.path.join("02_data", "raw")

# Get a sorted list of all .raw files in the input folder
input_raw_files = glob.glob(os.path.join(input_raw_folder, "*.raw"))
input_raw_files.sort()

# Print the number of input raw files found
print(f"Number of input raw files found: {len(input_raw_files)}")

# ─────────────────────────────
# Convert Thermo raw files to mzML
# ─────────────────────────────
"""
Multi-threaded conversion from .raw to .mzML using ThermoRawFileParser.
Mono must be installed in the specified conda environment.
"""

# Define output directory
output_mzML_folder = os.path.join("02_data", "mzML", "01_converted")
os.makedirs(output_mzML_folder, exist_ok=True)

# Function to convert a single file
def convert_file(file_name):
    input_file = os.path.join(input_raw_folder, file_name)
    command = f"conda run -n {conda_env_name} mono {thermo_parser_path} -i={input_file} -o={output_mzML_folder}"
    print(f"Running: {command}")
    os.system(command)

# List raw files
files = [f for f in os.listdir(input_raw_folder) if os.path.isfile(os.path.join(input_raw_folder, f))]
files.sort()

# Parallel conversion
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(convert_file, file_name) for file_name in files]
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            print(f"An error occurred during conversion: {e}")

# ─────────────────────────────
# Split spectra into pos/neg ionization mode
# ─────────────────────────────
"""
Splits each mzML file into separate files based on positive or negative polarity.
Outputs are saved to '02_data/mzML/02_split/pos' and '.../neg'.
No output is generated if the polarity is missing.
"""

# Define input/output folders
input_mzML_folder = os.path.join("02_data", "mzML", "01_converted")
output_mzML_folder_pos = os.path.join("02_data", "mzML", "02_split", "pos")
output_mzML_folder_neg = os.path.join("02_data", "mzML", "02_split", "neg")
os.makedirs(output_mzML_folder_pos, exist_ok=True)
os.makedirs(output_mzML_folder_neg, exist_ok=True)

# Get list of mzML files
input_mzML_files = glob.glob(os.path.join(input_mzML_folder, "*.mzML"))

# Split each file based on polarity
for input_mzML_file in input_mzML_files:
    exp = oms.MSExperiment()
    oms.MzMLFile().load(input_mzML_file, exp)

    exp_positive = oms.MSExperiment()
    exp_negative = oms.MSExperiment()

    for spectrum in exp:
        polarity = spectrum.getInstrumentSettings().getPolarity()
        if polarity == oms.IonSource.Polarity.POSITIVE:
            exp_positive.addSpectrum(spectrum)
        elif polarity == oms.IonSource.Polarity.NEGATIVE:
            exp_negative.addSpectrum(spectrum)

    base_filename = os.path.splitext(os.path.basename(input_mzML_file))[0]
    output_file_positive = os.path.join(output_mzML_folder_pos, base_filename + ".mzML")
    output_file_negative = os.path.join(output_mzML_folder_neg, base_filename + ".mzML")

    if exp_positive.getSpectra():
        oms.MzMLFile().store(output_file_positive, exp_positive)
        print(f"Saved {output_file_positive}")

    if exp_negative.getSpectra():
        oms.MzMLFile().store(output_file_negative, exp_negative)
        print(f"Saved {output_file_negative}")
