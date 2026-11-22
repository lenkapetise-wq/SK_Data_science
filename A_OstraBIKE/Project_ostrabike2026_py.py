import datetime
from ipaddress import collapse_addresses
from logging import info

import pandas as pd
import os

from pandas import isna
from pandas.core.groupby import groupby
from seaborn._stats import aggregation

print(os.getcwd())

jizdy = pd.read_csv("jizdy.csv")
stanice = pd.read_csv("stanice.csv")
kola = pd.read_csv("kola.csv")
uzivatele = pd.read_csv("uzivatele.csv")
pocasi = pd.read_csv("pocasi.csv")

#PŘÍPRAVA DAT

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


print(stanice.info())                                                   # všechny hodnoty jsou doplněny
print(stanice.head())

print(stanice.duplicated().sum())                                       #žádné duplicity
print(stanice["station_id"].duplicated().sum())                         #ověřena unikátnost "station_id"

print(stanice["opened"].head())
stanice["opened"] = pd.to_datetime(stanice["opened"])                   #změna formátu ["opened"] na typ datum
print(stanice.info())
print(stanice["capacity"].describe())                                   #statistické informace o kapacitě


print(kola.info())
print(kola.head())

print(kola.isna().sum())                                                #žádné chybějící hodnoty
print(kola.duplicated().sum())                                          #žádné duplicitní hodnoty


kola["purchase_date"] = pd.to_datetime(kola["purchase_date"])           #převod na datový typ-datum
kola["last_service"] = pd.to_datetime(kola["last_service"])             #převod na datový typ-datum

print(kola.info())

print(
    (kola["last_service"] < kola["purchase_date"]).sum()                #žádné kolo nebylo servisováno před nákupem
)

print(uzivatele.info())                                                 #birth_year-float
print(uzivatele.head())
print(uzivatele.isna().sum())                                           #chybějící hodnoty_1336-sloupec birth year
print(uzivatele.duplicated().sum())                                     #0

print(uzivatele[uzivatele["birth_year"].isna()]["user_type"].value_counts())  #686NA-"user_typ":pay_as_you_go, 650NA_předplatne
print(uzivatele["birth_year"].describe())                               # min "birth_year" =1900; max"birth_year" =2025
print(uzivatele[uzivatele["birth_year"] > 2016])                        # všichni uživatelé mladší 10 let mají rok narození 2025
print(uzivatele[uzivatele["birth_year"] < 1926])                        # všichni uživatelé starší 100 let mají rok naorzení 1900

print((uzivatele["birth_year"] == 2025).sum())                          #20 uživatelů s nerálným_příliš nízký rokem narození pro pronájem kola
print((uzivatele["birth_year"] == 1900).sum())                          #40 uživaatelů s nerálným příliš vysokým věkem pro pronájem kola

median_rok = uzivatele["birth_year"].median()                           # median roku narození použit pro vyplnění chybějících hodnot

uzivatele["birth_year"] = (
    uzivatele["birth_year"]
    .fillna(median_rok)
)

print(uzivatele.info())                                                 # kontrola- nulové hodnoty odstraněny

uzivatele = uzivatele[
    (uzivatele["birth_year"] > 1900) &                                  # uživatelé bez odlehlých dat narození
    (uzivatele["birth_year"] < 2025)
]
print(uzivatele.info())

uzivatele["birth_year"] = uzivatele["birth_year"].astype(int)           #změna datového typu u "birth_year" na integr
print(uzivatele.info())

print(pocasi.head())
print(pocasi.info())                                                    # date-změnit z typu object na datetype
print(pocasi.isna().sum())                                              # terp_avg _14 hodnot
print(pocasi.duplicated().sum())                                        # 0

pocasi["date"] = pd.to_datetime(pocasi["date"])

print(pocasi[pocasi["temp_avg"].isna()])                                # zobrazení 14 chybějících hodnot "temp_avg"
pocasi["temp_avg"] = pocasi["temp_avg"].interpolate()                   # doplnění chybějících teplot interpolací
print(pocasi.info())


# SPOJOVÁNÍ TABULEK DO TABULKY JIZDYANL

print(jizdy.columns)
print(uzivatele.columns)
print(kola.columns)
print(stanice.columns)
print(pocasi.columns)

jizdy_an = jizdy.merge(                                                       # tabulka:jizdy_an je propojeni tabulek jizdy a uzivatele
    uzivatele,
    on="user_id",
    how="left"
)
print(jizdy_an.info())

jizdy_anb = jizdy_an.merge(                                                   #tabulka jizdy_anb: je propojení tabulek jizdy, uzivatele, kola
    kola,
    on="bike_id",
    how="left"
)
print(jizdy_anb.info())

