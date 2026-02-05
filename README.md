# Simmo's SV-COMP scripts
This repository is a dumping ground for various [SV-COMP]-related scripts from a participant's perspective.
This is unlike the official [competition-scripts] which are from an organizer's perspective.

[sv-comp]: https://sv-comp.sosy-lab.org/
[competition-scripts]: gitlab.com/sosy-lab/benchmarking/competition-scripts

## Scripts
For easy running use [uv].

[uv]: https://docs.astral.sh/uv/

### `download-prerun`
Downloads SV-COMP prerun results for one verifier.
By default, all data related to the verifier is downloaded: BenchExec results XMLs, BenchExec results HTMLs and logfiles for both the verifier and all of its validators.

```console
$ uv run download-prerun.py
usage: download-prerun.py [-h] [--year YEAR] --verifier VERIFIER --output OUTPUT
                          [--download-verifier-xmls DOWNLOAD_VERIFIER_XMLS]
                          [--download-verifier-tables DOWNLOAD_VERIFIER_TABLES]
                          [--download-verifier-logs DOWNLOAD_VERIFIER_LOGS]
                          [--download-validator-xmls DOWNLOAD_VALIDATOR_XMLS]
                          [--download-validator-logs DOWNLOAD_VALIDATOR_LOGS]
```

### Others
Undocumented and possibly not in working order anymore.
