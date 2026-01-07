# MEGIS_Ba_Wue

## 1. Initializing - Installing Python and Anaconda if not yet done
- Miniconda is recommended, download here for free: 
- **https://www.anaconda.com/docs/getting-started/miniconda/main#is-miniconda-free-for-me**
## 2. Create environment from yml-File
- Open Anaconda prompt
- Type the following: conda env create -f environment.yml 
- Or specifically (and replace MY_ENV with the desired environment name): conda env -n MY_ENV -f environment.yml
## 3. Define the Python-path in the EXECUTION.bat File (right click > open with Notepad): 
- Find the third paragraph (::Parameter that must be set once::)
- Change to the Python Path in the just created environment
- This looks usually like this:
- C:\Users\YOUR_USER_NAME\anaconda\envs\MY_ENV\python.exe
## 4. Set Paths for execution in EXECUTION.bat File (::Parameters to set::)
- las_file_path -> Define here the path to the point cloud (.las or .laz) that shall be converted to .tif
- tif_dtm_path -> Define here the path to the DTM raster (.tif)
## 5. If desired, set optional parameters (but recommended to keep them constant): 
- height_cutoff -> Defines if a certain cutoff shall be subtracted from the data array (e.g. if z-values are too high and shall be reduced by the cutoff).
- pxl_size -> Defines the resolution / pixel size the resulting raster shall have
- interpolation -> Defines how the points in one pixel shall be interpolated / grouped (maximum, minimum, mean, median, percentile)
- epsg_code -> Defines the EPSG-Code of the CRS
- no_data_value -> Defined the no_data_value of the resulting rasters
- perc_clip -> Defines the cutoff in the xy-Dimension (important if there are outliers present, which are far away from the actual cloud)


