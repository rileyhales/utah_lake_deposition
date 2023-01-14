import glob
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import rch

os.chdir('/Users/rchales/Projects/utah_lake_deposition/')

unique_dates = map(lambda t: t.split('_')[1], glob.glob('./tiffs/*.tiff'))
unique_dates = sorted(set(unique_dates))

gdf = gpd.read_file('./utah_lake.gpkg')

res = 30
xmin = -12463032
xmax = -12428250
ymin = 4867575
ymax = 4918525
coords, x, y = rch.arrays.uniform_xy_coords(xmin, xmax, ymin, ymax, res)
mask = rch.gis.polygon_raster_mask(gdf.to_crs(epsg=3857), x=x, y=y)

values = {
    'date': [],
    'tp': [],
    'tn': [],
    'op': [],
}

# unit conversion parameters
res_m = 30
kg_per_mg = 1 / 1000 / 1000
l_per_m3 = 1000
m_per_mm = 1 / 1000
pixel_area_m2 = res_m * res_m

for date in unique_dates:
    try:
        with rasterio.open(f'./tiffs/p_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
            precip_raster = f.read(1)

        # SUM(
        #  (nutrient_raster mg/L) * (.000001 kg/mg) * (1000 L/m^3) * (precip_depth_mm) * (1000 mm/m) * (pixel_area_m2)
        # ) = kg_deposited

        for nutrient in ['tp', 'tn', 'op']:
            tiff_path = f'./tiffs/{nutrient}_{date}_IDW2_{res_m}m_3857.tiff'
            if not os.path.exists(tiff_path):
                values[nutrient].append(np.nan)
                continue
            with rasterio.open(f'./tiffs/{nutrient}_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
                nutrient_raster = f.read(1)
            kg_deposited = np.nansum(
                nutrient_raster * precip_raster * mask) * kg_per_mg * l_per_m3 * m_per_mm * pixel_area_m2
            values[nutrient].append(kg_deposited)

        values['date'].append(date)
    except Exception as e:
        print(e)
        continue

df = pd.DataFrame(values)
for nutrient in ['tp', 'tn', 'op']:
    df[f'cum_{nutrient}'] = df[nutrient].cumsum()
df = df.dropna()
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
df = df.set_index('date', drop=True)
df.to_csv('./mitch_data/utah_lake_deposition.csv')

fig, ax = plt.subplots(figsize=(9, 6), dpi=1000, tight_layout=True)
df[['cum_tp', 'cum_tn', 'cum_op']].plot(ax=ax)
fig.suptitle('Cumulative Nutrient Deposition in Utah Lake')
ax.set_ylabel('Cumulative Nutrient Deposition (kg)')
ax.set_xlabel('Date')
ax.grid(True)
fig.savefig('./mitch_data/cum_nut_dep.png')
