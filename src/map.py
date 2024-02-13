#%%
import sys
sys.path.append('..')
from keys import MyKeys
mykey = MyKeys("../config.ini")

import pandas as pd
import geojson
import geopandas as gpd
import geopy
from shapely.geometry import Polygon, LineString, Point
import matplotlib.pyplot as plt
import folium
import branca.colormap as cm
from folium.plugins import MarkerCluster
import os


   
#%%
block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/AttributesAdded/AttributesAdded.shp')
block_df.rename(columns={'OBJECTID':'block_group_id'}, inplace=True)
#%%

map_block_df = block_df[['block_group_id','geometry']].copy(deep=True)
map_block_df.to_crs("EPSG:4326",inplace=True)
block_json_path = f'{mykey.sharepoint}/Data/Data Samples/map_block.geojson'
map_block_df.to_file(block_json_path, driver='GeoJSON')

#%%
EJ_df = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/block_ej.csv')
EJ_sub = EJ_df[['block_group_id','bg_flare_index_national','bg_vulnerability_index_national','bg_ej_index_national','bg_flare_percentile_national','bg_ej_percentile_national']].copy(deep=True)
blockgroup_tooltip = map_block_df.merge(EJ_sub, how='left', on='block_group_id')

#%%
flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/CleanedFlares/CleanedFlares.shp')
flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)
flare_measures = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/flare_ej.csv')
flare_measures['flare_id'] = flare_measures['flare_id'].astype(str)
flare_measures_sub = flare_measures[['flare_id','flare_bcm','flare_index_national','flare_ej_index_national']].copy(deep=True)

flare_merge = flare_df.merge(flare_measures_sub, how='left', on='flare_id')

#%%
m = folium.Map(location=[31, -100], zoom_start=6)

fg1 = folium.FeatureGroup(name='Flare Impact',overlay=False).add_to(m)
fg2 = folium.FeatureGroup(name='EJ Index',overlay=False).add_to(m)
# fg3 = folium.FeatureGroup(name='Flares',overlay=True).add_to(m)

custom_scale = custom_scale = (EJ_sub['bg_flare_percentile_national'].quantile((0,0.2,0.4,0.6,0.8,1))).tolist()

# flare_leg = cm.LinearColormap(["yellow", "orange", "red"], vmin=0, vmax=EJ_sub['Flare_Index_Percentile'].max())
# m.add_child(flare_leg)


flare_impact = folium.Choropleth(
        geo_data=block_json_path,
        data=EJ_sub,
        columns=['block_group_id', 'bg_flare_percentile_national'],  
        key_on='feature.properties.block_group_id', 
        threshold_scale=custom_scale, #use the custom scale we created for legend
        fill_color='YlOrRd',
        nan_fill_color="White", #Use white color if there is no data available
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Flare Impact',
        highlight=True,
        overlay=False,
        line_color='black').geojson.add_to(fg1)

folium.features.GeoJson(
                    data=blockgroup_tooltip,
                    name='Block Group Flare Index',
                    smooth_factor=2,
                    style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['block_group_id',
                                'bg_flare_index_national',
                               ],
                        aliases=["Block Group ID",
                                 "Flare Index",
                                ], 
                        localize=True,
                        sticky=False,
                        labels=True,
                        style="""
                            background-color: #F0EFEF;
                            border: 2px solid black;
                            border-radius: 3px;
                            box-shadow: 3px;
                        """,
                        max_width=800,),
                            highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                        ).add_to(fg1)   

# step = cm.LinearColormap(["yellow", "orange", "red"], vmin=0, vmax=EJ_sub['Flare_Index_Percentile'].max())
# step.add_to(fg1)

ej_index =  folium.Choropleth(
        geo_data=block_json_path,
        data=EJ_sub,
        columns=['block_group_id', 'bg_ej_percentile_national'],  
        key_on='feature.properties.block_group_id', 
        threshold_scale=custom_scale, #use the custom scale we created for legend
        fill_color='YlGnBu',
        nan_fill_color="White", #Use white color if there is no data available
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Environmental Justice Impact',
        highlight=True,
        overlay=False,
        line_color='black').geojson.add_to(fg2)




folium.features.GeoJson(
                    data=blockgroup_tooltip,
                    name='Block Group EJ Index',
                    smooth_factor=2,
                    style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['block_group_id',
                                'bg_flare_index_national',
                                'bg_vulnerability_index_national',
                                'bg_ej_index_national' 
                               ],
                        aliases=["Block Group ID:",
                                 "Flare Index:",
                                 "Vulnerability Index:",
                                 "Environmental Justice Index:"
                                ], 
                        localize=True,
                        sticky=False,
                        labels=True,
                        style="""
                            background-color: #F0EFEF;
                            border: 2px solid black;
                            border-radius: 3px;
                            box-shadow: 3px;
                        """,
                        max_width=800,),
                            highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                        ).add_to(fg2)   

# Convert points to GeoJSON
# flare_gjson = folium.features.GeoJson(flare_df, name="flares")
# flare_gjson.add_to(fg3)


# #Loop through each row in the dataframe
# for i,row in flare_merge.iterrows():
#     html=f'<h5> Flare Info</h5><p>Flare ID:{row["flare_id"]}<br>Flare BCM:{row["flare_bcm"]}</p>'
#     #Setup the content of the popup
#     iframe = folium.IFrame(html=html)
    
#     #Initialise the popup using the iframe
#     popup = folium.Popup(iframe, min_width=300, max_width=300)

    
#     #Add each row to the map
#     folium.CircleMarker(location=[row['Latitude'],row['Longitude']],radius=3, fill_color='red',
#                   popup = popup).add_to(fg3)


# folium.features.GeoJson(
#                     data=flare_df,
#                     name='Flare Index',
#                     smooth_factor=2,
#                     style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
#                     tooltip=folium.features.GeoJsonTooltip(
#                         fields=['flare_id',
#                                 'BCM 2022'],
#                         aliases=["Flare ID:",
#                                  "BCM:",
#                                 ], 
#                         localize=True,
#                         sticky=False,
#                         labels=True,
#                         style="""
#                             background-color: #F0EFEF;
#                             border: 2px solid black;
#                             border-radius: 3px;
#                             box-shadow: 3px;
#                         """,
#                         max_width=800,),
#                             highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
#                         ).add_to(fg3)  





#Add layer control to the map
# folium.TileLayer('cartodbdark_matter',overlay=True,name="View in Dark Mode").add_to(m)
folium.TileLayer('cartodbpositron',overlay=True,name="Base Map").add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

m

# m.save(f'{mykey.sharepoint}/Data/January Data/heat_map.html')
#%%
