#%%
import sys
sys.path.append('..')
from keys import MyKeys
mykey = MyKeys("../config.ini")

import pandas as pd
import numpy as np
import geopandas as gpd
import geopy
from shapely.geometry import Polygon, LineString, Point
import matplotlib.pyplot as plt
import folium

#%%
# gdf_joined = gpd.read_file(f'{mykey.sharepoint}/Data/January Data/flare_blockgroup_overlay.shp')
gdf_joined = pd.read_csv(f'{mykey.sharepoint}/Data/January Data/flare_blockgroup_overlay.csv')
gdf_joined['block_id'] = gdf_joined['block_id'].apply(str)
gdf_joined['flare_id'] = gdf_joined['flare_id'].apply(str)
# %%

# All crs should be in meters
block_df = gpd.read_file(f'{mykey.sharepoint}/Data/Data Samples/BG_shapefile/AllJoinBG.shp')
block_df.rename(columns={'ID':'block_id'}, inplace=True)
block_df['block_id'] = block_df['block_id'].apply(str)
block_df['ACSTOTPOP'] = block_df['ACSTOTPOP'].apply(int)

#crs = EPSG:4326 WGS84 geodetic latitude (degree)
flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/VIIRS_flaring_data/USA_2022.shp')
flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)

flare_df.to_crs(block_df.crs, inplace=True)

# %%
block_index_df = block_df[['block_id','STATE_NAME','ST_ABBREV','ACSTOTPOP','DEMOG_EJ_I']].copy(deep=True)


flare_info_df = flare_df[['flare_id','BCM 2022','Detection','Clear Obs.','Type']].copy(deep=True)



gdf_analysis = gdf_joined[['block_id','flare_id','fraction_blockgroup_covered_by_flare']].copy(deep=True)

merge_analysis = gdf_analysis.merge(flare_info_df, how='left',on='flare_id')
merge_analysis = merge_analysis.merge(block_index_df, how='left',on='block_id')
# %%

merge_analysis['bg_population_impacted_by_flare'] = merge_analysis['ACSTOTPOP']*merge_analysis['fraction_blockgroup_covered_by_flare']

# %%
wavg_overlap = lambda x: np.ma.average(np.ma.array(x, mask=np.isnan(x)), weights=merge_analysis.loc[x.index, "fraction_blockgroup_covered_by_flare"]) if ((np.any(merge_analysis.loc[x.index, "fraction_blockgroup_covered_by_flare"]!= 0)) and np.any(pd.notnull(x))) else np.average(np.ma.array(x, mask=np.isnan(x))) if np.any(pd.notnull(x)) else np.nan
wavg_population = lambda x: np.ma.average(np.ma.array(x, mask=np.isnan(x)), weights=merge_analysis.loc[x.index, "bg_population_impacted_by_flare"]) if ((np.any(merge_analysis.loc[x.index, "bg_population_impacted_by_flare"]!= 0)) and np.any(pd.notnull(x))) else np.average(np.ma.array(x, mask=np.isnan(x))) if np.any(pd.notnull(x)) else np.nan

flare_measures = merge_analysis.groupby('flare_id').agg(impacted_population_bg=('ACSTOTPOP','sum'),
                                       bcm = ('BCM 2022','first'),
                                       detection = ('Detection','first'),
                                       clear_observations = ('Clear Obs.','first'),
                                       flare_type = ('Type','first'),
                                       impacted_population_radius=('bg_population_impacted_by_flare','sum'),
                                       average_vulnerability =('bg_vulnerability_by_flare',wavg_overlap),
                                       average_vulnerability_population = ('bg_vulnerability_by_flare',wavg_population))
# %%
flare_measures.to_csv(f'{mykey.sharepoint}/Data/January Data/flare_measures.csv')
# %%
