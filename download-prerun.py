import requests
import lxml.html
import re
import shutil
import os
import argparse
from dataclasses import dataclass
from typing import List, Set
from urllib.parse import unquote

from rich.console import Group
from rich.live import Live
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn, MofNCompleteColumn


# https://stackoverflow.com/a/43357954/854540
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')



parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=2026)
parser.add_argument("--verifier", type=str, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--download-verifier-xmls", type=str2bool, default=True)
parser.add_argument("--download-verifier-tables", type=str2bool, default=True)
parser.add_argument("--download-verifier-logs", type=str2bool, default=True)
parser.add_argument("--download-validator-xmls", type=str2bool, default=True)
parser.add_argument("--download-validator-logs", type=str2bool, default=True)
args = parser.parse_args()

# TODO: lowercase
BASE_URL = f"https://sv-comp.sosy-lab.org/{args.year}/results"
DATA_DIR = args.output
short_year = args.year % 100


os.makedirs(DATA_DIR)
if args.download_verifier_xmls or args.download_verifier_tables or args.download_verifier_logs:
    os.makedirs(f"{DATA_DIR}/results-verified")
if args.download_validator_xmls or args.download_validator_logs:
    os.makedirs(f"{DATA_DIR}/results-validated")

http_errors_file = open(f"{DATA_DIR}/http-errors.log", "w")

@dataclass(frozen=True)
class ToolRun:
    tool: str
    date: str
    run_definition: str
    task_set: str
    fixed: bool
    validator: bool

@dataclass(frozen=True)
class MetaRun:
    tool: str
    task_set: str

@dataclass(frozen=True)
class ValidatorRun:
    verifier: str
    kind: str
    version: str
    validator: str
    date: str


download_progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None),
    TaskProgressColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
)

def download(url, filename):
    print(f"Download {url}")
    download_task = download_progress.add_task(filename[-30:], start=False)
    with requests.get(url, stream=True) as response:
        # sosy-lab.org returns html tables also with HTTP compression, but streaming requests doesn't decompress it like any normal HTTP downloader by default
        # https://github.com/psf/requests/issues/2155#issuecomment-287628933
        response.raw.decode_content = True
        try:
            response.raise_for_status()
            download_progress.update(download_task, total=int(response.headers["Content-length"]))
            download_progress.start_task(download_task)
            with download_progress.wrap_file(response.raw, task_id=download_task) as f0, open(filename, "wb") as f:
                shutil.copyfileobj(f0, f)
        except requests.exceptions.HTTPError as e:
            http_errors_file.write(f"{e}\n")
        download_progress.update(download_task, visible=False)

def download2(filename):
    url = f"{BASE_URL}/{filename}"
    download(url, f"{DATA_DIR}/{filename}")



get_verifier_runs_re = re.compile(r"([\w%-]+)\.(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.results\.(SV-COMP\d{2}_[\w-]+).([\w.-]+?).xml.bz2(.fixed.xml.bz2)?.table.html")
get_verifier_runs_meta_re = re.compile(r"META_([\w.-]+?)_([\w%-]+)\.table\.html")
get_validator_runs_loose_re = re.compile(r""""href": "..\/results-validated\/.*?.logfiles""")
get_validator_runs_re = re.compile(r""""href": "..\/results-validated\/([\w%.-]+)-validate-(violation|correctness)-witnesses-([12].0)-([\w%.-]+).(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).logfiles""")

def get_all_verifier_runs() -> tuple[List[ToolRun], List[MetaRun]]:
    with requests.get(f"{BASE_URL}/results-verified/results-per-tool.php") as response:
        tree = lxml.html.fromstring(response.text)
        ret = []
        ret_meta = []
        for a_elem in tree.xpath("//a"):
            m = get_verifier_runs_re.fullmatch(a_elem.text)
            if m:
                tool = m.group(1)
                date = m.group(2)
                run_definition = m.group(3)
                task_set = m.group(4)
                fixed = m.group(5) is not None
                ret.append(ToolRun(tool=tool, date=date, run_definition=run_definition, task_set=task_set, fixed=fixed, validator=False))

            m = get_verifier_runs_meta_re.fullmatch(a_elem.text)
            if m:
                task_set = m.group(1)
                tool = m.group(2)
                ret_meta.append(MetaRun(tool=tool, task_set=task_set))

        return (ret, ret_meta)

