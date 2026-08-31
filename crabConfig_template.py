"""
CRAB config template for L1T NanoAOD-from-MiniAOD reprocessing.

Copy this per dataset (or use submit_all.py to loop over several
datasets programmatically instead of hand-editing per-dataset copies).

Fill in every <PLACEHOLDER> before submitting.
"""

from CRABClient.UserUtilities import config
config = config()

config.General.requestName     = '<UNIQUE_REQUEST_NAME>'   # e.g. L1TNano_Muon0_Run2025B_v1 -- must be unique per task
config.General.workArea        = 'crab_projects'
config.General.transferOutputs = True
config.General.transferLogs    = False

config.JobType.pluginName  = 'Analysis'
config.JobType.psetName    = 'customl1nano.py'   # the cmsDriver.py-generated PSet
config.JobType.maxMemoryMB = 2500                # keep <= site-guaranteed default (commonly 2500 for numCores=1)
config.JobType.numCores    = 1
config.JobType.allowUndistributedCMSSW = True    # helps if worker-node CMSSW distribution lags for a very recent release

config.Data.inputDataset = '<DATASET, e.g. /Muon0/Run2025B-PromptReco-v1/MINIAOD>'
config.Data.inputDBS     = 'global'

config.Data.splitting   = 'FileBased'   # or 'LumiBased' if you have a lumiMask ready
config.Data.unitsPerJob = 50            # size this from `time cmsRun customl1nano.py` on a full file, not the crab --dryrun estimate
# config.Data.lumiMask  = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions25/Cert_Collisions2025_<...>_Golden.json'

config.Data.outLFNDirBase    = '/store/group/<your/group/output/path>'   # LFN, must start with /store/... -- NOT a physical /eos/... path
config.Data.publication      = False
config.Data.outputDatasetTag = '<TAG, e.g. L1TNano_v1>'

config.Site.storageSite = '<SITE, e.g. T2_CH_CERN>'   # must match the actual storage backend behind outLFNDirBase
