from gredos2x.gredos2gpkg import Gredos2GPKG

# definiramo najprej vse uvozne in izvozne poti 

gredos_mdb_povezava = r"C:\Users\ep5065\OneDrive - Elektro Primorska d.d\GREDOS\Gredos 2026\modeli\26_1_2026\26_1_2026.mdb"
gredos_materiali_povezava = r"C:\GredosMO_10\Defaults\material_2000_v10.mdb"
izvozi_v = r"C:\Users\ep5065\OneDrive - Elektro Primorska d.d\GREDOS\Gredos 2026\modeli\26_1_2026\referencni_modeli_izvoz.gpkg"


# poženemo, v imeniku izvozi_v se pojavi datoteka
gredos2gpkg = Gredos2GPKG(povezava_mdb=gredos_mdb_povezava, pot_materiali=gredos_materiali_povezava, povezava_gpkg=izvozi_v)
gredos2gpkg.pozeni_uvoz(show_progress=True, pretvori_crs=True, set_crs='EPSG:3912')
