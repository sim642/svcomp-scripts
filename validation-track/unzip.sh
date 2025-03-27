#!/bin/bash

# https://zenodo.org/records/15012085
# For some reason they are gzipped as well
unzip -j svcomp25-results.zip results-validated/witness-database.csv.gz results-validated/witness-classification.csv.gz

gunzip witness-database.csv.gz witness-classification.csv.gz

unzip svcomp25-results.zip 'results-verified/*fileHashes.json.gz' 'results-validated/*fileHashes.json.gz'
