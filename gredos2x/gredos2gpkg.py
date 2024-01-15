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
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import geopandas as gpd
import pandas as pd
from datetime import datetime
import time
import sys, subprocess
import io
from shutil import which


class Gredos2GPKG:
    """
        Gredos2GPKG je orodje ETL za izvoz modela energetskega sistema Gredos in pretvorbo v GPKG datoteko, ki združuje vse razpoložljive podatkovne vire za gradnjo modela.
        Jedro uvoza je sestavljeno tako, da deluje tudi na linux sistemu. Pri tem je potrebno imeti instaliran mdb-tools paket za linux. 
        Za debian sistme se ga namesti z : sudo apt install mdb-tools 
        
        Args: 
        
            povezava_mdb (string) : povezava do mdb datoteke osnovnega modela
            pot_materiali (string) : povezava do datoteke materialov (npr.material_2000_v10.mdb)
            gpkg_ime (string) : ime in lokacija datoteke GPKG npr. izvoz.gpkg
            insert_strategy (string)
    """
    def __init__(self, povezava_mdb='', pot_materiali='', povezava_gpkg=''):
        self.mdb_povezava = os.path.normpath(povezava_mdb)
        self.pot_materiali = os.path.normpath(pot_materiali)
        self.gredos_file_name = os.path.basename(self.mdb_povezava).split('.')[0]
        self.spisek_tabel = ['LNode', 'Node', 'Section', 'Transformer', 'Switching_device','Branch']
        self.mdb_driver = "Microsoft Access Driver (*.mdb, *.accdb)"
        
        
        
        if povezava_gpkg == '' and povezava_mdb != '':
            self.gpkg_path = os.path.join('intmodel',
                                            self.gredos_file_name + '.gpkg')
        else:
            self.gpkg_path = os.path.relpath(povezava_gpkg)

        # počistimo staro datoteko, če obstaja in ima isto ime. 
        if os.path.exists(self.gpkg_path):
            try: 
                os.remove(self.gpkg_path)
            except Exception as e:
                pass
        
        if sys.platform.startswith('win'):
            #TODO: make ODBC driver check and auto discovery mechanism using pyodbc package listing...
            connection_string = (
                f"DRIVER={self.mdb_driver};"
                f"DBQ={povezava_mdb};"

            )
            connection_uri = f"access+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
            self.connection = create_engine(connection_uri).connect()
            
        else: 
            print(f"Platform {sys.platform} is not supported.")

    def pd_dataframe_to_gpkg(self, pd_dataframe, geopackage_pth, table_name):
        """Transfer pandas dataframe to geopackage.

        Args:
            pd_dataframe (pd.DataFrame): dataframe to transfer
            geopackage_pth (str): location of geopackage file 
            table_name (str):  table name
        """
        engine = create_engine(f'sqlite:///{geopackage_pth}', echo=False) #uses only absolute paths ?! or relative wtf 
        #connection = engine.connect() # pandas using engine and not connection 2022
        pd_dataframe.to_sql(table_name, engine, if_exists='replace', index=False)

    def shp_to_geopackage(self,filepath_shp, geopackage_pth, layer_name, pretvori_crs = False, set_crs = 'EPSG:3794'):
        """ Pretvorba iz SHP v geodataframe. Ta metoda razreda ni uporabljena direktno, lahko pa se jo uporabo ob morebitnih novih virih. 

        Args:
            filepath_shp (_type_): lokacija shp datoteke za pretvorbo 
            geopackage_pth (_type_): lokacija gpkg datoteke za izvoz 
            layer_name (_type_): ime plasti v gpkg datoteki 
            crs_conversion (bool, optional): Pretvori v drug koordinatni sistem (True/False). Defaults to False.
            set_crs (str, optional): Izhodni koordinatni sistem. Defaults to 'EPSG:3912'. Pretvorba je zanimiva predvsem v 'EPSG:3794'
        """
        shp = gpd.GeoDataFrame.from_file(filepath_shp, crs='EPSG:3912', encoding='cp1250')
        shp.set_crs('EPSG:3912', inplace=True)
        if pretvori_crs: 
            shp.to_crs(crs=set_crs, inplace=True)
        else: 
            set_crs = 'EPSG:3912' #pustimo crs v obliki, ki jo ima trenutno Gredos
        shp.to_file(geopackage_pth, driver='GPKG', layer=layer_name, crs=set_crs,  encoding='cp1250')

    def uvozi_podatke_mdb(self, show_progress = False):
        """Osnovna funkcija za uvoz podatkov. Imena uvoznih tabel so predefinirana, prav tako format in tip podatkov uvoza. Pomembno, ker so nekateri modeli s šiframi v drugih formatih.

            Args: 
            
                show_progress(bool): V terminalu prikaže proces nalaganja posamezne tabele ali seznam vseh tabel (samo linux). 
        
        """
        if os.path.exists(self.mdb_povezava):
            if sys.platform.startswith('win'): 
                for ime_tabele in self.spisek_tabel:
                    if show_progress: 
                        print(f"Uvažam tabelo {ime_tabele} v Windows okolju.")
                    sql = text(f"select * from {ime_tabele}")
                    tabela = pd.read_sql_query(sql, self.connection)
                    self.pd_dataframe_to_gpkg(tabela, self.gpkg_path, ime_tabele)
            if sys.platform.startswith('linux'):
                available_tables = subprocess.Popen(["mdb-tables", self.mdb_povezava],
                                        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
                if show_progress: 
                    print(available_tables)
                if which('mdb-export') is not None: #shutil which za preverit ali je mdb-tables instaliran
                    
                    for ime_tabele in self.spisek_tabel:
                        if show_progress: 
                            print(f"Podatke uvažam z mdb-tools (Linux): tabela : {ime_tabele}")
                        contents = subprocess.Popen(["mdb-export", self.mdb_povezava,ime_tabele],
                                        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
                        
                        # weird import declarations (String IDs with numbers only - Only in Gredos ?!)
                        types = None
                        if ime_tabele.startswith('Node'): 
                            
                            types = {'NodeId':str, 'LNodeId': str, 'XDbId':str, 'OrgId':str}
                        if ime_tabele.startswith('Branch'): 
                            types = {'BranchId': str, 'FeederBrId':str, 'XDbId':str, 'Node1':str, 'Node2':str}
                        if ime_tabele.startswith('LNode'): 
                            types = {'LNodeId': str, 'OrgId':str}
                        if ime_tabele.startswith('Section'): 
                            types = {'BranchId': str}
                            
                        tabela = pd.read_csv(io.StringIO(str(contents)),sep=',', header=0, converters=types, encoding='cp1250', index_col=False, engine='python')
                        self.pd_dataframe_to_gpkg(tabela, self.gpkg_path, ime_tabele)
                  
            
    def zgradi_indekse_tabelam(self): 
        """
            Zgradi indekse tabelam za hitrejše branje in poizvedbe po podatkovni bazi. 
        """
        
        engine = create_engine(f'sqlite:///{self.gpkg_path}', echo=False) #POZOR ! - tale sprejema samo relativne poti
        connection = engine.connect()
        
        sqls = ["create index if not exists branch_index on Branch(BranchId)", 
                "create index if not exists node_index on Node(NodeId);",  
                "create index if not exists node_lnode_index on Node(LNodeId)",
                "create index if not exists node_generation_index on Node(Generation);", 

                "create index if not exists section_index on Section(BranchId);",
                "create index if not exists lnode_index on LNode(LNodeId);" ,
                "create index if not exists lnode_type_index on LNode(Type);",

                "create index if not exists transformer_index on Transformer(BranchId);",
                "create index if not exists switching_device_index on Switching_device(BranchId);"]

        for sql in sqls: 
            s = text(sql)
            connection.execute(s)
            

    def uvozi_podatke_materialov_mdb(self):
        """
            Metoda razreda za uvoz podatkov materialov iz Gredos v gpkg datoteko. Datoteke na Windows platformi beremo z {Microsoft Access Driver (*.mdb, *.accdb)}, 
            uvoz podatkov na linux platformi pa temelji na osnovi mdb-tools. 
            
            Datoteka materialov se običajno v distribuciji Gredos nahaja v imeniku C:\GredosMO\Defaults 
            
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
                #stlačim še materiale v geopackage
                material = pd.read_sql_query(sql_material, con_material)
                self.pd_dataframe_to_gpkg(material, self.gpkg_path, 'MATERIAL')

                return True
            except Exception as e:
                return False
        if sys.platform.startswith('lin'): 
            contents = subprocess.Popen(["mdb-export", self.pot_materiali,'MATERIAL'],
                                    stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
            
            tabela = pd.read_csv(io.StringIO(str(contents)),sep=',', header=0, encoding='cp1250', index_col=False)
            self.pd_dataframe_to_gpkg(tabela, self.gpkg_path, 'MATERIAL')
            
            

    def uvozi_geografske_datoteke(self, show_progress=False, pretvori_crs = False, set_crs='EPSG:3794'):
        """
        
         Uvozi podatke SHP gredos  kot  geografsko plast  v  datoteko. Pot do datoteke je definirana s spremenljivko razreda self.gpkg_path. 
         v Default EPSG koda je 3912 (GK48), med prenosom je možna pretvorba iz tega v drug koordinatni sistem, ki je kompatibilen z GIS ali 
         drugimi prikazovalniki, ki imajo npr. podlago za prikaz v WGS84. S tem smo pokrili večino uporabniških primerov. 
        
        Args:
            
            show_progress (bool, optional): Prikaži napredek uvoza. Defaults to False.
            pretvori_crs (bool, optional): Pretvori v drug crs (default 3794). Defaults to True.
            set_crs (string, optional): Sets CRS of conversion data. 
            
        Returns:
            True, če je število uvoženih SHP datotek pod 3 (POINT, LNODE, LINE). Če bi se v imeniku nahajalo več datotek SHP bi tako vrnil napako. 
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
                    self.shp_to_geopackage(os.path.join(imenik_projekta,file), self.gpkg_path, 'POINT_geo', pretvori_crs=pretvori_crs, set_crs=set_crs)
            if 'LINE' in splitfile[0]:
                i = i + 1
                if 'shp' in splitfile[1]:
                    if show_progress: 
                        print(f"Uvažam: {file}")
                    self.shp_to_geopackage(os.path.join(imenik_projekta, file), self.gpkg_path, 'LINE_geo', pretvori_crs=pretvori_crs,set_crs=set_crs)

            if 'LNODE' in splitfile[0]:
                i=i + 1
                if 'shp' in splitfile[1]:
                    if show_progress: 
                        print(f"Uvažam: {file}")
                    self.shp_to_geopackage(os.path.join(imenik_projekta, file), self.gpkg_path, 'LNODE_geo', pretvori_crs=pretvori_crs, set_crs=set_crs)
        if i == 3:
            return False
        else:
            return True

    def pozeni_uvoz(self, show_progress = False, pretvori_crs = False, set_crs = 'EPSG:3794'):
        """ Izvozi vse podatke Gredos v lokalno GPKG datoteko na disku, glede na nastavljeno lokacijo. 
            Omogoča tudi pretvorbo koordinatnega sistema v druge oblike npr. WGS84 za spletne aplikacije ali EPSG:3794 (D96/TM Slovenski koordinatni sistem)


        Args:
            show_progress (bool, optional): med izvozom prikazuj obvestila v terminalu.
            pretvori_crs (bool, optional): pretvori v drug koordinatni sistem npr. wgs84 (EPSG:4326) ali epsg: 3794 (Geodetic CRS: Slovenia 1996)

        Returns:
            uvozeno (bool) : True, če je geografske datoteke ustrezno uvozilo
        """
        
        uvozeno = self.uvozi_geografske_datoteke(show_progress, pretvori_crs=pretvori_crs, set_crs = set_crs)
        self.uvozi_podatke_mdb(show_progress)
        self.uvozi_podatke_materialov_mdb()
        self.zgradi_indekse_tabelam()

        return uvozeno
