#ifndef _INPUT_H_
#define _INPUT_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "common.h"
#include "error_handler.h"
#include "raw_binary_io.h"
#include "espa_metadata.h"

/* There are currently a maximum of 7 reflective bands (Landsat 8 has 7,
   Landsats 4-7 have 6) in the output surface reflectance product */
#define NBAND_REFL_MAX 7

/* Structure for the 'input' data type, particularly to handle the file/SDS
   IDs and the band-specific information */
typedef struct {
    bool refl_open;          /* open reflectance file flag; open = true */
    int nrefl_band;          /* number of input reflectance bands */
    int nlines;              /* number of input lines */
    int nsamps;              /* number of input samples */
    float pixsize[2];        /* pixel size x, y */
    int refl_band[NBAND_REFL_MAX]; /* band numbers for reflectance data */
    char *file_name[NBAND_REFL_MAX];  
                             /* Name of the input image files */
    int16 *refl_buf[NBAND_REFL_MAX]; /* input data buffer for unscaled
                                reflectance data (PROC_NLINES lines of data) */
    FILE *fp_bin[NBAND_REFL_MAX];  /* file pointer for binary files */
    int16 refl_fill;         /* fill value for reflectance bands */
    float refl_scale_fact;   /* scale factor for reflectance bands */
    int refl_saturate_val;   /* saturation value for reflectance bands */
} Input_t;

/* Prototypes */
Input_t *open_input
(
    Espa_internal_meta_t *metadata,     /* I: input metadata */
    bool toa         /* I: are we processing TOA reflectance data, otherwise
                           process surface reflectance data */
);

void close_input
(
    Input_t *this    /* I: pointer to input data structure */
);

void free_input
(
    Input_t *this    /* I: pointer to input data structure */
);

int get_input_refl_lines
(
    Input_t *this,   /* I: pointer to input data structure */
    int iband,       /* I: current band to read (0-based) */
    int iline,       /* I: current line to read (0-based) */
    int nlines       /* I: number of lines to read */
);

#endif
