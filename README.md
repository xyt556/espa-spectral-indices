## Spectral Indices Version 2.1.0 Release Notes
Release Date: December 3, 2014

The spectral indices project contains application source code for producing spectral index products.  It currently supports Landsat 4-8 using a single application.

Spectral index products are commonly used to identify or highlight certain features such as vegetation, water, and burn areas. They are based on band ratios utilizing known responses of the desired feature in the visible, near infrared (NIR) and short wave infrared bands (SWIR). 

This application processes Landsat surface reflectance products or TOA reflectance products to generate the following index products: 
* NDVI - Normalized Difference Vegetation Index 
* NDMI - Normalized Difference Moisture Index (also referred to as NDWI for water index and NDII) 
* NBR - Normalized Burn Ratio 
* NBR2 - Normalized Burn Ratio2 
* SAVI - Soil Adjusted Vegetation Index (soil adjustment factor is a constant of 0.5) 
* MSAVI - Modified Soil Adjusted Vegetation Index (soil adjustment factor is "self-adjustable" so as to increase the SAVI vegetation sensitivity by increasing the dynamic range and further reducing the soil background effects) 
* EVI - Enhanced Vegetation Index 

This project is hosted by the US Geological Survey (USGS) Earth Resources Observation and Science (EROS) Land Satellite Data Systems (LSDS) Science Research and Development (LSRD) Project. For questions regarding this source code, please contact the Landsat Contact Us page and specify USGS CDR/ECV in the "Regarding" section. https://landsat.usgs.gov/contactus.php 

### Downloads
Spectral Indices source code

    git clone https://github.com/USGS-EROS/espa-spectral-indices.git

See git tag [version_2.1.0]

### Installation
  1. Install dependent libraries - ESPA product formatter (https://github.com/USGS-EROS/espa-product-formatter)
  2. Set up environment variables.  Can create an environment shell file or add the following to your bash shell.  For C shell, use 'setenv VAR "directory"'.
```
    export PREFIX="path_to_directory_for_spectral_indices_build_data"
```

  3. Download (from Github USGS-EROS spectral-indices project) and install source files
```
cd src
make
make install
make clean
```
This will create an executable file under $PREFIX/bin: spectral_indices (tested in Linux with the gcc compiler). It will also copy the Python scripts for running spectral indices from the scripts directory up the the $PREFIX/bin directory.

  4. Test - Download Landsat surface reflectance products or top of atmosphere products from ESPA.  Then run the spectral_indices binary or do_spectral_indices.py script.  User information is available via the --help command-line argument.
```
spectral_indices --help
do_spectral_indices.py --help
```

  5. Check output - There will be a separate ESPA file generated for each of the spectral index products specified on the command line.  In addition each band should be added to the input XML file.
```
{scene_name}_ndvi.bin
{scene_name}_ndmi.bin
{scene_name}_nbr.bin
{scene_name}_nbr2.bin
{scene_name}_savi.bin
{scene_name}_evi.bin
```

### Dependencies
  * ESPA raw binary and ESPA common libraries from ESPA product formatter and associated dependencies
  * XML2 library

### Data Preprocessing
This version of the spectral indices application requires the input Landsat products to be in the ESPA internal file format.

### Data Postprocessing
After compiling the ESPA product formatter raw\_binary libraries and tools, the convert\_espa\_to\_gtif and convert\_espa\_to\_hdf command-line tools can be used to convert the ESPA internal file format to HDF or GeoTIFF.  Otherwise the data will remain in the ESPA internal file format, which includes each band in the ENVI file format (i.e. raw binary file with associated ENVI header file) and an overall XML metadata file.

### Associated Scripts
A python script exists in the scripts directory to assist in running the spectral indices application.  do\_spectral\_indices.py grabs the user-specified options and generates the desire spectral index products by calling the spectral\_indices executable.

### Verification Data

### User Manual

### Product Guide

## Changes From Previous Version
#### Updates on December 23, 2014 - USGS EROS
  * src
    1. Modified the spectral indices to process Landsat 8 products, OLI and OLI_TIRS.
