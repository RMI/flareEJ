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
# gdf_joined = gpd.read_file(f'{mykey.sharepoint}/Data/January Data/flare_blockgroup_overlay.csv')
gdf_joined = pd.read_csv(f'{mykey.sharepoint}/Data/January Data/flare_blockgroup_overlay.csv')
# %%
