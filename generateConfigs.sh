#! /bin/bash

echo "--- Generating base configuration for customL1toNANO..."

cmsDriver.py customL1toNANO \
  --conditions auto:run3_data_prompt \
  -s NANO:@PHYS+@L1FULL \
  --datatier NANOAOD \
  --eventcontent NANOAOD \
  --data \
  --process customl1nano \
  --scenario pp \
  --era Run3 \
  --customise_unsch Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
  -n 100 \
  --fileout file:out_2025.root \
  --python_filename=customl1nano_2025B.py \
  --no_exec

echo "--- Done! Configuration for 2025B is ready."

cmsDriver.py customL1toNANO \
  --conditions auto:run3_data \
  -s NANO:@PHYS+@L1FULL \
  --datatier NANOAOD \
  --eventcontent NANOAOD \
  --data \
  --process customl1nano \
  --scenario pp \
  --era Run3,run3_nanoAOD_pre142X \
  --customise_unsch Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
  -n 100 \
  --fileout file:out_2022.root \
  --python_filename=customl1nano_2022.py \
  --no_exec

echo "--- Done! Configuration for 2022 is ready."