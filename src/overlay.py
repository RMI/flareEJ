
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


def calculate_percent_overlay(polygone_df, point_df, point_buffer_distance,export_file_name):

    #crs should be in metres

    #Change flare crs to be in metres
    point_df = point_df.to_crs(polygone_df.crs)


    #create buffer distance
    buffer_distance = point_buffer_distance #we want 5 km
    point_df['buffered_geometry'] = point_df['geometry'].buffer(buffer_distance)


    #replace old point geometry with buffered geometry
    point_sub = point_df[['flare_id','buffered_geometry']].copy(deep=True)
    point_sub.rename(columns={'buffered_geometry':'geometry'}, inplace=True)

    polygone_sub = polygone_df[['block_id','geometry']].copy(deep=True)
    
    polygone_sub['area_block'] = polygone_sub.area
    point_sub['area_flare'] = point_sub.area

    #Find intersecting geometry for each flare/bg combination with overlap
    gdf_joined = gpd.overlay(polygone_sub,point_sub, how='intersection')

    # Calculating the areas of the newly-created geometries
    gdf_joined['area_joined'] = gdf_joined.area

    # # Calculating the areas of the newly-created geometries in relation 
    # # to the original grid cells
    gdf_joined['fraction_blockgroup_covered_by_flare'] = ((gdf_joined['area_joined'] / 
                                                    gdf_joined['area_block']))

    #Some rounding issues may produce more than 100...catch those
    gdf_joined['fraction_blockgroup_covered_by_flare'] = gdf_joined['fraction_blockgroup_covered_by_flare'].apply(lambda x: 1 if x > 1 else x)


    #run test
    flare_grouped = gdf_joined.groupby('flare_id').agg({'area_joined':'sum',
                                        'area_flare':'first'})

    flare_grouped['flare_coverage'] = flare_grouped['area_joined']/flare_grouped['area_flare']

    #export
    gdf_joined.to_csv(f'{mykey.sharepoint}/Data/January Data/{export_file_name}.csv')

if __name__=='__main__':

    #import shape files
    #crs = EPSG:3857 WGS84 metre
    block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Data Samples/BG_shapefile/AllJoinBG.shp')
    block_df.rename(columns={'ID':'block_group_id'}, inplace=True)

    #crs = EPSG:4326 WGS84 geodetic latitude (degree)
    flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/VIIRS_flaring_data/USA_2022.shp')
    flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)

    calculate_percent_overlay(block_df, flare_df, 5000,'flare_blockgroup_overlay')
