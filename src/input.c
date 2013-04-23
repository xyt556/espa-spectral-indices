#include "input.h"

#define INPUT_PROVIDER ("DataProvider")
#define INPUT_SAT ("Satellite")
#define INPUT_INST ("Instrument")
#define INPUT_ACQ_DATE ("AcquisitionDate")
#define INPUT_PROD_DATE ("Level1ProductionDate")
#define INPUT_SUN_ZEN ("SolarZenith")
#define INPUT_SUN_AZ ("SolarAzimuth")
#define INPUT_WRS_SYS ("WRS_System")
#define INPUT_WRS_PATH ("WRS_Path")
#define INPUT_WRS_ROW ("WRS_Row")
#define INPUT_NBAND ("NumberOfBands")
#define INPUT_BANDS ("BandNumbers")
#define INPUT_PIXEL_SIZE ("PixelSize")
#define INPUT_FILL_VALUE ("_FillValue")
#define INPUT_SATURATE_VALUE ("_SaturateValue")
#define INPUT_SCALE_FACTOR ("scale_factor")
#define INPUT_WEST_BOUND  ("WestBoundingCoordinate")
#define INPUT_EAST_BOUND  ("EastBoundingCoordinate")
#define INPUT_NORTH_BOUND ("NorthBoundingCoordinate")
#define INPUT_SOUTH_BOUND ("SouthBoundingCoordinate")
#define INPUT_UL_LAT_LONG ("UpperLeftCornerLatLong")
#define INPUT_LR_LAT_LONG ("LowerRightCornerLatLong")

#define N_LSAT_WRS1_ROWS  (251)
#define N_LSAT_WRS1_PATHS (233)
#define N_LSAT_WRS2_ROWS  (248)
#define N_LSAT_WRS2_PATHS (233)

#define SDS_PREFIX ("band")

