# Troubleshooting log

Running log of issues hit while setting up this recipe, and how they were
resolved. Add to this file as new issues come up.

---

## `ProductNotFound` for `GlobalAlgBlk` / `GlobalExtBlk` / L1T objects

**Symptom:** cmsRun fails trying to read L1T raw digi collections.

**Cause:** the input MiniAOD doesn't retain L1T raw digi collections at
all. Not every MiniAOD campaign keeps them.

**Check:**
```bash
edmDumpEventContent your_file.root | grep -i l1t
```
If nothing relevant shows up, this recipe cannot recover L1T info from
this particular MiniAOD — the digis were dropped at MiniAOD-production
time and aren't recoverable without going back to RAW.

---

## CRAB `outLFNDirBase` / `storageSite` mismatch

**Symptom:** confusion about where output actually lands, or write
failures.

**Cause:** `outLFNDirBase` must be a logical file name starting with
`/store/...`, never a physical path like `/eos/cms/store/...`. It must
also correspond to the site named in `storageSite` — e.g.
`/store/group/dpg_trigger/...` lives at `T2_CH_CERN`, not
`T3_CH_CERNBOX` (a different storage backend, personal CERNBox space
under `/store/user/<username>/...` only).

**Fix:** match LFN prefix to the actual site, and verify before
submitting:
```bash
crab checkwrite --site=T2_CH_CERN --lfn=/store/group/<your/path>
```

---

## CRAB memory warning: "jobs may not find a site... stay idle forever"

**Symptom:**
```
Task requests 3000 MB of memory, but only 2500 are guaranteed to be
available. Jobs may not find a site where to run and stay idle forever.
```

**Cause:** `config.JobType.maxMemoryMB` set above what's guaranteed per
core at most sites for `numCores=1`.

**Fix:** lower `maxMemoryMB` (2000–2500 MB is normally plenty for this
L1T-unpacking-only workload — it's not doing heavy PF reclustering).

---

## `crab submit --dryrun` estimated job time looks absurd (e.g. "2240 minutes")

**Cause:** the dry-run estimate extrapolates from the local
`preparelocal` test job, which by default only processes a handful of
events (not a full file). Fixed startup overhead (conditions/GT
loading) dominates that small sample, so scaling it up to "per file"
badly overestimates.

**Fix:** ignore the dry-run time estimate; measure for real instead:
```bash
time cmsRun customl1nano.py   # on a full file, no maxEvents limit
```
and use that to size `unitsPerJob`.

---

## `UnknownUserFloat: pileupJetIdPuppi:fullDiscriminant is not available`

**Symptom:** crash in `jetPuppiTable` when processing early Run3 (2022,
`12_4_x`-produced) MiniAOD with `-s NANO:@PHYS+@L1FULL`.

**Cause:** that PUPPI jet pileup-ID discriminant was added to standard
MiniAOD/NanoAOD jet content later in the Run3 campaign. Early-Run3
MiniAOD doesn't have it.

**Fix:** add the era modifier for pre-content-change Run3 MiniAOD:
```
--era Run3,run3_nanoAOD_pre142X
```

---

## `pat::Tau: the ID byVVVLooseDeepTau2018v2p5VSjet can't be found`

**Symptom:** crash in `boostedTauTable` / `finalTaus` selector, also on
early Run3 (2022) MiniAOD, even with `run3_nanoAOD_pre142X` added.

**Cause:** discretized DeepTau v2p5 working-point IDs were embedded into
MiniAOD later in the Run3 campaign; 2022 MiniAOD only has the **raw
score** (`byDeepTau2018v2p5VSjetraw`), not the discretized WP booleans.
NanoAOD's tau-table code only auto-recomputes these for the Run2-UL era
modifier (`run2_nanoAOD_106Xv2`) — for Run3 (with or without
`run3_nanoAOD_pre142X`) it assumes the WPs are already embedded in the
input MiniAOD.

**Two options:**

1. **If you don't need standard `@PHYS` object content** (jets, taus,
   muons, etc.) and only want L1T branches: drop `@PHYS` entirely and
   run `-s NANO:@L1FULL` alone. This avoids scheduling the jet/tau/etc.
   table producers altogether, sidestepping this whole class of
   era-content mismatch issues (this one and the jet one above, and
   likely others not yet hit for 2022).

2. **If you do need full `@PHYS` content:** force re-embedding of the
   missing tau IDs from the raw score via a small customize function
   (untested against the full 2022 chain as of this writing — treat as
   a starting point):
   ```python
   # customizeTauID2022.py
   def addMissingTauIDs(process):
       from PhysicsTools.NanoAOD.nano_cff import nanoAOD_addTauIds
       process = nanoAOD_addTauIds(process, idsToRun=["deepTau2018v2p5"],
                                    addPNetCHS=False, addUParTPuppi=False)
       return process
   ```
   added via `--customise customizeTauID2022.addMissingTauIDs`. Leave
   `addPNetCHS`/`addUParTPuppi` as `False` here since
   `run3_nanoAOD_pre142X` already triggers those separately elsewhere in
   the standard NanoAOD customization — re-running them here risks a
   module-name collision.

See [`docs/2022-notes.md`](2022-notes.md) for the live status of getting
the full 2022 (C–G) batch working.
