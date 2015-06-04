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
