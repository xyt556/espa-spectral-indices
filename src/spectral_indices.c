#include "si.h"

/******************************************************************************
MODULE:  spectral_indices

PURPOSE:  Computes the specified spectral indices for the TOA or surface
reflectance product.

RETURN VALUE:
Type = int
Value           Description
-----           -----------
ERROR           An error occurred during processing of the spectral indices
SUCCESS         Processing was successful

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date          Programmer       Reason
----------    ---------------  -------------------------------------
4/6/2013      Gail Schmidt     Original Development
5/9/2013      Gail Schmidt     Modified to support MSAVI (modified SAVI)
8/30/2013     Gail Schmidt     Modified to write the vegetation indices to
                               the same output file (NDVI, EVI, SAVI, MSAVI)
2/13/2014     Gail Schmidt     Modified to utilize the ESPA internal raw
                               binary file format
3/14/2014     Gail Schmidt     Updated to make sure that at least one spectral
                               index product was specified for processing
10/15/2014    Gail Schmidt     Modified to support Landsat 8 data

NOTES:
  1. The products are output as {base_scene_name}-{spectral_index_ext}.hdf.
     However, the NDVI, EVI, SAVI, and MSAVI products will all be written
     to one output file {base_scene_name}-vi.hdf.  The order is as specified
     in the previous sentence, based on which indices were actually specified.
  2. Reflectance bands are stored in the buffer as 0=b1, 1=b2, 2=b3, 3=b4,
     4=b5, 5=b7.
  3. TOA products will have an "toa_" in the file name and SR products will
     have an "sr_" in the file name to designate products processed with TOA
     bands vs. SR bands.  Otherwise the source will be key along with the band
     name to pull the appropriate band from the XML file.
******************************************************************************/
int main (int argc, char *argv[])
{
    bool verbose;            /* verbose flag for printing messages */
    bool toa_flag;           /* should the TOA bands be processed, otherwise
                                process surface reflectance bands */
    bool ndvi_flag;          /* should we process the NDVI product? */
    bool ndmi_flag;          /* should we process the NDMI product? */
    bool nbr_flag;           /* should we process the NBR product? */
    bool nbr2_flag;          /* should we process the NBR2 product? */
    bool savi_flag;          /* should we process the SAVI product? */
    bool msavi_flag;         /* should we process the modified SAVI product? */
    bool evi_flag;           /* should we process the EVI product? */

    char FUNC_NAME[] = "main"; /* function name */
    char errmsg[STR_SIZE];     /* error message */
    char envi_file[STR_SIZE];  /* name of the output ENVI header file */
    char short_si_names[MAX_OUT_BANDS][STR_SIZE]; /* output short names for SI
                                                     bands */
    char long_si_names[MAX_OUT_BANDS][STR_SIZE];  /* output long names for SI
                                                     bands */
    char *xml_infile = NULL; /* input XML filename */
    char *cptr = NULL;       /* pointer to the file extension */

    int retval;              /* return status */
    int k;                   /* variable to keep track of the % complete */
    int i;                   /* looping variable */
    int ib;                  /* looping variable for bands */
    int line;                /* current line to be processed */
    int nlines_proc;         /* number of lines to process at one time */
    int num_si;              /* number of spectral index products */
    int si_indx[NUM_SI];     /* index of each of the bands within the spectral
                                index product */
    int16 *blue=NULL;        /* blue band index */
    int16 *red=NULL;         /* red band index */
    int16 *nir=NULL;         /* NIR band index */
    int16 *mir=NULL;         /* MIR band index */
    int16 *swir=NULL;        /* SWIR band index */
    int16 *ndvi=NULL;        /* NDVI values */
    int16 *ndmi=NULL;        /* NDMI values */
    int16 *nbr=NULL;         /* NBR values */
    int16 *nbr2=NULL;        /* NBR2 values */
    int16 *savi=NULL;        /* SAVI values */
    int16 *msavi=NULL;       /* MSAVI values */
    int16 *evi=NULL;         /* EVI values */
    Input_t *refl_input=NULL;  /* input structure for the TOA or SR product */
    Output_t *si_output=NULL;   /* output structure and metadata for the
                                   SI products */
    Espa_internal_meta_t xml_metadata;  /* XML metadata structure */
    Espa_global_meta_t *gmeta = NULL; /* pointer to global meta */
    Envi_header_t envi_hdr;   /* output ENVI header information */

    printf ("Starting spectral indices processing ...\n");

    /* Read the command-line arguments */
    retval = get_args (argc, argv, &xml_infile, &toa_flag, &ndvi_flag,
        &ndmi_flag, &nbr_flag, &nbr2_flag, &savi_flag, &msavi_flag, &evi_flag,
        &verbose);
    if (retval != SUCCESS)
    {   /* get_args already printed the error message */
        exit (ERROR);
    }

    /* Provide user information if verbose is turned on */
    if (verbose)
    {
        printf ("  XML input file: %s\n", xml_infile);

        if (toa_flag)
            printf ("  Process TOA reflectance bands\n");
        else
            printf ("  Process surface reflectance bands\n");

        printf ("  Process NDVI - ");
        if (ndvi_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process EVI  - ");
        if (evi_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process SAVI - ");
        if (savi_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process MSAVI - ");
        if (msavi_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process NDMI - ");
        if (ndmi_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process NBR  - ");
        if (nbr_flag)
            printf ("yes\n");
        else
            printf ("no\n");

        printf ("  Process NBR2 - ");
        if (nbr2_flag)
            printf ("yes\n");
        else
            printf ("no\n");
    }

    if (!ndvi_flag && !ndmi_flag && !nbr_flag && !nbr2_flag && !savi_flag &&
        !msavi_flag && !evi_flag)
    {
        sprintf (errmsg, "No index product was specified for processing.");
        error_handler (true, FUNC_NAME, errmsg);
        exit (ERROR);
    }

    /* Validate the input metadata file */
    if (validate_xml_file (xml_infile) != SUCCESS)
    {  /* Error messages already written */
        exit (ERROR);
    }

    /* Initialize the metadata structure */
    init_metadata_struct (&xml_metadata);

    /* Parse the metadata file into our internal metadata structure; also
       allocates space as needed for various pointers in the global and band
       metadata */
    if (parse_metadata (xml_infile, &xml_metadata) != SUCCESS)
    {  /* Error messages already written */
        exit (ERROR);
    }
    gmeta = &xml_metadata.global;

    /* Open the reflectance product, set up the input data structure, and
       allocate memory for the data buffers */
    refl_input = open_input (&xml_metadata, toa_flag);
    if (refl_input == (Input_t *) NULL)
    {
        sprintf (errmsg, "Error opening/reading the reflectance data: %s",
            xml_infile);
        error_handler (true, FUNC_NAME, errmsg);
        exit (ERROR);
    }

    /* Output some information from the input files if verbose */
    if (verbose)
    {
        printf ("  Number of lines/samples: %d/%d\n", refl_input->nlines,
            refl_input->nsamps);
        printf ("  Number of reflective bands: %d\n", refl_input->nrefl_band);
        printf ("  Fill value: %d\n", refl_input->refl_fill);
        printf ("  Scale factor: %f\n", refl_input->refl_scale_fact);
        printf ("  Saturation value: %d\n", refl_input->refl_saturate_val);
    }

    /* Initialize the si_indx */
    for (i = 0; i < NUM_SI; i++)
        si_indx[i] = -1;

    /* Allocate memory for the NDVI */
    num_si = 0;
    if (ndvi_flag)
    {
        ndvi = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (ndvi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NDVI");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update band info for opening the VI product */
        si_indx[SI_NDVI] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_ndvi");
        else
            strcpy (short_si_names[num_si], "sr_ndvi");
        strcpy (long_si_names[num_si++],
            "normalized difference vegetation index");
    }

    /* Allocate memory for the EVI */
    if (evi_flag)
    {
        evi = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (evi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the EVI");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_EVI] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_evi");
        else
            strcpy (short_si_names[num_si], "sr_evi");
        strcpy (long_si_names[num_si++], "enhanced vegetation index");
    }

    /* Allocate memory for the NDMI */
    if (ndmi_flag)
    {
        ndmi = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (ndmi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NDMI");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_NDMI] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_ndmi");
        else
            strcpy (short_si_names[num_si], "sr_ndmi");
        strcpy (long_si_names[num_si++],
            "normalized difference moisture index");
    }

    /* Allocate memory for the SAVI */
    if (savi_flag)
    {
        savi = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (savi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the SAVI");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_SAVI] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_savi");
        else
            strcpy (short_si_names[num_si], "sr_savi");
        strcpy (long_si_names[num_si++], "soil adjusted vegetation index");
    }

    /* Allocate memory for the MSAVI */
    if (msavi_flag)
    {
        msavi = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (msavi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the MSAVI");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_MSAVI] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_msavi");
        else
            strcpy (short_si_names[num_si], "sr_msavi");
        strcpy (long_si_names[num_si++], 
            "modified soil adjusted vegetation index");
    }

    /* Allocate memory for the NBR */
    if (nbr_flag)
    {
        nbr = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (nbr == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NBR");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_NBR] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_nbr");
        else
            strcpy (short_si_names[num_si], "sr_nbr");
        strcpy (long_si_names[num_si++], "normalized burn ratio");
    }

    /* Allocate memory for the NBR2 */
    if (nbr2_flag)
    {
        nbr2 = calloc (PROC_NLINES*refl_input->nsamps, sizeof (int16));
        if (nbr2 == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NBR2");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        /* update info for opening the VI product */
        si_indx[SI_NBR2] = num_si;
        if (toa_flag)
            strcpy (short_si_names[num_si], "toa_nbr2");
        else
            strcpy (short_si_names[num_si], "sr_nbr2");
        strcpy (long_si_names[num_si++], "normalized burn ratio 2");
    }

    /* Open the specified output files and create the metadata structure */
    if (num_si > 0)
    {
        si_output = open_output (&xml_metadata, refl_input, num_si,
            short_si_names, long_si_names);
        if (si_output == NULL)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }

    /* Print the processing status if verbose */
    if (verbose)
    {
        printf ("  Processing %d lines at a time\n", PROC_NLINES);
        printf ("  Spectral indices -- %% complete: 0%%\r");
    }

    /* Loop through the lines and samples in the reflectance product,
       computing the desired indices */
    nlines_proc = PROC_NLINES;
    k = 0;
    for (line = 0; line < refl_input->nlines; line += PROC_NLINES)
    {
        /* Do we have nlines_proc left to process? */
        if (line + nlines_proc >= refl_input->nlines)
            nlines_proc = refl_input->nlines - line;

        /* Update processing status? */
        if (verbose && (100 * line / refl_input->nlines > k))
        {
            k = 100 * line / refl_input->nlines;
            printf ("  Spectral indices -- %% complete: %d%%\r", k);
            fflush (stdout);
        }

        /* Read the current lines from the reflectance file for each of the
           reflectance bands */
        for (ib = 0; ib < refl_input->nrefl_band; ib++)
        {
            if (get_input_refl_lines (refl_input, ib, line, nlines_proc) !=
                SUCCESS)
            {
                sprintf (errmsg, "Error reading %d lines from band %d of the "
                    "reflectance file starting at line %d", nlines_proc, ib,
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }  /* end for ib */

        /* Compute the NDVI and write to output file
           NDVI = (nir - red) / (nir + red) */
        if (ndvi_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                red = refl_input->refl_buf[2];  /* b3 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                red = refl_input->refl_buf[3];  /* b4 */
            }

            make_spectral_index (nir, red, refl_input->refl_fill,
                refl_input->refl_saturate_val, nlines_proc,
                refl_input->nsamps, ndvi);

            if (put_output_line (si_output, ndvi, si_indx[SI_NDVI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NDVI data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the EVI and write to output file
           EVI = (nir - red) / (nir + C1 * red - C2 * blue + L) */
        if (evi_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                red = refl_input->refl_buf[2];  /* b3 */
                blue = refl_input->refl_buf[0]; /* b1 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                red = refl_input->refl_buf[3];  /* b4 */
                blue = refl_input->refl_buf[1]; /* b2 */
            }

            make_evi (nir, red, blue, refl_input->refl_scale_fact,
                refl_input->refl_fill, refl_input->refl_saturate_val,
                nlines_proc, refl_input->nsamps, evi);

            if (put_output_line (si_output, evi, si_indx[SI_EVI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output EVI data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the SAVI and write to output file
           SAVI = ((nir - red) / (nir + red + L)) * (1 + L), where L is a
           constant 0.5. */
        if (savi_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                red = refl_input->refl_buf[2];  /* b3 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                red = refl_input->refl_buf[3];  /* b4 */
            }

            make_savi (nir, red, refl_input->refl_scale_fact,
                refl_input->refl_fill, refl_input->refl_saturate_val,
                nlines_proc, refl_input->nsamps, savi);

            if (put_output_line (si_output, savi, si_indx[SI_SAVI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output SAVI data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the MSAVI (modified SAVI) and write to output file
           MSAVI = (2 * nir + 1) - SQRT (SQR (2 * nir + 1) - (8 * (nir - red)))
                    * L
           where L is the soil brightness correction factor of 0.5*/
        if (msavi_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                red = refl_input->refl_buf[2];  /* b3 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                red = refl_input->refl_buf[3];  /* b4 */
            }

            make_modified_savi (nir, red, refl_input->refl_scale_fact,
                refl_input->refl_fill, refl_input->refl_saturate_val,
                nlines_proc, refl_input->nsamps, msavi);

            if (put_output_line (si_output, msavi, si_indx[SI_MSAVI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output MSAVI data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the NDMI and write to output file
           NDMI = (nir - mir) / (nir + mir) */
        if (ndmi_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                mir = refl_input->refl_buf[4];  /* b5 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                mir = refl_input->refl_buf[5];  /* b6 */
            }

            make_spectral_index (nir, mir, refl_input->refl_fill,
                refl_input->refl_saturate_val, nlines_proc,
                refl_input->nsamps, ndmi);

            if (put_output_line (si_output, ndmi, si_indx[SI_NDMI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NDMI data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the NBR and write to output file
           NBR = (nir - swir) / (nir + swir) */
        if (nbr_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                nir = refl_input->refl_buf[3];  /* b4 */
                swir = refl_input->refl_buf[5]; /* b7 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                nir = refl_input->refl_buf[4];  /* b5 */
                swir = refl_input->refl_buf[6]; /* b7 */
            }

            make_spectral_index (nir, swir, refl_input->refl_fill,
                refl_input->refl_saturate_val, nlines_proc,
                refl_input->nsamps, nbr);

            if (put_output_line (si_output, nbr, si_indx[SI_NBR], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NBR data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }

        /* Compute the NBR2 and write to output file
           NBR2 = (mir - swir) / (mir + swir) */
        if (nbr2_flag)
        {
            if (!strcmp (gmeta->instrument, "TM") ||
                !strncmp (gmeta->instrument, "ETM", 3))
            {
                mir = refl_input->refl_buf[4];  /* b5 */
                swir = refl_input->refl_buf[5]; /* b7 */
            }
            else if (!strcmp (gmeta->instrument, "OLI_TIRS"))
            {
                mir = refl_input->refl_buf[5];  /* b6 */
                swir = refl_input->refl_buf[6]; /* b7 */
            }

            make_spectral_index (mir, swir, refl_input->refl_fill,
                refl_input->refl_saturate_val, nlines_proc,
                refl_input->nsamps, nbr2);

            if (put_output_line (si_output, nbr2, si_indx[SI_NBR2], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NBR2 data for line %d", line);
                error_handler (true, FUNC_NAME, errmsg);
                exit (ERROR);
            }
        }
    }  /* end for line */

    /* Print the processing status if verbose */
    if (verbose)
        printf ("  Spectral indices -- %% complete: 100%%\n");

    /* Close the reflectance product */
    close_input (refl_input);
    free_input (refl_input);

    /* Write the ENVI header for spectral indices files */
    for (ib = 0; ib < si_output->nband; ib++)
    {
        /* Create the ENVI header file this band */
        if (create_envi_struct (&si_output->metadata.band[ib],
            &xml_metadata.global, &envi_hdr) != SUCCESS)
        {
            sprintf (errmsg, "Creating ENVI header structure.");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
  
        /* Write the ENVI header */
        strcpy (envi_file, si_output->metadata.band[ib].file_name);
        cptr = strchr (envi_file, '.');
        strcpy (cptr, ".hdr");
        if (write_envi_hdr (envi_file, &envi_hdr) != SUCCESS)
        {
            sprintf (errmsg, "Writing ENVI header file.");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }
  
    /* Append the spectral index bands to the XML file */
    if (append_metadata (si_output->nband, si_output->metadata.band,
        xml_infile) != SUCCESS)
    {
        sprintf (errmsg, "Appending spectral index bands to XML file.");
        error_handler (true, FUNC_NAME, errmsg);
        exit (ERROR);
    }
  
    /* Free the metadata structure */
    free_metadata (&xml_metadata);

    /* Close the output spectral indices products */
    close_output (si_output);
    free_output (si_output);

    /* Free the filename pointers */
    free (xml_infile);

    /* Free the mask pointers */
    free (ndvi);
    free (ndmi);
    free (nbr);
    free (nbr2);
    free (savi);
    free (msavi);
    free (evi);

    /* Indicate successful completion of processing */
    printf ("Spectral indices processing complete!\n");
    exit (SUCCESS);
}


/******************************************************************************
MODULE:  usage

PURPOSE:  Prints the usage information for this application.

RETURN VALUE:
Type = None

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
4/6/2013    Gail Schmidt     Original Development
2/14/2014   Gail Schmidt     Modified to support TOA vs. SR input bands

NOTES:
******************************************************************************/
void usage ()
{
    printf ("spectral_indices produces the desired spectral index products "
            "for the input surface reflectance or TOA reflectance bands. The "
            "options include NDVI, EVI, SAVI, MSAVI, NDMI (also known as NDWI "
            "or NDII), NBR, and NBR2. The user may specify one, some, or all "
            "of the supported indices for output.\n\n");
    printf ("usage: spectral_indices "
            "--xml=input_xml_filename [--toa] "
            "[--ndvi] [--evi] [--savi] [--msavi] [--ndmi] [--nbr] [--nbr2] "
            "[--verbose]\n");

    printf ("\nwhere the following parameters are required:\n");
    printf ("    -xml: name of the input XML file to be processed\n");

    printf ("\nwhere the following parameters are optional:\n");
    printf ("    -toa: process the TOA reflectance bands instead of the "
            "surface reflectance bands.\n");
    printf ("    -ndvi: process the normalized difference vegetation index "
            "(NDVI) product\n");
    printf ("    -evi: process the enhanced vegetation index (EVI) product\n");
    printf ("    -savi: process the soil adjusted vegetation index (SAVI) "
            "product (uses a soil brightness factor of 0.5)\n");
    printf ("    -msavi: process the modified soil adjusted vegetation index "
            "(MSAVI) product (uses a dynamic soil brightness factor)\n");
    printf ("    -ndmi: process the normalized difference moisture index "
            "(NDMI) product.  This is also known as the water index (NDWI) "
            "or NDII.\n");
    printf ("    -nbr: process the normalized burn ratio (NBR) product\n");
    printf ("    -nbr2: process the normalized burn ratio 2 (NBR2) product\n");
    printf ("    -verbose: should intermediate messages be printed? (default "
            "is false)\n");
    printf ("\nspectral_indices --help will print the usage statement\n");
    printf ("\nExample: spectral_indices "
            "--xml=LT50400331995173AAA02.xml "
            "--ndvi --ndmi --nbr --evi "
            "--verbose\n");
}

