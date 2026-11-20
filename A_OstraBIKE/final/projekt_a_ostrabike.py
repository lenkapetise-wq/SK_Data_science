# =====================================================================================
# ZÁVĚREČNÝ PROJEKT A – OstraBike: jak se daří sdíleným kolům?
# =====================================================================================
#
# OTÁZKA: Jak se systému sdílených kol OstraBike daří a co ovlivňuje počet jízd, je
# někde problém s koly nebo stanicemi, jak dopadlo zdražení odemknutí 1. 6. 2026
# a kam má provozní tým směřovat peníze?
#
# ZÁVĚR:
# 1. Jízd je letos o 16 % víc než loni, ale jen díky 8 novým stanicím – na starých stanicích
#    se jezdí stejně jako loni; nejvíc počet jízd ovlivňuje počasí: každý stupeň tepla přidá
#    asi 5 jízd denně a v deštivý den se jezdí skoro o polovinu méně.
# 2. Největší provozní problémy jsou dva: 16 rozbitých kol, na kterých skoro žádná jízda
#    nevydrží déle než 2 minuty (zákazníci za ně přesto zaplatili 58 tis. Kč), a kola, která
#    lidé ráno odvezou z obytných čtvrtí do práce a doma pak chybí (asi 12 kol každé ráno).
# 3. Po zdražení odemknutí jezdí zákazníci bez předplatného o 18 % méně, zatímco ostatních
#    jízd mírně přibylo, a firma na nich přesto nevydělala víc (tržba -4 %) – doporučuji
#    opravit rozbitá kola, ráno vozit kola zpět do obytných čtvrtí, stavět další stanice
#    a zdražení přehodnotit.
#
# OMEZENÍ: u zdražení nevíme jistě, že pokles způsobila právě cena – mohlo se změnit i 
# něco jiného; nových stanic je jen 8, takže závěr o nich stojí na malém vzorku; v datech 
# nejsou náklady na opravy ani na převážení kol, takže nevíme, kolik by doporučení stála.
#
# Výstupy: složka outputs/ – grafy (PNG), tabulky (CSV) a log čištění.
# =====================================================================================

# -------------------------------------------------------------------------------------
# 0) IMPORTY A NASTAVENÍ
# -------------------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates                            # formát data na ose x (01. 03.)
import seaborn as sns                                        # heatmapa jedním řádkem

pd.set_option("display.width", 2000)                         # výpisy tabulek se nezalamují

# Cesta ke složce s daty (jizdy.csv, stanice.csv, kola.csv, uzivatele.csv, pocasi.csv).
# Data leží o složku výš (A_OstraBIKE), skript se spouští ze složky final.
CESTA = ".."
os.makedirs("outputs", exist_ok=True)                        # vytvoří složku na výstupy

# Klíčová data: sledované období, zdražení odemknutí a otevření nových stanic
OBDOBI_OD = pd.Timestamp("2025-03-01")
OBDOBI_DO = pd.Timestamp("2026-10-31")
ZMENA_CENY = pd.Timestamp("2026-06-01")
OTEVRENI_NOVYCH_STANIC = pd.Timestamp("2026-04-01")
VSECHNY_DNY = pd.date_range(OBDOBI_OD, OBDOBI_DO, freq="D")  # celý kalendář (610 dní)

TYPY = ["predplatne", "pay_as_you_go", "turista"]
NAZVY_TYPU = {"predplatne": "Předplatné (členové)", "pay_as_you_go": "Pay as you go", "turista": "Turisté"}
DNY = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

# Barvy: šedá = kontext, modrá = to podstatné, oranžová = problém / úbytek
MODRA = "#2a78d6"
SVETLA_MODRA = "#a9c8f0"
ORANZOVA = "#eb6834"
SEDA = "#52514e"
SVETLE_SEDA = "#c9c8c1"

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.8,
                     "axes.axisbelow": True,
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": SEDA,
                     "xtick.color": SEDA, "ytick.color": SEDA, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11,
                     "savefig.dpi": 150, "savefig.bbox": "tight"})

# Log čištění: u každého kroku zapíšeme, kolik řádků bylo před, po a proč
log_cisteni = []



# -------------------------------------------------------------------------------------
# 1) NAČTENÍ DAT A PRVNÍ POHLED
# -------------------------------------------------------------------------------------
jizdy = pd.read_csv(CESTA + "/jizdy.csv")
stanice = pd.read_csv(CESTA + "/stanice.csv")
kola = pd.read_csv(CESTA + "/kola.csv")
uzivatele = pd.read_csv(CESTA + "/uzivatele.csv")
pocasi = pd.read_csv(CESTA + "/pocasi.csv")

print("jizdy", jizdy.shape, "| stanice", stanice.shape, "| kola", kola.shape,
      "| uzivatele", uzivatele.shape, "| pocasi", pocasi.shape)
# KONTROLA: očekávané počty řádků (40 000 jízd, 60 stanic, 400 kol, 9 000 uživatelů, 610 dní)
assert len(jizdy) == 40000 and len(stanice) == 60 and len(kola) == 400
assert len(uzivatele) == 9000 and len(pocasi) == 610

jizdy.info()                                                 # distance_km je "object" = text, ne číslo!
print(jizdy.isna().sum())                                    # prázdné hodnoty: jen user_id

log_cisteni.append({"krok": "načtení jizdy.csv", "radku_pred": len(jizdy), "radku_po": len(jizdy),
                    "proc": "výchozí stav"})



# -------------------------------------------------------------------------------------
# 2) ČIŠTĚNÍ JÍZD
# -------------------------------------------------------------------------------------
# --- 2a) Duplicitní řádky ---
# Stejné trip_id, čas, kolo i uživatel = tatáž jízda exportovaná při migraci dvakrát.
# Kontrola: duplicit BEZ trip_id je stejně jako úplných duplicit -> neexistují "skryté"
# duplicity s novým trip_id, stačí smazat úplně shodné řádky.
pred = len(jizdy)
assert jizdy.duplicated().sum() == jizdy.drop(columns="trip_id").duplicated().sum()
jizdy = jizdy.drop_duplicates().reset_index(drop=True)
assert jizdy["trip_id"].is_unique                            # KONTROLA: každá jízda je teď jen jednou
print("Duplicity odstraněny:", pred - len(jizdy))
log_cisteni.append({"krok": "duplicitní řádky", "radku_pred": pred, "radku_po": len(jizdy),
                    "proc": "úplně shodný řádek = stejná jízda exportovaná dvakrát"})

# --- 2b) Dva formáty času ---
# Starý systém psal "dd.mm.rrrr hh:mm", nový "rrrr-mm-dd hh:mm".
# to_datetime bez formátu hádá a "10.03.2025" přečte jako 3. ŘÍJNA (měsíc první) – ukázka:
print("Bez formátu se '10.03.2025 06:25' přečte jako:", pd.to_datetime("10.03.2025 06:25"))
# Proto čteme každý formát zvlášť: nejdřív nový formát (kde nesedí -> NaT) a prázdná místa
# doplníme starým formátem.
stary_format = jizdy["start_time"].str.contains(r"\.")       # řádky ve starém formátu (s tečkami)
for sloupec in ["start_time", "end_time"]:
    cas = pd.to_datetime(jizdy[sloupec], format="%Y-%m-%d %H:%M", errors="coerce")
    cas = cas.fillna(pd.to_datetime(jizdy[sloupec], format="%d.%m.%Y %H:%M", errors="coerce"))
    jizdy[sloupec] = cas
assert jizdy["start_time"].notna().all() and jizdy["end_time"].notna().all()   # KONTROLA: oba formáty prošly
print(f"Starý formát času: {stary_format.sum()} jízd, od {jizdy.loc[stary_format, 'start_time'].min():%d.%m.%Y} "
      f"do {jizdy.loc[stary_format, 'start_time'].max():%d.%m.%Y}; nový formát od "
      f"{jizdy.loc[~stary_format, 'start_time'].min():%d.%m.%Y}")
assert jizdy["start_time"].between(OBDOBI_OD, OBDOBI_DO + pd.Timedelta(days=1)).all()   # jen sledované období

# --- 2c) Doba jízdy: konec před začátkem a jízdy delší než 24 h ---
jizdy["doba_min"] = (jizdy["end_time"] - jizdy["start_time"]).dt.total_seconds() / 60

