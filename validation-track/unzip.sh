#!/bin/bash

# https://zenodo.org/records/10669731
# For some reason they are gzipped as well
# unzip -j svcomp24-results.zip results-validated/witness-database.csv.gz results-validated/witness-classification.csv.gz

# gunzip witness-database.csv.gz witness-classification.csv.gz

unzip svcomp24-results.zip 'results-verified/*fileHashes.json.gz' 'results-validated/*fileHashes.json.gz'
