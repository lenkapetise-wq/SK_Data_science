print("ahoj")
import pandas as pd

objednavky = pd.read_csv(
    r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\lekce 0911\objednavky2.csv"
)

produkty = pd.read_csv(
    r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\lekce 0911\produkty2.csv"
)

zakaznici = pd.read_csv(
    r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\lekce 0911\zakaznici2.csv"
)

print(objednavky.head())
print(produkty.head())
print(zakaznici.head())

objednavky["order_date"]=pd.to_datetime(objednavky["order_date"], format="%Y-%m-%d %H:%M")
zakaznici["registrace"]=pd.to_datetime(zakaznici["registrace"], format="%Y-%m-%d")
op=objednavky.merge(produkty,on="product_id", how="left", validate="m:1")

pd.set_option("display.max_columns",40)
pd.set_option("display.width",2000)

objednavky + produkty + zakaznici
opz=op.merge(zakaznici,on="customer_id", how="left", validate="m:1")
assert len(opz)==len(op)
print(opz.head())

# trzba_bez_dph
op["trzba_bez_dph"]=op["quantity"]*op["cena_za_kus_bez_dph"]*(1-op["discount_pct"]/100)
print(op.head())

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
rozdil=konec-zacatek
print(rozdil.days)
testovaci_obdobi=123

import numpy as np

agg_tabulka["obdobi"]=np.where(agg_tabulka["order_date"]<=hranice, "historicka data", "budoucnost")
print(agg_tabulka["obdobi"].value_counts())

registrovani=agg_tabulka.dropna(subset=["customer_id"]).copy()

dokoncene_obchody=registrovani[registrovani["obdobi"]=="dokonceno"].copy()
print(dokoncene_obchody)

obchody_historie=dokoncene_obchody[dokoncene_obchody["obdobi"]=="historicka data"].copy()
obchody_budoucnost=dokoncene_obchody[dokoncene_obchody["obdobi"]=="budoucnost"].copy()

zakaznik=(pd.DataFrame({"customer_id":obchody_historie["customer_id"].unique()})
.set_index("customer_id")
.sort_index())
print(zakaznik)

zakaznik["koupi_znovu"]=zakaznik.index.isin(obchody_budoucnost["customer_id"].unique()).astype(int)
print("Počet zákazníků ", len(zakaznik), ". Podíl zákazníků, kteří koupí znovu ", round(zakaznik["koupi_znovu"].mean(),2 ))

nakupy=(obchody_historie
.groupby("customer_id")
.agg(posledni_nakup=("order_date","max"),
    frekvence=("order_id","count"),
    monetary=("trzba_bez_dph", "sum"))
)
print(nakupy)

#prumerna hodnota objednavky
zakaznik["AVG_hodnota_objednavky"]=zakaznik["monetary"]/zakaznik["frekvence"]

y=zakaznik["koupi_znovu"] #cíl, který předpovídáme
X=zakaznik.drop(columns=["koupi_znovu"])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

median=X_train.median()
X_train = X_train.fillna(median)
X_test = X_test.fillna(median)

# x=zakaznik.drop(columns=["koupi_znovu","posledni_nakup"])

prumer=X_train.mean()
odchylka=X_train.std()
X_train_s=(X_train-prumer)/odchylka
X_test_s=(X_test-prumer)/odchylka

print(X_train_s)

model = LogisticRegression()
model.fit(X_train_s,y_train)
auc=model.score(X_test_s,y_test)

print(auc)