# Konec před začátkem: rozdíl je od 5 minut až po ~10 hodin. Kdyby šlo o chybu hodin
# (posun časového pásma), byly by rozdíly celé hodiny – nejsou (viz výpis), takže to
# opravit posunem nejde. Nevíme, který z obou časů je špatně; prohozením bychom délku
# jízdy vymysleli (a záporná délka by stáhla průměr dolů). Jde o desetiny procenta jízd -> vyřazujeme.
pred = len(jizdy)
zaporne = jizdy["doba_min"] < 0
print(f"Konec před začátkem: {zaporne.sum()} jízd (o {-jizdy.loc[zaporne, 'doba_min'].max():.0f} "
      f"až {-jizdy.loc[zaporne, 'doba_min'].min():.0f} min); celé hodiny jsou jen u "
      f"{(jizdy.loc[zaporne, 'doba_min'] % 60 == 0).mean() * 100:.0f} % z nich -> nejde o posun hodin")
jizdy = jizdy[~zaporne]
log_cisteni.append({"krok": "konec před začátkem", "radku_pred": pred, "radku_po": len(jizdy),
                    "proc": "nevíme, který čas je špatně; opravou bychom délku jízdy vymysleli"})

# Jízdy > 24 h: běžné jízdy končí do 2 h, pak je mezera a až potom "jízdy" na několik dní
# = nevrácené / nezamčené kolo, ne skutečná jízda. Ukážeme, co by udělaly s průměrem.
pred = len(jizdy)
dlouhe = jizdy["doba_min"] > 24 * 60
print(f"Jízdy > 24 h: {dlouhe.sum()}; průměrná doba s nimi {jizdy['doba_min'].mean():.1f} min, "
      f"bez nich {jizdy.loc[~dlouhe, 'doba_min'].mean():.1f} min")
jizdy = jizdy[~dlouhe].reset_index(drop=True)
log_cisteni.append({"krok": "jízdy delší než 24 h", "radku_pred": pred, "radku_po": len(jizdy),
                    "proc": "nevrácené/nezamčené kolo, ne jízda; zkreslilo by průměrnou dobu"})

# Zajímavost: přesně 120 minut trvá výrazně víc jízd než 119 nebo 118 minut (hlavně turisté,
# s reálnou vzdáleností 20–45 km). Vypadá to na strop výpůjčky 2 h, kdy systém jízdu ukončí.
# Jsou to skutečné jízdy, proto je NEMAŽEME – jen víme, že doba nad 2 h se v datech neobjeví.
print("Jízdy dlouhé přesně 120 min:", (jizdy["doba_min"] == 120).sum(),
      "| 119 min:", (jizdy["doba_min"] == 119).sum())

# --- 2d) distance_km jako text ---
# Část řádků má desetinnou ČÁRKU ("14,67"), proto pandas celý sloupec načetl jako text (object).
# Čárku nahradíme tečkou a teprve pak převedeme na číslo.
print("distance_km s desetinnou čárkou:", jizdy["distance_km"].str.contains(",").sum())
jizdy["distance_km"] = pd.to_numeric(jizdy["distance_km"].str.replace(",", ".", regex=False), errors="coerce")
assert jizdy["distance_km"].notna().all()                    # KONTROLA: převod nevyrobil žádné NaN

# --- 2e) ID stanic: malá písmena a stanice mimo číselník ---
# "st013" a "ST013" je tatáž stanice, ale merge porovnává text přesně -> řádky s malými
# písmeny by nenašly svou stanici. Ukázka, kolik jízd by se nespárovalo:
print("Jízdy, jejichž start / cíl by merge nenašel (u cíle včetně ST999):",
      (~jizdy["start_station_id"].isin(stanice["station_id"])).sum(), "/",
      (~jizdy["end_station_id"].isin(stanice["station_id"])).sum())
jizdy["start_station_id"] = jizdy["start_station_id"].str.upper()   # v číselníku stanic jsou ID velkými písmeny
jizdy["end_station_id"] = jizdy["end_station_id"].str.upper()

print("Startovní stanice mimo číselník:", sorted(set(jizdy["start_station_id"]) - set(stanice["station_id"])))
print("Cílové stanice mimo číselník:", sorted(set(jizdy["end_station_id"]) - set(stanice["station_id"])))
# ST999 je jen CÍLOVÁ stanice a jízdy do ní mají běžnou délku i cenu -> jízda proběhla,
# kolo jen neskončilo v řádné stanici (servis / vráceno mimo stanici).
# V počtech jízd a tržbách je necháváme, z analýzy stanic (toky, mapa) je vyřazujeme.
jizdy["cil_mimo_stanici"] = ~jizdy["end_station_id"].isin(stanice["station_id"])
print("Jízd do cíle mimo číselník (ST999):", jizdy["cil_mimo_stanici"].sum())

# --- 2f) Záporné ceny ---
# Záporné částky odpovídají běžným cenám (např. -59 Kč = jízda turisty) -> jde o VRÁCENÍ
# peněz za jízdu. Jízda proběhla (počítáme ji), ale tržbu nepřinesla: do tržby dáváme 0
# a vratky vykazujeme zvlášť. Kdybychom je sečetli, snížily by tržbu jiných jízd.
jizdy["vratka"] = jizdy["price_czk"] < 0
jizdy["trzba_czk"] = np.where(jizdy["vratka"], 0, jizdy["price_czk"])
vratky_czk = -jizdy.loc[jizdy["vratka"], "price_czk"].sum()
print(f"Záporné ceny (vratky): {jizdy['vratka'].sum()} jízd, {vratky_czk} Kč")

# --- 2g) Prázdné user_id ---
# Ověření jedním porovnáním: prázdné user_id mají PŘESNĚ všechny jízdy turistů
# (jednorázová jízda bez účtu) -> vlastnost dat, ne chyba; nic nemažeme.
print(pd.crosstab(jizdy["user_id"].isna(), jizdy["user_type"]))
assert (jizdy["user_id"].isna() == (jizdy["user_type"] == "turista")).all()

# --- 2h) Kontrola ceníku: členové mají jízdy do 30 min zdarma ---
# Pokud data pravidlo dodržují, můžeme jim věřit i u ostatních cen. Výsledek: nikdo nad 30 min
# nejel zdarma; "placené do 30 min" jsou jízdy přesně 30 min za 1 Kč – časy jsou zaokrouhlené
# na minuty, jízda tedy trvala 30 min a pár sekund a zaplatila se 1. minuta navíc. Pravidlo platí.
clenove = jizdy[(jizdy["user_type"] == "predplatne") & ~jizdy["vratka"]]
print("Členové – placené jízdy do 30 min:", ((clenove["price_czk"] > 0) & (clenove["doba_min"] <= 30)).sum(),
      "| zdarma jízdy nad 30 min:", ((clenove["price_czk"] == 0) & (clenove["doba_min"] > 30)).sum(),
      "| placené nad 30 min:", ((clenove["price_czk"] > 0) & (clenove["doba_min"] > 30)).sum())

log_cisteni.append({"krok": "výsledek čištění jízd", "radku_pred": 40000, "radku_po": len(jizdy),
                    "proc": "opraveno: formát času, distance_km, ID stanic; vratky mimo tržbu"})



# -------------------------------------------------------------------------------------
# 3) ČIŠTĚNÍ MENŠÍCH TABULEK
# -------------------------------------------------------------------------------------
# --- Počasí: chybějící teploty ---
pocasi["date"] = pd.to_datetime(pocasi["date"], format="%Y-%m-%d")
assert pocasi["date"].is_unique and len(pocasi) == len(VSECHNY_DNY)   # KONTROLA: 1 řádek = 1 den celého období
assert pocasi["date"].is_monotonic_increasing                # dny jdou po sobě (potřeba pro interpolaci níže)
chybi_teplota = pocasi["temp_avg"].isna().sum()
# Teplota se ze dne na den mění plynule -> chybějící den doplníme průměrem sousedních dní
# (interpolace). Smazáním dní bychom rozbili úplný denní kalendář.
pocasi["temp_avg"] = pocasi["temp_avg"].interpolate()
print(f"Počasí: doplněno {chybi_teplota} chybějících teplot; chybějící srážky: {pocasi['rain_mm'].isna().sum()}")
log_cisteni.append({"krok": "počasí – chybějící teploty", "radku_pred": len(pocasi), "radku_po": len(pocasi),
                    "proc": f"{chybi_teplota} teplot doplněno interpolací (teplota se mění plynule)"})

