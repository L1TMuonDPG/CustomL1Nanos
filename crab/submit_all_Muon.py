#!/usr/bin/env python3
"""
Submit CRAB tasks for several datasets in one go, using the CRAB Python
API (crabCommand) in isolated processes to avoid CMSSW memory caching errors.

Usage:
    source /cvmfs/cms.cern.ch/common/crab-setup.sh
    voms-proxy-init --voms cms --valid 168:00
    python3 submit_all.py            # dry run by default, see DRYRUN below
"""

from CRABAPI.RawCommand import crabCommand
from CRABClient.UserUtilities import config
from multiprocessing import Process

# Set to False once you've inspected the dry-run output for every entry
# and are ready to actually submit for real.
DRYRUN = True

PSET_NAME_2025 = "customl1nano_2025B.py"
PSET_NAME_2022 = "customl1nano_2022.py"
STORAGE_SITE   = "T2_CH_CERN"
UNITS_PER_JOB  = 50
MAX_MEMORY_MB  = 2500

DATASETS = [
    # 2025B
    {
        "requestName":   "L1TNano_Muon0_Run2025B",
        "inputDataset":  "/Muon0/Run2025B-PromptReco-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2025B",
        "pset":          PSET_NAME_2025
    },
    {
        "requestName":   "L1TNano_Muon1_Run2025B",
        "inputDataset":  "/Muon1/Run2025B-PromptReco-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2025B_Muon1",
        "pset":          PSET_NAME_2025
    },
    # 2022
    {
        "requestName":   "L1TNano_Muon_Run2022C",
        "inputDataset":  "/Muon/Run2022C-22Sep2023-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2022C",
        "pset":          PSET_NAME_2022
    },
    {
        "requestName":   "L1TNano_Muon_Run2022D",
        "inputDataset":  "/Muon/Run2022D-22Sep2023-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2022D",
        "pset":          PSET_NAME_2022
    },
    {
        "requestName":   "L1TNano_Muon_Run2022E",
        "inputDataset":  "/Muon/Run2022E-22Sep2023-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2022E",
        "pset":          PSET_NAME_2022
    },
    {
        "requestName":   "L1TNano_Muon_Run2022F",
        "inputDataset":  "/Muon/Run2022F-22Sep2023-v2/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2022F",
        "pset":          PSET_NAME_2022
    },
    {
        "requestName":   "L1TNano_Muon_Run2022G",
        "inputDataset":  "/Muon/Run2022G-22Sep2023-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/nplastir/Reprocess/2022G",
        "pset":          PSET_NAME_2022
    },
]

def build_config(entry):
    cfg = config()
    cfg.General.requestName     = entry["requestName"]
    cfg.General.workArea        = "crab_projects"
    cfg.General.transferOutputs = True
    cfg.General.transferLogs    = False

    cfg.JobType.pluginName  = "Analysis"
    cfg.JobType.psetName    = entry["pset"]
    cfg.JobType.maxMemoryMB = MAX_MEMORY_MB
    cfg.JobType.numCores    = 1
    cfg.JobType.allowUndistributedCMSSW = True

    cfg.Data.inputDataset = entry["inputDataset"]
    cfg.Data.inputDBS     = "global"
    cfg.Data.splitting    = "FileBased"
    cfg.Data.unitsPerJob  = UNITS_PER_JOB

    cfg.Data.outLFNDirBase    = entry["outLFNDirBase"]
    cfg.Data.publication      = False
    cfg.Data.outputDatasetTag = "L1TNano_v1"

    cfg.Site.storageSite = STORAGE_SITE
    return cfg

# This function will run isolated in its own process
def submit_task(cfg):
    try:
        crabCommand("submit", config=cfg, dryrun=DRYRUN)
    except Exception as e:
        print(f"FAILED for {cfg.General.requestName}: {e}")

def main():
    for entry in DATASETS:
        cfg = build_config(entry)
        print(f"\n=== Submitting: {entry['requestName']} ({entry['inputDataset']}) using {entry['pset']} ===")
        
        # Spawn a new process so the CMSSW config memory is cleared after submission
        p = Process(target=submit_task, args=(cfg,))
        p.start()
        p.join() # Wait for the process to finish before moving to the next dataset

    if DRYRUN:
        print("\nAll tasks submitted in dry-run mode. Inspect each with:")
        print("    crab status -d crab_projects/crab_<requestName>")
        print("Then set DRYRUN = False above and re-run to submit for real,")
        print("or run `crab proceed -d crab_projects/crab_<requestName>` per task.")

if __name__ == "__main__":
    main()