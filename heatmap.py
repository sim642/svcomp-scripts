import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

data = pd.read_csv("out5.csv")
print(data)

data = data[data["validator"].map(lambda v: v.endswith("correctness-witnesses-2.0"))]

true = data[data["expected_verdict"] == "true"]
false = data[data["expected_verdict"] == "false"]

def is_false(s):
    return s.startswith("false")

true_correct = true[true["verifier_status"] == "true"]
false_correct = false[false["verifier_status"].map(is_false, na_action="ignore")]

true_valid = true_correct[(true_correct["validator_status"] == "true") | (true_correct["validator_status"] == "done")]
false_valid = false_correct[false_correct["validator_status"].map(is_false, na_action="ignore") | (false_correct["validator_status"] == "done")]

true_correct_group = true_correct[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")
false_correct_group = false_correct[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")
true_valid_group = true_valid[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")
false_valid_group = false_valid[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")

true_ratio = true_valid_group / true_correct_group
false_ratio = false_valid_group / false_correct_group

print(true_ratio)
print(false_ratio)

true_pivot = true_ratio.pivot_table(index="verifier", columns="validator", values="count").filter(axis=1, like="correctness") # TODO: some violation validators confirm trues?
false_pivot = false_ratio.pivot_table(index="verifier", columns="validator", values="count").filter(axis=1, like="violation") # TODO: some correctness validators confirm falses?
pivot = true_pivot.join(false_pivot, how="outer").sort_index(axis=1)

(pivot * 100).to_csv("yaml-correctness2_5.csv")

plt.figure(figsize=(12, 9))
h = sns.heatmap(data=pivot, vmin=0.0, vmax=1.0, square=True, cmap="RdYlGn", xticklabels=True, yticklabels=True)
h.get_figure().savefig("yaml-correctness2_5.svg", bbox_inches="tight")