# --- Uživatelé: nesmyslné roky narození ---
# Rok 1900 je zjevně výchozí hodnota formuláře, rok 2025 by byl kojenec. Platný rozsah
# 1925–2010 (věk 15–100 let); mimo něj -> NaN (věk neznámý). Uživatele ale NEMAŽEME –
# jeho jízdy jsou platné, jen nevíme, kolik mu je. Prázdné roky necháváme prázdné.
assert uzivatele["user_id"].is_unique
neplatny_rok = uzivatele["birth_year"].notna() & ~uzivatele["birth_year"].between(1925, 2010)
print(f"Uživatelé: {neplatny_rok.sum()} nesmyslných roků narození -> NaN "
      f"(hodnoty {sorted(uzivatele.loc[neplatny_rok, 'birth_year'].unique())}); "
      f"nevyplněno: {uzivatele['birth_year'].isna().sum()}")
uzivatele.loc[neplatny_rok, "birth_year"] = np.nan
log_cisteni.append({"krok": "uživatelé – rok narození", "radku_pred": len(uzivatele), "radku_po": len(uzivatele),
                    "proc": f"{neplatny_rok.sum()} roků mimo 1925–2010 nastaveno na neznámé"})

# --- Stanice a kola: text -> datum ---
stanice["opened"] = pd.to_datetime(stanice["opened"], format="%Y-%m-%d")
stanice["nova"] = stanice["opened"] >= OTEVRENI_NOVYCH_STANIC
print("Nové stanice (otevřené od 1. 4. 2026):", stanice["nova"].sum())
kola["last_service"] = pd.to_datetime(kola["last_service"], format="%Y-%m-%d")
assert stanice["station_id"].is_unique and kola["bike_id"].is_unique   # číselníky bez duplicit

pd.DataFrame(log_cisteni).to_csv("outputs/cisteni_log.csv", index=False, encoding="utf-8-sig")



# -------------------------------------------------------------------------------------
# 4) SPOJENÍ TABULEK (merge) – po každém kontrola počtu řádků
# -------------------------------------------------------------------------------------
pocet_jizd = len(jizdy)
sloupce_stanice = ["station_id", "name", "nova"]              # k jízdám potřebujeme název a příznak nové stanice

# Startovní stanice. add_prefix("start_") přidá před názvy sloupců "start_", aby se
# nepletly s údaji o cílové stanici (start_name, start_nova ...).
jizdy = jizdy.merge(stanice[sloupce_stanice].add_prefix("start_"), on="start_station_id",
                    how="left", validate="m:1")
assert len(jizdy) == pocet_jizd                              # KONTROLA: merge nepřidal ani neubral řádek
assert jizdy["start_name"].notna().all()                     # každá startovní stanice je v číselníku

# Cílová stanice – údaje chybí jen u ST999 (mimo číselník)
jizdy = jizdy.merge(stanice[sloupce_stanice].add_prefix("end_"), on="end_station_id",
                    how="left", validate="m:1")
assert len(jizdy) == pocet_jizd
assert (jizdy["end_name"].isna() == jizdy["cil_mimo_stanici"]).all()

# Kola
jizdy = jizdy.merge(kola, on="bike_id", how="left", validate="m:1")
assert len(jizdy) == pocet_jizd
assert jizdy["bike_type"].notna().all()                      # každé kolo je v číselníku

# Uživatelé – turisté účet nemají (user_id prázdné), ostatní musí být v registru
jizdy = jizdy.merge(uzivatele.rename(columns={"user_type": "user_type_registr"}), on="user_id",
                    how="left", validate="m:1")
assert len(jizdy) == pocet_jizd
assert (jizdy["registered"].isna() == jizdy["user_id"].isna()).all()   # registrovaný = nalezen v registru
nesoulad_typu = jizdy["user_id"].notna() & (jizdy["user_type"] != jizdy["user_type_registr"])
print("Jízdy, kde user_type nesedí s registrem uživatelů:", nesoulad_typu.sum())

# Odvozené časové sloupce
jizdy["datum"] = jizdy["start_time"].dt.normalize()          # datum bez času
jizdy["rok"] = jizdy["start_time"].dt.year
jizdy["mesic"] = jizdy["start_time"].dt.month
jizdy["den_tydne"] = jizdy["start_time"].dt.dayofweek        # 0 = pondělí ... 6 = neděle
jizdy["hodina"] = jizdy["start_time"].dt.hour
jizdy["vikend"] = jizdy["den_tydne"] >= 5

# Denní tabulka přes CELÝ kalendář: reindex doplní i dny bez jediné jízdy (= 0 jízd),
# jinak by průměr na den byl nadsazený. Pak přidáme počasí (4. tabulka).
denni = (jizdy.groupby("datum")
         .agg(jizd=("trip_id", "count"), trzba_czk=("trzba_czk", "sum"))
         .reindex(VSECHNY_DNY, fill_value=0)
         .rename_axis("date")
         .reset_index())
assert len(denni) == len(VSECHNY_DNY)                        # KONTROLA: 610 dní
assert denni["jizd"].sum() == len(jizdy)                     # KONTROLA: součet jízd sedí
assert denni["trzba_czk"].sum() == jizdy["trzba_czk"].sum()  # KONTROLA: součet tržeb sedí
denni = denni.merge(pocasi, on="date", how="left", validate="1:1")
assert len(denni) == len(VSECHNY_DNY) and denni["temp_avg"].notna().all()
print("Dny bez jediné jízdy:", (denni["jizd"] == 0).sum())

denni["rok"] = denni["date"].dt.year
denni["mesic"] = denni["date"].dt.month
denni["rok_mesic"] = denni["date"].dt.to_period("M")
denni["jizd_7d"] = denni["jizd"].rolling(7, center=True, min_periods=4).mean()   # klouzavý 7denní průměr
# Deštivý den = aspoň 1 mm srážek (běžná meteorologická hranice srážkového dne;
# mrholení pod 1 mm jízdy prakticky neovlivní).
denni["destivy"] = denni["rain_mm"] >= 1



# -------------------------------------------------------------------------------------
# 5) OTÁZKA 1 – SEZÓNNOST A POČASÍ
# -------------------------------------------------------------------------------------
prumer_mesice = denni.groupby("rok_mesic")["jizd"].mean().round(1)
assert len(prumer_mesice) == 20                              # KONTROLA: 20 měsíců (III/2025 – X/2026)
print("Průměrný počet jízd za den podle měsíce:\n", prumer_mesice)
# Kolik jízd je denně: průměr i medián přes CELÝ kalendář (i zimní dny)
print(f"Jízd za den: průměr {denni['jizd'].mean():.1f}, medián {denni['jizd'].median():.0f}, "
      f"nejméně {denni['jizd'].min()} ({denni.loc[denni['jizd'].idxmin(), 'date']:%d.%m.%Y}), "
      f"nejvíce {denni['jizd'].max()} ({denni.loc[denni['jizd'].idxmax(), 'date']:%d.%m.%Y})")

# --- Graf 1: stejné období dvou let ---
# Rok 2025 má v datech i listopad a prosinec, rok 2026 i leden a únor -> srovnáváme
# jen měsíce III–X, které jsou v OBOU letech (stejná sezóna).
# V roce 2026 přibylo 8 stanic, proto růst počítáme i jen pro stanice existující už v 2025.
d25 = denni[denni["mesic"].between(3, 10) & (denni["rok"] == 2025)]
d26 = denni[denni["mesic"].between(3, 10) & (denni["rok"] == 2026)]
rust_celkem = (d26["jizd"].sum() / d25["jizd"].sum() - 1) * 100
stare_stanice = jizdy[~jizdy["start_nova"] & jizdy["mesic"].between(3, 10)]
rust_stare = ((stare_stanice["rok"] == 2026).sum() / (stare_stanice["rok"] == 2025).sum() - 1) * 100

