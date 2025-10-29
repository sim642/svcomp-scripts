import requests
import lxml.html
import re
import shutil
import os
from dataclasses import dataclass
from typing import List, Set

BASE_URL = "https://sv-comp.sosy-lab.org/2026/results"
DATA_DIR = "data_svcomp26-2"
DRY_RUN = False

verifier = "goblint"

if not DRY_RUN:
    os.makedirs(DATA_DIR)
    os.makedirs(f"{DATA_DIR}/results-verified")
    os.makedirs(f"{DATA_DIR}/results-validated")

@dataclass(frozen=True)
class ToolRun:
    tool: str
    date: str
    run_definition: str
    task_set: str

@dataclass(frozen=True)
class ValidatorRun:
    verifier: str
    kind: str
    version: str
    validator: str
    date: str

def download(url, filename):
    print(f"Download {url}")
    if DRY_RUN:
        with requests.head(url) as response:
            response.raise_for_status()
    else:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(filename, "wb") as f:
                shutil.copyfileobj(response.raw, f)



get_verifier_runs_re = re.compile(r"([\w-]+)\.(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.results\.(SV-COMP26_[\w-]+).([\w.-]+?).xml.bz2(.fixed.xml.bz2)?.table.html")
get_validator_runs_re = re.compile(r""""href": "..\/results-validated\/([\w.-]+)-validate-(violation|correctness)-witnesses-([12].0)-([\w.-]+).(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).logfiles""")

def get_verifier_runs() -> List[ToolRun]:
    with requests.get(f"{BASE_URL}/results-verified/results-per-tool.php") as response:
        tree = lxml.html.fromstring(response.text)
        ret = []
        for a_elem in tree.xpath("//a"):
            m = get_verifier_runs_re.fullmatch(a_elem.text)
            if m:
                tool = m.group(1)
                date = m.group(2)
                run_definition = m.group(3)
                task_set = m.group(4)
                ret.append(ToolRun(tool=tool, date=date, run_definition=run_definition, task_set=task_set))
        return ret

def get_validator_runs(tool_run: ToolRun) -> Set[ValidatorRun]:
    def get_validator_runs_table(table_filename):
        with requests.get(f"{BASE_URL}/results-verified/{table_filename}") as response:
            ret = set()
            for m in get_validator_runs_re.finditer(response.text):
                validator = m.group(1)
                kind = m.group(2)
                version = m.group(3)
                verifier = m.group(4)
                date = m.group(5)
                ret.add(ValidatorRun(validator=validator, kind=kind, version=version, date=date, verifier=verifier))
            return ret

    fixed = get_validator_runs_table(f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2.fixed.xml.bz2.table.html")
    unfixed = get_validator_runs_table(f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2.table.html")
    return fixed.union(unfixed)

def download_tool_run_xml(tool_run: ToolRun, validator: bool):
    filename = f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2"
    if validator:
        url = f"{BASE_URL}/results-validated/{filename}"
        download(url, f"{DATA_DIR}/results-validated/{filename}")
    else:
        url = f"{BASE_URL}/results-verified/{filename}"
        download(url, f"{DATA_DIR}/results-verified/{filename}")

verifier_runs = get_verifier_runs()
for i, tool_run in enumerate(verifier_runs):
    if tool_run.tool != verifier:
        continue

    print(f"{i + 1}/{len(verifier_runs)}: {tool_run}")
    download_tool_run_xml(tool_run, validator=False)

    s = get_validator_runs(tool_run)
    for a in s:
        tool = f"{a.validator}-validate-{a.kind}-witnesses-{a.version}-{a.verifier}"
        validator_tool_run = ToolRun(tool=tool, date=a.date, run_definition=tool_run.run_definition, task_set=tool_run.task_set)
        print(f"  {a}")
        print(f"    {validator_tool_run}")
        download_tool_run_xml(validator_tool_run, validator=True)


