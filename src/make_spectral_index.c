#include "si.h"

/******************************************************************************
MODULE:  make_spectral_index

PURPOSE:  Computes the spectral index using the specified input bands.
index - (band1 - band2) / (band1 + band2)

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
4/6/2013     Gail Schmidt     Original Development

NOTES:
  1. Input and output arrays are 1D arrays of size nlines * nsamps.
  2. The index products will be created using the scaled reflectance
     values as it doesn't matter if they are scaled or unscaled for these
     simple band ratios.  Both bands are scaled by the same amount.
  3. If the current pixel is saturated in either band, then the output pixel
     value for the index will also be saturated.  The same applies for fill.
******************************************************************************/
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
)
{
    int pix;                /* current pixel being processed */
    float ratio;            /* band ratio */

    /* Loop through the pixels in the array and compute the spectral index */
    for (pix = 0; pix < nlines * nsamps; pix++)
    {
        /* If the current pixel is saturated in either band then the output
           is saturated.  Ditto for fill. */
        if (band1[pix] == fill_value || band2[pix] == fill_value)
            spec_indx[pix] = FILL_VALUE;
        else if (band1[pix] == satu_value || band2[pix] == satu_value)
            spec_indx[pix] = SATURATE_VALUE;
        else
        {
            /* Compute the band ratio */
            ratio = (float) (band1[pix] - band2[pix]) /
                    (float) (band1[pix] + band2[pix]);

            /* Keep the ratio between -1.0, 1.0 */
            if (ratio > 1.0)
                ratio = 1.0;
            else if (ratio < -1.0)
                ratio = -1.0;

            /* Scale to an int16 */
            if (ratio >= 0.0)
                spec_indx[pix] = (int16) (ratio * FLOAT_TO_INT + 0.5);
            else
                spec_indx[pix] = (int16) (ratio * FLOAT_TO_INT - 0.5);
        }
    }
}


/******************************************************************************
MODULE:  make_savi

PURPOSE:  Computes the soil adjusted vegetation index using the specified input bands.
SAVI = ((nir - red) / (nir + red + L)) * (1 + L)
where L is the soil brightness correction factor (0.5)

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
4/6/2013     Gail Schmidt     Original Development

NOTES:
  1. Input and output arrays are 1D arrays of size nlines * nsamps.
  2. The index products will be created using the unscaled reflectance
     values.
  3. If the current pixel is saturated in either band, then the output pixel
     value for the index will also be saturated.  The same applies for fill.
******************************************************************************/
void make_savi
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
    int16 *savi           /* O: output SAVI */
)
{
    int pix;                /* current pixel being processed */
    float ratio;            /* band ratio */
    float red_unscaled;     /* red pixel unscaled */
    float nir_unscaled;     /* nir pixel unscaled */
    float L=0.5;            /* soil brightness factor */

    /* Loop through the pixels in the array and compute the spectral index */
    for (pix = 0; pix < nlines * nsamps; pix++)
    {
        /* If the current pixel is saturated in either band then the output
           is saturated.  Ditto for fill. */
        if (nir[pix] == fill_value || red[pix] == fill_value)
            savi[pix] = FILL_VALUE;
        else if (nir[pix] == satu_value || red[pix] == satu_value)
            savi[pix] = SATURATE_VALUE;
        else
        {
            /* Compute the band ratio */
            nir_unscaled = (float) (nir[pix] * scale_factor);
            red_unscaled = (float) (red[pix] * scale_factor);
            ratio = ((nir_unscaled - red_unscaled) /
                    (nir_unscaled + red_unscaled + L)) * (1.0 + L);

            /* Keep the ratio between -1.0, 1.0 */
            if (ratio > 1.0)
                ratio = 1.0;
            else if (ratio < -1.0)
                ratio = -1.0;

            /* Scale to an int16 */
            if (ratio >= 0.0)
                savi[pix] = (int16) (ratio * FLOAT_TO_INT + 0.5);
            else
                savi[pix] = (int16) (ratio * FLOAT_TO_INT - 0.5);
        }
    }
}


