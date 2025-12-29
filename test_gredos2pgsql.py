from gredos2x.gredos2pgsql import Gredos2PGSQL

#izvoz datoteke v EPSG:3794 -> definiran je koordinatni sistem in izvoz v datoteko 'izvoz.gpkg'
#gu = Gredos2GPKG('tests/testnetwork/testnetwork.mdb', 'tests/testnetwork/material_2000_v10.mdb','tests/testnetwork/izvoz.gpkg')
#gu.pozeni_uvoz(True,pretvori_crs=True,set_crs='EPSG:3794')



parametri_povezave = {
                "drivername": "postgresql+psycopg2",
                "username": "postgres",
                "password": "your password",
                "host": "localhost",
                "port": "5432",
                "database": "postgres"
            }

g2pgsql = Gredos2PGSQL('tests/testnetwork/testnetwork.mdb', 'tests/testnetwork/material_2000_v10.mdb',parametri_povezave_pgsql=parametri_povezave)
g2pgsql.pozeni_uvoz(True, pretvori_crs=True, set_crs='EPSG:3794')