fig, ax = plt.subplots(figsize=(11, 4.8))
# Data roku 2025 posuneme o rok dopředu, aby oba roky ležely na stejné ose (1. 3. – 31. 10.)
osa_25 = d25["date"] + pd.DateOffset(years=1)
ax.plot(osa_25, d25["jizd"], color=SVETLE_SEDA, linewidth=0.7)            # tenká čára = jednotlivé dny
ax.plot(d26["date"], d26["jizd"], color=SVETLA_MODRA, linewidth=0.7)
ax.plot(osa_25, d25["jizd_7d"], color=SEDA, linewidth=2.2)                 # silná čára = 7denní průměr
ax.plot(d26["date"], d26["jizd_7d"], color=MODRA, linewidth=2.6)
ax.text(osa_25.iloc[-1], d25["jizd_7d"].iloc[-1], "  2025", color=SEDA, va="center", fontweight="bold")
ax.text(d26["date"].iloc[-1], d26["jizd_7d"].iloc[-1], "  2026", color=MODRA, va="center", fontweight="bold")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d. %m."))
ax.set_ylim(bottom=0)
ax.set_xlabel("Den v roce (1. 3. – 31. 10.)")
ax.set_ylabel("Počet jízd za den (silná čára = průměr 7 dní)")
jizd_26 = f"{d26['jizd'].sum():,}".replace(",", " ")       # 19603 -> "19 603" (mezera mezi tisíci)
jizd_25 = f"{d25['jizd'].sum():,}".replace(",", " ")
ax.set_title(f"Za 1. 3. – 31. 10. 2026 bylo {jizd_26} jízd, o {abs(rust_celkem):.0f} % "
             f"{'více' if rust_celkem > 0 else 'méně'} než loni ({jizd_25});\n"
             f"na stanicích, které existovaly už loni, je změna jen {rust_stare:+.0f} % – růst přinesly "
             f"nové stanice", loc="left")
fig.savefig("outputs/01_denni_jizdy_2025_vs_2026.png")       # uložit PŘED plt.show()
plt.show()

# --- Graf 2: vztah k teplotě ---
# Přímku prokládáme jen SUCHÝMI dny, aby déšť nezkresloval vliv samotné teploty.
suche = denni[~denni["destivy"]]
mokre = denni[denni["destivy"]]
sklon, posun = np.polyfit(suche["temp_avg"], suche["jizd"], 1)   # přímka y = sklon * x + posun
korelace = denni["temp_avg"].corr(denni["jizd"])

fig, ax = plt.subplots(figsize=(8.5, 5.2))
ax.scatter(suche["temp_avg"], suche["jizd"], s=12, color=SVETLE_SEDA, label=f"suchý den (n = {len(suche)})")
ax.scatter(mokre["temp_avg"], mokre["jizd"], s=14, color=MODRA, label=f"deštivý den ≥ 1 mm (n = {len(mokre)})")
x_cara = np.linspace(denni["temp_avg"].min(), denni["temp_avg"].max(), 50)
ax.plot(x_cara, sklon * x_cara + posun, color=SEDA, linewidth=1.5, linestyle="--")
ax.text(x_cara[-1], sklon * x_cara[-1] + posun, f" {sklon:+.1f} jízdy/°C", color=SEDA, va="center")
ax.set_ylim(bottom=0)
ax.set_xlabel("Průměrná denní teplota (°C)")
ax.set_ylabel("Počet jízd za den")
ax.legend(frameon=False, loc="upper left")
ax.set_title(f"Každý stupeň navíc přidá zhruba {sklon:.1f} jízdy denně (korelace r = {korelace:.2f});\n"
             f"deštivé dny leží {'pod' if mokre['jizd'].mean() < suche['jizd'].mean() else 'nad'} "
             f"suchými dny se stejnou teplotou", loc="left")
fig.savefig("outputs/02_teplota_a_jizdy.png")
plt.show()

# --- Graf 3: deštivý × suchý den ---
# Férové srovnání: deštivých dní je v různých měsících různě mnoho, a léto má samo o sobě
# víc jízd. Proto porovnáváme deštivý a suchý den VE STEJNÉM MĚSÍCI a rozdíly zprůměrujeme
# (váha = počet deštivých dní v měsíci).
mesic_dest = denni.groupby(["rok_mesic", "destivy"])["jizd"].agg(["mean", "count"]).unstack()
assert mesic_dest["count"].sum().sum() == len(denni)         # KONTROLA: každý den je v jedné skupině
assert mesic_dest.notna().all().all()                        # každý měsíc má deštivé i suché dny
rozdil_mesic = mesic_dest[("mean", True)] / mesic_dest[("mean", False)] - 1
efekt_deste = (rozdil_mesic * mesic_dest[("count", True)]).sum() / mesic_dest[("count", True)].sum() * 100

# Do grafu: průměr za teplou a chladnou sezónu s počtem dní (n). Rozdělení IV–IX / zbytek
# odpovídá grafu 1: od dubna do září je denních jízd zhruba dvojnásobek oproti zbytku roku,
# takže smíchat obě sezóny do jednoho průměru by rozdíl déšť × sucho zkreslilo.
denni["sezona"] = np.where(denni["mesic"].between(4, 9), "teplá sezóna (IV–IX)", "chladná (III, X–II)")
srovnani_dest = denni.groupby(["sezona", "destivy"])["jizd"].agg(prumer="mean", dni="count").reset_index()
assert srovnani_dest["dni"].sum() == len(denni)
srovnani_dest.to_csv("outputs/destive_vs_suche_dny.csv", index=False, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(8, 4.8))
poradi_sezon = ["teplá sezóna (IV–IX)", "chladná (III, X–II)"]
for _, radek in srovnani_dest.iterrows():
    x = poradi_sezon.index(radek["sezona"]) * 2.6 + int(radek["destivy"])   # pozice sloupce
    ax.bar(x, radek["prumer"], color=MODRA if radek["destivy"] else SVETLE_SEDA, width=0.9)
    ax.text(x, radek["prumer"], f"{radek['prumer']:.0f}\nn = {radek['dni']} dní", ha="center", va="bottom", fontsize=9)
    ax.text(x, -2, "deštivý" if radek["destivy"] else "suchý", ha="center", va="top", fontsize=9)
ax.set_xticks([0.5, 3.1])
ax.set_xticklabels(poradi_sezon)
ax.tick_params(axis="x", pad=18)
ax.grid(axis="x", visible=False)
ax.set_ylim(0, srovnani_dest["prumer"].max() * 1.2)          # osa od nuly + místo pro popisky
ax.set_ylabel("Průměrný počet jízd za den")
ax.set_title(f"Deštivý den (≥ 1 mm) má o {abs(efekt_deste):.0f} % {'méně' if efekt_deste < 0 else 'více'} "
             f"jízd než suchý den ve stejném měsíci", loc="left")
fig.savefig("outputs/03_destive_vs_suche_dny.png")
plt.show()

denni.drop(columns=["rok_mesic", "jizd_7d"]).to_csv("outputs/denni_jizdy_a_pocasi.csv", index=False, encoding="utf-8-sig")



# -------------------------------------------------------------------------------------
# 6) OTÁZKA 2 – KDY SE JEZDÍ A KDO
# -------------------------------------------------------------------------------------
# Heatmapa den v týdnu × hodina pro každý typ uživatele (small multiples).
# Buňka = % jízd daného typu, aby šly porovnat TVARY dne skupin s různým počtem jízd;
# barevná škála je pro všechny tři grafy SPOLEČNÁ (stejné vmin/vmax).
tydenni = jizdy.groupby(["user_type", "den_tydne", "hodina"])["trip_id"].count()
assert tydenni.sum() == len(jizdy)                           # KONTROLA: žádná jízda se neztratila
podil_tydenni = tydenni / tydenni.groupby("user_type").transform("sum") * 100

podil_vikend = jizdy.groupby("user_type")["vikend"].mean() * 100
assert len(podil_vikend) == 3                                # KONTROLA: tři typy uživatelů
print("Podíl jízd o víkendu podle typu (%):", podil_vikend.round(1).to_dict())

fig, osy = plt.subplots(1, 3, figsize=(16, 4.6), sharey=True)
for i, typ in enumerate(TYPY):
    matice = podil_tydenni[typ].unstack(fill_value=0).reindex(index=range(7), columns=range(24), fill_value=0)
    den_spicky, hodina_spicky = podil_tydenni[typ].idxmax()
    sns.heatmap(matice, ax=osy[i], cmap="Blues", vmin=0, vmax=podil_tydenni.max(), xticklabels=3,
                cbar=(i == 2), cbar_kws={"label": "Podíl jízd skupiny (%)"})   # barevná legenda jen u posledního
    osy[i].set_title(f"{NAZVY_TYPU[typ]} (n = {(jizdy['user_type'] == typ).sum():,} jízd)\n".replace(",", " ")
                     + f"víkend = {podil_vikend[typ]:.0f} % jízd, špička {DNY[den_spicky]} {hodina_spicky} h", fontsize=10)
    osy[i].set_xlabel("Hodina začátku jízdy (h)")
    osy[i].set_ylabel("")
    osy[i].axhline(5, color="white", linewidth=3)            # oddělí pracovní dny od víkendu