/******************************************************************************
MODULE:  make_modified_savi

PURPOSE:  Computes the soil adjusted vegetation index using the specified input bands.
MSAVI = (2 * nir + 1 - SQRT (SQR (2 * nir + 1) - (8 * (nir - red)))) * L
where L is the soil brightness correction factor and a value of 0.5.

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
5/9/2013     Gail Schmidt     Original Development

NOTES:
  1. Input and output arrays are 1D arrays of size nlines * nsamps.
  2. The index products will be created using the unscaled reflectance
     values.
  3. If the current pixel is saturated in either band, then the output pixel
     value for the index will also be saturated.  The same applies for fill.
  4. The algorithm for this is based on the MSAVI2 algorithm defined in the
     publication "A Modified Soil Adjusted Vegetation Index" by Qi, et al.
     in the Remote Sensing Environment. 48:119-126 (1994).
******************************************************************************/
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
)
{
    int pix;                /* current pixel being processed */
    float ratio;            /* band ratio */
    float red_unscaled;     /* red pixel unscaled */
    float nir_unscaled;     /* nir pixel unscaled */
    float L=0.5;            /* soil brightness factor */

    /* Loop through the pixels in the array and compute the spectral index */
    for (pix = 0; pix < nlines * nsamps; pix++)
    {
        /* If the current pixel is saturated in either band then the output
           is saturated.  Ditto for fill. */
        if (nir[pix] == fill_value || red[pix] == fill_value)
            msavi[pix] = FILL_VALUE;
        else if (nir[pix] == satu_value || red[pix] == satu_value)
            msavi[pix] = SATURATE_VALUE;
        else
        {
            /* Compute the band ratio */
            nir_unscaled = (float) (nir[pix] * scale_factor);
            red_unscaled = (float) (red[pix] * scale_factor);
            ratio = ((2.0 * nir_unscaled + 1.0) -
                sqrt ((2.0 * nir_unscaled + 1.0) * (2.0 * nir_unscaled + 1.0) -
                (8.0 * (nir_unscaled - red_unscaled)))) * L;

            /* Keep the ratio between -1.0, 1.0 */
            if (ratio > 1.0)
                ratio = 1.0;
            else if (ratio < -1.0)
                ratio = -1.0;

            /* Scale to an int16 */
            if (ratio >= 0.0)
                msavi[pix] = (int16) (ratio * FLOAT_TO_INT + 0.5);
            else
                msavi[pix] = (int16) (ratio * FLOAT_TO_INT - 0.5);
        }
    }
}


/******************************************************************************
MODULE:  make_evi

PURPOSE:  Computes the enhanced vegetation index using the specified input
bands.
EVI = (nir - red) / (nir + C1 * red - C2 * blue + L)
where C1 = 6, C2 = 7.5, and L = 1.0 (same coefficients used for the standard
MODIS EVI product)

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
4/6/2013     Gail Schmidt     Original Development

NOTES:
  1. Input and output arrays are 1D arrays of size nlines * nsamps.
  2. The index products will be created using the unscaled reflectance
     values.
  3. If the current pixel is saturated in either band, then the output pixel
     value for the index will also be saturated.  The same applies for fill.
******************************************************************************/
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
)
{
    int pix;                /* current pixel being processed */
    float ratio;            /* band ratio */
    float red_unscaled;     /* red pixel unscaled */
    float nir_unscaled;     /* nir pixel unscaled */
    float blue_unscaled;    /* blue pixel unscaled */

    /* Loop through the pixels in the array and compute the spectral index */
    for (pix = 0; pix < nlines * nsamps; pix++)
    {
        /* If the current pixel is saturated in either band then the output
           is saturated.  Ditto for fill. */
        if (nir[pix] == fill_value || red[pix] == fill_value ||
            blue[pix] == fill_value)
            evi[pix] = FILL_VALUE;
        else if (nir[pix] == satu_value || red[pix] == satu_value ||
            blue[pix] == satu_value)
            evi[pix] = SATURATE_VALUE;
        else
        {
            /* Compute the band ratio */
            nir_unscaled = (float) (nir[pix] * scale_factor);
            red_unscaled = (float) (red[pix] * scale_factor);
            blue_unscaled = (float) (blue[pix] * scale_factor);
            ratio = (nir_unscaled - red_unscaled) /
               (nir_unscaled + 6.0 * red_unscaled - 7.5 * blue_unscaled + 1.0);

            /* Keep the ratio between -1.0, 1.0 */
            if (ratio > 1.0)
                ratio = 1.0;
            else if (ratio < -1.0)
                ratio = -1.0;

            /* Scale to an int16 */
            if (ratio >= 0.0)
                evi[pix] = (int16) (ratio * FLOAT_TO_INT + 0.5);
            else
                evi[pix] = (int16) (ratio * FLOAT_TO_INT - 0.5);
        }
    }
}
