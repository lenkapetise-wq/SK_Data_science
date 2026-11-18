import pandas as pd
from pandas._config import display
from pandas.io.formats import info

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

objednavky2  = pd.read_csv(r"C:\Users\PC\PycharmProjects\Skillmea-Data-Science\objednavky2.csv")
produkty2 = pd.read_csv(r"C:\Users\PC\PycharmProjects\Skillmea-Data-Science\produkty2.csv")
zakaznici2 = pd.read_csv(r"C:\Users\PC\PycharmProjects\Skillmea-Data-Science\zakaznici2.csv")

print(objednavky2.head())
print(produkty2.head())
print(zakaznici2.head())

print(objednavky2.info())
print(produkty2.info())
print(zakaznici2.info())

#převod na správný datový typ
zakaznici2["registrace"]=pd.to_datetime(zakaznici2["registrace"], format="%Y-%m-%d")
print(zakaznici2.info())
print(zakaznici2.head())

objednavky2["order_date"]=pd.to_datetime(objednavky2["order_date"], format="%Y-%m-%d %H:%M")
print(objednavky2.info())
print(objednavky2.head())

#spojeni objednavky a produkty- přes product_id
op=objednavky2.merge(produkty2, on="product_id",how="left",validate="m:1")
assert len(op)==len(objednavky2)
print(op)
print(op.info())

#tržba bez DPH
op["trzba_bez_dph"]=op["quantity"]*op["cena_za_kus_bez_dph"]*(1-op["discount_pct"]/100)
print(op.head())
print(op.info())

#aggregovana tabulka
agg_tabulka=(op
.groupby("order_id")
.agg(order_date=("order_date", "first"),
    customer_id=("customer_id", "first"),
    status=("status", "first"),
    channel=("channel", "first"),
    payment=("payment", "first"),
    dopravce=("dopravce", "first"),
    delivery_days=("delivery_days", "first"),
    pocet_polozek=("radek", "count"),
    kusy=("quantity", "sum"),
    trzba_bez_dph=("trzba_bez_dph", "sum"),
    sleva_prumer=("discount_pct", "mean"))
.reset_index()
.reset_index(drop=True)
.sort_values(["order_date","order_id"])
)
hranice=pd.Timestamp("2026-06-30 23:59")
zacatek=pd.Timestamp("2026-06-30 23:59")
konec=pd.Timestamp("2026-10-31 23:59")
rozdil= konec-zacatek
print(rozdil.days)


import numpy as np
agg_tabulka["obdobi"]=np.where(agg_tabulka["order_date"]<=hranice, "historicka data", "budoucnost")
print(agg_tabulka["obdobi"].value_counts())
print(agg_tabulka)

registrovani=agg_tabulka.dropna(subset=["customer_id"]).copy()                                          # dropna zahodí objednávky bez zákazníka (hosté); copy = vlastní kopie
dokoncene_obchody=registrovani[registrovani["status"]=="dokonceno"].copy()                              # jen dokončené (vrácené a zrušené se nepočítají jako nákup)
print(dokoncene_obchody)

 #rozdělení historických a budoucích obchodů                                                            # KONTROLA: ve sloupci status jsou jen "dokonceno"
obchody_historie=dokoncene_obchody[dokoncene_obchody["obdobi"]=="historicka data"].copy()               # z těchto objednávek budou PŘÍZNAKY tj. identifikace registrovaných zákazníků
obchody_budoucnost=dokoncene_obchody[dokoncene_obchody["obdobi"]=="budoucnost"].copy()                  # z těchto objednávek bude CÍL - registrovaní zakazníci s opakovaným nákupm

# vytovřeni DataFrame zakaznik
zakaznik=(pd.DataFrame({"customer_id":obchody_historie["customer_id"].unique()})                        # unique() = každý zákazník jednou
          .set_index("customer_id")                                                                     # ID zákazníka se stane indexem (jménem řádku)
          .sort_index())                                                                                # seřadit podle ID, ať je pořadí stabilní
print(zakaznik)

zakaznik["koupi_znovu"]=zakaznik.index.isin(obchody_budoucnost["customer_id"].unique()).astype(int)     #jsou stejní zákazníci v budoucích obchode?, astype(int) - zobrazí 1 nebo 0
print(zakaznik)


