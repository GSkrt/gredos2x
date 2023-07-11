import pandas as pd
import sqlalchemy as sa 
import geopandas as gpd
import fiona
import sqlite3

class GredosGPKG2df(): 
    def __init__(self, povezava_gpkg='base.gpkg', pregled_vsebine = False): 
        self.gpkg_povezava = povezava_gpkg
        self.debug = pregled_vsebine
        
    def list_gpkg_tables(self):
        """ Preglej vse tabele, ki so shranjene v GPKG datoteki. 

        Returns:
            list: list of layers stored in GPKG database 
        """
        layers =fiona.listlayers(self.gpkg_povezava)
        return layers
    
    def nalozi_negeografsko_tabelo(self,ime_tabele:str): 
        """Uvoz negeografske tabele v klasičen pandas dataframe (npr.'LNode', 'Node', 'Section', 'Transformer', 'Switching_device', 'Branch', 'MATERIAL' )

        Args:
            ime_tabele (str): Ime tabele za uvoz, pregled tabel uporabimo metodo list_gpkg_tables
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(self.gpkg_povezava)

            # Read the table into a DataFrame
            table_name = "your_table"
            query = f"SELECT * FROM {ime_tabele}"
            df = pd.read_sql_query(query, conn)
            
            if self.debug: 
                print('\n\n{ime_tabele}')
                print(df.head)

            # Close the database connection
            conn.close()
            
            return df

        except sqlite3.Error as e:
            # Handle SQLite database errors
            print("Error occurred while working with the database:", e)
            
            return None

        except pd.io.sql.DatabaseError as e:
            # Handle pandas database errors
            print("Error occurred while reading data into DataFrame:", e)
            
            return None 
        
    def preberi_geografsko_tabelo_iz_gpkg(self, layer_name:str, epsg_set = 'EPSG:3912'):
        """
        Preberi geografsko tabelo iz gpkg. Geografske tabele imajo pri ustvarjanju oznako _geo
        
        Keyword arguments:
        
        layer_name (str): ime plasti za uvoz
        epsg_set (str, optional): EPSG koda koordinatnega sistema, ki je vsebovana v GPKG datoteki. Defaults to 'EPSG:3912'.

        Return: geodataframe s predpisanim koordinatnim sistemom 
        """
                  
        try:
            # Read each layer into a GeoDataFrame
            layer_gdf = gpd.read_file(self.gpkg_povezava , layer=layer_name)
            layer_gdf.set_crs(epsg_set, inplace=True)
            if self.debug: 
                print(f"Layer Name: {layer_name}")
                print(layer_gdf.head())
                
            

        except Exception as e:
            print(f"Error occurred while reading layer {layer_name}: {e}")
        
        return layer_gdf
        
