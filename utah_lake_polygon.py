import geopandas as gpd

gdf = gpd.read_file('/Users/rchales/Desktop/Utah_Lakes_NHD/LakesNHDHighRes.shp')
gdf[gdf['GNIS_Name'] == 'Utah Lake'].to_file('./utah_lake.gpkg', driver='GPKG')
