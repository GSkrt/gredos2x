# GREDOS2X (v 1.0.5) - Pretvornik Gredos modela v druge formate 

Posodobitve : 

Posodobljen PIP paket.  Dodan izvoz v PostGIS bazo. 
Preverjeno je bilo delovanje na Windows sistemu. 


gredos2x package aims to be a comprehensive set of tools to convert Slovenian (Gredos) distribution power system model to other formats. 
As such is a simple conversion program to other formats such as open source load flow programs and other end points such as GIS. 
Main goal of this package is to make a simple conversion of formats to enable integration of GIS data for other (closed and open source) simulators.

Gradnja izvoznih datotek za druge programske pakete je zaželena kot tudi širitve modela v druge oblike. 

Gredos2x je paket za pretvorbo Gredos podatkovnih virov v druge formate. Trenutno je implementiran le izvoz v gpkg (geografsko datotečno podatkovno bazo). 
Cilj paketa je poenotiti izvoze v druge formate za simulacijo na osnovi odprtokodne iniciative, ki lahko omogočijo širitev analiz na druge platforme in 
simulacijske programe. S tem paketom je omogočena osnovna analiza. 

## Zgodovina modela: 

Gredos je simulacijski program za izračune pretokov moči v omrežju, ki ga v Sloveniji uporabljamo za 
osnovne statične analize pretokov moči v sistemu in je nastal leta 1991 pod okriljem EIMV. Kot tak je model celovit in ga uporabljamo za optimizacijo distribucijskega omrežja. Podatke distributerji v platformi redno posodabljajo v skladu z izdelavo dolgoročnih razvojnih načrtov (REDOS). Pomanjkljivost trenutnega modela je v integraciji z drugimi sistemi, saj je geografski del vezan na (dwg) datoteke, ki jih ni možno enostavno posodabljati z direktno integracijo v GIS. Celoten model se tako ročno posodablja. 

Prav zaradi tega dolgoročno nima prihodnosti. 

## Cilji tega paketa 

Cilji tega orodja za transformacijo modela so preprosti: izvesti pretvorbo podatkovnega modela v druge oblike, ki bo omogočala uporabo širšega spektra simulatorjev in njihovih funkcionalnosti, poleg tega pa omogočiti lažji prehod na integriran model z GIS. 
Kljub pomanjkljivostim in dologoročno nezadostnim izhodiščem je to trenutno edini model, ki je poenoten za celotno Slovenijo in konvergira. 

V izhodišču model tako zgolj pretvarja podatkovna izhodišča Gredos v združeno datoteko temelječo na GPKG formatu . Nadgradnja pa bo v prihodnje sledila z izvozom in verzioniranjem v GIS. S prehodom na GIS podatkovno bazo bo omogočena tudi integracija modela z drugimi viri kot je npr. GIS, SCADA ali AMI, kar trenutni model ne omogoča. 
 
##  Instalacija

        pip install gredos2x


## Opis funkcionalnosti 

