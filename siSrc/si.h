#ifndef _SI_H_
#define _SI_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "bool.h"
#include "mystring.h"
#include "error_handler.h"
#include "input.h"
#include "output.h"
#include "space.h"

/* Prototypes */
void usage ();

void find_scenename
(
    char *sr_filename,   /* I: Input surface reflectance filename */
    char *dir_name,      /* O: Output directory name */
    char *scene_name     /* O: Output scene name */
);

short get_args
(
    int argc,             /* I: number of cmd-line args */
    char *argv[],         /* I: string of cmd-line args */
    char **sr_infile,     /* O: address of input surface reflectance file */
    bool *ndvi,           /* O: flag to process NDVI */
    bool *ndmi,           /* O: flag to process NDMI */
    bool *nbr,            /* O: flag to process NBR */
    bool *nbr2,           /* O: flag to process NBR2 */
    bool *savi,           /* O: flag to process SAVI */
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
