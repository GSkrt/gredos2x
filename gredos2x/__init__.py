"""
gredos2x je pretvornik Gredos podatkovnih virov v druge formate in načine shranjevanja. Osnovni namen tega paketa je 
pretvoriti podatkvne vire v skupni geografsko podprt format, kjer se nahajajo vse tabele (vključno z materiali), ki so 
potrebne za izvajanje osnovnega pretoka moči v distribucijskem omrežju in razširiti uporabo modela na druge simulacijske platforme in standardizirane formate.
Pri tem ohranjamo geografsko osnovo modela, ki je ključna za uspešno obvladovanje modela omrežja v prihodnje in omogočimo morebiten nadalnji razvoj modela v 
smeri postopne nadgradnje in integracije delov omrežja z GIS. 

eng: 
gredos2x is ETL tool for conversion of Gredos distribution power system model (mdb, shp, dwg format) to other 
formats and distribution power system software keeping GEO information stored within model.
Model is still in use in Slovenia for basic MV long term studies and was developed on EIMV (ELEKTROINŠTITUT MILAN VIDMAR). 
"""

__version__ = "1.0.0"
__author__ = 'Gregor Skrt'
__credits__ = 'My mom (rip)'