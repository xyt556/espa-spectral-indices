## Spectral Indices Version 2.2.0 Release Notes
Release Date: October XX, 2015

See git tag [version_2.2.0]

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

This project is provided by the US Geological Survey (USGS) Earth Resources Observation and Science (EROS) Land Satellite Data Systems (LSDS) Science Research and Development (LSRD) Project. For questions regarding products produced by this source code, please contact the Landsat Contact Us page and specify USGS CDR/ECV in the "Regarding" section. https://landsat.usgs.gov/contactus.php

## Installation

### Dependencies
* ESPA raw binary libraries, tools, and it's dependencies, found here [espa-product-formatter](https://github.com/USGS-EROS/espa-product-formatter)
* Python 2.7

### Environment Variables
* Required for building this software
```
export PREFIX="path_to_Installation_Directory"
export XML2INC="path_to_LIBXML2_include_files"
export XML2LIB="path_to_LIBXML2_libraries"
export ESPAINC="path_to_ESPA_PRODUCT_FORMATTER_include_files"
export ESPALIB="path_to_ESPA_PRODUCT_FORMATTER_libraries"
```

### Build Steps
* Clone the repository and replace the defaulted version(master) with this
  version of the software
```
git clone https://github.com/USGS-EROS/espa-spectral-indices.git
cd espa-spectral-indices
git checkout version_<version>
```
* Build and install the software
```
make
make install
```

## Usage
See `spectral_indices.py --help` for command line details.

### Environment Variables
* PATH - Must be updated to include `$PREFIX/espa-spectral-indices/bin`

### Data Processing Requirements
This version of the Spectral Indices application requires the input products to be in the ESPA internal file format.

The following input data are required to generate the spectral indicies products:
* Top of Atmosphere Reflectance, <b>or</b>
* Surface Reflectance

These products can be generated using the [LEDAPS](https://github.com/USGS-EROS/espa-surface-reflectance) or [L8_SR](https://github.com/USGS-EROS/espa-surface-reflectance) software found in our [espa-surface-reflectance](https://github.com/USGS-EROS/espa-surface-reflectance) project.  Or through our ondemand processing system [ESPA](https://espa.cr.usgs.gov), be sure to select the ENVI output format.

### Data Postprocessing
After compiling the [espa-product-formatter](https://github.com/USGS-EROS/espa-product-formatter) libraries and tools, the `convert_espa_to_gtif` and `convert_espa_to_hdf` command-line tools can be used to convert the ESPA internal file format to HDF or GeoTIFF.  Otherwise the data will remain in the ESPA internal file format, which includes each band in the ENVI file format (i.e. raw binary file with associated ENVI header file) and an overall XML metadata file.

## Changes From Previous Version
#### Updates on October XX, 2015 - USGS EROS
  * Replaced do_spectral_indices.py with spectral_indices.py
  * Enhanced Makefile's for build and installing the software
  * Installation installs to $PREFIX/espa-spectral-indices
