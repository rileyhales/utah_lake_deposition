import glob
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

import rch

os.chdir('/Users/rchales/Projects/utah_lake_deposition/')

unique_dates = set(map(lambda t: t.split('_')[1], glob.glob('./tiffs/*.tiff')))

gdf = gpd.read_file('./utah_lake.gpkg')
coords, x, y = rch.arrays.uniform_xy_coords(-112.05, -111.55, 39.9, 40.4, 0.005)

mask = rch.gis.polygon_raster_mask(gdf, x=x, y=y)

values = {
    'tp': [],
    'tn': [],
    'op': [],
    'date': [],
}

res_m = 30
kg_per_mg = .001
l_per_m3 = 1000
mm_per_m = 1000
pixel_area_m2 = res_m * res_m

for date in unique_dates:
    try:
        with rasterio.open(f'./tiffs/p_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
            precip_raster = f.read(1)
        with rasterio.open(f'./tiffs/tp_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
            tp_raster = f.read(1)
        with rasterio.open(f'./tiffs/op_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
            op_raster = f.read(1)
        with rasterio.open(f'./tiffs/tn_{date}_IDW2_{res_m}m_3857.tiff', 'r') as f:
            tn_raster = f.read(1)

        # SUM(
        #     (nutrient_raster mg/L) * (.001 kg/mg) * (1000 L/m^3) * (precip_depth_mm) * (1000 mm/m) * (pixel_area_m2)
        # ) = kg_deposited
        tp_deposited = np.sum(tp_raster * precip_raster * mask) * kg_per_mg * l_per_m3 * mm_per_m * pixel_area_m2
        op_deposited = np.sum(op_raster * precip_raster * mask) * kg_per_mg * l_per_m3 * mm_per_m * pixel_area_m2
        tn_deposited = np.sum(tn_raster * precip_raster * mask) * kg_per_mg * l_per_m3 * mm_per_m * pixel_area_m2

        values['tp'].append(tp_deposited)
        values['op'].append(op_deposited)
        values['tn'].append(tn_deposited)
        values['date'].append(date)
    except Exception as e:
        print(e)
        continue

pd.DataFrame(values).to_csv('./utah_lake_deposition.csv')
