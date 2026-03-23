#!/bin/bash

# Unpacks YAML witnesses.

# https://unix.stackexchange.com/questions/168807/mount-zip-file-as-a-read-only-filesystem:
# * fuse-zip
# * archivemount
# * fuse-archive
# * ratarmount

mkdir svcomp26-witnesses
fuse-zip -r svcomp26-witnesses.zip svcomp26-witnesses

unzip svcomp26-results.zip 'results-verified/*fileHashes.json.gz'

./unpackFileStoresYamlWitness.py -o yaml-witnesses results-verified/*fileHashes.json.gz

umount svcomp26-witnesses
