from logging import info

import pandas as pd
objednavky=pd.read_csv(r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\objednavky.csv")
produkty=pd.read_csv(r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\produkty.csv")
zakaznici=pd.read_csv(r"C:\Users\PC\OneDrive\Dokumenty\Lenka Petikova\DATA ANALYTIC\PYTHON\zakaznici.csv")


print(objednavky.head())
print(objednavky.info())
print(objednavky.describe())

print(objednavky.isna().sum())
objednavky["order_date"]=pd.to_datetime(objednavky["order_date"], format="%Y-%m-%d %H:%M")
print(objednavky["order_date"].head())

print("zakaznici:")
print(zakaznici.head())
print(zakaznici.info())
zakaznici["registrace"] = pd.to_datetime(zakaznici["registrace"], format="%Y-%m-%d")
print(zakaznici["registrace"].head())


print("produkty:")
print(produkty.head())
print(produkty.info())
# -----------------------------------------------------------------------------
# seskupování - mini tabulka
obj_mini=pd.DataFrame({"obj":["A", "B", "C","D", "E"], "prod":["P1", "P2", "P2","P3", "P9"]})
kat_mini=pd.DataFrame({"prod":["P1", "P2", "P3","P4"], "nazev":["mys", "klavesnice","notebook", "monitor"]})
print(obj_mini)
print(kat_mini)

spojena_mini_tabulka=obj_mini.merge(kat_mini, on="prod",how="outer")
print(spojena_mini_tabulka.head())
print(spojena_mini_tabulka)
# -----------------------------------------------------------------------------

objednavky["hrube_trzby"]=objednavky["quantity"]*objednavky["cena_za_kus_bez_dph"]
print(objednavky.info())

print(objednavky["hrube_trzby"].sum())
# -------------------------------------------------------------------------------
pocet_radku_pred=len(objednavky)
print(pocet_radku_pred)
spojena_tabulka_obj_prod=objednavky.merge(produkty,on="product_id",how="left")
print(spojena_tabulka_obj_prod.head())
print(spojena_tabulka_obj_prod.info())


spojena_tabulka2_obj_prod_zak=spojena_tabulka_obj_prod.merge(zakaznici,on="customer_id",how="left")
print(spojena_tabulka2_obj_prod_zak.head())
print(spojena_tabulka2_obj_prod_zak.info())

mega_tabulka=spojena_tabulka2_obj_prod_zak
mega_tabulka.to_csv("mega_tabulka.csv", index=False)

print(mega_tabulka["customer_id"].isna().sum())
mega_tabulka["customer_id"]=mega_tabulka["customer_id"].fillna("nezaregistrovan")
# mega_tabulka["rok_narozeni"]=mega_tabulka["rok_narozeni"].fillna(1973)

#mega_tabulka["rok_narozeni"]=mega_tabulka["rok_narozeni"].fillna(mega_tabulka["rok_narozeni"].median())
#print(mega_tabulka["rok_narozeni"].isna().sum())
#print(mega_tabulka["rok_narozeni"].count())
# ______________________________________________________________________________________________________

objednavky["rok"] = objednavky["order_date"].dt.year

rok2025 = objednavky[objednavky["rok"] == 2025]
rok2026 = objednavky[objednavky["rok"] == 2026]

print(objednavky.info())
print(objednavky.head())

#CONCAT: spojení 2 souborů rok2025 a rok2026
spojeno_2025_2026=pd.concat([rok2025, rok2026], ignore_index=True)
#print("pocet_zaznamu_rok2025", len(rok2025), "pocet_zaznamu_rok2026", len(rok2026),"pocet_zazanmu_dohromady", len(spojeno_2025_2026))

print("pocet_zaznamu_rok2025", len(rok2025))
print("pocet_zaznamu_rok2026", len(rok2026))
print("pocet_zaznamu_dohromady", len(spojeno_2025_2026))
#-------------------------------------------------------------------------------------------------------
print(objednavky.isna().sum())
print(objednavky["discount_pct"])
objednavky["discount_pct"]=objednavky["discount_pct"].fillna(0)
print(objednavky["discount_pct"])
print(objednavky.info())
#-------------------------------------------------------------------------------------------------------
print(mega_tabulka.info())
print(mega_tabulka[["quantity", "cena_za_kus_bez_dph","naklad"]])
mega_tabulka["hruby_zisk"]=(mega_tabulka["cena_za_kus_bez_dph"]-mega_tabulka["naklad"])*mega_tabulka["quantity"]
print(mega_tabulka[["quantity", "cena_za_kus_bez_dph","naklad", "hruby_zisk"]])
print(mega_tabulka["hruby_zisk"].sum())
print(mega_tabulka.info())
mega_tabulka["cena_za_kus_s_dph"]=mega_tabulka["cena_za_kus_bez_dph"]*1.21
print(mega_tabulka[["cena_za_kus_bez_dph","cena_za_kus_s_dph"]])

#____________________________________________________________________________________________________________
print(mega_tabulka.info())
print(mega_tabulka.head())

mega_tabulka["order_id"] = mega_tabulka["order_id"].str.replace("OBJ-", "").astype(int)
print(mega_tabulka["order_id"])

#print(mega_tabulka[mega_tabulka["payment"] == "dobirka"])
#print(mega_tabulka[mega_tabulka["payment"] == "dobirka"].head())

#datumové operace
mega_tabulka["rok_objednavky"]=mega_tabulka["order_date"].dt.year #2025,2026
mega_tabulka["mesic_objednavky"]=mega_tabulka["order_date"].dt.month #1-12
mega_tabulka["rok_mesic_objednavky"]=mega_tabulka["order_date"].dt.to_period("M")
mega_tabulka["den_v_tydnu_objednavky"]=mega_tabulka["order_date"].dt.day_of_week+1 #0 - pondělí 6 - neděle

mega_tabulka["den_v_tydnu_nazev_objednavky"]=(mega_tabulka["order_date"]
                                   .dt.day_of_week
                                   .map({0:"PO", 1:"Ut", 2:"St", 3:"CT",4:"PA", 5:"SO", 6:"NE"}))

print(mega_tabulka["den_v_tydnu_nazev_objednavky"])
print(mega_tabulka[["order_date","registrace"]])

mega_tabulka["rozdil_v_datech"]=(mega_tabulka["order_date"]-mega_tabulka["registrace"]).dt.days
print(mega_tabulka["rozdil_v_datech"])

#tržby z dokončených objednávke
print(mega_tabulka.info())
print(mega_tabulka[["status", "hruby_zisk"]])
print(mega_tabulka[mega_tabulka["status"]=="dokonceno"]["hruby_zisk"].sum())

#tržby z dokončených objednávke v jednotlivýh měsících
dokoncene_objednavky_mega=mega_tabulka[mega_tabulka["status"]=="dokonceno"]
trzby_dle_mesice=dokoncene_objednavky_mega.groupby(["rok_objednavky", "mesic_objednavky"])["hruby_zisk"].sum()
print(trzby_dle_mesice)

import numpy as np
print(mega_tabulka[[ "hruby_zisk"]].describe())

#kategorizace poled hrubého zisku
mega_tabulka["velikost_objednavky"]=np.where(mega_tabulka["hruby_zisk"]>750,"velka","bezna")
print(mega_tabulka[["hruby_zisk","velikost_objednavky"]])

# tržby dle objednavek a roku-mesic
trzby_dle_mesice_obj=dokoncene_objednavky_mega.groupby(["order_id", "rok_mesic_objednavky"])["hruby_zisk"].sum()
print(trzby_dle_mesice_obj)
print(trzby_dle_mesice_obj.info())
print(mega_tabulka.info())

#pomocna tabulka pro graf
pomocna_tabulka=zakaznici.groupby("segment")["registrace"].count()
print(pomocna_tabulka)


import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(16,9))
ax.bar(pomocna_tabulka.index, pomocna_tabulka.values)
plt.savefig("graf_zakaznici.png")
plt.show()