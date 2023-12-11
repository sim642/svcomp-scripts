import pandas as pd

data = pd.read_csv("out2_property.csv")

goblint = data[(data["verifier"] == "goblint") & (data["validator"] == "goblint-validate-correctness-witnesses-2.0")][["property", "expected_verdict", "verifier_status", "validator_status", "count"]]

def is_false(s):
    return s.startswith("false")

correct = goblint[goblint["expected_verdict"] == "true"]
verified = correct[correct["verifier_status"] == "true"]
confirmed = verified[verified["validator_status"] == "true"][["property", "count"]].set_index("property")
refuted = verified[verified["validator_status"].map(is_false, na_action="ignore")][["property", "count"]].set_index("property")

correct_group = correct[["property", "count"]].groupby("property").agg("sum")
verified_group = verified[["property", "count"]].groupby("property").agg("sum")

joined = correct_group.join(verified_group, lsuffix="_correct", rsuffix="_verified").join(confirmed.join(refuted, lsuffix="_confirmed", rsuffix="_refuted")).fillna(0)
joined.insert(3, "count_unconfirmed", joined["count_verified"] - joined["count_confirmed"] - joined["count_refuted"])
joined.loc['total']= joined.sum()
joined.insert(3, "ratio_confirmed", joined["count_confirmed"] / joined["count_verified"] * 100)

print(joined)
