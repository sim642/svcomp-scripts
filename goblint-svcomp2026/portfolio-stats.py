# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas==3.0.0rc0", # this version tells why merge validation fails
# ]
# ///

import pandas as pd

data = pd.read_csv("table-generator-level.table.csv", skiprows=2, sep="\t")
# TODO: this also counts unconfirmed!
print("true:")
data_true = data[data["status"] == "true"]
data_levels = data_true["level"].groupby(data["level"]).count().rename("count")
data_cumlevels = data_levels.cumsum().rename("cumcount")
data_levels_pct = (data_levels / data_levels.sum() * 100).rename("pct")
print(pd.concat([data_cumlevels, data_levels, data_levels_pct], axis=1))


print()

def is_ro(s):
    return s.startswith("TIMEOUT") or s.startswith("OUT OF MEMORY")

print("resource out (TIMEOUT, OUT OF MEMORY):")
data_ro = data[data["status"].map(is_ro)]
data_ro_levels = data_ro["level-started"].groupby(data["level-started"]).count().rename("count")
data_ro_cumlevels = data_ro_levels.cumsum().rename("cumcount")
data_ro_levels_pct = (data_ro_levels / data_ro_levels.sum() * 100).rename("pct")
print(pd.concat([data_ro_cumlevels, data_ro_levels, data_ro_levels_pct], axis=1))


# TODO: this also counts unconfirmed!
print("Overall score:")
data_score = data #[data["status"] == "true"]
# print(data_score)
weights = pd.read_csv("weightstable.csv")
weights = weights[weights["overallweight"].notnull()]
# print(weights)
data_weights = pd.merge(data_score, weights, how="left", left_on=["sv-benchmarks/c/", "Unnamed: 1"], right_on=["ymlfile", "property"], validate="1:1")

data_weights_true = data_weights[data_weights["status"] == "true"]
data_weights_true["overall_score"] = data_weights_true["overallweight"] * 2 # assuming only trues
# print(data_weights_true)
data_weights_levels = data_weights_true.groupby(data_weights_true["level"])["overall_score"].sum()
data_weights_cumlevels = data_weights_levels.cumsum().rename("cumsum").round()
data_weights_levels = data_weights_cumlevels.diff().fillna(data_weights_cumlevels).rename("overall_score")
data_weights_levels_pct = (data_weights_levels / data_weights_levels.sum() * 100).rename("pct")
print(pd.concat([data_weights_cumlevels, data_weights_levels, data_weights_levels_pct], axis=1))

