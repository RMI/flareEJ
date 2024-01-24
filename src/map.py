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

def create_overlay_map(gdf_base, gdf_point):

    #Ensure all shape files are in the same crs are folium map
    gdf_block = gdf_base.to_crs("EPSG:4326") 
    gdf_flare = gdf_point.to_crs("EPSG:4326") 
    
    
    #create base map
    m = folium.Map(location=[31, -100], zoom_start=6)


    for _, r in gdf_block.iterrows():
        # Without simplifying the representation of each borough,
        # the map might not be displayed
        sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "blue"})
        
        geo_j.add_to(m)
    

    for _, r in gdf_flare.iterrows():
        # Without simplifying the representation of each borough,
        # the map might not be displayed
        sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.0001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "red"})
        
        geo_j.add_to(m)
    

    # for _, r in gdf_joined.iterrows():
    #     # Without simplifying the representation of each borough,
    #     # the map might not be displayed
    #     sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.0001)
    #     geo_j = sim_geo.to_json()
    #     geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "green"})
        
    #     geo_j.add_to(m)
    
    return m
#%%

if __name__ == '__main__':

    #%%
    block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Data Samples/BG_shapefile/AllJoinBG.shp')
    block_df.rename(columns={'ID':'block_group_id'}, inplace=True)

    #crs = EPSG:4326 WGS84 geodetic latitude (degree)
    flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/VIIRS_flaring_data/USA_2022.shp')
    flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)

    gdf_joined = gpd.read_file(f'{mykey.sharepoint}/Data/January Data/flare_blockgroup_overlay.shp')
    #%%
    create_overlay_map(block_df, flare_df)
    #%%