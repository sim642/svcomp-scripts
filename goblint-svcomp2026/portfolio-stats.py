# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
# ]
# ///

import pandas as pd

data = pd.read_csv("table-generator-level.table.csv", skiprows=2, sep="\t")
# TODO: this also counts unconfirmed!
data_true = data[data["status"] == "true"]
data_levels = data_true["level"].groupby(data["level"]).count().rename("count")
data_cumlevels = data_levels.cumsum().rename("cumcount")
data_levels_pct = (data_levels / data_levels.sum() * 100).rename("pct")
# print(data_levels)
# print(data_cumlevels)
# print(data_levels_pct)
print(pd.concat([data_cumlevels, data_levels, data_levels_pct], axis=1))