/******************************************************************************
MODULE:  open_input

PURPOSE:  Sets up the input data structure, opens the input reflectance file
for read access, allocates space, and stores some of the metadata for later
reference.

RETURN VALUE:
Type = Input_t*
Value      Description
-----      -----------
NULL       Error occurred opening or reading the file
non-NULL   Successful completion
 

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
4/6/2013    Gail Schmidt     Original Development (based on input routines
                             from the LEDAPS lndsr application)

NOTES:
  1. This routine opens the input reflectance file and associated SDSs.  It
     also allocates memory for pointers in the input structure.  It is up to
     the caller to use close_input and free_input to close the HDF file and
     free up the memory when done using the input data structure.
******************************************************************************/
Input_t *open_input
(
    char *refl_file_name      /* I: input reflectance filename */
)
{
    char FUNC_NAME[] = "open_input";   /* function name */
    char errmsg[STR_SIZE];    /* error message */
    char sds_name[STR_SIZE];  /* name of the current SDS */
    int ib;                   /* index for bands */
    int ir;                   /* index for dimension rank */
    double dval[10];          /* double value for reading the attributes for
                                 the current band like fill, saturation
                                 value, and scale factor */
    Myhdf_dim_t *dim[2];      /* dimensions for the current SDS */
    Input_t *this = NULL;     /* input data structure to be initialized,
                                 populated, and returned to the caller */
    Myhdf_attr_t attr;        /* values for the SDS attributes */
    int16 *buf = NULL;        /* temporary buffer to allocate memory for
                                 the reflectance bands */
  
    /* Create the Input data structure */
    this = (Input_t *) malloc (sizeof (Input_t));
    if (this == NULL) 
    {
        strcpy (errmsg, "Error allocating memory for Input data structure");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    /* Populate the filename in the data structure */
    this->refl_file_name = dup_string (refl_file_name);
    if (this->refl_file_name == NULL)
    {
        free (this);
        strcpy (errmsg, "Error duplicating the reflectance filename");
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }

    /* Open the file for SD access */
    this->refl_sds_file_id = SDstart ((char *)refl_file_name, DFACC_RDONLY);
    if (this->refl_sds_file_id == HDF_ERROR)
    {
        free (this->refl_file_name);
        free (this);  
        sprintf (errmsg, "Error opening the input reflectance file: %s",
            refl_file_name);
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
    this->refl_open = true;
  
    /* Get the global metadata from the input reflectance file */
    if (get_input_meta (this) != SUCCESS)
    {
        free (this->refl_file_name);
        free (this);  
        sprintf (errmsg, "Error reading the input metadata from file: %s",
            refl_file_name);
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
  
    /* Get SDS information and start SDS access */
    for (ib = 0; ib < this->nrefl_band; ib++)
    {
        this->refl_sds[ib].name = NULL;
        this->refl_sds[ib].dim[0].name = NULL;
        this->refl_sds[ib].dim[1].name = NULL;
        this->refl_buf[ib] = NULL;
    }
  
    /* Loop through the image bands and obtain the SDS information */
    strcpy (errmsg, "none");
    for (ib = 0; ib < this->nrefl_band; ib++)
    {
        /* Get the SDS name and information */
        sprintf (sds_name, "%s%d", SDS_PREFIX, this->meta.refl_band[ib]);
        this->refl_sds[ib].name = dup_string (sds_name);
        if (this->refl_sds[ib].name == NULL)
        {
            sprintf (errmsg, "Error getting the SDS name for reflectance "
                "band %d", ib);
            break;
        }
    
        if (get_sds_info (this->refl_sds_file_id, &this->refl_sds[ib])
            != SUCCESS)
        {
            sprintf (errmsg, "Error getting the SDS info for reflectance "
                "band %d", ib);
            break;
        }
    
        /* Check rank */
        if (this->refl_sds[ib].rank != 2)
        {
            sprintf (errmsg, "Invalid rank for the SDS for reflectance "
                "band %d", ib);
            break;
        }
    
        /* Check SDS type */
        if (this->refl_sds[ib].type != DFNT_INT16)
        {
            sprintf (errmsg, "Invalid data type for the SDS for "
                "reflectance band %d.  Should be INT16.", ib);
            break;
        }
    
        /* Get dimensions */
        for (ir = 0; ir < this->refl_sds[ib].rank; ir++)
        {
            dim[ir] = &this->refl_sds[ib].dim[ir];
            if (get_sds_dim_info (this->refl_sds[ib].id, ir, dim[ir])
                != SUCCESS)
            {
                sprintf (errmsg, "Error obtaining the dimensions of the SDS "
                    "for reflectance band %d.", ib);
                break;
            }
        }
    
        /* Save and check line and sample dimensions */
        if (ib == 0)
        {
            this->nlines = dim[0]->nval;
            this->nsamps = dim[1]->nval;
        }
        else
        {
            if (this->nlines != dim[0]->nval)
            {
                sprintf (errmsg, "Dimensions for the number of lines in "
                    "reflectance band %d does not match the previous "
                    "dimensions for band 0.", ib);
                break;
            }
            if (this->nsamps != dim[1]->nval)
            {
                sprintf (errmsg, "Dimensions for the number of samples in "
                    "reflectance band %d does not match the previous "
                    "dimensions for band 0.", ib);
                break;
            }
        }
    
        /* If this is the first image band read the attribute metadata */
        if (ib == 0)
        {
            /* Fill value */
            attr.type = DFNT_INT16;
            attr.nval = 1;
            attr.name = INPUT_FILL_VALUE;
            if (get_attr_double (this->refl_sds[ib].id, &attr, dval) != SUCCESS)
            {
                sprintf (errmsg, "Error reading the fill value SDS attribute "
                    "for reflectance band %d.", ib);
                break;
            }
            if (attr.nval != 1) 
            {
                sprintf (errmsg, "Invalid number of values for the fill value "
                    "for reflectance band %d.", ib);
                break;
            }
            this->refl_fill = (int) dval[0];

            /* Scale factor */
            attr.type = DFNT_FLOAT32;
            attr.nval = 1;
            attr.name = INPUT_SCALE_FACTOR;
            if (get_attr_double (this->refl_sds[ib].id, &attr, dval) != SUCCESS)
            {
                sprintf (errmsg, "Error reading the scale factor SDS "
                    "attribute for reflectance band %d.", ib);
                break;
            }
            if (attr.nval != 1) 
            {
                sprintf (errmsg, "Invalid number of values for the scale "
                    "factor for reflectance band %d.", ib);
                break;
            }
            this->refl_scale_fact = dval[0];

            /* Saturation value */
            attr.type = DFNT_INT16;
            attr.nval = 1;
            attr.name = INPUT_SATURATE_VALUE;
            if (get_attr_double (this->refl_sds[ib].id, &attr, dval) != SUCCESS)
            {
                sprintf (errmsg, "Error reading the saturation value SDS "
                    "attribute for reflectance band %d.", ib);
                break;
            }
            if (attr.nval != 1) 
            {
                sprintf (errmsg, "Invalid number of values for the saturation "
                    "value for reflectance band %d.", ib);
                break;
            }
            this->refl_saturate_val = (int) dval[0];
        }  /* end if first band */
    }  /* for ib */
  
    /* Check for any errors processing the reflectance bands and use the
       error message already created */
    if (strcmp (errmsg, "none"))
    {
        close_input (this);
        free_input (this);
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }

    /* Allocate input buffers.  Reflectance buffer has multiple bands.
       Thermal band has one band.  Allocate PROC_NLINES of data for each
       band. */
    buf = (int16 *) calloc (PROC_NLINES * this->nsamps * this->nrefl_band,
        sizeof (int16));
    if (buf == NULL)
    {
        close_input (this);
        free_input (this);
        sprintf (errmsg, "Error allocating memory for input reflectance "
            "buffer containing %d lines.", PROC_NLINES);
        error_handler (true, FUNC_NAME, errmsg);
        return (NULL);
    }
    else
    {
        /* Set up the memory buffers for each band */
        this->refl_buf[0] = buf;
        for (ib = 1; ib < this->nrefl_band; ib++)
            this->refl_buf[ib] = this->refl_buf[ib-1] +
                PROC_NLINES * this->nsamps;
    }

    return (this);
}


/******************************************************************************
MODULE:  close_input

PURPOSE:  Ends SDS access and closes the input file.

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
1/2/2012    Gail Schmidt     Original Development (based on input routines
                             from the LEDAPS lndsr application)

NOTES:
******************************************************************************/
void close_input
(
    Input_t *this    /* I: pointer to input data structure */
)
{
    int ib;      /* loop counter for bands */
  
    /* Close the reflectance SDSs and HDF file */
    if (this->refl_open)
    {
        /* Close reflectance SDSs */
        for (ib = 0; ib < this->nrefl_band; ib++)
            SDendaccess (this->refl_sds[ib].id);
  
        /* Close the HDF file */
        SDend (this->refl_sds_file_id);
        this->refl_open = false;
    }
}


/******************************************************************************
MODULE:  free_input

PURPOSE:  Frees memory in the input data structure.

RETURN VALUE:
Type = None

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
1/2/2012    Gail Schmidt     Original Development (based on input routines
                             from the LEDAPS lndsr application)

NOTES:
******************************************************************************/
void free_input
(
    Input_t *this    /* I: pointer to input data structure */
)
{
    char FUNC_NAME[] = "free_input";   /* function name */
    char errmsg[STR_SIZE];             /* error message */
    int ib;                            /* loop counter for bands */
    int ir;                            /* loop counter for dimension ranks */
   
    if (this != NULL)
    {
        if (this->refl_open) 
        {
            strcpy (errmsg, "Freeing input data structure, but reflectance "
                "file is still open. Use close_input to close the file and "
                "SDSs.");
            error_handler (false, FUNC_NAME, errmsg);
        }
  
        /* Free image band SDSs */
        for (ib = 0; ib < this->nrefl_band; ib++)
        {
            for (ir = 0; ir < this->refl_sds[ib].rank; ir++)
            {
                if (this->refl_sds[ib].dim[ir].name != NULL) 
                    free (this->refl_sds[ib].dim[ir].name);
            }
            if (this->refl_sds[ib].name != NULL) 
                free (this->refl_sds[ib].name);
        }
  
        /* Free the data buffers */
        if (this->refl_buf[0] != NULL)
            free (this->refl_buf[0]);
        if (this->refl_file_name != NULL)
            free (this->refl_file_name);

        /* Free the data structure */
        free (this);
    } /* end if */
}


/******************************************************************************
MODULE:  get_input_refl_lines

PURPOSE:  Reads the reflectance data for the current band and lines, and
populates the refl_buf buffer in the Input_t data structure.

RETURN VALUE:
Type = int
Value      Description
-----      -----------
ERROR      Error occurred reading data for this band
SUCCESS    Successful completion

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
1/2/2012    Gail Schmidt     Original Development (based on input routines
                             from the LEDAPS lndsr application)

NOTES:
  1. The Input_t data structure needs to be populated and memory allocated
     before calling this routine.  Use open_input to do do.
******************************************************************************/
int get_input_refl_lines
(
    Input_t *this,   /* I: pointer to input data structure */
    int iband,       /* I: current band to read (0-based) */
    int iline,       /* I: current line to read (0-based) */
    int nlines       /* I: number of lines to read */
)
{
    char FUNC_NAME[] = "get_input_refl_line";   /* function name */
    char errmsg[STR_SIZE];    /* error message */
    int32 start[2];           /* array of starting line/samp for reading */
    int32 nval[2];            /* array of number of lines/samps to be read */
    void *buf = NULL;         /* pointer to the buffer for the current band */
  
    /* Check the parameters */
    if (this == (Input_t *) NULL) 
    {
        strcpy (errmsg, "Input structure has not been opened/initialized");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (!this->refl_open)
    {
        strcpy (errmsg, "Reflectance file has not been opened");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (iband < 0 || iband >= this->nrefl_band)
    {
        strcpy (errmsg, "Invalid band number for the reflectance file");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (iline < 0 || iline >= this->nlines)
    {
        strcpy (errmsg, "Invalid line number for reflectance band");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
  
    /* Read the data */
    start[0] = iline;    /* line to start reading */
    start[1] = 0;        /* sample to start reading */
    nval[0] = nlines;         /* number of lines to read */
    nval[1] = this->nsamps;   /* number of samples to read */
    buf = (void *) this->refl_buf[iband];
  
    if (SDreaddata (this->refl_sds[iband].id, start, NULL, nval, buf) ==
        HDF_ERROR)
    {
        sprintf (errmsg, "Error reading %d lines from reflectance band "
            "%d starting at line %d", nlines, iband, iline);
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
  
    return (SUCCESS);
}


/******************************************************************************
MODULE:  get_input_meta

PURPOSE:  Reads the global metadata from the input file

RETURN VALUE:
Type = int
Value      Description
-----      -----------
ERROR      Error occurred reading the metadata
SUCCESS    Successful completion

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
1/2/2012    Gail Schmidt     Original Development (based on input routines
                             from the LEDAPS lndsr application)
3/22/2013   Gail Schmidt     Modified to read the UL and LR lat/long coords

NOTES:
******************************************************************************/
int get_input_meta
(
    Input_t *this    /* I: pointer to input data structure */
)
{
    char FUNC_NAME[] = "get_input_meta";   /* function name */
    char errmsg[STR_SIZE];        /* error message */
    int ib;                       /* index for band looping */
    Myhdf_attr_t attr;            /* HDF info for the current attribute */
    double dval[NBAND_REFL_MAX];  /* double value read */
    char date[MAX_DATE_LEN + 1];  /* date value */
    Input_meta_t *meta = NULL;    /* pointer to the global metadata structure
                                     within the metadata structure */

    /* Check the parameters */
    if (!this->refl_open)
    {
        strcpy (errmsg, "Reflectance file is not open");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    /* Set metadata pointer to point to the global metadata for easy access */
    meta = &this->meta;

    /* Read the metadata */
    attr.type = DFNT_CHAR8;
    attr.nval = STR_SIZE;
    attr.name = INPUT_PROVIDER;
    if (get_attr_string (this->refl_sds_file_id, &attr, meta->provider)
        != SUCCESS)
    {
        strcpy (errmsg, "Error reading data provider attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_CHAR8;
    attr.nval = STR_SIZE;
    attr.name = INPUT_SAT;
    if (get_attr_string (this->refl_sds_file_id, &attr, meta->sat) != SUCCESS)
    {
        strcpy (errmsg, "Error reading satellite attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_CHAR8;
    attr.nval = STR_SIZE;
    attr.name = INPUT_INST;
    if (get_attr_string (this->refl_sds_file_id, &attr, meta->inst) != SUCCESS)
    {
        strcpy (errmsg, "Error reading instrument attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_CHAR8;
    attr.nval = MAX_DATE_LEN;
    attr.name = INPUT_ACQ_DATE;
    if (get_attr_string (this->refl_sds_file_id, &attr, date) != SUCCESS)
    {
        strcpy (errmsg, "Error reading acquisition date attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (date_init (date, DATE_FORMAT_DATEA_TIME, &meta->acq_date) != SUCCESS)
    {
        strcpy (errmsg, "Error converting acquisition date");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_CHAR8;
    attr.nval = MAX_DATE_LEN;
    attr.name = INPUT_PROD_DATE;
    if (get_attr_string (this->refl_sds_file_id, &attr, date) != SUCCESS)
    {
        strcpy (errmsg, "Error reading production date attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (date_init (date, DATE_FORMAT_DATEA_TIME, &meta->prod_date) != SUCCESS)
    {
        strcpy (errmsg, "Error converting production date");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    /* Get the solar zenith angle */
    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_SUN_ZEN;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Error reading solar zenith attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for solar zenith attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (dval[0] < -90.0  ||  dval[0] > 90.0)
    {
        strcpy (errmsg, "Solar zenith angle is out of range");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->solar_zen = (float)(dval[0] * RAD);

    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_SUN_AZ;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Error reading solar azimuth attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for solar azimuth attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (dval[0] < -360.0  ||  dval[0] > 360.0)
    {
        strcpy (errmsg, "Solar azimuth angle is out of range");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->solar_az = (float)(dval[0] * RAD);

    attr.type = DFNT_CHAR8;
    attr.nval = STR_SIZE;
    attr.name = INPUT_WRS_SYS;
    if (get_attr_string (this->refl_sds_file_id, &attr, meta->wrs_sys)
        != SUCCESS)
    {
        strcpy (errmsg, "Error reading WRS system attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_INT16;
    attr.nval = 1;
    attr.name = INPUT_WRS_PATH;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Error reading WRS path attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for WRS path attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->path = (int) floor (dval[0] + 0.5);
    if (meta->path < 1) 
    {
        strcpy (errmsg, "WRS path out of range");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    attr.type = DFNT_INT16;
    attr.nval = 1;
    attr.name = INPUT_WRS_ROW;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Error reading WRS row attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for WRS row attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->row = (int)floor(dval[0] + 0.5);
    if (meta->row < 1) 
    {
        strcpy (errmsg, "WRS row out of range");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    /* There should be 6 reflectance bands in this product */
    this->nrefl_band = 6;

    for (ib = 0; ib < this->nrefl_band; ib++)
    {
        if (ib < 5)
            meta->refl_band[ib] = ib + 1;
        else  /* need to add 1 to the band number to skip band 6 */
            meta->refl_band[ib] = ib + 2;

    }

    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_PIXEL_SIZE;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Error reading pixel size attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for pixel size attribute");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->pixsize = dval[0];

    /* Get the upper left and lower right corners */
    meta->ul_corner.is_fill = false;
    attr.type = DFNT_FLOAT32;
    attr.nval = 2;
    attr.name = INPUT_UL_LAT_LONG;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the UL lat/long coordinates.  "
            "Processing will continue but the scene will be assumed to be "
            "a normal, north-up scene and not an ascending polar scene.  Thus "
            "the solar azimuth will be used as-is and not adjusted if the "
            "scene is flipped.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->ul_corner.is_fill = true;
    }
    if (attr.nval != 2) 
    {
        strcpy (errmsg, "Invalid number of values for the UL lat/long "
            "coordinate.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->ul_corner.lat = dval[0];
    meta->ul_corner.lon = dval[1];

    meta->lr_corner.is_fill = false;
    attr.type = DFNT_FLOAT32;
    attr.nval = 2;
    attr.name = INPUT_LR_LAT_LONG;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the LR lat/long coordinates.  "
            "Processing will continue but the scene will be assumed to be "
            "a normal, north-up scene and not an ascending polar scene.  Thus "
            "the solar azimuth will be used as-is and not adjusted if the "
            "scene is flipped.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->lr_corner.is_fill = true;
    }
    if (attr.nval != 2) 
    {
        strcpy (errmsg, "Invalid number of values for the LR lat/long "
            "coordinate.");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }
    meta->lr_corner.lat = dval[0];
    meta->lr_corner.lon = dval[1];

    /* Get the bounding coordinates if they are available */
    meta->bounds.is_fill = false;
    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_WEST_BOUND;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the west bounding coordinate.  "
            "Processing will continue but the bounding coordinates will not "
            "be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for west bounding "
            "coordinate.  Processing will continue but the bounding "
            "coordinates will not be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    meta->bounds.min_lon = dval[0];

    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_EAST_BOUND;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the east bounding coordinate.  "
            "Processing will continue but the bounding coordinates will not "
            "be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for east bounding "
            "coordinate.  Processing will continue but the bounding "
            "coordinates will not be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    meta->bounds.max_lon = dval[0];

    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_NORTH_BOUND;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the north bounding coordinate.  "
            "Processing will continue but the bounding coordinates will not "
            "be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for north bounding "
            "coordinate.  Processing will continue but the bounding "
            "coordinates will not be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    meta->bounds.max_lat = dval[0];

    attr.type = DFNT_FLOAT32;
    attr.nval = 1;
    attr.name = INPUT_SOUTH_BOUND;
    if (get_attr_double (this->refl_sds_file_id, &attr, dval) != SUCCESS)
    {
        strcpy (errmsg, "Unable to read the south bounding coordinate.  "
            "Processing will continue but the bounding coordinates will not "
            "be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    if (attr.nval != 1) 
    {
        strcpy (errmsg, "Invalid number of values for south bounding "
            "coordinate.  Processing will continue but the bounding "
            "coordinates will not be written to the output product.");
        error_handler (false, FUNC_NAME, errmsg);
        meta->bounds.is_fill = true;
    }
    meta->bounds.min_lat = dval[0];

    /* Check WRS path/rows */
    if (!strcmp (meta->wrs_sys, "1"))
    {
        if (meta->path > N_LSAT_WRS1_PATHS)
        {
            strcpy (errmsg, "WRS path number out of range for WRS system 1");
            error_handler (true, FUNC_NAME, errmsg);
            return (ERROR);
        }
        else if (meta->row > N_LSAT_WRS1_ROWS)
        {
            strcpy (errmsg, "WRS row number out of range for WRS system 1");
            error_handler (true, FUNC_NAME, errmsg);
            return (ERROR);
        }
    }
    else if (!strcmp (meta->wrs_sys, "2"))
    {
        if (meta->path > N_LSAT_WRS2_PATHS)
        {
            strcpy (errmsg, "WRS path number out of range for WRS system 2");
            error_handler (true, FUNC_NAME, errmsg);
            return (ERROR);
        }
        else if (meta->row > N_LSAT_WRS2_ROWS)
        {
            strcpy (errmsg, "WRS row number out of range for WRS system 2");
            error_handler (true, FUNC_NAME, errmsg);
            return (ERROR);
        }
    }
    else
    {
        strcpy (errmsg, "Invalid WRS system");
        error_handler (true, FUNC_NAME, errmsg);
        return (ERROR);
    }

    return (SUCCESS);
}
