@echo off

::Parameters to set:: 

set las_file_path=F:\2025_10_17BuchauerStra_e71\test_run\Test_Punktwolke.laz
set tif_dtm_path=F:\2025_10_17BuchauerStra_e71\test_run\test_dtm.tif

::Parameters that can be set, but should be kept constant::

set height_cutoff=0
set pxl_size=0.02
set interpolation=percentile
set epsg_code=25832
set no_data_value=9999
set perc_clip=2

::Parameter that must be set once::
set python_path=C:\Users\matth\anaconda3\envs\base_env\python.exe

%python_path% BaWue_LAS_to_TIF.py %las_file_path% %tif_dtm_path% %height_cutoff% %pxl_size% %interpolation% %epsg_code% %no_data_value% %perc_clip%

pause