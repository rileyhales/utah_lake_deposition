import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin

import rch

if __name__ == '__main__':
    # input_file = './mitch_data/deposition_data_20230113.csv'
    input_file = './mitch_data/precipitation_data.csv'

    df = pd.read_csv(input_file, index_col=0)
    df['longitude'] = -df['longitude'].abs()
    df.columns = [c.replace('/', '') for c in df.columns]

    epsg = 3857
    pt_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs='EPSG:4326')
    pt_gdf.to_file(input_file.replace('.csv', '.gkpg'), driver='GPKG')
    pt_gdf = pt_gdf.to_crs(epsg=epsg)
    pt_gdf['longitude'] = pt_gdf.geometry.x
    pt_gdf['latitude'] = pt_gdf.geometry.y

    res = 30

    xmin = round(pt_gdf.longitude.min(), 0) - 60
    # xmax = round(pt_gdf.longitude.max(), 0) + 60
    # ymin = round(pt_gdf.latitude.min(), 0) - 60
    ymax = round(pt_gdf.latitude.max(), 0) + 120
    xmax = -12428250
    ymin = 4867575

    coords, x, y = rch.arrays.uniform_xy_coords(xmin, xmax, ymin, ymax, res)
    xx, yy = np.meshgrid(x, y)

    # Set the origin (top left corner) of the raster
    origin_x = x[0]
    origin_y = y[0]

    # Set the pixel size of the raster
    pixel_size_x = x[1] - x[0]
    pixel_size_y = y[0] - y[1]

    # Create the transformation matrix that maps pixel coordinates to coordinates in the specified projection
    transform = from_origin(origin_x, origin_y, pixel_size_x, pixel_size_y)

    p = 2

    for column in pt_gdf.drop(columns='geometry').columns[3:]:
        a = pt_gdf[['longitude', 'latitude', column]].values
        idw = rch.arrays.idw_grid_vector(a, xx, yy, p=p)

        # Create a new raster with the specified dimensions and transformation matrix
        with rasterio.open(f'./tiffs/{column}_IDW{p}_{res}m_{epsg}.tiff', 'w', driver='GTiff',
                           width=idw.shape[1], height=idw.shape[0],
                           count=1, dtype=idw.dtype,
                           crs=f'EPSG:{epsg}', transform=transform) as dst:
            # Write the values to the raster
            dst.write(idw, 1)
