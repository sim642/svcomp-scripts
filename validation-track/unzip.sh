#!/bin/bash

# Unzips witness-database and witness-classification.

# https://zenodo.org/records/18651757
# For some reason they are gzipped as well
unzip -j svcomp26-results.zip results-validated/witness-database.csv.gz results-validated/witness-classification.csv.gz

gunzip witness-database.csv.gz witness-classification.csv.gz

# TODO: what are these for here?
# unzip svcomp26-results.zip 'results-verified/*fileHashes.json.gz' 'results-validated/*fileHashes.json.gz'
