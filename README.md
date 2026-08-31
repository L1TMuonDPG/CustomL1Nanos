# L1T NanoAOD Reprocessing from MiniAOD

Recipe + CRAB tooling to add L1T information to Data/MC samples that were produced without it, by re-deriving L1T branches from the L1T raw digis stored in MiniAOD and writing them out as extra NanoAOD branches.

Based on:
https://github.com/cms-sw/cmssw/tree/master/DPGAnalysis/L1TNanoAOD

---

## 1. Setup environment

```bash
cmsrel CMSSW_15_0_5
cd CMSSW_15_0_5/src/
cmsenv
git cms-init
git cms-addpkg DPGAnalysis/L1TNanoAOD
scram b -j8
cmsenv
mkdir CustomL1Nanos && cd CustomL1Nanos
```

Note: Make sure to use CMSSW release that corresponds to the dataset you want to process 

---

## 2. Generate the cmsRun config (PSet)

### For data produced in the same content-era as the release (validated: 2025B)

```bash
cmsDriver.py customL1toNANO --conditions auto:run3_data_prompt \
  -s NANO:@PHYS+@L1FULL \
  --datatier NANOAOD --eventcontent NANOAOD \
  --data --process customl1nano --scenario pp --era Run3 \
  --customise_unsch Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
  -n 100 \
  --filein /store/data/<run_path>/<file>.root \
  --fileout file:out.root \
  --python_filename=customl1nano.py
```

Notes:
- `-s NANO:@PHYS+@L1FULL` gives you both the standard NanoAOD physics-object content **and** the L1T branches. If you only need L1T info (no jets, muons, taus, etc. from the standard NanoAOD content), use `-s NANO:@L1FULL` alone — this avoids a whole class of era-content compatibility issues.
- `--conditions auto:run3_data_prompt` is a symbolic global tag that  resolves conditions by run-number (IOV), so — as confirmed against a real production example spanning 2022–2025 — it works correctly across the whole Run3 data-taking period, not just "current" data. You do not need a different GT per era.

### Local validation before touching CRAB

Always test on one file first:
```bash
cmsRun customl1nano.py
time cmsRun customl1nano.py    # full-file timing, informs CRAB unitsPerJob later
edmDumpEventContent out.root | grep -i l1t   # confirm L1 branches present & populated
```

---

## 3. CRAB submission

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

## 5. Datasets processed so far

| Dataset | Release | Recipe | Status |
|---|---|---|---|
| `/Muon0/Run2025B-PromptReco-v1/MINIAOD` | CMSSW_15_0_5 | `@PHYS+@L1FULL`, era `Run3` | ✅ Validated, submitted to CRAB |
| `/Muon1/Run2025B-PromptReco-v1/MINIAOD` | CMSSW_15_0_5 | same as above | Submitted |

---

## 6. Troubleshooting reference

See [`docs/troubleshooting.md`](docs/troubleshooting.md) for known issues and fixes encountered so far (missing L1T raw collections, era-contentmismatches, CRAB memory/site issues, etc.).
