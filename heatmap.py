import pandas as pd
import seaborn as sns

data = pd.read_csv("out.csv")
# data = pd.read_csv("out.csv", index_col=["verifier", "validator", "expected_verdict", "verifier_status", "validator_status"])
print(data)

correct = data[data["verifier_status"] == data["expected_verdict"]]
correct_valid = correct[(correct["validator_status"] == correct["expected_verdict"]) | (correct["validator_status"] == "done")]
print(correct)
print(correct_valid)

correct2 = correct[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")
correct_valid2 = correct_valid[["verifier", "validator", "count"]].groupby(["verifier", "validator"]).agg("sum")

ratio = correct_valid2 / correct2
ratio = ratio.pivot_table(index="verifier", columns="validator", values="count")
print(ratio)

h = sns.heatmap(data=ratio, vmin=0.0, vmax=1.0, square=True, cmap="RdYlGn", xticklabels=True, yticklabels=True)
h.get_figure().savefig("out.svg", bbox_inches="tight")
