#%%
import sys
sys.path.append('..')
from keys import MyKeys
mykey = MyKeys("../config.ini")

import json
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
non_flare_shp = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/NonFlareDissolved/NonFlareDissolved.shp')
non_flare_shp.to_crs("EPSG:4326",inplace=True)
#%%
block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/flare_block_groups/flare_block_groups.shp')
block_df.rename(columns={'OBJECTID':'block_group_id'}, inplace=True)
#%%

map_block_df = block_df[['block_group_id','geometry']].copy(deep=True)
map_block_df.to_crs("EPSG:4326",inplace=True)
map_block_df['block_group_id'] = map_block_df['block_group_id'].astype(float)
map_block_df['block_group_id'] = map_block_df['block_group_id'].astype(int)
block_json_path = f'{mykey.sharepoint}/Data/Final Data/map_block.geojson'
map_block_df.to_file(block_json_path, driver='GeoJSON')


#%%
EJ_df = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/block_ej.csv')
EJ_df['block_group_id'] = EJ_df['block_group_id'].astype(int)
EJ_sub = EJ_df[['block_group_id','bg_flare_index_national','bg_vulnerability_index_national','bg_ej_index_national','bg_flare_percentile_national','bg_ej_percentile_national']].copy(deep=True)
blockgroup_tooltip = map_block_df.merge(EJ_sub, how='left', on='block_group_id')
tooltip_json_path = f'{mykey.sharepoint}/Data/Final Data/blockgroup_tooltip.geojson'
blockgroup_tooltip.to_file(tooltip_json_path, driver='GeoJSON')

#%%
flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/CleanedFlares/CleanedFlares.shp')
flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)
flare_measures = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/flare_ej.csv')
flare_measures['flare_id'] = flare_measures['flare_id'].astype(str)
flare_measures_sub = flare_measures[['flare_id','flare_bcm','flare_index_national','flare_ej_index_national']].copy(deep=True)

flare_merge = flare_df.merge(flare_measures_sub, how='left', on='flare_id')

#%%
# reading JSON file
with open(tooltip_json_path) as access_json:
    tooltip_json = json.load(access_json)

feature_access = tooltip_json['features']





