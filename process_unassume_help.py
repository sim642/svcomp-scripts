from lxml import etree
import bz2
from pathlib import Path
import collections
import csv
import re

DATA_DIR = "data4"

def load_run_results(filename):
    with bz2.open(filename) as f:
        tree = etree.parse(f)

        ret = {}
        for run in tree.xpath("""//run"""):
            name = run.get("name")
            properties = run.get("properties")
            expected_verdict = run.get("expectedVerdict")
            status_column = run.find("""column[@title="status"]""")
            if status_column is not None:
                status = status_column.get("value")
            else:
                status = None
            ret[(name, properties, expected_verdict)] = status
        return ret

def load_tool_results(tool):
    ret = {}
    for file in Path(f"{DATA_DIR}/").glob(f"{tool}.*.results.*.xml.bz2"):
        ret |= load_run_results(file)
    return ret

def get_unassume_help_results(goblint_verifier_results, validator_results):
    results = set()
    for task, validator_status in validator_results.items():
        if task in goblint_verifier_results:
            goblint_verifier_status = goblint_verifier_results[task]
        else:
            goblint_verifier_status = None

        _, _, expected_verdict = task
        if goblint_verifier_status != expected_verdict and validator_status == expected_verdict:
            results.add((task, goblint_verifier_status))
    return results

# verifiers = ["goblint", "mopsa", "uautomizer", "cpachecker"]
# validators = verifiers

get_verifiers_re = re.compile(r"([\w.-]+)\.(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.results\.(SV-COMP24_[\w-]+).([\w.-]+?).xml.bz2")
get_validators_re = re.compile(r"([\w.-]+-validate-(violation|correctness)-witnesses-[12].0)-([\w.-]+)")

def get_verifiers():
    ret = set()
    for file in Path(f"{DATA_DIR}/").glob(f"*.results.*.xml.bz2"):
        m = get_verifiers_re.fullmatch(file.name)
        if m:
            verifier = m.group(1)
            if "witnesses" not in verifier:
                ret.add(verifier)
    return ret

def get_validators(verifier0):
    ret = set()
    for file in Path(f"{DATA_DIR}/").glob(f"*.results.*.xml.bz2"):
        m = get_verifiers_re.fullmatch(file.name)
        if m:
            verifier = m.group(1)
            # print(verifier)
            m2 = get_validators_re.fullmatch(verifier)
            # print(m2)
            if m2:
                verifier2 = m2.group(3)
                validator = m2.group(1)
                # print((validator, verifier2))
                if verifier2 == verifier0:
                    ret.add(validator)
    # assert False
    return ret

verifiers = get_verifiers()

goblint_verifier_results = load_tool_results("goblint")

with open("out4_unassume_help.csv", "w", newline="") as csvfile:
    fields = ["verifier", "name", "property", "expected_verdict", "goblint_verifier_status"]
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    for verifier in verifiers:
        # if verifier != "goblint":
        #     continue
        print(verifier)
        verifier_results = load_tool_results(verifier)
        validators = get_validators(verifier)
        for validator in validators:
            if validator != "goblint-validate-correctness-witnesses-2.0":
                continue
            print(f"  {validator}")
            validator_results = load_tool_results(f"{validator}-{verifier}")

            results = get_unassume_help_results(goblint_verifier_results, validator_results)
            # print(results)

            for result in results:
                task, goblint_verifier_status = result
                name, property, expected_verdict = task
                writer.writerow({
                    "verifier": verifier,
                    "name": name,
                    "property": property,
                    "expected_verdict": expected_verdict,
                    "goblint_verifier_status": goblint_verifier_status,
                })

