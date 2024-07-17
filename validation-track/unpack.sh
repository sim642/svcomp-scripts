#!/bin/bash

# https://unix.stackexchange.com/questions/168807/mount-zip-file-as-a-read-only-filesystem:
# * fuse-zip
# * archivemount
# * fuse-archive
# * ratarmount

# fuse-zip -r svcomp24-witnesses.zip svcomp24-witnesses

# unzip svcomp24-results.zip 'results-verified/*fileHashes.json.gz'

./unpackFileStoresYamlWitness.py -o yaml-witnesses results-verified/*fileHashes.json.gz
