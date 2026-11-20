import pandas as pd
import os

from pandas import isna

print(os.getcwd())

jizdy = pd.read_csv("jizdy.csv")
stanice = pd.read_csv("stanice.csv")
kola = pd.read_csv("kola.csv")
uzivatele = pd.read_csv("uzivatele.csv")
pocasi = pd.read_csv("pocasi.csv")

print(jizdy.info())
print(jizdy.head())


print(jizdy.duplicated().sum())                     # počet duplicitních jízd 400
print(jizdy["trip_id"].duplicated().sum())          # unikanti trip_id potvrzeni, že se jedná o 400 duplicit
jizdy_ciste = jizdy.drop_duplicates()
print(jizdy_ciste.info())                           # počet záznamů 39600

print(jizdy.isna().sum())                            #chybějící záznamy: user_id  7276
print(
    jizdy[jizdy["user_id"].isna()]["user_type"]      #turista 7276: všechny chybějící hodnoty vyfiltrovali turistu-nemá účet
    .value_counts())


#jizdy["start_time"] = pd.to_datetime(jizdy["start_time"])       #různé formáty data
#jizdy["end_time"] = pd.to_datetime(jizdy["end_time"])

print(jizdy["start_time"].str.contains(r"\.", na=False).sum())  # počet záznamů datum s tečkami 1415
print(jizdy["end_time"].str.contains(r"\.", na=False).sum())    # 1415

jizdy["start_time"] = pd.to_datetime(
    jizdy["start_time"],
    format="mixed"
)

jizdy["end_time"] = pd.to_datetime(
    jizdy["end_time"],
    format="mixed"
)
print(jizdy.info())                                                 # datetime64[ns] pro "start" i "end"

print(jizdy["distance_km"].head())                                  #datový typ změnit na float
jizdy["distance_km"] = (                                            #formát pro desetinné číslo musí být s tečko
    jizdy["distance_km"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)

jizdy["delka_jizdy"] = jizdy["end_time"] - jizdy["start_time"]
print(jizdy.info())
print(jizdy.head())
print(jizdy.describe())                                               # kontrola dat: záporné hodnoty, min délka jízdy=231 days
print((jizdy["delka_jizdy"] < pd.Timedelta(0)).sum())                 # vyhledání počtu záporných hodnot_143
egativni_jizdy = jizdy[
    jizdy["delka_jizdy"] < pd.Timedelta(0)
]

negativni_jizdy = jizdy[
    jizdy["delka_jizdy"] < pd.Timedelta(0)
]
print(
    negativni_jizdy[
        ["trip_id",
         "start_time",
         "end_time",
         "delka_jizdy"]
    ].head(20)
)
negativni_jizdy["delka_jizdy"].sort_values().head(20)                   # podobný charakter end_time je dříve než start_time
#                                                                       # jde o nekonzistentní data, proto budou odstraněna

# print(negativni_jizdy["delka_jizdy"].min())
# jizdy.sort_values("delka_jizdy").head(10)
#
# jizdy["delka_jizdy_hod"] = (
#     jizdy["delka_jizdy"]
#     .dt.total_seconds() / 3600
# )
#
# print(jizdy["delka_jizdy_hod"].describe())

jizdy = jizdy[
    jizdy["delka_jizdy"] >= pd.Timedelta(0)                             # vynechání řádků se zápornou hodnotou "delka_jizdy"
]
print((jizdy["delka_jizdy"] < pd.Timedelta(0)).sum())
# commit_test

# print(stanice.info())
# print(stanice.head())
#
# print(kola.info())
# print(kola.head())
#
# print(uzivatele.info())
# print(uzivatele.head())
#
# print(pocasi.info())
# print(pocasi.head())

# print(jizdy.columns)
# print(kola.columns)
# print(pocasi.columns)
# print(stanice.columns)
# print(uzivatele.columns)
# print(pocasi.columns)
#
# jizdy
# print(jizdy.isna().suma())