def get_verifier_runs(verifier: str) -> tuple[List[ToolRun], List[MetaRun]]:
    runs, meta_runs = get_all_verifier_runs()
    return ([tool_run for tool_run in runs if tool_run.tool == verifier], [meta_run for meta_run in meta_runs if meta_run.tool == verifier])

def get_validator_runs(tool_run: ToolRun) -> Set[ValidatorRun]:
    def get_validator_runs_table(table_filename):
        with open(f"{DATA_DIR}/results-verified/{table_filename}", "r") as f:
            ret = set()
            for m in get_validator_runs_loose_re.finditer(f.read()):
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

    filename = f"{tool_run.tool}.{tool_run.date}.results.{tool_run.run_definition}.{tool_run.task_set}.xml.bz2{'.fixed.xml.bz2' if tool_run.fixed else ''}.table.html"
    # TODO: used to find validator runs from both fixed and unfixed HTML, does the latter ever exist? should it be added back?
    return get_validator_runs_table(filename)

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

def download_tool_run_logs(filename: str, validator: bool):
    if validator:
        download2(f"results-validated/{filename}")
    else:
        download2(f"results-verified/{filename}")

# These were old full tables:
# if args.download_verifier_tables:
#     download2(f"results-verified/{args.verifier}.results.SV-COMP{short_year}.table.html")

verifier_runs, meta_runs = get_verifier_runs(args.verifier) # TODO: progress
if args.download_verifier_tables: # TODO: progress
    for meta_run in meta_runs:
        download2(f"results-verified/META_{meta_run.task_set}_{meta_run.tool}.table.html")

verifier_progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    TimeRemainingColumn(elapsed_when_finished=True),
)

 # TODO: with
live = Live(Group(download_progress, verifier_progress), refresh_per_second=10, transient=False,)
live.start()

if args.download_verifier_xmls:
    # TODO: why doesn't verifier_progress.track work? (stays at 0)
    verifier_xmls_task = verifier_progress.add_task("Verifier XMLs", total=len(verifier_runs))
    for tool_run in verifier_runs:
        download_tool_run_xml(tool_run, fixed=False)
        download_tool_run_xml(tool_run, fixed=True)
        verifier_progress.advance(verifier_xmls_task)

if args.download_verifier_tables:
    # TODO: why doesn't verifier_progress.track work? (stays at 0)
    verifier_tables_task = verifier_progress.add_task("Verifier tables", total=len(verifier_runs))
    for tool_run in verifier_runs:
        download_tool_run_table(tool_run)
        verifier_progress.advance(verifier_tables_task)

if args.download_verifier_logs:
    # TODO: why doesn't verifier_progress.track work? (stays at 0)
    verifier_logs = set(f"{tool_run.tool}.{tool_run.date}.logfiles.zip" for tool_run in verifier_runs)
    verifier_logs_task = verifier_progress.add_task("Verifier logs", total=len(verifier_logs))
    for filename in verifier_logs:
        download_tool_run_logs(filename, validator=False)
        verifier_progress.advance(verifier_logs_task)

if args.download_validator_xmls or args.download_validator_logs:
    validator_runs = []
    for tool_run in verifier_runs:
        # TODO: progress
        for a in get_validator_runs(tool_run): # TODO: check that tables are downloaded
            tool = f"{a.validator}-validate-{a.kind}-witnesses-{a.version}-{a.verifier}"
            validator_tool_run = ToolRun(tool=tool, date=a.date, run_definition=tool_run.run_definition, task_set=tool_run.task_set, fixed=False, validator=True)
            # print(f"  {a}")
            # print(f"    {validator_tool_run}")
            validator_runs.append(validator_tool_run)

    if args.download_validator_xmls:
        validator_xmls_task = verifier_progress.add_task("Validator XMLs", total=len(validator_runs))
        for validator_tool_run in validator_runs:
            download_tool_run_xml(validator_tool_run, fixed=False)
            verifier_progress.advance(validator_xmls_task)
            # download_tool_run_table(validator_tool_run, validator=True)

    if args.download_validator_logs:
        validator_logs = set(f"{tool_run.tool}.{tool_run.date}.logfiles.zip" for tool_run in validator_runs)
        validator_logs_task = verifier_progress.add_task("Validator logs", total=len(validator_logs))
        for filename in validator_logs:
            download_tool_run_logs(filename, validator=True)
            verifier_progress.advance(validator_logs_task)

live.stop()