#%%
def folium_flare_map(choropleth_flare_layer, choropleth_ej_layer, choropleth_scale):
    m = folium.Map(location=[31, -100], zoom_start=6)

    fg0 = folium.FeatureGroup(name='Well Counties', overlay=True).add_to(m)
    fg1 = folium.FeatureGroup(name='Flare Impact',overlay=False).add_to(m)
    fg2 = folium.FeatureGroup(name='EJ Impact',overlay=False).add_to(m)
    fg3 = folium.FeatureGroup(name='Flares',overlay=True).add_to(m)
    
    for _, r in non_flare_shp.iterrows():
        # Without simplifying the representation of each borough,
        # the map might not be displayed
        sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "black",'color':'block','width':1})
        geo_j.add_to(fg0)

    flare_impact = folium.Choropleth(
            geo_data=block_json_path,
            data=EJ_sub,
            columns=['block_group_id', choropleth_flare_layer],  
            key_on='feature.properties.block_group_id', 
            threshold_scale=choropleth_scale, #use the custom scale we created for legend
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



    ej_index =  folium.Choropleth(
            geo_data=block_json_path,
            data=EJ_sub,
            columns=['block_group_id', choropleth_ej_layer],  
            key_on='feature.properties.block_group_id', 
            threshold_scale=choropleth_scale, #use the custom scale we created for legend
            fill_color='YlGnBu',
            nan_fill_color="White", #Use white color if there is no data available
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Environmental Justice Impact',
            highlight=True,
            overlay=False,
            line_color='black').geojson.add_to(fg2)
    
    def bg_html(dict):
        ej_index = dict['bg_flare_index_national']
        html = """
        <!DOCTYPE html>
        <html>
        <left><h5 style="margin-bottom:5"; width="200px">Block ID: {}</h5>""".format(dict["block_group_id"]) + """</left>
        <left><h5 style="margin-bottom:5"; width="200px">Country: {}</h5>""".format('Example County') + """</left>
        <left><h5 style="margin-bottom:5"; width="200px">State: {}</h5>""".format('Example State') + """</left>
        <details> 
            <summary style="font-size:small"> Block Group EJ Index: {}""".format(ej_index) + """</summary>
        
                <p>
                    Info on bg EJ Index
                </p>
        </details>
        </html>
        
        """
        return html

    
    for feature_data in feature_access:
        property_data = feature_data['properties']
        geo_json_style = {'fillColor': '#00000000', 
                          'color': 'black',
                          'fill_opacity':0}
        geo_json = folium.GeoJson(block_json_path,
                                  style_function=lambda x: geo_json_style)
        html = bg_html(property_data)
        #Setup the content of the popup
        iframe = folium.IFrame(html=html)
        
        #Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=300)
        geo_json.add_child(popup)
    
    geo_json.add_to(fg2)
    # folium.features.GeoJson(
    #                     data=blockgroup_tooltip,
    #                     name='Block Group EJ Index',
    #                     smooth_factor=2,
    #                     style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
    #                     tooltip=folium.features.GeoJsonTooltip(
    #                         fields=['block_group_id',
    #                                 'bg_flare_index_national',
    #                                 'bg_vulnerability_index_national',
    #                                 'bg_ej_index_national' 
    #                             ],
    #                         aliases=["Block Group ID:",
    #                                 "Flare Index:",
    #                                 "Vulnerability Index:",
    #                                 "Environmental Justice Index:"
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
    #                         ).add_to(fg2)   


    def popup_html(row):
        bcm = round((row["flare_bcm"])*1000,3)
        flare_ej = round(row["flare_ej_index_national"],4)

        html = """
        <!DOCTYPE html>
        <html>
        <left><h5 style="margin-bottom:5"; width="200px">Flare ID: {}</h5>""".format(row["flare_id"]) + """</left>
        <left><h5 style="margin-bottom:5"; width="200px">Country: {}</h5>""".format('Example County') + """</left>
        <left><h5 style="margin-bottom:5"; width="200px">State: {}</h5>""".format('Example State') + """</left>
        <details> 
            <summary style="font-size:small"> Flare Volume: {} mcm""".format(bcm) + """</summary>
        
                <p>
                    The volume of flared gas in million cubic meters. Around 140 bcm of 
                    natural gas is flared globally each year. 
                    This is a major source of CO2 emissions, methane and black soot, 
                    and is damaging to health.
                </p>
        </details>
        <details> 
            <summary style="font-size:small"> Flare EJ Index (National): {}""".format(flare_ej) + """</summary>
    
                <p>
                    The Flare EJ Index score is a combined measure of the environmental impact of a single
                    flare and the vulnerability of the impacted population. A negative Flare EJ Index indicates that
                    the environmental justice impact of the flare is below average for flares. However, it is 
                    important to remember that ANY flaring is detremental to human health and the environment
                </p>

        </details>
        </html>
        
        """
        return html


    #Loop through each row in the dataframe
    for i,row in flare_merge.iterrows():

        html = popup_html(row)
        #Setup the content of the popup
        iframe = folium.IFrame(html=html)
        
        #Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=300)

        
        #Add each row to the map
        folium.CircleMarker(location=[row['Latitude'],row['Longitude']],
                            color='black',
                            weight=1,
                            radius=3, 
                            fill_color='red',
                            opacity=1,
                            fill_opacity=.8,
                            popup = popup).add_to(fg3)




    # Add layer control to the map
    # folium.TileLayer('cartodbdark_matter',overlay=True,name="View in Dark Mode").add_to(m)
    folium.TileLayer('cartodbpositron',overlay=True,name="Base Map").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


#%%
custom_scale_percentile = (EJ_sub['bg_flare_percentile_national'].quantile((0,0.2,0.4,0.6,0.8,1))).tolist()
# custom_scale_zscore = [-3,-2,-1,0,1,2,3,4,5,6,7]

# choropleth_zscore_map = folium_flare_map('bg_flare_index_national', 'bg_ej_index_national', custom_scale_zscore)
choropleth_percentile_map = folium_flare_map('bg_flare_percentile_national', 'bg_ej_percentile_national', custom_scale_percentile)
#%%
# choropleth_zscore_map.save(f'{mykey.sharepoint}/Data/Final Data/choropleth_zscore_map.html')
choropleth_percentile_map.save(f'{mykey.sharepoint}/Data/Final Data/choropleth_percentile_map.html')
#%%
