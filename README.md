# L1T NanoAOD Reprocessing from MiniAOD

Recipe and automated CRAB tooling to add L1T information to Data/MC samples that were produced without it. This re-derives L1T branches from the L1T raw digis stored in MiniAOD and writes them out as extra NanoAOD branches.

Based on: [DPGAnalysis/L1TNanoAOD](https://github.com/cms-sw/cmssw/tree/master/DPGAnalysis/L1TNanoAOD)

---

## 1. Setup Environment

```bash
cmsrel CMSSW_15_0_5
cd CMSSW_15_0_5/src/
cmsenv
git cms-init
git cms-addpkg DPGAnalysis/L1TNanoAOD
scram b -j8
cmsenv
git clone https://github.com/L1TMuonDPG/CustomL1Nanos.git
cd CustomL1Nanos
```

---

## 2. Generate the CMSSW Configurations

Because different eras require different Global Tags and era modifiers, we generate separate Python configurations for 2022 and 2025 data.

Run the bash script:

```bash
./generateConfigs.sh
```
This runs `cmsDriver.py` in the background and generates two files:
- `customl1nano_2025B.py` (Uses auto:run3_data_prompt)

- `customl1nano_2022.py` (Uses auto:run3_data and the run3_nanoAOD_pre142X modifier)

## 3. Local Validation

Always test locally before submitting to the grid. Ensure you have an active proxy to stream the test files:

```bash
voms-proxy-init --voms cms --valid 168:00
```
Open the configuration file and replace `file:customL1toNANO_PAT.root` with a MINIAOD file from a dataset that you want to run. 
For example:
- `customl1nano_2025B.py`: Replace it with `/store/data/Run2025B/Muon0/MINIAOD/PromptReco-v1/000/391/870/00000/5660d01e-f39b-453d-b1e0-616692224a2b.root`

- `customl1nano_2022.py`: Replace it with `/store/data/Run2022C/Muon/MINIAOD/22Sep2023-v1/2520000/b954c535-714a-475a-8aad-448b18503b04.root`

Note: For 2022, use the reprocessed samples with tag `22Sep2023` instead of the Prompt-Reco ones

You can quickly find a dataset to test with `dasgoclient`:

```bash
dasgoclient -query="file dataset=/Muon0/Run2025B-PromptReco-v1/MINIAOD" --limit=1
dasgoclient -query="file dataset=/Muon/Run2022C-22Sep2023-v1/MINIAOD" --limit=1
```

Run the configs (they are limited to 100 events):
```
cmsRun customl1nano_2025B.py
cmsRun customl1nano_2022.py
```

Verify the L1 branches exist in the output:
```bash
edmDumpEventContent out_2025.root
edmDumpEventContent out_2022.root  # confirm L1 branches present & populated
```

## 4. CRAB submission

Templates: [`crab/crabConfig_template.py`](crab/crabConfig_template.py) and
[`crab/submit_all.py`](crab/submit_all.py).

### Key config points

- `config.JobType.psetName` points at the `cmsDriver.py`-generated PSet  (e.g. `customl1nano.py`). Because it's a standard `PoolSource` config, CRAB automatically overrides `process.source.fileNames` per job — no edits needed to the PSet itself.
- `config.Data.outLFNDirBase` must be a **logical file name (LFN)**, always starting with `/store/...` — never a physical `/eos/...` path.
  CRAB maps the LFN to the physical location based on `storageSite`.
- `config.Site.storageSite` must match the actual storage backend behind your chosen `outLFNDirBase`. E.g. `/store/group/dpg_trigger/...` lives
  at `T2_CH_CERN`, **not** `T3_CH_CERNBOX` (personal CERNBox storage — different backend, only reachable under `/store/user/<username>/...`).
- Check write access to a group area *before* submitting:
  ```bash
  crab checkwrite --site=T2_CH_CERN --lfn=/store/group/<your/output/path>
  ```

### Submission workflow

```bash
source /cvmfs/cms.cern.ch/common/crab-setup.sh
voms-proxy-init --voms cms --valid 168:00

crab submit -c crabConfig.py --dryrun   # sanity-check job count/splitting first
crab proceed -d crab_projects/<task_dir>   # if dry run looks right, continue to real submission
```

`--dryrun` will print a rough time estimate based on the local test job —**ignore this estimate if it looks wildly large**; it's extrapolated from
however many events your local `preparelocal` test processed (often just
a handful), so fixed startup overhead (conditions loading, etc.) can
dominate and badly skew the extrapolation. Trust your own `time cmsRun`
measurement on a full file instead.

### Monitoring

```bash
crab status -d crab_projects/<task_dir>
crab resubmit -d crab_projects/<task_dir>     # for failed jobs
crab kill -d crab_projects/<task_dir>         # to stop a task
```
The status of the CRAB jobs can also be checked using mrCrabs. This will provide an overview of all the jobs submitted in the `crab_projects` folder
```
git clone git@github.com:CMS-L1T-Jet-Tagging/mrCrabs.git
python3 mrCrabs/mrCrabs.py crab_projects/<task_dir>
```

### Memory requests

Keep `config.JobType.maxMemoryMB` at or below what's guaranteed
per-core at most sites (commonly ~2500 MB for `numCores=1`). Requesting
more can leave jobs idle indefinitely waiting for a rare site that offers
more — watch for this warning in `crab status`:
```
Task requests 3000 MB of memory, but only 2500 are guaranteed to be
available. Jobs may not find a site where to run and stay idle forever.
```

### Splitting

- `FileBased` is simplest to reason about; `unitsPerJob` = files per job.
- `LumiBased` (needs a `lumiMask`/Golden JSON) only processes certified
  lumis — more efficient if you don't need uncertified data at all, at
  the cost of requiring the JSON to exist for your run range (may lag
  behind PromptReco for very recent data).
- Size `unitsPerJob` from your local `time cmsRun` measurement on a full
  file. This recipe is cheap (L1T unpacking, not full reco), so per-file
  time is typically well under a minute — batch generously.

---

## 4. Batch-submitting multiple datasets

Each CRAB task = one dataset, one unique `requestName`. See
[`crab/submit_all.py`](crab/submit_all.py) for a script that loops over a
list of `(requestName, inputDataset)` pairs and submits each via the
CRAB Python API (`crabCommand`), rather than hand-editing a config file
per dataset.

Confirm exact dataset names with DAS before adding them to the list:
```bash
dasgoclient -query="dataset dataset=/<primary>/<era>-<version>/MINIAOD"
```

---