osy[0].set_yticklabels(DNY, rotation=0)
osy[0].set_ylabel("Den v týdnu")
nejvic_vikend = podil_vikend.drop("predplatne").idxmax()
fig.suptitle(f"Členové jezdí ve všední dny ráno a odpoledne (víkend jen {podil_vikend['predplatne']:.0f} % jízd), "
             f"{NAZVY_TYPU[nejvic_vikend].lower()} hlavně o víkendu přes den "
             f"({podil_vikend[nejvic_vikend]:.0f} % jízd; rovnoměrně by to bylo 29 %)",
             x=0.06, y=1.06, ha="left", fontweight="bold")
fig.savefig("outputs/04_heatmapa_den_hodina.png")
plt.show()

# Doplněk z tabulky uživatelů: věk jezdců podle typu (turisté věk nemají – nemají účet)
jizdy["vekova_skupina"] = pd.cut(2026 - jizdy["birth_year"], bins=[14, 25, 35, 50, 65, 101],
                                 labels=["15–25", "26–35", "36–50", "51–65", "66+"])
vek_tab = pd.crosstab(jizdy["vekova_skupina"], jizdy["user_type"], normalize="columns").mul(100).round(1)
assert (vek_tab.sum() - 100).abs().max() < 0.5               # KONTROLA: každý sloupec dává dohromady 100 %
print("Věk jezdců podle typu (% jízd se známým věkem):\n", vek_tab)
vek_tab.to_csv("outputs/vek_jezdcu_podle_typu.csv", encoding="utf-8-sig")



# -------------------------------------------------------------------------------------
# 7) OTÁZKA 3 – ZDRAVÍ VOZOVÉHO PARKU
# -------------------------------------------------------------------------------------
# Jízda do 2 minut ujede jen pár desítek metrů: zákazník kolo odemkne a hned vrátí
# (kolo nejede). Hranice 2 min: pod ní je ujetá vzdálenost téměř nulová.
HRANICE_KRATKA_MIN = 2
jizdy["kratka"] = jizdy["doba_min"] <= HRANICE_KRATKA_MIN
# Tržbu za nepovedené krátké jízdy nepovažujeme za poctivou – zákazník kolo nepoužil.
jizdy["trzba_skutecne_jizdy"] = np.where(jizdy["kratka"], 0, jizdy["trzba_czk"])
print(f"Krátké jízdy (≤ {HRANICE_KRATKA_MIN} min): {jizdy['kratka'].sum()}, "
      f"průměrná vzdálenost {jizdy.loc[jizdy['kratka'], 'distance_km'].mean():.2f} km")

# Žebříček kol
kolo_stat = (jizdy.groupby("bike_id")
             .agg(jizd=("trip_id", "count"), kratkych=("kratka", "sum"),
                  trzba_czk=("trzba_czk", "sum"), trzba_skutecne_jizdy=("trzba_skutecne_jizdy", "sum"),
                  bike_type=("bike_type", "first"), last_service=("last_service", "first"))
             .reset_index())
assert kolo_stat["jizd"].sum() == len(jizdy)                 # KONTROLA: součet jízd
assert kolo_stat["trzba_czk"].sum() == jizdy["trzba_czk"].sum()   # KONTROLA: součet tržeb
kolo_stat["skutecnych_jizd"] = kolo_stat["jizd"] - kolo_stat["kratkych"]
kolo_stat["podil_kratkych"] = kolo_stat["kratkych"] / kolo_stat["jizd"] * 100
# Podíl krátkých jízd je dvouvrcholový: zdravá kola mají 0 %, vadná přes 90 %.
# Hranice 50 % proto leží bezpečně mezi oběma skupinami.
HRANICE_VADNE_PCT = 50
kolo_stat["vadne"] = kolo_stat["podil_kratkych"] > HRANICE_VADNE_PCT
kolo_stat = kolo_stat.sort_values("podil_kratkych", ascending=False).reset_index(drop=True)
vadna = kolo_stat[kolo_stat["vadne"]]
zdrava = kolo_stat[~kolo_stat["vadne"]]
n_vadnych = len(vadna)
print(f"Vadná kola (> {HRANICE_VADNE_PCT} % krátkých jízd): {n_vadnych}; zdravá kola: medián "
      f"{zdrava['podil_kratkych'].median():.1f} %, maximum {zdrava['podil_kratkych'].max():.1f} % krátkých jízd")
print("Typ kola – vadná × celý park (%):\n",
      pd.DataFrame({"vadna": vadna["bike_type"].value_counts(normalize=True) * 100,
                    "vsechna": kola["bike_type"].value_counts(normalize=True) * 100}).round(0))
print("Poslední servis – medián: vadná", vadna["last_service"].median().date(),
      "| zdravá", zdrava["last_service"].median().date())

# Kolik to stojí:
# a) ušlý příjem: vadné kolo udělá jen pár skutečných jízd (> 2 min), zdravé desítky.
#    Ušlý příjem = počet vadných kol × (tržba zdravého kola − tržba vadného kola), jen ze
#    skutečných jízd; přepočet na rok: období má 610 dní.
# b) zákazníci za nepovedené jízdy na vadných kolech platili -> riziko reklamací a ztráty důvěry.
usly_prijem = n_vadnych * (zdrava["trzba_skutecne_jizdy"].mean() - vadna["trzba_skutecne_jizdy"].mean())
usly_prijem_rok = usly_prijem / len(VSECHNY_DNY) * 365
porucha = jizdy["bike_id"].isin(vadna["bike_id"]) & jizdy["kratka"]   # nepovedené jízdy na vadných kolech
zaplaceno_za_poruchy = jizdy.loc[porucha, "trzba_czk"].sum()
print(f"Skutečné jízdy na kolo za období: zdravé {zdrava['skutecnych_jizd'].mean():.0f}, "
      f"vadné {vadna['skutecnych_jizd'].mean():.0f}; nepovedené pokusy na vadné kolo {vadna['kratkych'].mean():.0f}")
print(f"Ušlý příjem: {usly_prijem:,.0f} Kč za období (~{usly_prijem_rok:,.0f} Kč/rok); zákazníci zaplatili "
      f"za {porucha.sum()} nepovedených jízd {zaplaceno_za_poruchy:,.0f} Kč".replace(",", " "))
print(f"NÁVRH: stáhnout {n_vadnych} kol do servisu (seznam v outputs/kola_zebricek.csv), vrátit zákazníkům "
      f"peníze za nepovedené jízdy a hlídat podíl jízd ≤ {HRANICE_KRATKA_MIN} min u každého kola každý týden.")
kolo_stat.to_csv("outputs/kola_zebricek.csv", index=False, encoding="utf-8-sig")

# --- Graf 5: rozdělení doby jízdy ---
podil_na_vadnych = porucha.sum() / jizdy["kratka"].sum() * 100
fig, ax = plt.subplots(figsize=(10, 4.6))
biny = np.arange(0, 122, 1)                                  # koše po 1 minutě, 0–121 min
ax.hist(jizdy.loc[~jizdy["kratka"], "doba_min"], bins=biny, color=SVETLE_SEDA)
ax.hist(jizdy.loc[jizdy["kratka"], "doba_min"], bins=biny, color=ORANZOVA)
ax.text(HRANICE_KRATKA_MIN + 1.5, ax.get_ylim()[1] * 0.9,
        f"≤ {HRANICE_KRATKA_MIN} min: {jizdy['kratka'].sum():,} jízd".replace(",", " "), color=ORANZOVA)
ax.set_xlim(0, 121)
ax.set_xlabel("Doba jízdy (min)")
ax.set_ylabel("Počet jízd")
ax.set_title(f"{jizdy['kratka'].mean() * 100:.0f} % jízd trvá nejvýš {HRANICE_KRATKA_MIN} minuty "
             f"a {podil_na_vadnych:.0f} % z nich připadá na pouhých {n_vadnych} kol z {len(kola)}", loc="left")
fig.savefig("outputs/05_rozdeleni_doby_jizdy.png")
plt.show()