print("Počet zákazníků ", len(zakaznik), ". Podíl zákazníků, kteří koupí znovu ", round(zakaznik["koupi_znovu"].mean(),2 ))
print(len(zakaznik[zakaznik["koupi_znovu"] == 1]))

#analýza nákupů
nakupy=(obchody_historie
    .groupby("customer_id")
    .agg(posledni_nakup=("order_date","max"),
        frekvence=("order_id","count"),
        monetary=("trzba_bez_dph", "sum"))
    )
print(nakupy)

#propojení zákazníka a nákupů
zakaznik=zakaznik.join(nakupy)                                                                             # .join = spojení podle INDEXU (obě tabulky mají index customer_id)
print(zakaznik)

#průměrná hodnota objednávky
zakaznik["AVG_hodnota_objednavky"]=zakaznik["monetary"]/zakaznik["frekvence"]
print(zakaznik)

#predikce
from sklearn.model_selection import train_test_split                 # rozdělení dat na učící (train) a testovací (test) část
from sklearn.linear_model import LogisticRegression                  # logistická regrese = model pro předpověď ANO/NE jako pravděpodobnosti
from sklearn.metrics import roc_auc_score                            # AUC = kvalita ŘAZENÍ zákazníků podle pravděpodobnosti

y=zakaznik["koupi_znovu"]                                           #cíl, který předpovídáme
# x=příznaky                                                        příznak/sloupce, které se odstraňují ["koupí_znovu"] - python by hledal vazby
                                                                                    #["posledni_nakup"]_buď odstranit a připojit později nebo hned převést na datový typ

X=zakaznik.drop(columns=["koupi_znovu","posledni_nakup"])
print(zakaznik)
print(X)
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.2,random_state=42)
                                                                # test_size=0.2: pětina zákazníků půjde do testu; random_state=42: stejné rozdělení pokaždé (každý dostane totéž)
print(X.isna().sum())
median=X_train.median()                                                       #Doplnění prázdných hodnot MEDIÁNEM Z TRAINU – test dostane STEJNÁ čísla (pravidlo 2)
                                                                              # medián každého sloupce jen z trainu
X_train = X_train.fillna(median)                                              # doplnit median z train
X_test = X_test.fillna(median)                                                # doplnit median z train
                                                                             #Tady zatím žádné prázdné hodnoty nejsou (RFM je má vždy). Důležité budou, až přibude interval mezi nákupy a věk.

# Škálování (z-skóre): (hodnota − průměr) / směrodatná odchylka; obojí bereme z trainu
# Proč škálovat: logistická regrese by jinak "přeceňovala" sloupce s velkými čísly (koruny) oproti malým (kusy).

prumer=X_train.mean()                                        # průměr každého sloupce z trainu
odchylka=X_train.std()                                       # směrodatná odchylka každého sloupce z trainu
X_train_s=(X_train-prumer)/odchylka                          # škálovaný train (průměr 0, odchylka 1)
X_test_s=(X_test-prumer)/odchylka                            # škálovaný test – čísla z TRAINU, proto průměr testu vyjde "zhruba" 0 a tak to má být
print(X_train_s)                                             # KONTROLA: hodnoty kolem 0, v rozmezí zhruba −3 až +3
print(X_test_s)


model = LogisticRegression()                                 # prázdný model
model.fit(X_train_s,y_train)                                 # fit = učení; model se učí JEN na trainu
accuracy=model.score(X_test_s,y_test)                        # Upozornění: score() u klasifikace vrací PŘESNOST (accuracy), špatně jsem to pojmenoval
print(zakaznik)                                              # KONTROLA: celá tabulka zákazník × příznaky
print(accuracy)                                               # přesnost: podíl zákazníků v testu, které model uhodl
# # OTÁZKA: Je přesnost např. 0,66 dobrá? Odpověď: záleží – "vždy tipuj 1" má přesnost 0,62. Proto potřebujeme AUC (viz pokračování).
print(model.predict(X_test_s))                               # predict = tvrdý odhad 0/1 pro každého zákazníka v testu
print(y_test)                                                # skutečné hodnoty cíle v testu – porovnej s předchozím výpisem

# zakaznik["recency"]=(hranice-zakaznik["posledni_nakup"]).dt.days
# print(zakaznik.head())



