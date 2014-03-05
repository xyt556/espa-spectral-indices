#include <time.h>
#include <ctype.h>
#include "output.h"


/******************************************************************************
MODULE:  open_output

PURPOSE:  Set up the output data structure.  Open the output file for write
    access.

RETURN VALUE:
Type = Output_t
Value          Description
-----          -----------
NULL           Error occurred opening the HDF file
Valid output   Successful completion
data structure

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
2/12/2012    Gail Schmidt     Original Development (based on input routines
                              from the LEDAPS lndsr application)
2/14/2014    Gail Schmidt     Modified to work with ESPA internal raw binary
                              file format

NOTES:
  1. Don't allocate space for buf, since pointers to existing buffers will
     be assigned in the output structure.
  2. TOA products will have an "toa_" in the file name and SR products will
     have an "sr_" in the file name to designate products processed with TOA
     bands vs. SR bands.  Otherwise the source will be key along with the band
     name to pull the appropriate band from the XML file.
******************************************************************************/
Output_t *open_output
(
    Espa_internal_meta_t *in_meta,  /* I: input metadata structure */
    Input_t *input,                 /* I: input reflectance band data */
    int nband,                      /* I: number of bands to be created */
    char short_si_names[][STR_SIZE], /* I: array of short names for SI bands */
    char long_si_names[][STR_SIZE]   /* I: array of long names for SI bands */
)
{
    Output_t *this = NULL;
    char FUNC_NAME[] = "open_output";   /* function name */
    char errmsg[STR_SIZE];       /* error message */
    char *upper_str = NULL;      /* upper case version of the SI short name */
    char *mychar = NULL;         /* pointer to '_' */
    char scene_name[STR_SIZE];   /* scene name for the current scene */
    char production_date[MAX_DATE_LEN+1]; /* current date/time for production */
    time_t tp;                   /* time structure */
    struct tm *tm = NULL;        /* time structure for UTC time */
    int ib;    /* looping variable for bands */
    int refl_indx = -1;          /* band index in XML file for the reflectance
                                    band */
    Espa_band_meta_t *bmeta = NULL;  /* pointer to the band metadata array
                                        within the output structure */

    /* Check parameters */
    if (nband < 1 || nband > MAX_OUT_BANDS)
    {
        sprintf (errmsg, "Invalid number of image bands");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    /* Create the Output data structure */
    this = (Output_t *) malloc (sizeof (Output_t));
    if (this == NULL) 
    {
        sprintf (errmsg, "Error allocating Output data structure");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    /* Find the representative band for metadata information.  SR vs. TOA
       shouldn't matter in this case.  They should be the same size and
       resolution. */
    for (ib = 0; ib < in_meta->nbands; ib++)
    {
        if (!strcmp (in_meta->band[ib].name, "toa_band1") &&
            !strcmp (in_meta->band[ib].product, "toa_refl"))
        {
            /* this is the index we'll use for reflectance band info */
            refl_indx = ib;
            break;
        }
    }

    /* Make sure we found the TOA band 1 */
    if (refl_indx == -1)
    {
        sprintf (errmsg, "Unable to find the TOA reflectance bands in the "
            "XML file for initializing the output metadata.");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }

    /* Initialize the internal metadata for the output product. The global
       metadata won't be updated, however the band metadata will be updated
       and used later for appending to the original XML file. */
    init_metadata_struct (&this->metadata);

    /* Allocate memory for the total bands */
    if (allocate_band_metadata (&this->metadata, nband) != SUCCESS)
    {
        sprintf (errmsg, "Allocating band metadata.");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
    bmeta = this->metadata.band;

    /* Determine the scene name */
    strcpy (scene_name, in_meta->band[refl_indx].file_name);
    mychar = strchr (scene_name, '_');
    if (mychar != NULL)
      *mychar = '\0';
  
    /* Get the current date/time (UTC) for the production date of each band */
    if (time (&tp) == -1)
    {
        sprintf (errmsg, "Unable to obtain the current time.");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    tm = gmtime (&tp);
    if (tm == NULL)
    {
        sprintf (errmsg, "Converting time to UTC.");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    if (strftime (production_date, MAX_DATE_LEN, "%Y-%m-%dT%H:%M:%SZ", tm) == 0)
    {
        sprintf (errmsg, "Formatting the production date/time.");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }

    /* Populate the data structure */
    this->open = false;
    this->nband = nband;
    this->nlines = input->nlines;
    this->nsamps = input->nsamps;
    for (ib = 0; ib < this->nband; ib++)
        this->fp_bin[ib] = NULL;
 
    for (ib = 0; ib < nband; ib++)
    {
        strncpy (bmeta[ib].short_name, in_meta->band[refl_indx].short_name, 3);
        bmeta[ib].short_name[3] = '\0';
        upper_str = upper_case_str (short_si_names[ib]);
        strcat (bmeta[ib].short_name, upper_str);
        strcpy (bmeta[ib].product, "spectral_indices");
        if (strstr (short_si_names[ib], "toa"))
            strcpy (bmeta[ib].source, "toa_refl");
        else
            strcpy (bmeta[ib].source, "sr_refl");
        strcpy (bmeta[ib].category, "index");
        bmeta[ib].nlines = this->nlines;
        bmeta[ib].nsamps = this->nsamps;
        bmeta[ib].pixel_size[0] = input->pixsize[0];
        bmeta[ib].pixel_size[1] = input->pixsize[1];
        strcpy (bmeta[ib].pixel_units, "meters");
        sprintf (bmeta[ib].app_version, "spectral_indices_%s", INDEX_VERSION);
        strcpy (bmeta[ib].production_date, production_date);
        bmeta[ib].data_type = ESPA_INT16;
        bmeta[ib].fill_value = FILL_VALUE;
        bmeta[ib].saturate_value = SATURATE_VALUE;
        bmeta[ib].scale_factor = SCALE_FACTOR;
        bmeta[ib].valid_range[0] = -FLOAT_TO_INT;
        bmeta[ib].valid_range[1] = FLOAT_TO_INT;
        strcpy (bmeta[ib].name, short_si_names[ib]);
        strcpy (bmeta[ib].long_name, long_si_names[ib]);
        strcpy (bmeta[ib].data_units, "band ratio index value");

        /* Set up the filename with the scene name and band name and open the
           file for write access */
        if (strstr (short_si_names[ib], "toa"))
            sprintf (bmeta[ib].file_name, "%s_%s.img", scene_name,
                bmeta[ib].name);
        else
            sprintf (bmeta[ib].file_name, "%s_sr_%s.img", scene_name,
                bmeta[ib].name);
        this->fp_bin[ib] = open_raw_binary (bmeta[ib].file_name, "w");
        if (this->fp_bin[ib] == NULL)
        {
            sprintf (errmsg, "Unable to open output band %d file: %s", ib,
                bmeta[ib].file_name);
            error_handler (true, FUNC_NAME, errmsg);
            return (NULL);
        }
    }  /* for ib */
    this->open = true;

    /* Successful completion */
    return this;
}


/******************************************************************************
MODULE:  close_output

PURPOSE:  Closes the output file.

RETURN VALUE:
Type = int
Value      Description
-----      -----------
ERROR      Error occurred closing the HDF file
SUCCESS    Successful completion

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
2/12/2012    Gail Schmidt     Original Development (based on input routines
                              from the LEDAPS lndsr application)
2/14/2014    Gail Schmidt     Modified to work with ESPA internal raw binary
                              file format

NOTES:
******************************************************************************/
int close_output
(
    Output_t *this    /* I/O: Output data structure to close */
)
{
    char FUNC_NAME[] = "close_output";   /* function name */
    char errmsg[STR_SIZE];    /* error message */
    int ib;                   /* looping variable */

    if (!this->open)
    {
        sprintf (errmsg, "File is not open, so it cannot be closed.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    /* Close raw binary products */
    for (ib = 0; ib < this->nband; ib++)
        close_raw_binary (this->fp_bin[ib]);
    this->open = false;

    return (SUCCESS);
}


/******************************************************************************
MODULE:  free_output

PURPOSE:  Frees the memory for the output data structure

RETURN VALUE:
Type = int
Value      Description
-----      -----------
ERROR      Error occurred freeing the data structure
SUCCESS    Successful completion

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
2/12/2012    Gail Schmidt     Original Development (based on input routines
                              from the LEDAPS lndsr application)
2/14/2014    Gail Schmidt     Modified to work with ESPA internal raw binary
                              file format

NOTES:
******************************************************************************/
int free_output
(
    Output_t *this    /* I/O: Output data structure to free */
)
{
    char FUNC_NAME[] = "free_output";   /* function name */
    char errmsg[STR_SIZE];    /* error message */
  
    if (this->open) 
    {
        sprintf (errmsg, "Spectral index file is still open, so cannot free "
            "memory.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
  
    if (this != NULL)
    {
        /* Free the data structure */
        free (this);
    }
  
    return (SUCCESS);
}


/******************************************************************************
MODULE:  put_output_line

PURPOSE:  Writes a line or lines of data to the output file.

RETURN VALUE:
Type = int
Value      Description
-----      -----------
ERROR      Error occurred writing the output data
SUCCESS    Successful completion

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
2/12/2012    Gail Schmidt     Original Development (based on input routines
                              from the LEDAPS lndsr application)
2/14/2014    Gail Schmidt     Modified to work with ESPA internal raw binary
                              file format

NOTES:
******************************************************************************/
int put_output_line
(
    Output_t *this,    /* I: Output data structure; buf contains the line to
                             be written */
    int16 *buf,        /* I: buffer to be written */
    int iband,         /* I: current band to be written (0-based) */
    int iline,         /* I: current line to be written (0-based) */
    int nlines         /* I: number of lines to be written */
)
{
    char FUNC_NAME[] = "put_output_line";   /* function name */
    char errmsg[STR_SIZE];        /* error message */
  
    /* Check the parameters */
    if (this == (Output_t *)NULL) 
    {
        sprintf (errmsg, "Invalid input structure");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (!this->open)
    {
        sprintf (errmsg, "File is not open.  Cannot write data.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (iband < 0 || iband >= this->nband)
    {
        sprintf (errmsg, "Invalid band number.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (iline < 0 || iline >= this->nlines)
    {
        sprintf (errmsg, "Invalid line number.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (nlines < 0 || iline+nlines > this->nlines)
    {
        sprintf (errmsg, "Line plus number of lines to be written exceeds "
            "the predefined size of the image.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
  
    /* Write the data */
    if (write_raw_binary (this->fp_bin[iband], nlines, this->nsamps,
        sizeof (int16), buf) != SUCCESS)
    {
        sprintf (errmsg, "Error writing the output line(s) for band %d.",
            iband);
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    
    return (SUCCESS);
}


/******************************************************************************
MODULE:  upper_case_str

PURPOSE:  Returns the upper case version of the input string.

RETURN VALUE:
Type = char *
Value      Description
-----      -----------
up_str     Upper case version of the input string

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date         Programmer       Reason
---------    ---------------  -------------------------------------
2/14/2012    Gail Schmidt     Original Development

NOTES:
******************************************************************************/
char *upper_case_str
(
    char *str    /* I: string to be converted to upper case */
)
{
    char *up_str = NULL;    /* upper case version of the input string */
    char *ptr = NULL;       /* pointer to the upper case string */

    up_str = strdup (str);
    ptr = up_str;
    while (*ptr != '\0')
    {
        if (islower (*ptr))
            *ptr = toupper (*ptr);
        ptr++;
    }

    return up_str;
}