# --- Graf 6: žebříček kol ---
top = kolo_stat.head(n_vadnych + 14)                         # vadná kola + pár zdravých pro srovnání
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.bar(top["bike_id"], top["podil_kratkych"], color=[ORANZOVA if v else SVETLE_SEDA for v in top["vadne"]])
ax.axhline(HRANICE_VADNE_PCT, color=SEDA, linestyle="--", linewidth=1)
ax.text(len(top) - 0.5, HRANICE_VADNE_PCT + 2, f"hranice {HRANICE_VADNE_PCT} %", ha="right", fontsize=9)
ax.text(n_vadnych + 0.5, 25, f"zbylých {len(zdrava)} kol: medián {zdrava['podil_kratkych'].median():.1f} %, "
        f"maximum {zdrava['podil_kratkych'].max():.1f} %", fontsize=9, color=SEDA)
ax.set_ylim(0, 105)
ax.set_xlabel("Kolo (seřazeno podle podílu krátkých jízd)")
ax.set_ylabel(f"Podíl jízd ≤ {HRANICE_KRATKA_MIN} min (%)")
ax.tick_params(axis="x", rotation=90, labelsize=8)
ax.set_title(f"{n_vadnych} kol je prakticky nepojízdných (téměř všechny jízdy ≤ {HRANICE_KRATKA_MIN} min); "
             f"oprava vrátí odhadem {usly_prijem_rok:,.0f} Kč tržeb ročně".replace(",", " "), loc="left")
fig.savefig("outputs/06_zebricek_kol.png")
plt.show()



# -------------------------------------------------------------------------------------
# 8) OTÁZKA 4 – ZMĚNA CENY ODEMKNUTÍ 1. 6. 2026
# -------------------------------------------------------------------------------------
# Jak férově srovnávat:
#  * stejné měsíce obou let (stejná sezóna) – ne celý rok,
#  * zasažená skupina (pay_as_you_go platí odemknutí) × ostatní (předplatné a turisté
#    odemknutí neplatí) – ostatní ukazují, jak by se jízdy vyvíjely bez zdražení,
#  * kontrola PŘED změnou (III–V): rostly obě skupiny stejně už předtím?
#  * jen stanice otevřené už v roce 2025, aby nové stanice nezkreslily meziroční růst.
cena_po_typu = (jizdy[~jizdy["vratka"]]
                .groupby(["user_type", np.where(jizdy.loc[~jizdy["vratka"], "start_time"] >= ZMENA_CENY, "po 1. 6. 2026", "před")])
                ["price_czk"].mean().unstack().round(1))
assert len(cena_po_typu) == 3
print("Průměrná cena jízdy (Kč, bez vratek):\n", cena_po_typu)

PO = "po (VI–X)"
PRED = "před (III–V)"
cena = jizdy[~jizdy["start_nova"] & jizdy["mesic"].between(3, 10)].copy()
cena["skupina"] = np.where(cena["user_type"] == "pay_as_you_go", "pay_as_you_go", "ostatní")
cena["obdobi"] = np.where(cena["mesic"] >= 6, PO, PRED)
srovnani_ceny = (cena.groupby(["skupina", "obdobi", "rok"])
                 .agg(jizd=("trip_id", "count"), trzba_czk=("trzba_czk", "sum"))
                 .unstack("rok"))
assert srovnani_ceny["jizd"].sum().sum() == len(cena)       # KONTROLA: součet jízd
assert srovnani_ceny["trzba_czk"].sum().sum() == cena["trzba_czk"].sum()   # KONTROLA: součet tržeb
srovnani_ceny.columns = [f"{a}_{b}" for a, b in srovnani_ceny.columns]     # ("jizd", 2025) -> "jizd_2025"
srovnani_ceny["zmena_jizd_pct"] = (srovnani_ceny["jizd_2026"] / srovnani_ceny["jizd_2025"] - 1) * 100
srovnani_ceny["zmena_trzby_pct"] = (srovnani_ceny["trzba_czk_2026"] / srovnani_ceny["trzba_czk_2025"] - 1) * 100
print(srovnani_ceny.round(1))
srovnani_ceny.to_csv("outputs/zmena_ceny_srovnani.csv", encoding="utf-8-sig")

payg_po = srovnani_ceny.loc[("pay_as_you_go", PO), "zmena_jizd_pct"]
ost_po = srovnani_ceny.loc[("ostatní", PO), "zmena_jizd_pct"]
payg_pred = srovnani_ceny.loc[("pay_as_you_go", PRED), "zmena_jizd_pct"]
ost_pred = srovnani_ceny.loc[("ostatní", PRED), "zmena_jizd_pct"]
zmena_trzby_payg_po = srovnani_ceny.loc[("pay_as_you_go", PO), "zmena_trzby_pct"]
# Rozdíl v rozdílech: o kolik procentních bodů PAYG zaostal za ostatními PO změně,
# očištěno o to, o kolik zaostával už PŘED změnou.
did = (payg_po - ost_po) - (payg_pred - ost_pred)
print(f"Rozdíl v rozdílech (PAYG − ostatní, po − před): {did:+.1f} p. b.; tržba PAYG VI–X {zmena_trzby_payg_po:+.1f} %")

# Kontrola počasí: nebylo léto 2026 výrazně jiné než 2025? (pak by pokles mohl být počasím)
pocasi_leto = denni[denni["mesic"].between(6, 10)].groupby("rok").agg(teplota=("temp_avg", "mean"),
                                                                       podil_destivych=("destivy", "mean"))
assert len(pocasi_leto) == 2
print("Počasí VI–X:\n", pocasi_leto.round(2))

# --- Graf 7: meziroční změna po měsících ---
mesicne = cena.groupby(["skupina", "mesic", "rok"])["trip_id"].count().unstack("rok")
assert mesicne.sum().sum() == len(cena)
mesicne["zmena_pct"] = (mesicne[2026] / mesicne[2025] - 1) * 100

fig, ax = plt.subplots(figsize=(10, 4.8))
rada_ost = mesicne.loc["ostatní", "zmena_pct"]
rada_payg = mesicne.loc["pay_as_you_go", "zmena_pct"]
ax.plot(rada_ost.index, rada_ost.values, color=SVETLE_SEDA, linewidth=2.2, marker="o")
ax.plot(rada_payg.index, rada_payg.values, color=MODRA, linewidth=2.8, marker="o")
ax.text(10.1, rada_ost.iloc[-1], " ostatní (předplatné + turisté)", color=SEDA, va="center")
ax.text(10.1, rada_payg.iloc[-1], " Pay as you go", color=MODRA, va="center", fontweight="bold")
ax.axhline(0, color=SEDA, linewidth=0.8)
ax.axvline(5.5, color=SEDA, linestyle="--", linewidth=1)
ax.text(5.55, ax.get_ylim()[1], " zdražení odemknutí 1. 6.", va="top", fontsize=9)
ax.set_xticks(range(3, 11))
ax.set_xticklabels(["III", "IV", "V", "VI", "VII", "VIII", "IX", "X"])
ax.set_xlim(2.7, 12)
ax.set_xlabel("Měsíc")
ax.set_ylabel("Změna počtu jízd 2026 proti 2025 (%)")
ax.set_title(f"Po zdražení {'ubylo' if payg_po < 0 else 'přibylo'} jízd bez předplatného o {abs(payg_po):.0f} %, "
             f"ostatních jízd {'přibylo' if ost_po >= 0 else 'ubylo'} o {abs(ost_po):.0f} % (proti stejným měsícům loni);\n"
             f"pomaleji rostly už před zdražením ({payg_pred:+.0f} % proti {ost_pred:+.0f} %), "
             f"ale po něm je rozdíl o {abs(did):.0f} bodů {'větší' if did < 0 else 'menší'}", loc="left")
fig.savefig("outputs/07_zmena_ceny_odemknuti.png")
plt.show()