Dokumentacija razredov se nahaja ([tukaj](https://gskrt.github.io/gredos2x/index.html))

Vhodni podatki so: 

Zgrajena sta dva modula: gredos2gpkg(), za uvoz podatkov v geopackage in gredos_gpkg2dataframes(), ki pretvarja podatke nazaj v geopandas dataframe ali pandas dataframe. Širitev modela se lahko izvede kasneje po izgradnji modula gredos2postgis modula. 
Dodatno se po novem podatke lahko izvaža v postgresql s postgis modulom. 

gredos.mdb - osnovna datoteka projekta
materiali.mdb - osnovna MDB datoteka z materiali modela
shp datoteke - LNODE.shp, POINT.shp , LINE.shp

Pred začetkom izvoza je potrebno v Gredos programskem paketu zagnati izvoz geografije (Gredos izvoz v shp). Možen je tudi uvoz brez slednje, vendar je 
za preglednost rezultatov te smiselno imeti v projektu, saj je prav podpora geografiji eden izmed ključnih elementov učinkovitega načrtovanja. 


Ta trenutno še ni pripravljena za produkcijo zato ni del tega projekta. 
Vsi koraki v programskem paketu so zastavljeni tako, da se zaključujejo preko GIS podprtega formata (GPKG), saj je ključ združiti vse informacije modela na enem mestu. 
S podporo podatkovne baze bo model pridobil možnost verzioniranja, kar je ključna lastnost načrtovalskega procesa. 

Verzije morajo biti vezane na spremembe modela zaradi načrtovalskega procesa in verzije posodobitve modela. Nadgradnja v tej smeri sledi.


## Primer izvoza v GPKG datoteko in branja iz nje 

V spodnjem primeru je imenik v katerem se nahajajo Gredos datoteke vključno z geografskimi datotekami: tests/testnetwork/

Povezave na osnovno mdb datoteko modela so izvedene tako z naslednjimi povezavami: 

                'tests/testnetwork/testnetwork.mdb'
                'tests/testnetwork/material_2000_v10.mdb'

Rezultat je gpkg geografska datoteka z vsemi podatki združenimi v root imeniku z imenom : 'izvoz.gpkg'



```python
from gredos2x.gredos2gpkg import Gredos2GPKG
from gredos2x.gredos_gpkg2dataframes import GredosGPKG2df

#izvoz datoteke v EPSG:3794 -> definiran je koordinatni sistem in izvoz v datoteko 'izvoz.gpkg'
gu = Gredos2GPKG('tests/testnetwork/testnetwork.mdb', 'tests/testnetwork/material_2000_v10.mdb','izvoz.gpkg')
gu.pozeni_uvoz(True,pretvori_crs=True,set_crs='EPSG:3794')

#izvoz datoteke v EPSG:4326 -> definiran je koordinatni sistem in izvoz v datoteko 'izvoz_wgs84.gpkg'
gu.gpkg_path = 'izvoz_wgs84.gpkg'
gu.pozeni_uvoz(True, pretvori_crs=True, set_crs='EPSG:4326')

#preberemo vsebino datoteke nazaj v dataframe, ki smo ga pretvorili v EPSG:3794

rd = GredosGPKG2df('izvoz.gpkg',pregled_vsebine=True)
spisek_tabel = rd.list_gpkg_tables()
print(spisek_tabel)

# nalaganje negeografskih datotek (običajno dovolj za izvoz v druge formate in sestavo modela)
material = rd.nalozi_negeografsko_tabelo('MATERIAL')

node = rd.nalozi_negeografsko_tabelo('Node')
section = rd.nalozi_negeografsko_tabelo('Section') #za faktorje polaganja 
transformer = rd.nalozi_negeografsko_tabelo('Transformer')
sw_device = rd.nalozi_negeografsko_tabelo('Switching_device')
branch = rd.nalozi_negeografsko_tabelo('Branch')


# Za pregled in deljenje geografskih podatkov (ali prikaz na kakšnem izmed GIS Python prikazovalniku)
# Navajeni smo, da se rezultati prikazujejo geografsko ob posameznem grafičnem elementu na zemljevidu, kar je dobra praksa za SNO še posebej pa za NNO omrežje

lnode = rd.preberi_geografsko_tabelo_iz_gpkg('LNODE_geo',epsg_set='EPSG:3794')
point = rd.preberi_geografsko_tabelo_iz_gpkg('POINT_geo',epsg_set='EPSG:3794')
line = rd.preberi_geografsko_tabelo_iz_gpkg('LINE_geo',epsg_set='EPSG:3794')
```

Dodan je izvoz v postgis bazo: 
```python
from gredos2x.gredos2pgsql import Gredos2PGSQL

 
parametri_povezave = {
                "drivername": "postgresql+psycopg2",
                "username": "",
                "password": "",
                "host": "",
                "port": "5432",
                "database": ""
            }

g2pgsql = Gredos2PGSQL('tests/testnetwork/testnetwork.mdb', 'tests/testnetwork/material_2000_v10.mdb',parametri_povezave_pgsql=parametri_povezave)
g2pgsql.pozeni_uvoz(True, pretvori_crs=True, set_crs='EPSG:3794')
```

TODO: dokumentacija
