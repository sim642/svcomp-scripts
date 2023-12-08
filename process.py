from lxml import etree
import bz2
from pathlib import Path
import collections

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
    for file in Path("data0/").glob(f"{tool}.*.results.*.xml.bz2"):
        ret |= load_run_results(file)
    return ret

def get_result_pairs(verifier_results, validator_results):
    result_pairs = collections.Counter()
    for task, verifier_status in verifier_results.items():
        if task in validator_results:
            validator_status = validator_results[task]
        else:
            validator_status = None

        result_pairs[(verifier_status, validator_status)] += 1

    return result_pairs

def ratio(result_pairs):
    verifier_trues = 0
    for result_pair, count in result_pairs.items():
        verifier_status, validator_status = result_pair
        if verifier_status == "true":
            verifier_trues += count

    verifier_trues_validated = result_pairs[("true", "true")]
    return (verifier_trues_validated, verifier_trues)

verifiers = ["goblint", "mopsa", "uautomizer", "cpachecker"]
validators = verifiers

for verifier in verifiers:
    print(verifier)
    verifier_results = load_tool_results(verifier)
    for validator in validators:
        print(f"  {validator}")
        validator_results = load_tool_results(f"{validator}-validate-correctness-witnesses-2.0-{verifier}")

        result_pairs = get_result_pairs(verifier_results, validator_results)
        verifier_trues_validated, verifier_trues = ratio(result_pairs)
        print(f"    {verifier_trues_validated}/{verifier_trues} = {verifier_trues_validated / verifier_trues * 100:.2f}%")
