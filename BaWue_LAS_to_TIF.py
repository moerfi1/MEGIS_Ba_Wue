# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 15:06:00 2026

@author: matth
"""

import pandas as pd
import numpy as np
import sys

import laspy 
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling


las_file_path = str(sys.argv[1])
tif_dtm_path = str(sys.argv[2])

height_cutoff = float(sys.argv[3])
pxl_size = float(sys.argv[4])
interpolation = str(sys.argv[5])
epsg_code = int(sys.argv[6])
no_data_value = float(sys.argv[7])
perc_clip = float(sys.argv[8])




def _point_to_raster_converter(x, y, data, cutoff = None, pxl_size = 0.1, interpolation = 'percentile', percentile = 95, epsg_code = 31287, no_data_value = -9999.9999, perc_clip = None, output_path = None):
    """
    Description
    ----------
    Function to take x- and y-coordinates as well as the z-values (or any other single data) of a point cloud and convert them to a Tif-File with a certain resolution. 

    Parameters
    ----------
    x : np.array
        Array of x-coordinates.
    y : np.array
        Array of y-coordinates.
    data : np.array
        Array of the z-values (or any other single value to be converted to Tif).
    cutoff : int / float
        Defines if a certain cutoff shall be subtracted from the data array (e.g. if z-values are too high and shall be reduced by the cutoff).
        Will be neglected if set to None.
        The default is None.
    pxl_size : float / int
        Pixel size of the Tif-File. 
        The default is 0.1.
    interpolation : str
        The type of calculation of the grouped values per pixel.
        Choose from 'maximum', 'minimum', 'mean', 'median', 'percentile'
        The default is 'percentile'.
    percentile : int
        Defines the percentile to calculate. Only necessary, if interpolation is set to 'percentile'. 
        The default is 95.
    epsg_code : int
        Integer number of the EPSG-Code of the CRS. 
        The default is 31287.
    no_data_value : int / float
        Defining the nodata value for the resulting Tif-File. 
        The default is -9999.9999.
    perc_clip : int
        If there are many outliers in the xy-dimension, define a percentile to clip in the xy-direction.
        If set to None, no clip will be performed. 
        The default is None.
    output_path : str
        Path to the destination Tif-File. 
        The default is None.

    Raises
    ------
    AttributeError
        Raises an error if the selected interpolation method is not available.

    Returns
    -------
    Writes Tif-File.

    """
    x_vals = np.round(x / pxl_size) * pxl_size
    y_vals = np.round(y / pxl_size) * pxl_size
    
    if perc_clip != None and type(perc_clip) == int: 
        x_min = np.percentile(x_vals, perc_clip)
        x_max = np.percentile(x_vals, 100 - perc_clip)
        y_min = np.percentile(y_vals, perc_clip)
        y_max = np.percentile(y_vals, 100 - perc_clip)
        
        mask = np.logical_and(np.logical_and(np.logical_and(x_vals >= x_min, x_vals <= x_max), y_vals >= y_min), y_vals <= y_max)
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]
        data = data[mask]
        
    else:
        x_min = min(x_vals)
        y_min = min(y_vals)
        x_max = max(x_vals)
        y_max = max(y_vals)
        
    if cutoff != None: 
        data = data - cutoff
    
    raster_df = pd.DataFrame()
    raster_df['x'] = x_vals
    raster_df['y'] = y_vals
    raster_df['data'] = data
    
    if interpolation == 'maximum': 
        grouped_df = raster_df.groupby(['x', 'y'])['data'].max().reset_index()
    
    elif interpolation == 'median': 
        grouped_df = raster_df.groupby(['x', 'y'])['data'].median().reset_index()
    
    elif interpolation == 'mean':
        grouped_df = raster_df.groupby(['x', 'y'])['data'].mean().reset_index()
    
    elif interpolation == 'minimum':
        grouped_df = raster_df.groupby(['x', 'y'])['data'].min().reset_index()
        
    elif interpolation == 'percentile':
        grouped_df = raster_df.groupby(['x', 'y'])['data'].apply(lambda g: np.percentile(g, percentile)).reset_index()
    
    else:
        raise AttributeError(f'{interpolation} as interpolation method not available. Please choose from the following: ["maximum", "minimum", "median", "mean", "percentile"]')
    
    
    x_coords = np.sort(grouped_df['x'].unique())
    y_coords = np.sort(grouped_df['y'].unique())
    X, Y = np.meshgrid(x_coords, y_coords)
    
    grid_arr = np.full(X.shape, np.nan)
    
    x_index = {v: i for i, v in enumerate(x_coords)}
    y_index = {v: i for i, v in enumerate(y_coords)}
    
    for _, row in grouped_df.iterrows():
        xi = x_index[row['x']]  # corrected
        yi = y_index[row['y']]  # corrected
        grid_arr[yi, xi] = row['data']
    
    if no_data_value != np.nan: 
        grid_arr[np.isnan(grid_arr)] = no_data_value
    
    if output_path != None: 
        out_transform = from_origin(x_coords.min(), y_coords.max(), pxl_size, pxl_size)
        out_profile = {
            'driver': 'GTiff', 
            'height': grid_arr.shape[0], 
            'width': grid_arr.shape[1], 
            'count': 1, 
            'dtype': grid_arr.dtype, 
            'crs': f'EPSG:{epsg_code}', 
            'transform': out_transform, 
            'nodata': no_data_value
            }
        with rasterio.open(output_path, 'w', **out_profile) as dst:
            dst.write(grid_arr, 1)


def _point_to_raster_converter_rgbi(x, y, red, green, blue, nir = None, pxl_size = 0.1, interpolation = 'percentile', percentile = 95, epsg_code = 31287, no_data_value = -9999.9999, perc_clip = None, output_path = None):
    """
    Description
    ----------
    Function to take x- and y-coordinates as well as RGB spectra of a point cloud and convert them to a Tif-File with a certain resolution. 

    Parameters
    ----------
    x : np.array
        Array of x-coordinates.
    y : np.array
        Array of y-coordinates.
    red : np.array
        Array of red spectra.
    green : np.array
        Array of green spectra.
    blue : np.array
        Array of blue spectra.
    nir : np.array
        If available, array of nIR spectra. Otherwise set to None.  
        The default is None.
    pxl_size : float / int
        Pixel size of the Tif-File. 
        The default is 0.1.
    interpolation : str
        The type of calculation of the grouped values per pixel.
        Choose from 'maximum', 'minimum', 'mean', 'median', 'percentile'
        The default is 'percentile'.
    percentile : int
        Defines the percentile to calculate. Only necessary, if interpolation is set to 'percentile'. 
        The default is 95.
    epsg_code : int
        Integer number of the EPSG-Code of the CRS. 
        The default is 31287.
    no_data_value : int / float
        Defining the nodata value for the resulting Tif-File. 
        The default is -9999.9999.
    perc_clip : int
        If there are many outliers in the xy-dimension, define a percentile to clip in the xy-direction.
        If set to None, no clip will be performed. 
        The default is None.
    output_path : str
        Path to the destination Tif-File. 
        The default is None.

    Raises
    ------
    AttributeError
        Raises an error if the selected interpolation method is not available.

    Returns
    -------
    Writes Tif-File.

    """
    x_vals = np.round(x / pxl_size) * pxl_size
    y_vals = np.round(y / pxl_size) * pxl_size
    
    if perc_clip != None and type(perc_clip) == int: 
        x_min = np.percentile(x_vals, perc_clip)
        x_max = np.percentile(x_vals, 100 - perc_clip)
        y_min = np.percentile(y_vals, perc_clip)
        y_max = np.percentile(y_vals, 100 - perc_clip)
        
        mask = np.logical_and(np.logical_and(np.logical_and(x_vals >= x_min, x_vals <= x_max), y_vals >= y_min), y_vals <= y_max)
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]
        red = red[mask]
        green = green[mask]
        blue = blue[mask]
        if nir != None: 
            nir = nir[mask]
        
    else:
        x_min = min(x_vals)
        y_min = min(y_vals)
        x_max = max(x_vals)
        y_max = max(y_vals)
    
    raster_df = pd.DataFrame()
    raster_df['x'] = x_vals
    raster_df['y'] = y_vals
    raster_df['red'] = red
    raster_df['green'] = green
    raster_df['blue'] = blue
    if nir != None:
        raster_df['nir'] = nir
    
    if interpolation == 'maximum': 
        grouped_df = raster_df.groupby(['x', 'y']).max().reset_index()
    
    elif interpolation == 'median': 
        grouped_df = raster_df.groupby(['x', 'y']).median().reset_index()
    
    elif interpolation == 'mean':
        grouped_df = raster_df.groupby(['x', 'y']).mean().reset_index()
    
    elif interpolation == 'minimum':
        grouped_df = raster_df.groupby(['x', 'y']).min().reset_index()
        
    elif interpolation == 'percentile':
        if nir == None:
            grouped_df = (
                raster_df
                .groupby(['x', 'y'])[['red', 'green', 'blue']]
                .quantile(percentile / 100)
                .reset_index()
            )
        else: 
            grouped_df = (
                raster_df
                .groupby(['x', 'y'])[['red', 'green', 'blue', 'nir']]
                .quantile(percentile / 100)
                .reset_index()
            )

    
    else:
        raise AttributeError(f'{interpolation} as interpolation method not available. Please choose from the following: ["maximum", "minimum", "median", "mean", "percentile"]')
    
    
    x_coords = np.sort(grouped_df['x'].unique())
    y_coords = np.sort(grouped_df['y'].unique())
    X, Y = np.meshgrid(x_coords, y_coords)
    
    grid_red = np.full(X.shape, np.nan)
    grid_green = np.full(X.shape, np.nan)
    grid_blue = np.full(X.shape, np.nan)
    if nir != None: 
        grid_nir = np.full(X.shape, np.nan)
    
    x_index = {v: i for i, v in enumerate(x_coords)}
    y_index = {v: i for i, v in enumerate(y_coords)}
    
    for _, row in grouped_df.iterrows():
        xi = x_index[row['x']]  
        yi = y_index[row['y']]  
        
        grid_red[yi, xi] = row['red']
        grid_green[yi, xi] = row['green']
        grid_blue[yi, xi] = row['blue']
        if nir != None: 
            grid_nir[yi, xi] = row['nir']
    
    if no_data_value != np.nan: 
        grid_red[np.isnan(grid_red)] = no_data_value
        grid_green[np.isnan(grid_green)] = no_data_value
        grid_blue[np.isnan(grid_blue)] = no_data_value
        if nir != None: 
            grid_nir[np.isnan(grid_nir)] = no_data_value
    
    if output_path != None: 
        band_count = 3 + (1 if nir is not None else 0)
        out_transform = from_origin(x_coords.min(), y_coords.max(), pxl_size, pxl_size)
        out_profile = {
            'driver': 'GTiff', 
            'height': grid_red.shape[0], 
            'width': grid_red.shape[1], 
            'count': band_count, 
            'dtype': grid_red.dtype, 
            'crs': f'EPSG:{epsg_code}', 
            'transform': out_transform, 
            'nodata': no_data_value
            }
        with rasterio.open(output_path, 'w', **out_profile) as dst:
            dst.write(grid_red, 1)
            dst.write(grid_green, 2)
            dst.write(grid_blue, 3)
            if nir != None: 
                dst.write(grid_nir, 4)
                
                
def _combine_DTM_with_calculated_DSM(dtm_path, dsm_path, out_path):
    """
    Description
    ----------
    Function to take a certain DTM-Tif-Path and the created DSM-Tif-Path, bring them to the same resolution and align them. Then fill the no-data-values of the DSM with the DTM values. 

    Parameters
    ----------
    dtm_path : str
        Path to the DTM-Tif-File.
    dsm_path : str
        Path to the DSM-Tif-File.
    out_path : str
        Path to the destination.

    Returns
    -------
    Writes Result to out_path.

    """
    with rasterio.open(dtm_path) as dtm_read: 
        # dtm = dtm_read.read(1)
        # dtm_epsg = dtm_read.crs.to_epsg()
        
        with rasterio.open(dsm_path) as dsm_read:
            dsm = dsm_read.read(1)
            # dsm_epsg = dsm_read.crs.to_epsg()
    
            dtm_dsm_resolution = np.empty((dsm_read.height, dsm_read.width), dtype = dsm_read.dtypes[0])
            reproject(
                source = rasterio.band(dtm_read, 1), 
                destination = dtm_dsm_resolution, 
                src_transform = dtm_read.transform, 
                src_crs = dtm_read.crs, 
                dst_transform = dsm_read.transform, 
                dst_crs = dsm_read.crs, 
                resampling = Resampling.bilinear
                )
            
            dsm_nodata = dsm_read.nodata
            
            if dsm_nodata is None: 
                mask = np.isnan(dsm)
            else: 
                mask = (dsm == dsm_nodata)
                
            out_combined = np.where(mask, dtm_dsm_resolution, dsm)
            
            profile = dsm_read.profile.copy()
            
            with rasterio.open(out_path, 'w', **profile) as dst:
                dst.write(out_combined, 1)


def main(las_file_path, tif_dtm_path, height_cutoff = None, pixel_size = 0.1, interpolation = 'percentile', epsg_code = 25832, no_data_value = -9999.9999, perc_clip = None):
    if las_file_path.endswith('.las'):
        dsm_path = las_file_path.replace('.las', '_DSM.tif')
        rgb_path = las_file_path.replace('.las', '_RGB.tif')
        com_path = las_file_path.replace('.las', '_DTM_DSM.tif')
    elif las_file_path.endswith('.laz'):
        dsm_path = las_file_path.replace('.laz', '.tif')
        rgb_path = las_file_path.replace('.laz', '_RGB.tif')
        com_path = las_file_path.replace('.laz', '_DTM_DSM.tif')
    else: 
        raise NameError('ERROR: Point Cloud Data has to be in .las or .laz format!')
        
    las_file = laspy.read(las_file_path)
    x_coords = np.array(las_file.x)
    y_coords = np.array(las_file.y)
    z_coords = np.array(las_file.z)
    red_arr = np.array(las_file.red)
    gre_arr = np.array(las_file.green)
    blu_arr = np.array(las_file.blue)
    
    print('Start conversion to DSM-Tif-File...')
    _point_to_raster_converter(x_coords, 
                               y_coords, 
                               z_coords, 
                               cutoff = height_cutoff, 
                               pxl_size = pixel_size, 
                               interpolation = interpolation, 
                               percentile = 95, 
                               epsg_code = epsg_code, 
                               no_data_value = no_data_value, 
                               perc_clip = perc_clip, 
                               output_path = dsm_path)
    
    print('Start conversion to RGB-Tif-File...')
    _point_to_raster_converter_rgbi(x_coords, 
                                    y_coords, 
                                    red_arr, 
                                    gre_arr, 
                                    blu_arr, 
                                    nir = None, 
                                    pxl_size = pixel_size, 
                                    interpolation = interpolation, 
                                    percentile = 95, 
                                    epsg_code = epsg_code, 
                                    no_data_value = no_data_value, 
                                    perc_clip = perc_clip, 
                                    output_path = rgb_path)
    
    print('Start alignment of DSM and DTM to each other...')
    _combine_DTM_with_calculated_DSM(tif_dtm_path, dsm_path, com_path)


if __name__ == '__main__':
    print('Loading point cloud...')
    main(
        las_file_path, 
        tif_dtm_path, 
        height_cutoff, 
        pxl_size, 
        interpolation, 
        epsg_code, 
        no_data_value, 
        perc_clip
        )
    print('Finished all tasks!')
