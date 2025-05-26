# ╭──────────────────────────────────────────────────────────────────────────╮
# │             03_sirius_annotation.py                                      │
# │ Run SIRIUS CLI with mode-specific adduct and structure search settings.  │
# ╰──────────────────────────────────────────────────────────────────────────╯

"""
Runs SIRIUS in headless mode for both positive and negative ionization mode MGF files.

Performs formula prediction, Zodiac scoring, fingerprinting, and structure search.
Also handles logging of commands and output in real-time for reproducibility.

Requirements:
- SIRIUS installed and accessible via command line
- User must be logged in via `sirius login` (credentials cached in ~/.sirius/)
- Input MGF files in `03_analysis/mzmine/pos|neg/export_sirius.mgf`
- Python packages: subprocess, select, pathlib, glob, os
"""

# ─────────────────────────────
# Imports
# ─────────────────────────────
import os
import glob
import subprocess
import select
from pathlib import Path

# ─────────────────────────────
# Ensure login to SIRIUS
# ─────────────────────────────

# Prompts for credentials if not logged in.
# Also checks SIRIUS installation via `--version`.
# If you're already logged in, this runs quickly and silently.
subprocess.run("sirius login && sirius --version", shell=True, check=True)

# ─────────────────────────────
# Configuration
# ─────────────────────────────

wd = Path("/path/to/02_metaboloimcs").resolve()
os.chdir(wd)

sirius_path = wd / "03_analysis" / "sirius"
pos_output_dir = sirius_path / "pos"
neg_output_dir = sirius_path / "neg"
log_dir = sirius_path / "log"
input_dir = wd / "03_analysis" / "mzmine"

# Create output/log directories
for path in [pos_output_dir, neg_output_dir, log_dir]:
    path.mkdir(parents=True, exist_ok=True)

log_pos_stdout = log_dir / "output_stdout_pos.txt"
log_pos_stderr = log_dir / "output_stderr_pos.txt"
log_neg_stdout = log_dir / "output_stdout_neg.txt"
log_neg_stderr = log_dir / "output_stderr_neg.txt"
command_log_file = log_dir / "commands_used.txt"

# ─────────────────────────────
# SIRIUS settings
# ─────────────────────────────

common_config = {
    "IsotopeSettings.filter": "true",
    "FormulaSearchDB": "",
    "Timeout.secondsPerTree": "1800",
    "FormulaSettings.enforced": "HCNOP",
    "Timeout.secondsPerInstance": "1800",
    "UseHeuristic.mzToUseHeuristicOnly": "650",
    "AlgorithmProfile": "orbitrap",
    "IsotopeMs2Settings": "IGNORE",
    "MS2MassDeviation.allowedMassDeviation": "10.0ppm",
    "NumberOfCandidatesPerIon": "1",
    "UseHeuristic.mzToUseHeuristic": "300",
    "FormulaSettings.detectable": "B,Cl,Br,Se,S",
    "NumberOfCandidates": "10",
    "ZodiacNumberOfConsideredCandidatesAt300Mz": "10",
    "ZodiacRunInTwoSteps": "true",
    "ZodiacEdgeFilterThresholds.minLocalConnections": "10",
    "ZodiacEdgeFilterThresholds.thresholdFilter": "0.95",
    "ZodiacEpochs.burnInPeriod": "2000",
    "ZodiacEpochs.numberOfMarkovChains": "10",
    "ZodiacNumberOfConsideredCandidatesAt800Mz": "50",
    "ZodiacEpochs.iterations": "20000",
    "FormulaResultThreshold": "true",
    "InjectElGordoCompounds": "true",
    "StructureSearchDB": "BIO,METACYC,CHEBI,COCONUT,ECOCYCMINE,GNPS,HMDB,HSDB,KEGG,KEGGMINE,KNAPSACK,MACONDA,MESH,NORMAN,UNDP,PLANTCYC,PUBCHEM,PUBMED,YMDB,YMDBMINE,ZINCBIO"
}

pos_config = {
    "input_file": input_dir / "pos" / "export_sirius.mgf",
    "output_dir": pos_output_dir,
    "adduct_settings_detectable": "[[M-H2O+H]+,[M+H]+,[M+Na]+,[M-H4O2+H]+,[M+H3N+H]+,[M+K]+]",
    "adduct_settings_fallback": "[[M+H]+,[M+Na]+,[M+K]+]",
    "log_stdout": log_pos_stdout,
    "log_stderr": log_pos_stderr
}

neg_config = {
    "input_file": input_dir / "neg" / "export_sirius.mgf",
    "output_dir": neg_output_dir,
    "adduct_settings_detectable": "[[M+Cl]-,[M+Br]-,[M-H2O-H]-,[M-H]-]",
    "adduct_settings_fallback": "[[M+Br]-,[M+Cl]-,[M-H]-]",
    "log_stdout": log_neg_stdout,
    "log_stderr": log_neg_stderr
}

# ─────────────────────────────
# Helper functions
# ─────────────────────────────

def build_command(config, common_config, cores=4, recompute=False):
    """Build the SIRIUS CLI command for a given mode and config."""
    command = [
        "sirius",
        f"--cores={cores}",
        f"-i={config['input_file']}",
        f"-o={config['output_dir']}",
        "config"
    ]
    for key, value in common_config.items():
        command.append(f"--{key}={value}")
    command.append(f"--AdductSettings.detectable={config['adduct_settings_detectable']}")
    command.append(f"--AdductSettings.fallback={config['adduct_settings_fallback']}")
    command.extend(["zodiac", "fingerprint", "structure", "canopus", "write-summaries"])
    return command

def run_command(command, stdout_log, stderr_log, command_log):
    """Run the command and log stdout/stderr in real-time."""
    with open(stdout_log, "w") as stdout_file, open(stderr_log, "w") as stderr_file, open(command_log, "a") as cmd_log:
        cmd_log.write(" ".join(map(str, command)) + "\n")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        while True:
            reads = [process.stdout.fileno(), process.stderr.fileno()]
            ret = select.select(reads, [], [])
            for fd in ret[0]:
                if fd == process.stdout.fileno():
                    read = process.stdout.readline()
                    if read:
                        print(read, end="")
                        stdout_file.write(read)
                        stdout_file.flush()
                elif fd == process.stderr.fileno():
                    read = process.stderr.readline()
                    if read:
                        print(read, end="")
                        stderr_file.write(read)
                        stderr_file.flush()
            if process.poll() is not None:
                break

# ─────────────────────────────
# Run annotation
# ─────────────────────────────

pos_command = build_command(pos_config, common_config, cores=24)
neg_command = build_command(neg_config, common_config, cores=24)

run_command(pos_command, pos_config["log_stdout"], pos_config["log_stderr"], command_log_file)
run_command(neg_command, neg_config["log_stdout"], neg_config["log_stderr"], command_log_file)
