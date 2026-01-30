 # 
 # Copyright (c) 2022 Gregor Skrt.
 # 
 # This program is free software: you can redistribute it and/or modify  
 # it under the terms of the GNU General Public License as published by  
 # the Free Software Foundation, version 3.
 #
 # This program is distributed in the hope that it will be useful, but 
 # WITHOUT ANY WARRANTY; without even the implied warranty of 
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 # General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License 
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #


import os
import urllib
from sqlalchemy import create_engine, exc
from sqlalchemy.engine import URL
from sqlalchemy.sql import text
from sqlalchemy.types import LargeBinary
import geopandas as gpd
import pandas as pd
from datetime import datetime
import time
import sys, subprocess
import io
from shutil import which

class Gredos2MSSQL:
    """
        Gredos2MSSQL je orodje ETL za izvoz modela energetskega sistema Gredos in pretvorbo tabel v MS SQL Server, ki združuje vse razpoložljive podatkovne vire za gradnjo modela.
        Poleg definicije povezav in parametrov baze, je potrebno določiti tudi ime sheme, kamor se podatki shranjujejo. Gre za osnovni prenos podatkov in ne za podatkovno vodenje
        tabel v bazi.
        
        
        Jedro uvoza je sestavljeno tako, da deluje tudi na linux sistemu. Pri tem je potrebno imeti instaliran mdb-tools paket za linux.
        Za debian sistme se ga namesti z : sudo apt install mdb-tools (Debian). Na Windows sistemu uporabimo ""Microsoft Access Driver (*.mdb, *.accdb)", ki ga dobimo poleg
        acess programa ali pa ga instaliramo posebej.
        
        Pri inicializaciji razreda se preveri tudi povezava. V kolikor povezava ni uspešna se rezultat izpiše v terminalu.
        
        Prilagojena je za Linux in Windows OS.
        
        Args:
            povezava_mdb (str): povezava do mdb datoteke osnovnega modela (mdb)
            pot_materiali (str): povezava do datoteke materialov (npr.material_2000_v10.mdb)
            parametri_povezave_mssql (dict): parametri povezave mssql (klasični zapis)
            ime_sheme (str): ime sheme v mssql bazi, kamor se bodo tabele izvozile (shema mora predhodno obstajati)

            Primer `parametri_povezave_mssql`:
                "drivername": "ODBC Driver 17 for SQL Server", # Ali drug ustrezen ODBC gonilnik
                "username": "vpisi_uporabnisko_ime_s_pravicami_za_pisanje",
                "password": "geslo",
                "host": "naslov_streznika",
                "port": 1433, 
                "database": "podatkovna_baza"
            }
    """
    def __init__(self, povezava_mdb='', pot_materiali='', parametri_povezave_mssql = {}, ime_sheme='ep'):
        self.table_prefix = 'g2x_'
        self.mdb_povezava = os.path.normpath(povezava_mdb)
        self.pot_materiali = os.path.normpath(pot_materiali)
        self.gredos_file_name = os.path.basename(self.mdb_povezava).split('.')[0]
        self.spisek_tabel = ['LNode', 'Node', 'Section', 'Transformer', 'Switching_device','Branch']
        self.mdb_driver = "Microsoft Access Driver (*.mdb, *.accdb)"
        self.ime_sheme = ime_sheme
        if parametri_povezave_mssql: 
            self.dict_povezava = parametri_povezave_mssql
        else:             
            self.dict_povezava = {
                "drivername": "ODBC Driver 17 for SQL Server", # Ali drug ustrezen ODBC gonilnik
                "username": "vpisi_uporabnisko_ime_s_pravicami_za_pisanje",
                "password": "geslo",
                "host": "naslov_streznika",
                "port": 1433, 
                "database": "podatkovna_baza"
            }
        
        if sys.platform.startswith('win'):
            #TODO: make ODBC driver check and auto discovery mechanism using pyodbc package listing...
            connection_string = (
                f"DRIVER={self.mdb_driver};"
                f"DBQ={povezava_mdb};"

            )
            connection_uri = f"access+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
            self.connection_mdb = create_engine(connection_uri).connect()
            
        if sys.platform.startswith('lin'):
            print('Linux power')
        else:  
            print(f"Platform {sys.platform} is not supported.")
            
        # vzpostavimo povezavo še s mssql 
        params = urllib.parse.quote_plus(
            f"DRIVER={self.dict_povezava.get('drivername', '{ODBC Driver 17 for SQL Server}')};"
            f"SERVER={self.dict_povezava.get('host')};"
            f"DATABASE={self.dict_povezava.get('database')};"
            f"UID={self.dict_povezava.get('username')};"
            f"PWD={self.dict_povezava.get('password')};"
            "APP=gredos_etl;"
        )

        connection_uri_mssql = f"mssql+pyodbc:///?odbc_connect={params}"

        self.mssql_engine = create_engine(connection_uri_mssql)
        
        try:
    # Connect to the database and execute a simple query
            with self.mssql_engine.connect() as connection:
                query = text("SELECT 1")
                result = connection.execute(query)
                if result.scalar() == 1:
                    print("Database is responding.")
                else:
                    print("Database responded but returned an unexpected result.")
        except exc.SQLAlchemyError as e:
            print(f"An error occurred while connecting to the database: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
        shema_exists = self.check_schema_exists(self.mssql_engine, self.ime_sheme)
            
        if shema_exists: 
            pass
        else: 
            print(f"Shema {self.ime_sheme} ni v podatkovni bazi.Potrebno jo je še ustvariti")
        
        
        
    def check_schema_exists(self,engine, schema_name):
        """Preveri ali shema v bazi obstaja. 

        Args: 
            engine (sqlalchemy.engine.base.Engine): Sqlalchemy engine
            schema_name (str): ime sheme

        Returns:
            bool: True, če shema obstaja...
        """
        try:
            with engine.connect() as connection:
                query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name")
                query = query.bindparams(schema_name=schema_name)
                result = connection.execute(query)
                return result.fetchone() is not None
        except exc.SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return False

    def _add_table_comment(self, connection, table_name, comment):
        """Adds extended property description to the table."""
        safe_comment = comment.replace("'", "''")
        sql = f"""
        EXEC sys.sp_addextendedproperty 
          @name = N'MS_Description', 
          @value = N'{safe_comment}', 
          @level0type = N'SCHEMA', @level0name = N'{self.ime_sheme}', 
          @level1type = N'TABLE',  @level1name = N'{table_name}';
        """
        try:
            connection.execute(text(sql))
        except Exception as e:
            print(f"Warning: Could not add comment to table {table_name}: {e}")


    def pd_dataframe_v_mssql(self, pd_dataframe, mssql_engine, table_name):
        """Shrani datoteke v podatkovno bazo. 
        
        Args: 
            pd_dataframe (pandas.DataFrame): dataframe to transfer
            mssql_engine (sqlachemy engine): sqlalchemy mssql engine 
            table_name (str):  table name
        """
        
        prefixed_table_name = f"{self.table_prefix}{table_name}"
        pd_dataframe.to_sql(prefixed_table_name, mssql_engine, schema =self.ime_sheme, if_exists='replace', index=False)
        
        with mssql_engine.connect() as connection:
            self._add_table_comment(connection, prefixed_table_name, f"Source MDB: {self.mdb_povezava}")
            connection.commit()

    def _geodf_to_mssql(self, gdf, table_name, srid):
        """
        Helper function to write a GeoDataFrame to SQL Server.
        It converts geometries to WKB and uses raw SQL INSERTs. It's a helper to write to MSSQL table with geometry. 
        """
        prefixed_table_name = f"{self.table_prefix}{table_name}"
        # Create a copy to avoid modifying the original GeoDataFrame
        df = gdf.copy()
        # Convert geometry to WKB and drop the original geometry column
        df['geom_wkb'] = df['geometry'].apply(lambda g: g.wkb if g else None)
        df = df.drop('geometry', axis=1)

        # Reset index to write it as a regular column 'id' without creating a DB index
        df.index.name = 'id'
        df = df.reset_index()

        with self.mssql_engine.connect() as connection:
            trans = connection.begin()
            try:
                # 1. Upload data with WKB string using pandas.to_sql
                df.to_sql(
                    prefixed_table_name,
                    connection,
                    schema=self.ime_sheme,
                    if_exists='replace',
                    index=False,
                    dtype={'geom_wkb': LargeBinary}
                )

                # 1.1 Set Primary Key on id
                alter_col_sql = f"ALTER TABLE {self.ime_sheme}.{prefixed_table_name} ALTER COLUMN id BIGINT NOT NULL;"
                connection.execute(text(alter_col_sql))

                add_pk_sql = f"ALTER TABLE {self.ime_sheme}.{prefixed_table_name} ADD CONSTRAINT PK_{prefixed_table_name} PRIMARY KEY (id);"
                connection.execute(text(add_pk_sql))

                # 2. Add a GEOMETRY column to the new table
                add_geom_col_sql = f"ALTER TABLE {self.ime_sheme}.{prefixed_table_name} ADD Shape GEOMETRY;"
                connection.execute(text(add_geom_col_sql))
           
                # 3. Update the table, converting WKB to GEOMETRY
                update_geom_sql = f"UPDATE {self.ime_sheme}.{prefixed_table_name} SET Shape = geometry::STGeomFromWKB(geom_wkb, {srid}) WHERE geom_wkb IS NOT NULL;"
                connection.execute(text(update_geom_sql))
               
                # 4. Drop the temporary WKB column
                drop_wkb_col_sql = f"ALTER TABLE {self.ime_sheme}.{prefixed_table_name} DROP COLUMN geom_wkb;"
                connection.execute(text(drop_wkb_col_sql))

                # 5. Create Spatial Index
                if not gdf.empty and gdf['geometry'].notna().any():
                    minx, miny, maxx, maxy = gdf.total_bounds
                    # Expand bounds slightly to avoid boundary issues and ensure xmin < xmax
                    pad = 100
                    minx, miny, maxx, maxy = minx - pad, miny - pad, maxx + pad, maxy + pad
                    
                    spatial_index_sql = f"""
                        CREATE SPATIAL INDEX [SI_{prefixed_table_name}] ON {self.ime_sheme}.{prefixed_table_name}(Shape)
                        WITH ( BOUNDING_BOX = ( {minx}, {miny}, {maxx}, {maxy} ) );
                    """
                    connection.execute(text(spatial_index_sql))

                self._add_table_comment(connection, prefixed_table_name, f"Source MDB: {self.mdb_povezava}")

                trans.commit()
            except Exception as e:
                print(f"Error writing spatial data: {e}")
                trans.rollback()
                raise

    def shp_to_mssql(self,filepath_shp, ime_tabele, pretvori_crs = False, set_crs = 'EPSG:3794'):
        """Pretvorba iz SHP v geodataframe in uvoz v SQL Server.
            Uporablja spremenljivko razreda self.mssql_engine za povezavo z bazo. Potrebno pa je definirati shemo v bazi, ki mora predhodno obstajati.

        Args:
            filepath_shp (str): lokacija shp datoteke
            ime_tabele (str): Ime tabele za izvoz
            pretvori_crs (bool, optional): _Pretvori crs pri izvozu ?_. Defaults to False.
            set_crs (str, optional): Izhodni koordinatni sistem. Defaults to 'EPSG:3912'. Pretvorba je zanimiva predvsem v 'EPSG:3794'
        """
        shp = gpd.GeoDataFrame.from_file(filepath_shp, crs='EPSG:3912', encoding='cp1250')
        shp.set_crs('EPSG:3912', inplace=True)
        srid = 3912
        if pretvori_crs: 
            shp.to_crs(crs=set_crs, inplace=True)
            srid = int(set_crs.split(':')[-1])
        else: 
            set_crs = 'EPSG:3912' #pustimo crs v obliki, ki jo ima trenutno Gredos
        
        self._geodf_to_mssql(shp, ime_tabele, srid)

    def mdb_2_mssql(self, show_progress = False):
        """Osnovna funkcija za uvoz podatkov. Imena uvoznih tabel so predefinirana, prav tako format in tip podatkov uvoza. Pomembno, ker so nekateri modeli s šiframi v drugih formatih.
           Osnovni spisek imen tabel v mdb je definiran spremenljivki razreda spisek_tabel.

        Args:
            show_progress (bool): V terminalu prikaže proces nalaganja posamezne tabele ali seznam vseh tabel (samo linux).
        """
        if os.path.exists(self.mdb_povezava):
            if sys.platform.startswith('win'): 
                for ime_tabele_v_bazi in self.spisek_tabel:
                    if show_progress: 
                        print(f"Uvažam tabelo {ime_tabele_v_bazi} v Windows okolju.")
                    sql = text(f"select * from {ime_tabele_v_bazi}")
                    pd_tabela = pd.read_sql_query(sql, self.connection_mdb) 
                    self.pd_dataframe_v_mssql(pd_tabela, self.mssql_engine, ime_tabele_v_bazi)
            if sys.platform.startswith('linux'):
                available_tables = subprocess.Popen(["mdb-tables", self.mdb_povezava],
                                        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
                if show_progress: 
                    print(available_tables)
                if which('mdb-export') is not None: #shutil which za preverit ali je mdb-tables instaliran
                    
                    for ime_tabele_v_bazi in self.spisek_tabel:
                        if show_progress: 
                            print(f"Podatke uvažam z mdb-tools (Linux): tabela : {ime_tabele_v_bazi}")
                        contents = subprocess.Popen(["mdb-export", self.mdb_povezava,ime_tabele_v_bazi],
                                        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
                        
                        # weird import declarations (String IDs with numbers only - Only in Gredos ?!)
                        types = None
                        if ime_tabele_v_bazi.startswith('Node'): 
                            
                            types = {'NodeId':str, 'LNodeId': str, 'XDbId':str, 'OrgId':str}
                        if ime_tabele_v_bazi.startswith('Branch'): 
                            types = {'BranchId': str, 'FeederBrId':str, 'XDbId':str, 'Node1':str, 'Node2':str}
                        if ime_tabele_v_bazi.startswith('LNode'): 
                            types = {'LNodeId': str, 'OrgId':str}
                        if ime_tabele_v_bazi.startswith('Section'): 
                            types = {'BranchId': str}
                            
                        pd_tabela = pd.read_csv(io.StringIO(str(contents)),sep=',', header=0, converters=types, encoding='cp1250', index_col=False, engine='python')
                        self.pd_dataframe_v_mssql(pd_tabela, self.mssql_engine, ime_tabele_v_bazi)
                  
            

    def uvozi_podatke_materialov_mdb(self):
        """
            Metoda razreda za uvoz podatkov materialov iz Gredos v MS SQL Server bazo. Datoteke na Windows platformi beremo z {Microsoft Access Driver (*.mdb, *.accdb)}, 
            uvoz podatkov na linux platformi pa temelji na osnovi mdb-tools.
            
            Datoteka materialov se običajno v distribuciji Gredos nahaja v imeniku C:\GredosMO\Defaults
            
            Returns:
                True, če je uvoz uspešen, sicer False.
            
        """
        
        if sys.platform.startswith('win'): 
            connection_string = (
                u"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                f"DBQ={self.pot_materiali};"
            )
            connection_uri = f"access+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
            con_material = create_engine(connection_uri).connect()

            sql_material = text("select * from MATERIAL")

            try:
                #stlačim še materiale v postgresql
                material = pd.read_sql_query(sql_material, con_material, dtype=str)
                self.pd_dataframe_v_mssql(material, self.mssql_engine, 'MATERIAL')

                return True
            except Exception as e:
                return False
            
        if sys.platform.startswith('lin'): 
            contents = subprocess.Popen(["mdb-export", self.pot_materiali,'MATERIAL'],
                                    stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
            try: 
                tabela = pd.read_csv(io.StringIO(str(contents)),sep=',', header=0, encoding='cp1250', index_col=False)
                self.pd_dataframe_v_mssql(tabela, self.mssql_engine, 'MATERIAL')
                return True
            except Exception as e:
                return False
            
            

    def uvozi_geografske_datoteke(self, show_progress=False, pretvori_crs = False, set_crs='EPSG:3794'):
        """
        
         Uvozi podatke SHP gredos  kot  geografsko plast  v  MS SQL Server.
         v Default EPSG koda je 3912 (GK48), med prenosom je možna pretvorba iz tega v drug koordinatni sistem, ki je kompatibilen z GIS ali
         drugimi prikazovalniki, ki imajo npr. podlago za prikaz v WGS84. S tem smo pokrili večino uporabniških primerov.
        
        Args:
            show_progress (bool, optional): Prikaži napredek uvoza. Defaults to False.
            pretvori_crs (bool, optional): Pretvori v drug crs (default 3794). Defaults to True.
            set_crs (str, optional): Sets CRS of conversion data.
        Returns:
            bool: True, če je število uvoženih SHP datotek pod 3 (POINT, LNODE, LINE). Če bi se v imeniku nahajalo več datotek SHP bi tako vrnil napako.
            Slednje se običajno zgodi, ko je v uvoznem imeniku, kjer se nahaja temeljna mdb datoteka več datotek. 
        """

        imenik_projekta =os.path.dirname(self.mdb_povezava)
        onlyfiles = [f for f in os.listdir(imenik_projekta) if os.path.isfile(os.path.join(imenik_projekta, f))]
        i = 0
        
        for file in onlyfiles:
            splitfile = file.split('.')
            if 'POINT' in splitfile[0]:
                i = i + 1
                if 'shp' in splitfile[1]:
                    if show_progress: 
                        print(f"Uvažam: {file}")
                    self.shp_to_mssql(os.path.join(imenik_projekta,file), ime_tabele='POINT_geo' ,pretvori_crs=pretvori_crs, set_crs=set_crs)
                    
            if 'LINE' in splitfile[0]:
                i = i + 1
                if 'shp' in splitfile[1]:
                    if show_progress: 
                        print(f"Uvažam: {file}")
                    self.shp_to_mssql(os.path.join(imenik_projekta,file), ime_tabele='LINE_geo' ,pretvori_crs=pretvori_crs, set_crs=set_crs)
                    
            if 'LNODE' in splitfile[0]:
                i=i + 1
                if 'shp' in splitfile[1]:
                    if show_progress: 
                        print(f"Uvažam: {file}")
                    self.shp_to_mssql(os.path.join(imenik_projekta,file), ime_tabele='LNODE_geo', pretvori_crs=pretvori_crs, set_crs=set_crs)
                   
        if i == 3:
            return False
        else:
            return True

    def pozeni_uvoz(self, show_progress = False, pretvori_crs = False, set_crs = 'EPSG:3794'):
        """ Izvozi vse podatke Gredos v MSSQL  podatkovno bazo, pred tem je potrebno definirati shemo v katero bomo izvažali podatke. 
            Omogoča tudi pretvorbo koordinatnega sistema v druge oblike npr. WGS84 za spletne aplikacije ali EPSG:3794 (D96/TM Slovenski koordinatni sistem).


        Args:
            show_progress (bool, optional): med izvozom prikazuj obvestila v terminalu.
            pretvori_crs (bool, optional): pretvori v drug koordinatni sistem npr. wgs84 (EPSG:4326) ali epsg: 3794 (Geodetic CRS: Slovenia 1996).
            set_crs (str): crs string npr. EPSG:3912 (izvorni crs).
        Returns:
            bool: True, če je geografske datoteke ustrezno uvozilo.
        """
        
        uvozeno = self.uvozi_geografske_datoteke(show_progress=True, pretvori_crs=pretvori_crs, set_crs=set_crs)
        self.mdb_2_mssql(show_progress=True)
        self.uvozi_podatke_materialov_mdb()
        

        return uvozeno
