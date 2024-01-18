#%%
import sys
sys.path.append('..')
from keys import MyKeys
mykey = MyKeys("../config.ini")

import pandas as pd
import geopandas as gpd
import geopy
from shapely.geometry import Polygon, LineString, Point
import matplotlib.pyplot as plt
import folium


#%%

# df = pd.read_csv(f'{mykey.sharepoint}/Data/Data Samples/BG.csv')

#import shape files

#crs = EPSG:3857 WGS84 metre
block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Data Samples/BG_shapefile/AllJoinBG.shp')
# block_df = block_df[block_df['STATE_NAME']=='Texas'].copy(deep=True)

#crs = EPSG:4326 WGS84 geodetic latitude (degree)
flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/VIIRS_flaring_data/USA_2022.shp')

#Change flare crs to be in metres
flare_df = flare_df.to_crs(3857)
#%%


#%%


# base = block_df.plot(color='white', edgecolor='black')
# flare_df.plot(ax=base, marker='*', color='red', markersize=2);
    

#%%


#%%
buffer_distance = 5000 #we want 5 km
flare_df['buffered_geometry'] = flare_df['geometry'].buffer(buffer_distance)

#%%


#%%
flare_sub = flare_df[['ID 2022','buffered_geometry']].copy(deep=True)
flare_sub.rename(columns={'buffered_geometry':'geometry','ID 2022':'Flare ID'}, inplace=True)

block_sub = block_df[['ID','geometry']].copy(deep=True)
block_sub.rename(columns={'ID':'Block Group ID'}, inplace=True)

#%%

#%%
overlay_df = flare_sub.overlay(block_sub, how="intersection")
# newdf.plot()

# base = block_df.plot(color='white', edgecolor='black')
# flare_sub.plot(ax=base, color='red',alpha=0.5);
#%%

#%%

flare_sub['area_flare'] = flare_sub.area

block_sub['area_block'] = block_sub.area

# Performing overlay funcion
gdf_joined = gpd.overlay(flare_sub,block_sub, how='intersection')

# Calculating the areas of the newly-created geometries
gdf_joined['area_joined'] = gdf_joined.area

# # Calculating the areas of the newly-created geometries in relation 
# # to the original grid cells
gdf_joined['percent_blockgroup_covered_by_flare'] = ((gdf_joined['area_joined'] / 
                                                   gdf_joined['area_block'])*100)
#%%

#%%


gdf_block = block_sub.to_crs("EPSG:4326") 
gdf_flare = flare_sub.to_crs("EPSG:4326") 
gdf_overlay = overlay_df.to_crs("EPSG:4326") 

gdf_joined_test = gdf_joined[gdf_joined['percent_blockgroup_covered_by_flare']>100].to_crs("EPSG:4326") 
gdf_block_test = gdf_block[gdf_block['Block Group ID'].isin(gdf_joined_test['Block Group ID'])]
gdf_flare_test = gdf_flare[gdf_flare['Flare ID'].isin(gdf_joined_test['Flare ID'])]


print(gdf_block.crs)

m = folium.Map(location=[31, -100], zoom_start=6)
# folium.GeoJson(data=gdf["geometry"]).add_to(m) 
# m

# for _, r in gdf_block_test.iterrows():
#     # Without simplifying the representation of each borough,
#     # the map might not be displayed
#     sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
#     geo_j = sim_geo.to_json()
#     geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "blue"})
    
#     geo_j.add_to(m)
# m

for _, r in gdf_flare_test.iterrows():
    # Without simplifying the representation of each borough,
    # the map might not be displayed
    sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.0001)
    geo_j = sim_geo.to_json()
    geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "red"})
    
    geo_j.add_to(m)
m

for _, r in gdf_joined_test.iterrows():
    # Without simplifying the representation of each borough,
    # the map might not be displayed
    sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.0001)
    geo_j = sim_geo.to_json()
    geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "green"})
    
    geo_j.add_to(m)
m


#%%
gdf_joined['percent_blockgroup_covered_by_flare'] = gdf_joined['percent_blockgroup_covered_by_flare'].apply(lambda x: 1 if x > 1 else x)
#%%