# -------------------------------------------------------------------------------------
# 9) OTÁZKA 5 – STANICE A PŘESUN KOL
# -------------------------------------------------------------------------------------
# Čistý tok = příjezdy − odjezdy ČLENŮ v pracovní ráno (6:00–9:59).
#   záporný = kola ráno ubývají (je třeba je navážet), kladný = přibývají (odvážet).
# Okno 6–10 h: v heatmapě (graf 4) mají členové ve všední dny ranní špičku 6–8 h a v 9 h
# už slábne; po 10. hodině začíná jiný typ jízd.
# Jen členové: jezdí pravidelně do práce/školy, ranní tok je u nich nejstabilnější.
# Bez ST999 (mimo číselník). Dělíme počtem pracovních rán, kdy stanice EXISTOVALA,
# aby nové stanice (od 1. 4. 2026) nebyly znevýhodněné kratším provozem.
rano = jizdy[(jizdy["user_type"] == "predplatne") & ~jizdy["vikend"] & jizdy["hodina"].between(6, 9)]
odjezdy = rano.groupby("start_station_id")["trip_id"].count()
prijezdy = rano[~rano["cil_mimo_stanici"]].groupby("end_station_id")["trip_id"].count()
assert odjezdy.sum() == len(rano)                            # KONTROLA: součty odjezdů a příjezdů
assert prijezdy.sum() == (~rano["cil_mimo_stanici"]).sum()

vsedni_dny = VSECHNY_DNY[VSECHNY_DNY.dayofweek < 5]
toky = stanice.copy()
toky["pracovnich_rano"] = [(vsedni_dny >= max(otevreno, OBDOBI_OD)).sum() for otevreno in toky["opened"]]
toky["odjezdy"] = toky["station_id"].map(odjezdy)
toky["prijezdy"] = toky["station_id"].map(prijezdy)
assert toky["odjezdy"].sum() == odjezdy.sum() and toky["prijezdy"].sum() == prijezdy.sum()
assert toky[["odjezdy", "prijezdy"]].notna().all().all()     # každá stanice má ráno odjezdy i příjezdy
toky["cisty_tok_za_rano"] = (toky["prijezdy"] - toky["odjezdy"]) / toky["pracovnich_rano"]
toky =toky.sort_values("cisty_tok_za_rano").reset_index(drop=True)
toky.to_csv("outputs/stanice_ranni_tok.csv", index=False, encoding="utf-8-sig")

tok_typ = toky.groupby("station_type")["cisty_tok_za_rano"].sum().round(2).sort_values()
assert abs(tok_typ.sum() - toky["cisty_tok_za_rano"].sum()) < 0.05   # KONTROLA: součet po typech = celkem
print("Čistý ranní tok podle typu stanice (kola za ráno, součet):\n", tok_typ)

nejvic_ubyva = toky.iloc[0]
nejvic_pribyva = toky.iloc[-1]
ubytek_celkem = -toky.loc[toky["cisty_tok_za_rano"] < 0, "cisty_tok_za_rano"].sum()

# --- Graf 8: mapa s bublinami (lat/lon) ---
fig, ax = plt.subplots(figsize=(9, 7))
meritko = 900 / toky["cisty_tok_za_rano"].abs().max()       # největší bublina = 900 bodů
ubyvaji = toky[toky["cisty_tok_za_rano"] < 0]
pribyvaji = toky[toky["cisty_tok_za_rano"] >= 0]
ax.scatter(ubyvaji["lon"], ubyvaji["lat"], s=ubyvaji["cisty_tok_za_rano"].abs() * meritko,
           color=ORANZOVA, alpha=0.55, edgecolor="white", label="kola ráno ubývají")
ax.scatter(pribyvaji["lon"], pribyvaji["lat"], s=pribyvaji["cisty_tok_za_rano"].abs() * meritko,
           color=MODRA, alpha=0.55, edgecolor="white", label="kola ráno přibývají")
nove = toky[toky["nova"]]
ax.scatter(nove["lon"], nove["lat"], s=30, marker="x", color="black", label="nová stanice (od 1. 4. 2026)")
for _, radek in pd.concat([toky.head(3), toky.tail(3)]).iterrows():   # popisek jen 3 + 3 krajní stanice
    ax.annotate(f"{radek['name']} ({radek['cisty_tok_za_rano']:+.1f})", (radek["lon"], radek["lat"]),
                fontsize=8, xytext=(8, 6), textcoords="offset points")
# 1° zeměpisné délky je na 50° s. š. kratší než 1° šířky -> poměr os 1/cos(šířky), ať mapa není roztažená
ax.set_aspect(1 / np.cos(np.radians(toky["lat"].mean())))
ax.set_xlabel("Zeměpisná délka (°E)")
ax.set_ylabel("Zeměpisná šířka (°N)")
ax.legend(frameon=False, loc="lower left", markerscale=0.5)
ax.set_title(f"Ve všední ráno ubude nejvíc kol na stanici {nejvic_ubyva['name']} "
             f"({nejvic_ubyva['cisty_tok_za_rano']:.1f} kola/ráno),\n"
             f"nejvíc přibude na {nejvic_pribyva['name']} (+{nejvic_pribyva['cisty_tok_za_rano']:.1f}); "
             f"celkem je třeba přesunout ~{ubytek_celkem:.0f} kol každé ráno (jen členové)", loc="left")
fig.savefig("outputs/08_mapa_ranni_tok.png")
plt.show()

# --- Graf 9: nové × staré stanice ---
# Férově: jen období od 1. 4. 2026, kdy existovaly obě skupiny stanic. Nové stanice jsou
# jen obytné a univerzitní, proto srovnáváme i UVNITŘ stejného typu stanice.
od_otevreni = jizdy[jizdy["start_time"] >= OTEVRENI_NOVYCH_STANIC]
dni_od_otevreni = (OBDOBI_DO - OTEVRENI_NOVYCH_STANIC).days + 1
vykon = stanice[["station_id", "name", "station_type", "capacity", "nova"]].copy()
vykon["odjezdu_za_den"] = vykon["station_id"].map(od_otevreni.groupby("start_station_id")["trip_id"].count()) / dni_od_otevreni
assert round(vykon["odjezdu_za_den"].sum() * dni_od_otevreni) == len(od_otevreni)   # KONTROLA: součet odjezdů
vykon.to_csv("outputs/nove_vs_stare_stanice.csv", index=False, encoding="utf-8-sig")

vykon_typ = vykon.groupby(["station_type", "nova"])["odjezdu_za_den"].agg(["mean", "count"]).unstack("nova")
assert vykon_typ["count"].sum().sum() == len(stanice)
typy_s_novymi = vykon_typ.dropna().index.tolist()            # typy, kde jsou nové i staré stanice
print("Odjezdy za den od 1. 4. 2026 podle typu (False = staré, True = nové):\n", vykon_typ.round(2))
prumer_nove = vykon.loc[vykon["nova"], "odjezdu_za_den"].mean()
prumer_stare = vykon.loc[~vykon["nova"], "odjezdu_za_den"].mean()
rozdil_nove = (prumer_nove / prumer_stare - 1) * 100

fig, ax = plt.subplots(figsize=(9, 5))
for i, typ in enumerate(typy_s_novymi):
    for j, je_nova in enumerate([False, True]):
        hodnoty = vykon.loc[(vykon["station_type"] == typ) & (vykon["nova"] == je_nova), "odjezdu_za_den"]
        x = i * 2.6 + j
        ax.bar(x, hodnoty.mean(), color=MODRA if je_nova else SVETLE_SEDA, width=0.9)
        ax.scatter([x] * len(hodnoty), hodnoty, color=SEDA, s=12, zorder=3)   # tečky = jednotlivé stanice
        ax.text(x, hodnoty.max() + 0.05, f"{hodnoty.mean():.1f}\nn = {len(hodnoty)}", ha="center", va="bottom", fontsize=9)
        ax.text(x, -0.05, "nové" if je_nova else "staré", ha="center", va="top", fontsize=9)
ax.set_xticks([i * 2.6 + 0.5 for i in range(len(typy_s_novymi))])
ax.set_xticklabels([f"typ stanice: {t}" for t in typy_s_novymi])
ax.tick_params(axis="x", pad=18)
ax.grid(axis="x", visible=False)
ax.set_ylim(0, vykon["odjezdu_za_den"].max() * 1.3)
ax.set_ylabel("Odjezdy za den na stanici (1. 4. – 31. 10. 2026)")
ax.set_title(f"Nové stanice mají {prumer_nove:.1f} odjezdu denně, o {abs(rozdil_nove):.0f} % "
             f"{'více' if rozdil_nove > 0 else 'méně'} než staré ({prumer_stare:.1f});\n"
             f"více mají i ve srovnání se starými stanicemi stejného typu", loc="left")
fig.savefig("outputs/09_nove_vs_stare_stanice.png")
plt.show()



