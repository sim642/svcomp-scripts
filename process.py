from lxml import etree
import bz2
from pathlib import Path

def load_run_results(filename):
    with bz2.open(filename) as f:
        tree = etree.parse(f)

        ret = {}
        for run in tree.xpath("""//run[@expectedVerdict="true"]"""):
            name = run.get("name")
            properties = run.get("properties")
            # expected_verdict = run.get("expectedVerdict")
            status = run.find("""column[@title="status"]""").get("value")
            ret[(name, properties)] = status
        return ret

def load_tool_results(tool):
    ret = {}
    for file in Path(".").glob(f"{tool}.*.results.*.xml.bz2"):
        ret |= load_run_results(file)
    return ret

def ratio(verifier_results, validator_results):
    verifier_trues = 0
    verifier_trues_validated = 0
    for task, verifier_status in verifier_results.items():
        if verifier_status == "true":
            verifier_trues += 1

            if task in validator_results:
                validator_status = validator_results[task]
                if validator_status == "true":
                    verifier_trues_validated += 1

    return (verifier_trues_validated, verifier_trues)

verifiers = ["goblint", "mopsa", "uautomizer", "cpachecker"]
validators = verifiers

for verifier in verifiers:
    print(verifier)
    verifier_results = load_tool_results(verifier)
    for validator in validators:
        print(f"  {validator}")
        validator_results = load_tool_results(f"{validator}-validate-correctness-witnesses-2.0-{verifier}")
        verifier_trues_validated, verifier_trues = ratio(verifier_results, validator_results)
        print(f"    {verifier_trues_validated}/{verifier_trues} = {verifier_trues_validated / verifier_trues * 100:.2f}%")