jizdy_anb["date"] = jizdy_anb["start_time"].dt.normalize()                     #uprava formatu ["start_time"] pouze na format den
print(jizdy_anb["date"])                                                       #tabulka jizdy_anbp: je propojeni jizdy, uzivatele,pocasi

jizdy_anbp=jizdy_anb.merge(
        pocasi,
        on="date",
        how="left"
)
print(jizdy_anbp.info())

print(
jizdy_anbp[                                                                   #vypsání stanic psaných malým písmem
    jizdy_anbp["start_station_id"]
    != jizdy_anbp["start_station_id"].str.upper()
]["start_station_id"].value_counts()
)

jizdy_anbp["start_station_id"] = (                                            #oprva malých písmen na VELKÁ start_station_id
    jizdy_anbp["start_station_id"]
    .str.upper()
)

jizdy_anbp["end_station_id"] = (                                               #oprva malých písmen na VELKÁ -end_station_id
    jizdy_anbp["end_station_id"]
    .str.upper()
)

analytics = jizdy_anbp.merge(                                  #analytics: propojeni jizdy, uzivatele, pocasi, stanice
    stanice,
    left_on="start_station_id",
    right_on="station_id",
    how="left"
)
print(analytics.info())


analytics = jizdy_anbp.merge(                                   #analytics: propojeni jizdy, uzivatele, pocasi, stanice
    stanice,
    left_on="end_station_id",
    right_on="station_id",
    how="left"
)

print(analytics.info())
print(len(analytics))                                               #39857 řádků
print(analytics.isna().sum())                                       #181 NA po připojení stanic- nutno řešit

print(
analytics[
    analytics["station_id"].isna()
]["start_station_id"].unique()
)

print(
set(jizdy_anbp["end_station_id"]) - set(stanice["station_id"]))     #stanice "ST999" není uvedena v referenční tabulce stanic

print((analytics["end_station_id"] == "ST999").sum())               #181 jízd končí v ST999


# #DOTZY ZE ZADÁNÍ
#
# #MALÁ PÍSMENA V NÁZVECH STANIC:
# # pokud by byla malá písmena v názvech stanic,neproběhl by merge. Python je rozlišuje velká a malá písmena. Pro ověřní lze použít kód
# jizdy["start_station_id"] = (
#     jizdy["start_station_id"]
#     .str.upper()
# )
#
# jizdy["end_station_id"] = (
#     jizdy["end_station_id"]
#     .str.upper()
# )
# pokud kód nevrátí žáný řádek pak jsou v názvech stanic jen velká písmena

# #ST999? Zjištění přítmnosti ve sloupci
# jizdy[ jizdy["start_station_id"] == "ST999"]        # výsledek - ST999 není přítomna
#
# jizdy[jizdy["end_station_id"] == "ST999" ]          # výsledek - ST999 staní přítomna
#                                                     # nekonzistenntí identifikátor, vynechání z analýzy, protože neznám atributy stanice
# print(jizdy[jizdy["price_czk"] < 0])                # list 35 položek u kterých je záporná cena
# print(                                              # zobrazení 35 položek a příslušných záporných cen
#     jizdy.loc[
#         jizdy["price_czk"] < 0,
#         ["price_czk"]
#     ]
# )
# print(
#     jizdy[jizdy["price_czk"] < 0]["price_czk"]      #min-82CZK, max-10CZK, záporné částky odpovídají reálným částkám (komenzace/refundace)
#     .describe()                                     # částky budou zahrnuty do tržeb
# )

#ANALÝZA


#1 Sezónnost a počasí
#
# denni_analyza = (analytics
#     .groupby("date")
#     .agg(
#         pocet_jizd=("trip_id", "count"),
#         temp_avg=("temp_avg", "first"),
#         rain_mm=("rain_mm", "first")
#     )
#     .reset_index()
# )                                                       #ve výsledku NaN ve slopuci temp_avg a rain_mm, nutnost sladt format data
#
# print(denni_analyza.head())
#
# print(analytics["date"].dtype)
# print(pocasi["date"].dtype)
#
# print(analytics["date"].min())                                      #2025-01-03
# print(analytics["date"].max())                                      #2026-10-31
#
# print(analytics["temp_avg"].isna().sum())                           #86 řádků nemá hodnotu "temp_avg"
# print(
#     analytics[analytics["temp_avg"].isna()][["date"]].head(20)      #20 prvních NA jsou v lednu a únoru
# )
#
# print(pocasi["date"].min())                                         #2025-03-01
# print(pocasi["date"].max())                                         #2026-10-31