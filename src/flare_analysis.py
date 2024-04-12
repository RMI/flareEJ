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
import scipy.stats as ss


#%%
gdf_joined = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/flare_blockgroup_overlay.csv')
gdf_joined['block_group_id'] = gdf_joined['block_group_id'].apply(str)
gdf_joined['flare_id'] = gdf_joined['flare_id'].apply(str)
# %%

# EJ_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/AttributesAdded/AttributesAdded.shp')
EJ_df = pd.read_csv((f'{mykey.sharepoint}/Data/Final Data/block_ej.csv'))
EJ_df['block_group_id'] = EJ_df['block_group_id'].apply(str)


# #crs = EPSG:4326 WGS84 geodetic latitude (degree)
flare_df = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/CleanedFlares/Flares_shp.shp')
flare_df.rename(columns={'ID 2022':'flare_id'}, inplace=True)
flare_df[['BCM 2022','Detection','Clear Obs.']] = flare_df[['BCM 2022','Detection','Clear Obs.']].astype(float)

flare_df['Detection']=flare_df['Detection'].fillna(0)

# %%

#merge key columns
block_index_df = EJ_df[['block_group_id','state','bg_total_population','bg_vulnerability_index_national']].copy(deep=True)

flare_info_df = flare_df[['flare_id','BCM 2022','Detection','Clear Obs.','Type']].copy(deep=True)

gdf_analysis = gdf_joined[['block_group_id','flare_id','fraction_blockgroup_covered_by_flare']].copy(deep=True)

merge_analysis = gdf_analysis.merge(flare_info_df, how='left',on='flare_id')
merge_analysis = merge_analysis.merge(block_index_df, how='left',on='block_group_id')
# %%
#Get the proportion of the block group population impacted by the flare
merge_analysis['bg_population_impacted_by_flare'] = merge_analysis['bg_total_population']*merge_analysis['fraction_blockgroup_covered_by_flare']

# %%
# Aggregate flare measures
wavg_overlap = lambda x: np.ma.average(np.ma.array(x, mask=np.isnan(x)), weights=merge_analysis.loc[x.index, "fraction_blockgroup_covered_by_flare"]) if ((np.any(merge_analysis.loc[x.index, "fraction_blockgroup_covered_by_flare"]!= 0)) and np.any(pd.notnull(x))) else np.average(np.ma.array(x, mask=np.isnan(x))) if np.any(pd.notnull(x)) else np.nan
wavg_population = lambda x: np.ma.average(np.ma.array(x, mask=np.isnan(x)), weights=merge_analysis.loc[x.index, "bg_population_impacted_by_flare"]) if ((np.any(merge_analysis.loc[x.index, "bg_population_impacted_by_flare"]!= 0)) and np.any(pd.notnull(x))) else np.average(np.ma.array(x, mask=np.isnan(x))) if np.any(pd.notnull(x)) else np.nan

flare_measures = merge_analysis.groupby('flare_id').agg(state=('state','first'),
                                                        flare_impacted_population_bg=('bg_total_population','sum'),
                                                        flare_bcm = ('BCM 2022','first'),
                                                        flare_detection = ('Detection','first'),
                                                        flare_clear_observations = ('Clear Obs.','first'),
                                                        flare_type = ('Type','first'),
                                                        flare_impacted_population_radius=('bg_population_impacted_by_flare','sum'),
                                                        flare_vulnerability =('bg_vulnerability_index_national',wavg_overlap), #Change to raw score
                                                        flare_vulnerability_population = ('bg_vulnerability_index_national',wavg_population)) #Change to raw score

flare_measures.reset_index(inplace=True)
# %%

#Get the population of each block group impacted by the flare
flare_measures['flare_bcm_population'] = flare_measures['flare_bcm']*flare_measures['flare_impacted_population_radius']
#%%

#convert to 0-1 by dividing by max
scale_variables = ['flare_bcm','flare_detection','flare_bcm_population','flare_vulnerability','flare_vulnerability_population']
for s in scale_variables:
    flare_measures[f'{s}_scale'] = flare_measures[s]/flare_measures[s].max()

#Sum the scaled flare variables into an aggregated flare measure, this will be on a 0-3 scale
flare_measures['flare_aggregate'] = flare_measures['flare_detection_scale']+flare_measures['flare_bcm_scale']
#Rescale to 0-1
flare_measures['flare_aggregate_scale'] = flare_measures['flare_aggregate']/flare_measures['flare_aggregate'].max()

#Create flare ej score
flare_measures['flare_ej_scale'] = flare_measures['flare_aggregate_scale']*flare_measures['flare_vulnerability_scale']

#%%
index_variables = ['flare_aggregate_scale','flare_vulnerability_scale','flare_ej_scale']

for i in index_variables:
    flare_measures[f'{i.replace("_scale","").replace("_aggregate","")}_index_national'] = (flare_measures[i] - np.nanmean(flare_measures[i])) / np.nanstd(flare_measures[i])
    #If only one flare in the state, set index to 0...otherwise it will return a z score of 0
    flare_measures[f'{i.replace("_scale","").replace("_aggregate","")}_index_state']  =  flare_measures.groupby('state')[i].transform(lambda x: 0 if np.nanstd(x) == 0 else (x - np.nanmean(x)) / np.nanstd(x))

#%%
rank_variables = ['flare_index_national','flare_vulnerability_index_national','flare_ej_index_national']

for v in rank_variables:
    flare_measures[f'{v.replace("_index_national","")}_rank_national'] = flare_measures[v].rank(method='dense', ascending=False)
    flare_measures[f'{v.replace("_index_national","")}_percentile_national'] = flare_measures[v].rank(pct=True)

    flare_measures[f'{v.replace("_index_national","")}_rank_state'] = flare_measures.groupby(['state'])[v].rank(method="dense", ascending=False)
    flare_measures[f'{v.replace("_index_national","")}_percentile_state'] = flare_measures.groupby(['state'])[v].rank(pct=True)


#%%
if flare_measures.isna().any().any():
    print("The DataFrame 'flare_measures' contains NA values.")
    # Create a mask for NA values
    na_mask = flare_measures.isna()

    # Create a DataFrame with flare_id and column_info for NA values
    na_info = [(index, column) for index, row in na_mask.iterrows() for column in na_mask.columns if row[column]]
    na_df = pd.DataFrame(na_info, columns=['index', 'column_info'])
    print(na_df)
else:
    print("The DataFrame 'flare_measures' does not contain any NA values.")
# %%
flare_measures.to_csv(f'{mykey.sharepoint}/Data/Final Data/flare_ej.csv', index=False)
# %%

