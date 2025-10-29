import requests
import lxml.html
import re
import shutil
import os
import argparse
from dataclasses import dataclass
from typing import List, Set
from urllib.parse import unquote


parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=2026)
parser.add_argument("--verifier", type=str, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--download-verifier-xmls", type=bool, default=True)
parser.add_argument("--download-verifier-tables", type=bool, default=True)
parser.add_argument("--download-verifier-logs", type=bool, default=True)
parser.add_argument("--download-validator-xmls", type=bool, default=True)
args = parser.parse_args()

# TODO: lowercase
BASE_URL = f"https://sv-comp.sosy-lab.org/{args.year}/results"
DATA_DIR = args.output
short_year = args.year % 100


os.makedirs(DATA_DIR)
os.makedirs(f"{DATA_DIR}/results-verified")
if args.download_validator_xmls:
    os.makedirs(f"{DATA_DIR}/results-validated")

@dataclass(frozen=True)
class ToolRun:
    tool: str
    date: str
    run_definition: str
    task_set: str
    fixed: bool
    validator: bool

@dataclass(frozen=True)
class ValidatorRun:
    verifier: str
    kind: str
    version: str
    validator: str
    date: str

def download(url, filename):
    print(f"Download {url}")
    with requests.get(url, stream=True) as response:
        # sosy-lab.org returns html tables also with HTTP compression, but streaming requests doesn't decompress it like any normal HTTP downloader by default
        # https://github.com/psf/requests/issues/2155#issuecomment-287628933
        response.raw.decode_content = True
        response.raise_for_status()
        with open(filename, "wb") as f:
            shutil.copyfileobj(response.raw, f)

def download2(filename):
    url = f"{BASE_URL}/{filename}"
    download(url, f"{DATA_DIR}/{filename}")



get_verifier_runs_re = re.compile(r"([\w%-]+)\.(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.results\.(SV-COMP\d{2}_[\w-]+).([\w.-]+?).xml.bz2(.fixed.xml.bz2)?.table.html")
get_validator_runs_loose_re = re.compile(r""""href": "..\/results-validated\/.*?.logfiles""")
get_validator_runs_re = re.compile(r""""href": "..\/results-validated\/([\w%.-]+)-validate-(violation|correctness)-witnesses-([12].0)-([\w%.-]+).(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).logfiles""")

def get_all_verifier_runs() -> List[ToolRun]:
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
                fixed = m.group(5) is not None
                ret.append(ToolRun(tool=tool, date=date, run_definition=run_definition, task_set=task_set, fixed=fixed, validator=False))
        return ret

def get_verifier_runs(verifier: str) -> List[ToolRun]:
    return [tool_run for tool_run in get_all_verifier_runs() if tool_run.tool == verifier]

def get_validator_runs(tool_run: ToolRun) -> Set[ValidatorRun]:
    def get_validator_runs_table(table_filename):
        with requests.get(f"{BASE_URL}/results-verified/{table_filename}") as response:
            ret = set()
            for m in get_validator_runs_loose_re.finditer(response.text):
                m2 = get_validator_runs_re.fullmatch(m.group(0))
                assert m2 is not None, m.group(0)
                m = m2
                validator = unquote(m.group(1))
                kind = m.group(2)
                version = m.group(3)
                verifier = unquote(m.group(4))
                date = m.group(5)
                ret.add(ValidatorRun(validator=validator, kind=kind, version=version, date=date, verifier=verifier))
            return ret

    fixed = get_validator_runs_table(f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2.fixed.xml.bz2.table.html")
    unfixed = get_validator_runs_table(f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2.table.html")
    return fixed.union(unfixed)

def download_tool_run_xml(tool_run: ToolRun, fixed: bool):
    filename = f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2{'.fixed.xml.bz2' if tool_run.fixed and fixed else ''}"
    if tool_run.validator:
        download2(f"results-validated/{filename}")
    else:
        download2(f"results-verified/{filename}")

def download_tool_run_table(tool_run: ToolRun):
    filename = f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2{'.fixed.xml.bz2' if tool_run.fixed else ''}.table.html"
    if tool_run.validator:
        download2(f"results-validated/{filename}")
    else:
        download2(f"results-verified/{filename}")

def download_tool_run_logs(tool_run: ToolRun):
    filename = f"{tool_run.tool}.{tool_run.date}.logfiles.zip"
    if tool_run.validator:
        download2(f"results-validated/{filename}")
    else:
        download2(f"results-verified/{filename}")

if args.download_verifier_tables:
    download2(f"results-verified/{args.verifier}.results.SV-COMP{short_year}.table.html")

verifier_runs = get_verifier_runs(args.verifier)
downloaded_logs = False
for i, tool_run in enumerate(verifier_runs):
    print(f"{i + 1}/{len(verifier_runs)}: {tool_run}")
    if args.download_verifier_xmls:
        download_tool_run_xml(tool_run, fixed=False)
        download_tool_run_xml(tool_run, fixed=True)
    if args.download_verifier_tables:
        download_tool_run_table(tool_run)
    if args.download_verifier_logs and not downloaded_logs:
        download_tool_run_logs(tool_run) # TODO: check if logs with this timestamp actually exist when skipping
        downloaded_logs = True

    if args.download_validator_xmls:
        s = get_validator_runs(tool_run) # TODO: don't redownload table
        for a in s:
            tool = f"{a.validator}-validate-{a.kind}-witnesses-{a.version}-{a.verifier}"
            validator_tool_run = ToolRun(tool=tool, date=a.date, run_definition=tool_run.run_definition, task_set=tool_run.task_set, fixed=False, validator=True)
            print(f"  {a}")
            print(f"    {validator_tool_run}")
            download_tool_run_xml(validator_tool_run, fixed=False)
            # download_tool_run_table(validator_tool_run, validator=True)
            # TODO: download validator logs? maybe pointless if witnesses can't be downloaded, or maybe especially useful then
