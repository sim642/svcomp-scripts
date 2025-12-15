# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
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
