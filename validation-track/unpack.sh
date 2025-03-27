#!/bin/bash

# https://unix.stackexchange.com/questions/168807/mount-zip-file-as-a-read-only-filesystem:
# * fuse-zip
# * archivemount
# * fuse-archive
# * ratarmount

mkdir svcomp25-witnesses
fuse-zip -r svcomp25-witnesses.zip svcomp25-witnesses

unzip svcomp25-results.zip 'results-verified/*fileHashes.json.gz'

./unpackFileStoresYamlWitness.py -o yaml-witnesses results-verified/*fileHashes.json.gz
