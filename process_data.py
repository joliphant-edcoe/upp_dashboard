import os
import pandas as pd


district_names = {
    "0973783": "Black Oak Mine",
    "0961838": "Buckeye",
    "0961846": "Camino",
    "0910090": "EDCOE",
    "0961853": "El Dorado High",
    "0961879": "Gold Oak",
    "0961887": "Gold Trail",
    "0961895": "Indian Diggings",
    "0961903": "Lake Tahoe",
    "0961911": "Latrobe",
    "0961929": "Mother Lode",
    "0961945": "Pioneer",
    "0961952": "Placerville",
    "0961960": "Pollock Pines",
    "0961978": "Rescue",
    "0961986": "Silver Fork",
}


files = os.listdir("ca_data")
df_list = []

for f in files:
    with open(f"ca_data/{f}") as txt_file:
        for n, line in enumerate(txt_file.readlines()):
            if line.startswith("CharterLEACode"):
                i = n
            if line.startswith("TribalFosterYouthALL"):
                j = n

    df = pd.read_csv(
        f"ca_data/{f}",
        on_bad_lines="skip",
        skiprows=list(range(i, i + 50)),
        dtype={"NonCharterLEACode": "str", "NonCharterSchoolCode": "str"},
    )
    df2 = pd.read_csv(
        f"ca_data/{f}",
        header=i - 1,
        skiprows=list(range(j, j + 5)),
        dtype={"CharterLEACode": "str", "CharterSchoolCode": "str"},
    )
    fname = os.path.splitext(f)[0]
    yearcode = "-".join(fname.split("-")[-2:])
    column_names = [c.replace("Charter", "") for c in list(df2.columns)]
    df.columns = column_names
    df2.columns = column_names

    df_list.append(
        pd.concat([df.assign(charter=False), df2.assign(charter=True)]).assign(
            YEAR="'" + yearcode[2:4] + "-" + yearcode[-2:]
        )
    )


all_df = pd.concat(df_list).assign(LEA=lambda df_: df_.LEACode.map(district_names))
aggregate = (
    all_df.groupby(["LEA", "YEAR", "charter"])
    .agg(
        enrollment=("SchoolEnrlmt", "sum"),
        directCert=("DCert", "sum"),
        undupMeal=("UndupMeal", "sum"),
        engLearn=("EL", "sum"),
        undupMealEng=("UndupELMeal", "sum"),
    )
    .reset_index()
)


countyAggregate = (
    all_df.groupby(["YEAR", "charter"])
    .agg(
        countyEnroll=("LEAEnrlTotal", "first"),
        countyDirectCert=("LEADCertTotal", "first"),
        countyUndupMeal=("LEAUndupMealTotal", "first"),
        countyEngLearn=("LEAELTotal", "first"),
        countyUndupMealEng=("LEAUndupELMealTotal", "first"),
    )
    .reset_index()
)

homelessFoster = all_df.groupby(["YEAR"]).agg(
    homeless=("Homeless", "sum"),
    foster=("FosterPlacement", "sum"),
    tribalfoster=("TribalFosterYouth", "sum"),
)
