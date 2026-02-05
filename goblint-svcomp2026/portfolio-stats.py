# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas==3.0.0rc0", # this version tells why merge validation fails
# ]
# ///

import pandas as pd

data = pd.read_csv("table-generator-level.table.csv", skiprows=2, sep="\t")

# TODO: deduplicate this with computeweights
#open and read the exclude file
svbenchpath = "/home/simmo/dev/goblint/sv-comp/sv-benchmarks"
excluded = set()
with open(svbenchpath + "/Invalid-TaskDefs.set", 'r') as f:
    content=f.read()
    for line in content.splitlines():
        # ignore comments and empty lines
        line=line.strip()
        if line.startswith("#") or line == "":
            continue
        excluded.add(line.removeprefix("c/"))

# exclude invalid tasks
data.loc[data["sv-benchmarks/c/"].isin(excluded), "category"] = "missing" # like in fixed BenchExec results xml-s, they aren't adapted to invalid task for some reason, only HTMLs (now they are, so this is unnecessary and doesn't change results)

print("confirmed true:")
data_true = data[(data["status"] == "true") & (data["category"] == "correct")]
data_levels = data_true["level"].groupby(data["level"]).count().rename("count")
data_cumlevels = data_levels.cumsum().rename("cumcount")
data_levels_pct = (data_levels / data_levels.sum() * 100).rename("pct")
print(pd.concat([data_cumlevels, data_levels, data_levels_pct], axis=1))


print()

def is_ro(s):
    return s.startswith("TIMEOUT") or s.startswith("OUT OF MEMORY")

print("resource out (TIMEOUT, OUT OF MEMORY):")
data_ro = data[data["status"].map(is_ro) & (data["category"] != "missing")]
data_ro_levels = data_ro["level-started"].groupby(data["level-started"]).count().rename("count")
data_ro_cumlevels = data_ro_levels.cumsum().rename("cumcount")
data_ro_levels_pct = (data_ro_levels / data_ro_levels.sum() * 100).rename("pct")
print(pd.concat([data_ro_cumlevels, data_ro_levels, data_ro_levels_pct], axis=1))


print("Overall score:")
data_score = data #[data["status"] == "true"]
# print(data_score)
weights = pd.read_csv("weightstable.csv")
weights = weights[weights["overallweight"].notnull()]
# print(weights)
data_weights = pd.merge(data_score, weights, how="left", left_on=["sv-benchmarks/c/", "Unnamed: 1"], right_on=["ymlfile", "property"], validate="1:1")

# data_weights.to_csv("data-weights.csv")

data_weights_true = data_weights[(data_weights["status"] == "true") & (data_weights["category_x"] == "correct")]
data_weights_true["overall_score"] = data_weights_true["overallweight"] * 2 # assuming only trues
# print(data_weights_true)
data_weights_levels = data_weights_true.groupby(data_weights_true["level"])["overall_score"].sum()
data_weights_cumlevels = data_weights_levels.cumsum().rename("cumsum").astype(int)
data_weights_levels = data_weights_cumlevels.diff().fillna(data_weights_cumlevels).rename("overall_score")
data_weights_levels_pct = (data_weights_levels / data_weights_levels.sum() * 100).rename("pct")
print(pd.concat([data_weights_cumlevels, data_weights_levels, data_weights_levels_pct], axis=1))


data_weights_true["meta_score"] = data_weights_true["weight"] * 2 # assuming only trues
# print(data_weights_true)
data_weights_meta = data_weights_true[data_weights_true["category_x"] == "correct"].groupby(data_weights_true["metacategory"])["meta_score"].sum().astype(int)
print(data_weights_meta)

