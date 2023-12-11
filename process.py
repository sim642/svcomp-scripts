from lxml import etree
import bz2
from pathlib import Path
import collections
import csv
import re

DATA_DIR = "data2"

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

def get_result_pairs(verifier_results, validator_results):
    result_pairs = collections.Counter()
    for task, verifier_status in verifier_results.items():
        if task in validator_results:
            validator_status = validator_results[task]
        else:
            validator_status = None

        _, property, expected_verdict = task
        result_pairs[(property, expected_verdict, verifier_status, validator_status)] += 1

    return result_pairs

def ratio(result_pairs):
    corrects = 0
    corrects_validated = 0
    for result_pair, count in result_pairs.items():
        _, expected_verdict, verifier_status, validator_status = result_pair
        if verifier_status == expected_verdict:
            corrects += count
            if validator_status == expected_verdict or validator_status == "done":
                corrects_validated += count

    return (corrects_validated, corrects)

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

with open("out2_property.csv", "w", newline="") as csvfile:
    fields = ["verifier", "validator", "property", "expected_verdict", "verifier_status", "validator_status", "count"]
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    for verifier in verifiers:
        # if verifier != "goblint":
        #     continue
        print(verifier)
        verifier_results = load_tool_results(verifier)
        validators = get_validators(verifier)
        for validator in validators:
            # if validator != "goblint-validate-correctness-witnesses-2.0":
            #     continue
            print(f"  {validator}")
            validator_results = load_tool_results(f"{validator}-{verifier}")

            result_pairs = get_result_pairs(verifier_results, validator_results)

            for result_pair, count in result_pairs.items():
                property, expected_verdict, verifier_status, validator_status = result_pair
                writer.writerow({
                    "verifier": verifier,
                    "validator": validator,
                    "property": property,
                    "expected_verdict": expected_verdict,
                    "verifier_status": verifier_status,
                    "validator_status": validator_status,
                    "count": count,
                })

            corrects_validated, corrects = ratio(result_pairs)
            if corrects != 0:
                print(f"    {corrects_validated}/{corrects} = {corrects_validated / corrects * 100:.2f}%")
