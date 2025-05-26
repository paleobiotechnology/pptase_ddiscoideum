# ╭──────────────────────────────────────────────────────────────────────────╮
# │            02_mzmine_feature_detection.py                                │
# │ Batch update and execution of MZmine for both ionization modes.          │
# ╰──────────────────────────────────────────────────────────────────────────╯

"""
Modifies MZmine batch XML templates for positive and negative modes, 
injects correct file paths and adducts, and runs MZmine in headless mode.

Requirements:
- MZmine 4 installed and accessible via command line
- A valid MZmine user configuration file (`*.mzuser`) for headless execution
- A writable temporary directory with sufficient free disk space for intermediate files
- XML batch templates and adduct definition files for each ionization mode
- Python packages: pyopenms, pandas, xml.etree.ElementTree, etc.
"""

# ─────────────────────────────
# Import libraries
# ─────────────────────────────
import glob
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

# ─────────────────────────────
# Configuration
# ─────────────────────────────

# Working directory (project root)
wd = Path("/path/to/02_metaboloimcs").resolve()
os.chdir(wd)

# Base path to MZmine installation and related resources
# IMPORTANT:
# - The temp folder should be located on a disk with sufficient free space.
# - MZmine creates large temporary files during processing.
# - The user file is required for user-specific settings or authentication.
mzmine_base_path = "/path/to/mzmine4"

# Executable, temp, and user configuration paths
mzmine_path = f"{mzmine_base_path}/bin/mzmine"
mzmine_temp_dir = f"{mzmine_base_path}/tmp"
mzmine_user_file = f"{mzmine_base_path}/user/yourusername.mzuser"

# Create the temp directory if it does not exist
Path(mzmine_temp_dir).mkdir(parents=True, exist_ok=True)
# ─────────────────────────────
# Helper functions
# ─────────────────────────────

def prettify_xml(elem): 
    """Prettify and indent an XML element for better readability in output files."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return '\n'.join([line for line in reparsed.toprettyxml(indent='    ').split('\n') if line.strip()])

def update_export_path(root, module_name, new_paths):
    """Update 'Filename' parameters for specific MZmine export modules."""
    module_counter = 0
    for module in root.findall(f".//batchstep[@method='{module_name}']"):
        if module_counter < len(new_paths):
            filename_param = module.find(".//parameter[@name='Filename']")
            if filename_param is not None:
                current_file_element = filename_param.find("current_file")
                if current_file_element is not None:
                    current_file_element.text = new_paths[module_counter]
                    print(f"Updated {module_name} instance {module_counter + 1} to {new_paths[module_counter]}")
                    module_counter += 1
        else:
            break

def selective_index(my_list, indices):
    """Select elements from a list based on index positions and/or slice tuples."""
    result = []
    for item in indices:
        if isinstance(item, tuple):
            result.extend(my_list[item[0]:item[1]])
        else:
            result.append(my_list[item])
    return result

# ─────────────────────────────
# Prepare and modify batch files
# ─────────────────────────────

modes = ["pos", "neg"]

batch_template_folder = wd / "02_data" / "mzmine"
batch_template_file = glob.glob(str(batch_template_folder / "*_template*"))[0]
batch_modified_folder = batch_template_folder / "modified"
batch_modified_folder.mkdir(parents=True, exist_ok=True)

for mode in modes:
    tree = ET.parse(batch_template_file)
    root = tree.getroot()

    # Set input files
    input_mzml_folder = wd / "02_data" / "mzML" / mode
    input_files = sorted(glob.glob(str(input_mzml_folder / "*.mzML")))

    for param in root.findall(".//parameter[@name='File names']"):
        for existing_file in list(param):
            param.remove(existing_file)
        for file_path in input_files:
            file_elem = ET.SubElement(param, 'file')
            file_elem.text = file_path

    # Update export paths
    export_base = wd / "04_analysis" / "mzmine" / mode
    export_base.mkdir(parents=True, exist_ok=True)

    export_steps = [
        elem for elem in root.findall('.//batchstep')
        if 'method' in elem.attrib and 'io.export' in elem.attrib['method']
    ]

    for elem in export_steps:
        for file_elem in elem.findall(".//current_file"):
            base_name = file_elem.text
            file_elem.text = str(export_base / base_name).replace("C:\\Program Files\\mzmine\\", "")
            print(f"Updated path: {file_elem.text}")

    # Update project save location
    project_elem = root.find(
        ".//batchstep[@method='io.github.mzmine.modules.io.projectsave.ProjectSaveAsModule']/parameter[@name='Project file']/current_file"
    )
    project_elem.text = str(export_base / "project.mzmine")

    # Inject mode-specific adduct list
    adducts_file = batch_template_folder / f"adducts_{mode}.xml"
    with open(adducts_file, "r", encoding="utf-8") as f:
        adducts_content = f.read()

    adducts_element = ET.Element('parameter', {'name': 'Adducts'})
    wrapped_root = ET.fromstring(f"<root>{adducts_content}</root>")
    for child in wrapped_root:
        adducts_element.append(child)

    ion_identity_elem = root.find(
        ".//batchstep[@method='io.github.mzmine.modules.dataprocessing.id_ion_identity_networking.ionidnetworking.IonNetworkingModule']/parameter[@name='Ion identity library']"
    )
    old_adducts = ion_identity_elem.find("parameter[@name='Adducts']")
    if old_adducts is not None:
        ion_identity_elem.remove(old_adducts)
    ion_identity_elem.append(adducts_element)

    # Save updated batch file
    output_xml = batch_modified_folder / f"modified_batch_{mode}.xml"
    with open(output_xml, "w", encoding='utf-8') as f:
        f.write(prettify_xml(root))
    print(f"[INFO] Modified XML saved to: {output_xml}")

# ─────────────────────────────
# Run MZmine in headless mode
# ─────────────────────────────

modified_files = glob.glob(str(batch_modified_folder / "*.xml"))
for batch_file in modified_files:
    command = (
        f"{mzmine_path} -b {batch_file} -memory none "
        f"-temp {mzmine_temp_dir} "
        f"-user {mzmine_user_file}"
    )
    print(f"[INFO] Running MZmine batch: {batch_file}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] MZmine execution failed for: {batch_file}\n{e}")