# -------------------------------------------------------------------------------------
# 10) DASHBOARD PRO PROVOZNÍHO ŘEDITELE
# -------------------------------------------------------------------------------------
trzba_celkem = jizdy["trzba_czk"].sum()
mesicni = (jizdy.groupby([jizdy["start_time"].dt.to_period("M"), "user_type"])
           .agg(jizd=("trip_id", "count"), trzba_czk=("trzba_czk", "sum")))
assert mesicni["jizd"].sum() == len(jizdy) and mesicni["trzba_czk"].sum() == trzba_celkem
mesicni_jizdy = mesicni["jizd"].unstack(fill_value=0)[TYPY]
mesicni_trzba = mesicni["trzba_czk"].groupby(level=0).sum()
x_mesice = mesicni_jizdy.index.to_timestamp()                # období -> datum, aby šlo na osu x

fig, osy = plt.subplots(2, 3, figsize=(17, 9.5))
fig.subplots_adjust(hspace=0.5, wspace=0.6)

# a) KPI dlaždice
ax = osy[0, 0]
ax.axis("off")
kpi = [(f"{len(jizdy):,}".replace(",", " "), "platných jízd (1. 3. 2025 – 31. 10. 2026)", MODRA),
       (f"{rust_celkem:+.0f} %", "jízd v III–X 2026 proti 2025", MODRA),
       (f"{trzba_celkem / 1000:,.0f} tis. Kč".replace(",", " "), "tržba bez vratek", MODRA),
       (f"{n_vadnych} kol", f"nepojízdných, ~{usly_prijem_rok / 1000:.0f} tis. Kč ušlé tržby/rok", ORANZOVA),
       (f"{payg_po:+.0f} %", f"jízd bez předplatného po zdražení (ostatní {ost_po:+.0f} %)",
        ORANZOVA if payg_po < 0 else MODRA)]
for i, (hodnota, popis, barva) in enumerate(kpi):
    ax.text(0, 0.95 - i * 0.2, hodnota, fontsize=17, fontweight="bold", color=barva, va="top")
    ax.text(0, 0.86 - i * 0.2, popis, fontsize=9.5, color=SEDA, va="top")
ax.set_title("OstraBike v číslech", loc="left")

# b) jízdy po měsících podle typu
ax = osy[0, 1]
dole = np.zeros(len(mesicni_jizdy))
for typ, barva in zip(TYPY, [MODRA, SVETLA_MODRA, SVETLE_SEDA]):
    ax.bar(x_mesice, mesicni_jizdy[typ], bottom=dole, width=25, color=barva, label=NAZVY_TYPU[typ])
    dole = dole + mesicni_jizdy[typ].values
ax.set_ylim(0, mesicni_jizdy.sum(axis=1).max() * 1.45)       # místo nahoře pro legendu
ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
ax.tick_params(axis="x", rotation=45)
ax.set_xlabel("Měsíc")
ax.set_ylabel("Jízd za měsíc")
ax.set_title(f"Nejvíc jízd v {mesicni_jizdy.sum(axis=1).idxmax().strftime('%m/%Y')} "
             f"({mesicni_jizdy.sum(axis=1).max():,}); členové = "
             f"{(jizdy['user_type'] == 'predplatne').mean() * 100:.0f} % jízd".replace(",", " "), loc="left")

# c) tržba po měsících
ax = osy[0, 2]
ax.plot(mesicni_trzba.index.to_timestamp(), mesicni_trzba.values / 1000, color=MODRA, linewidth=2, marker="o", markersize=3)
ax.axvline(ZMENA_CENY, color=SEDA, linestyle="--", linewidth=1)
ax.text(ZMENA_CENY, 2, " zdražení", fontsize=8, color=SEDA)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
ax.tick_params(axis="x", rotation=45)
ax.set_xlabel("Měsíc")
ax.set_ylabel("Tržba (tis. Kč / měsíc)")
ax.set_title(f"Tržba za měsíc; od zdražení bez předplatného {zmena_trzby_payg_po:+.0f} %", loc="left")

# d) nejhorší kola
ax = osy[1, 0]
nejhorsi = kolo_stat.head(12).iloc[::-1]                     # obráceně, ať je nejhorší nahoře
ax.barh(nejhorsi["bike_id"], nejhorsi["podil_kratkych"], color=[ORANZOVA if v else SVETLE_SEDA for v in nejhorsi["vadne"]])
ax.set_xlim(0, 100)
ax.set_xlabel(f"Podíl jízd ≤ {HRANICE_KRATKA_MIN} min (%)")
ax.set_ylabel("Kolo (bike_id)")
ax.set_title(f"Do servisu: {n_vadnych} kol, téměř všechny jízdy ≤ {HRANICE_KRATKA_MIN} min", loc="left")

# e) ranní tok – stanice s největším úbytkem a přírůstkem
ax = osy[1, 1]
krajni = pd.concat([toky.head(6), toky.tail(6)])
ax.barh(krajni["name"], krajni["cisty_tok_za_rano"], color=[ORANZOVA if t < 0 else MODRA for t in krajni["cisty_tok_za_rano"]])
ax.axvline(0, color=SEDA, linewidth=0.8)
ax.tick_params(axis="y", labelsize=8)
ax.set_xlabel("Čistý tok kol za všední ráno (kola)")
ax.set_ylabel("Stanice")
ax.set_title(f"Ráno přesunout ~{ubytek_celkem:.0f} kol z cílů zpět do obytných stanic", loc="left")

# f) změna ceny – meziroční změna jízd po skupinách
ax = osy[1, 2]
popisky = ["PAYG\npřed", "ostatní\npřed", "PAYG\npo", "ostatní\npo"]
hodnoty = [payg_pred, ost_pred, payg_po, ost_po]
ax.bar(popisky, hodnoty, color=[SVETLA_MODRA, SVETLE_SEDA, MODRA, SVETLE_SEDA])
for x, h in enumerate(hodnoty):
    ax.text(x, h, f"{h:+.0f} %", ha="center", va="bottom" if h >= 0 else "top", fontsize=9)
ax.axhline(0, color=SEDA, linewidth=0.8)
ax.set_ylim(min(hodnoty) * 1.3, max(hodnoty) * 1.4)          # místo pro popisky nad / pod sloupci
ax.set_ylabel("Změna jízd 2026 vs 2025 (%)")
ax.set_title(f"Po zdražení {'ubylo' if payg_po < 0 else 'přibylo'} jízd bez předplatného ({payg_po:+.0f} %)", loc="left")

fig.suptitle("OstraBike – provozní přehled", x=0.07, ha="left", fontsize=16, fontweight="bold")
fig.savefig("outputs/10_dashboard.png")
plt.show()



# -------------------------------------------------------------------------------------
# 11) SOUHRN ČÍSEL PRO ZÁVĚR
# -------------------------------------------------------------------------------------
souhrn = pd.DataFrame([
    ("platné jízdy", len(jizdy)),
    ("průměr jízd za den (celý kalendář)", round(denni["jizd"].mean(), 1)),
    ("růst jízd III–X 2026 vs 2025 (%)", round(rust_celkem, 1)),
    ("růst jízd jen staré stanice (%)", round(rust_stare, 1)),
    ("jízd za °C (suché dny)", round(sklon, 2)),
    ("efekt deštivého dne (%)", round(efekt_deste, 1)),
    ("vadná kola", n_vadnych),
    ("ušlý příjem za rok (Kč)", round(usly_prijem_rok)),
    ("zaplaceno za nepovedené jízdy (Kč)", zaplaceno_za_poruchy),
    ("PAYG změna jízd VI–X (%)", round(payg_po, 1)),
    ("ostatní změna jízd VI–X (%)", round(ost_po, 1)),
    ("rozdíl v rozdílech (p. b.)", round(did, 1)),
    ("tržba PAYG VI–X změna (%)", round(zmena_trzby_payg_po, 1)),
    ("kol k přesunu každé ráno", round(ubytek_celkem, 1)),
    ("nové vs staré stanice – odjezdy (%)", round(rozdil_nove, 1)),
    ("tržba celkem (Kč)", trzba_celkem),
    ("vratky (Kč)", vratky_czk),
], columns=["ukazatel", "hodnota"])
souhrn.to_csv("outputs/souhrn.csv", index=False, encoding="utf-8-sig")
print(souhrn.to_string(index=False))
