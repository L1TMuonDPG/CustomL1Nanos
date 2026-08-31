#!/usr/bin/env python3
"""
Submit CRAB tasks for several datasets in one go, using the CRAB Python
API (crabCommand) instead of hand-editing crabConfig.py per dataset.

Usage:
    source /cvmfs/cms.cern.ch/common/crab-setup.sh
    voms-proxy-init --voms cms --valid 168:00
    python3 submit_all.py            # dry run by default, see DRYRUN below
"""

from CRABAPI.RawCommand import crabCommand
from CRABClient.UserUtilities import config
from httplib2 import Http

# Set to False once you've inspected the dry-run output for every entry
# and are ready to actually submit for real.
DRYRUN = True

# One entry per dataset. requestName must be unique across all your tasks.
DATASETS = [
    {
        "requestName":   "L1TNano_Muon0_Run2025B_v1",
        "inputDataset":  "/Muon0/Run2025B-PromptReco-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/<user>/Reprocess/2025B",
    },
    {
        "requestName":   "L1TNano_Muon1_Run2025B_v1",
        "inputDataset":  "/Muon1/Run2025B-PromptReco-v1/MINIAOD",
        "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/<user>/Reprocess/2025B_Muon1",
    },
    # Add more entries here, e.g. for the 2022 datasets once validated:
    # {
    #     "requestName":   "L1TNano_Muon_Run2022C_v1",
    #     "inputDataset":  "/Muon/Run2022C-PromptReco-v1/MINIAOD",
    #     "outLFNDirBase": "/store/group/dpg_trigger/comm_trigger/L1Trigger/<user>/Reprocess/2022C",
    # },
]

PSET_NAME     = "customl1nano.py"
STORAGE_SITE  = "T2_CH_CERN"
UNITS_PER_JOB = 50
MAX_MEMORY_MB = 2500


def build_config(entry):
    cfg = config()
    cfg.General.requestName     = entry["requestName"]
    cfg.General.workArea        = "crab_projects"
    cfg.General.transferOutputs = True
    cfg.General.transferLogs    = False

    cfg.JobType.pluginName  = "Analysis"
    cfg.JobType.psetName    = PSET_NAME
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


def main():
    for entry in DATASETS:
        cfg = build_config(entry)
        print(f"\n=== Submitting: {entry['requestName']} ({entry['inputDataset']}) ===")
        try:
            crabCommand("submit", config=cfg, dryrun=DRYRUN)
        except Exception as e:
            print(f"FAILED for {entry['requestName']}: {e}")
            continue

    if DRYRUN:
        print("\nAll tasks submitted in dry-run mode. Inspect each with:")
        print("    crab status -d crab_projects/crab_<requestName>")
        print("Then set DRYRUN = False above and re-run to submit for real,")
        print("or run `crab proceed -d crab_projects/crab_<requestName>` per task.")


if __name__ == "__main__":
    main()
