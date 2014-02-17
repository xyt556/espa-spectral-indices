#ifndef _SI_H_
#define _SI_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdbool.h>
#include "common.h"
#include "input.h"
#include "output.h"
#include "espa_metadata.h"
#include "parse_metadata.h"
#include "write_metadata.h"
#include "envi_header.h"
#include "error_handler.h"

/* Prototypes */
void usage ();

short get_args
(
    int argc,             /* I: number of cmd-line args */
    char *argv[],         /* I: string of cmd-line args */
    char **xml_infile,    /* O: address of input XML file */
    bool *toa,            /* O: flag to process TOA reflectance */
    bool *ndvi,           /* O: flag to process NDVI */
    bool *ndmi,           /* O: flag to process NDMI */
    bool *nbr,            /* O: flag to process NBR */
    bool *nbr2,           /* O: flag to process NBR2 */
    bool *savi,           /* O: flag to process SAVI */
    bool *msavi,          /* O: flag to process MSAVI */
    bool *evi,            /* O: flag to process EVI */
    bool *verbose         /* O: verbose flag */
);

void make_spectral_index
(
    int16 *band1,         /* I: input array of scaled reflectance data for
                                the spectral index */
    int16 *band2,         /* I: input array of scaled reflectance data for
                                the spectral index */
    int fill_value,       /* I: fill value for the reflectance values */
    int satu_value,       /* I: saturation value for the reflectance values */
    int nlines,           /* I: number of lines in the data arrays */
    int nsamps,           /* I: number of samples in the data arrays */
    int16 *spec_indx      /* O: output spectral index */
);

void make_savi
(
    int16 *nir,           /* I: input array of scaled reflectance data for
                                the nir band */
    int16 *red,           /* I: input array of scaled reflectance data for
                                the red band */
    float scale_value,    /* I: scale value for the reflectance values to
                                unscale the pixels to their true value */
    int fill_value,       /* I: fill value for the reflectance values */
    int satu_value,       /* I: saturation value for the reflectance values */
    int nlines,           /* I: number of lines in the data arrays */
    int nsamps,           /* I: number of samples in the data arrays */
    int16 *savi           /* O: output SAVI */
);

void make_modified_savi
(
    int16 *nir,           /* I: input array of scaled reflectance data for
                                the nir band */
    int16 *red,           /* I: input array of scaled reflectance data for
                                the red band */
    float scale_factor,   /* I: scale factor for the reflectance values to
                                unscale the pixels to their true value */
    int fill_value,       /* I: fill value for the reflectance values */
    int satu_value,       /* I: saturation value for the reflectance values */
    int nlines,           /* I: number of lines in the data arrays */
    int nsamps,           /* I: number of samples in the data arrays */
    int16 *msavi          /* O: output MSAVI */
);

void make_evi
(
    int16 *nir,           /* I: input array of scaled reflectance data for
                                the nir band */
    int16 *red,           /* I: input array of scaled reflectance data for
                                the red band */
    int16 *blue,          /* I: input array of scaled reflectance data for
                                the blue band */
    float scale_factor,   /* I: scale factor for the reflectance values to
                                unscale the pixels to their true value */
    int fill_value,       /* I: fill value for the reflectance values */
    int satu_value,       /* I: saturation value for the reflectance values */
    int nlines,           /* I: number of lines in the data arrays */
    int nsamps,           /* I: number of samples in the data arrays */
    int16 *evi            /* O: output EVI */
);

#endif
