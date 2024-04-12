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
import numpy as np

#%%

block_df_raw = gpd.read_file(f'{mykey.sharepoint}/Data/Final Data/AttributesAdded/Attributes.shp')

#%%
block_df = block_df_raw.copy(deep=True)
block_df.rename(columns={'OBJECTID':'block_group_id'}, inplace=True)
block_df['block_group_id'] = block_df['block_group_id'].apply(str)
block_df['ACSTOTPOP'] = block_df['ACSTOTPOP'].apply(int)

#%%
####### Calculate raw indexes ######
'''
'FlareCou_1': flare count
'area' in meters sq
'DetectionS': detection sum
'''
#Density = Flare Count/Area
#Area is in meters sq
block_df['bg_flare_density'] = block_df['FlareCou_1']/block_df['area']

#Avg. Detection = Detection Sum/Flare count
block_df['bg_avg_flare_detection'] = block_df['DetectionS']/block_df['FlareCou_1']
#fill NA with zeros where no flares are detected
block_df['bg_avg_flare_detection'] = block_df['bg_avg_flare_detection'].fillna(0)

#scale the flaring varibles so they can be summed
flare_scale_columns = ['BCMSum','bg_flare_density','bg_avg_flare_detection']
for x in flare_scale_columns:
    #Scale to 0-1
    block_df[f'{x}_scale'] = block_df[x]/block_df[x].max()
    
#Sum the three scaled flaring columns
block_df['bg_flare_aggregate'] = block_df[[f'{x}_scale' for x in flare_scale_columns]].sum(axis=1)


#weighted percent of vulnerable categories. EJScreen how they do demographic
block_df['bg_vulnerability'] = (.25*(block_df['PEOPCOLORP']))+(.25*(block_df['LOWINCPCT']))+(.125*(block_df['UNEMPPCT']))+(.125*(block_df['LINGISOPCT']))+(.125*(block_df['LESSHSPCT']))+(.125*(block_df['OVER64PCT']))+(.125*(block_df['UNDER5PCT']))

#scale the flaring and vulnerability variables so they can be combined into an EJ indicator
scale_variables = ['bg_flare_aggregate','bg_vulnerability']

for s in scale_variables:
    block_df[f'{s}_scale'] = block_df[s]/block_df[s].max()

#As a product of the other scaled variables, EJ does not need to be re-scaled
block_df['bg_ej_scale'] = block_df['bg_vulnerability_scale']*block_df['bg_flare_aggregate_scale']

#%%
#Convert all places with zero population to have Nan for the EJ and Vulnerabilty variables
block_df.loc[block_df['ACSTOTPOP'] == 0, 'bg_ej_scale'] = np.nan
block_df.loc[block_df['ACSTOTPOP'] == 0, 'bg_vulnerability_scale'] = np.nan
#%%

# Get rows where 'ACSTOTPOP' is greater than zero
positive_population_df = block_df[block_df['ACSTOTPOP'] > 0]
# Check if 'bg_ej_scale' or 'bg_vulnerability_scale' are null
if positive_population_df[['bg_ej_scale', 'bg_vulnerability_scale']].isna().any().any():
    raise ValueError("Alert: 'bg_ej_scale' or 'bg_vulnerability_scale' are null for one or more rows where 'ACSTOTPOP' is greater than zero.")

no_population_df = block_df[(block_df['ACSTOTPOP'] == 0) | (block_df['ACSTOTPOP'].isna())]
# Check if 'bg_ej_scale' or 'bg_vulnerability_scale' are not null
if no_population_df[['bg_ej_scale', 'bg_vulnerability_scale']].notnull().any().any():
    raise ValueError("Alert: 'bg_ej_scale' or 'bg_vulnerability_scale' are notnull for one or more rows where 'ACSTOTPOP' is than zero.")

#%%

#Create the z-scores at the state and national level for all scaled variables
index_variables = ['bg_flare_aggregate_scale','bg_vulnerability_scale','bg_ej_scale']

for i in index_variables:
    # block_df[f'{i.replace("_scale","").replace("_aggregate","")}_index_national'] = ss.zscore(block_df[i])
    block_df[f'{i.replace("_scale","").replace("_aggregate","")}_index_national'] = (block_df[i] - np.nanmean(block_df[i])) / np.nanstd(block_df[i])
    block_df[f'{i.replace("_scale","").replace("_aggregate","")}_index_state']  = block_df.groupby('STATE_NAME')[i].transform(lambda x: (x - np.nanmean(x)) / np.nanstd(x))

