#ifndef _COMMON_H_
#define _COMMON_H_

/* Define the spectral index products to be processed */
typedef enum {SI_NDVI=0, SI_EVI, SI_SAVI, SI_MSAVI, SI_NDMI, SI_NBR, SI_NBR2,
  NUM_SI} Mysi_list_t;

typedef signed short int16;
typedef unsigned char uint8;

/* Spectral index version */
#define INDEX_VERSION "2.0.1"

/* How many lines of data should be processed at one time */
#define PROC_NLINES 1000

#endif
