
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import pytest


###Tests
def test_columns_na_when_population_zero(df):
    # Get rows where 'bg_total_population' is zero
    zero_population_df = df[df['bg_total_population'] == 0]

    # Check that 'bg_ej_scale' and 'bg_vulnerability_scale' are NaN
    assert zero_population_df[['bg_ej_scale', 'bg_vulnerability_scale',
                               'bg_vulnerability_rank_national','bg_vulnerability_percentile_national',
                               'bg_vulnerability_rank_state','bg_vulnerability_percentile_state',
                               'bg_ej_rank_national','bg_ej_percentile_national',
                               'bg_ej_rank_state','bg_ej_percentile_state']].isna().all().all(), "Environmental justice and vulnerability columns should be NaN when 'bg_total_population' is zero"
    
    # Print a success message
    print("Test passed successfully. Environmental justice and vulnerability columns are NaN when 'bg_total_population' is zero.")

def test_columns_na_when_population_nonzero(df):
    # Get rows where 'bg_total_population' is zero
    zero_population_df = df[df['bg_total_population'] != 0]

    # Check that 'bg_ej_scale' and 'bg_vulnerability_scale' are NaN
    assert zero_population_df[['bg_ej_scale', 'bg_vulnerability_scale',
                               'bg_vulnerability_rank_national','bg_vulnerability_percentile_national',
                               'bg_vulnerability_rank_state','bg_vulnerability_percentile_state',
                               'bg_ej_rank_national','bg_ej_percentile_national',
                               'bg_ej_rank_state','bg_ej_percentile_state']].notnull().all().all(), "Environmental justice and vulnerability columns should have value when 'bg_total_population' is not zero"
    
    # Print a success message
    print("Test passed successfully. Environmental justice and vulnerability exist when 'bg_total_population' is non zero.")


if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from keys import MyKeys
    mykey = MyKeys("../config.ini")

    #%%
    #Import data
    EJ_df = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/block_ej.csv')
    flare_ej = pd.read_csv(f'{mykey.sharepoint}/Data/Final Data/flare_ej.csv')
    #%%
    test_columns_na_when_population_zero(EJ_df)
    test_columns_na_when_population_nonzero(EJ_df)