#%%
#Rank and get the percentages for all the the indexes 
rank_variables = ['bg_flare_index_national','bg_vulnerability_index_national','bg_ej_index_national']

for v in rank_variables:
    block_df[f'{v.replace("_index_national","")}_rank_national'] = block_df[v].rank(method='dense', ascending=False)
    block_df[f'{v.replace("_index_national","")}_percentile_national'] = block_df[v].rank(pct=True)

    block_df[f'{v.replace("_index_national","")}_rank_state'] = block_df.groupby(['STATE_NAME'])[v].rank(method="dense", ascending=False)
    block_df[f'{v.replace("_index_national","")}_percentile_state'] = block_df.groupby(['STATE_NAME'])[v].rank(pct=True)

#%%
# Get rows where 'ACSTOTPOP' is greater than zero
positive_population_df = block_df[block_df['ACSTOTPOP'] > 0]
# Check if 'bg_ej_scale' or 'bg_vulnerability_scale' are null
if positive_population_df[['bg_ej_index_national', 'bg_ej_rank_national', 'bg_ej_percentile_national']].isna().any().any():
    raise ValueError("Alert: 'ej scores are null for one or more rows where 'ACSTOTPOP' is greater than zero.")

no_population_df = block_df[(block_df['ACSTOTPOP'] == 0) | (block_df['ACSTOTPOP'].isna())]
# Check if 'bg_ej_scale' or 'bg_vulnerability_scale' are not null
if no_population_df[['bg_ej_index_national', 'bg_ej_rank_national', 'bg_ej_percentile_national']].notnull().any().any():
    raise ValueError("Alert: ej scores are notnull for one or more rows where 'ACSTOTPOP' is than zero.")

#%%

block_df.rename(columns = {'STATE_NAME':'state',
                           'CNTY_NAME':'county',
                           'ACSTOTPOP':'bg_total_population',
                            'PEOPCOLORP':'bg_people_of_color_pct',
                            'LOWINCPCT':'bg_low_income_pct',
                            'UNEMPPCT':'bg_unemployment_pct',
                            'LINGISOPCT':'bg_english_second_language_pct',
                            'LESSHSPCT':'bg_less_than_highschool_pct',
                            'OVER64PCT':'bg_over_64_pct',
                            'UNDER5PCT':'bg_under_5_pct',
                            'FlareCou_1':'bg_flare_count',
                            'DetectionS':'bg_flare_detection_sum',
                            'BCMSum':'bg_bcm_sum',
                            'BCMSum_scale':'bg_bcm_sum_scale',
                            'area':'area_m2'
                            },inplace=True)

#%%

EJ_df = block_df[['block_group_id','state','county','area_m2','bg_total_population',
 'bg_people_of_color_pct','bg_low_income_pct','bg_unemployment_pct',
 'bg_english_second_language_pct','bg_less_than_highschool_pct',
 'bg_over_64_pct','bg_under_5_pct',
 'bg_flare_count','bg_flare_detection_sum',
 'bg_bcm_sum','bg_flare_density','bg_avg_flare_detection',
 'bg_bcm_sum_scale','bg_flare_density_scale','bg_avg_flare_detection_scale',
 'bg_flare_aggregate','bg_flare_aggregate_scale','bg_flare_index_national','bg_flare_index_state',
 'bg_vulnerability','bg_vulnerability_scale','bg_vulnerability_index_national','bg_vulnerability_index_state',
 'bg_ej_scale','bg_ej_index_national','bg_ej_index_state',
 'bg_flare_rank_national','bg_flare_percentile_national','bg_flare_rank_state','bg_flare_percentile_state',
 'bg_vulnerability_rank_national','bg_vulnerability_percentile_national','bg_vulnerability_rank_state','bg_vulnerability_percentile_state',
 'bg_ej_rank_national','bg_ej_percentile_national','bg_ej_rank_state','bg_ej_percentile_state',
 ]].copy(deep=True)

#%%


EJ_df.to_csv(f'{mykey.sharepoint}/Data/Final Data/block_ej.csv', index=False)
# %%
