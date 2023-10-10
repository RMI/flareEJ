#%%

import geopandas as gpd
from shapely.geometry import Polygon
# %%
# Sample data: 4 points defining a square
data = {'geometry': [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]}
gdf = gpd.GeoDataFrame(data)

# %%
buffer_distance = 0.5
gdf['buffered_geometry'] = gdf['geometry'].buffer(buffer_distance)

# %%
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
gdf['geometry'].plot(ax=ax, color='blue', alpha=0.5, edgecolor='black')
gdf['buffered_geometry'].plot(ax=ax, color='red', alpha=0.3, edgecolor='black')
plt.show()

# %%
print(gdf.crs)
# %%
# Sample code to check if a point is within the buffered polygon
from shapely.geometry import Point
sample_point = Point(0.5, 0.5)
is_within = sample_point.within(gdf['buffered_geometry'].iloc[0])
print(is_within)


# %%
