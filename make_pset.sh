#!/usr/bin/env bash
# Generate the cmsRun PSet (customl1nano.py) for L1T NanoAOD-from-MiniAOD
# reprocessing. Validated for 2025B / CMSSW_15_0_5.
#
# Usage:
#   ./make_pset.sh /store/data/Run2025B/Muon0/MINIAOD/PromptReco-v1/.../file.root
#
# For 2022 datasets, see docs/2022-notes.md -- this script's defaults are
# NOT yet validated for that era (era modifiers / content flags differ,
# see docs/troubleshooting.md).

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input MiniAOD LFN, e.g. /store/data/...>"
    exit 1
fi

FILEIN="$1"
NEVENTS="${2:-100}"
OUTNAME="${3:-out.root}"
PSETNAME="${4:-customl1nano.py}"

cmsDriver.py customL1toNANO \
  --conditions auto:run3_data_prompt \
  -s NANO:@PHYS+@L1FULL \
  --datatier NANOAOD --eventcontent NANOAOD \
  --data --process customl1nano --scenario pp --era Run3 \
  --customise_unsch Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
  -n "${NEVENTS}" \
  --filein "${FILEIN}" \
  --fileout "file:${OUTNAME}" \
  --python_filename="${PSETNAME}"

echo "Generated ${PSETNAME}. Test it with:"
echo "  cmsRun ${PSETNAME}"
echo "  time cmsRun ${PSETNAME}   # full-file timing for CRAB unitsPerJob sizing"
echo "  edmDumpEventContent ${OUTNAME} | grep -i l1t"
