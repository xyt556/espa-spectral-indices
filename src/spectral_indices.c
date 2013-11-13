#include "si.h"

/******************************************************************************
MODULE:  spectral_indices

PURPOSE:  Computes the specified spectral indices for the surface reflectance
product.  This application also works on the TOA reflectance product.

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

NOTES:
  1. The products are output as {base_scene_name}-{spectral_index_ext}.hdf.
     However, the NDVI, EVI, SAVI, and MSAVI products will all be written
     to one output file {base_scene_name}-vi.hdf.  The order is as specified
     in the previous sentence, based on which indices were actually specified.
  2. Reflectance bands are stored in the buffer as 0=b1, 1=b2, 2=b3, 3=b4,
     4=b5, 5=b7.
******************************************************************************/
int main (int argc, char *argv[])
{
    bool verbose;            /* verbose flag for printing messages */
    bool ndvi_flag;          /* should we process the NDVI product? */
    bool ndmi_flag;          /* should we process the NDMI product? */
    bool nbr_flag;           /* should we process the NBR product? */
    bool nbr2_flag;          /* should we process the NBR2 product? */
    bool savi_flag;          /* should we process the SAVI product? */
    bool msavi_flag;         /* should we process the modified SAVI product? */
    bool evi_flag;           /* should we process the EVI product? */

    char FUNC_NAME[] = "main"; /* function name */
    char errmsg[STR_SIZE];   /* error message */
    char dir_name[STR_SIZE]; /* directory name of input SR file */
    char scene_base_name[STR_SIZE]; /* scene name of input SR file */
    char short_name[STR_SIZE];   /* output SDS short name */
    char out_sds_names[NUM_OUT_SDS][STR_SIZE];    /* output SDS names for the
                                                     single band products */
    char out_vi_sds_names[MAX_OUT_SDS][STR_SIZE]; /* output SDS names for the
                                                     VI product */
    char *hdf_grid_name = "Grid";  /* name of the grid for HDF-EOS */
    char *sr_infile=NULL;    /* input SR filename */
    char vi_outfile[STR_SIZE];   /* output VI filename, containing all the
                                    user-specified SDSs which are vegetation
                                    index products */
    char ndmi_outfile[STR_SIZE]; /* output NDMI filename */
    char nbr_outfile[STR_SIZE];  /* output NBR filename */
    char nbr2_outfile[STR_SIZE]; /* output NBR2 filename */
    char ehdr_file[STR_SIZE];    /* temporary ENVI header filename */

    int retval;              /* return status */
    int k;                   /* variable to keep track of the % complete */
    int band;                /* current band to be processed */
    int line;                /* current line to be processed */
    int nlines_proc;         /* number of lines to process at one time */
    int num_vi;              /* number of vegetation index products */
    int vi_indx[MAX_OUT_SDS]; /* index of each of the VI bands within the VI
                                 product */
    int out_sds_types[NUM_OUT_SDS];     /* array of image SDS types for single
                                           band products */
    int out_vi_sds_types[MAX_OUT_SDS];  /* array of image SDS types for the
                                           VI product */

    int16 *ndvi=NULL;        /* NDVI values */
    int16 *ndmi=NULL;        /* NDMI values */
    int16 *nbr=NULL;         /* NBR values */
    int16 *nbr2=NULL;        /* NBR2 values */
    int16 *savi=NULL;        /* SAVI values */
    int16 *msavi=NULL;       /* MSAVI values */
    int16 *evi=NULL;         /* EVI values */

    Input_t *sr_input=NULL;  /* input structure for the SR product */
    Space_def_t space_def;   /* spatial definition information */
    Output_t *vi_output=NULL;   /* output structure and metadata for the
                                   VI products - NDVI, EVI, SAVI, MSAVI */
    Output_t *ndmi_output=NULL; /* NDMI output structure and metadata */
    Output_t *nbr_output=NULL;  /* NBR output structure and metadata */
    Output_t *nbr2_output=NULL; /* NBR2 output structure and metadata */

    printf ("Starting spectral indices processing ...\n");

    /* Read the command-line arguments */
    retval = get_args (argc, argv, &sr_infile, &ndvi_flag, &ndmi_flag,
        &nbr_flag, &nbr2_flag, &savi_flag, &msavi_flag, &evi_flag, &verbose);
    if (retval != SUCCESS)
    {   /* get_args already printed the error message */
        exit (ERROR);
    }

    /* Provide user information if verbose is turned on */
    if (verbose)
    {
        printf ("  Surface reflectance input file: %s\n", sr_infile);

        printf ("  Process NDVI - ");
        if (ndvi_flag)
            printf ("yes (written to the VI output product)\n");
        else
            printf ("no\n");

        printf ("  Process EVI  - ");
        if (evi_flag)
            printf ("yes (written to the VI output product)\n");
        else
            printf ("no\n");

        printf ("  Process SAVI - ");
        if (savi_flag)
            printf ("yes (written to the VI output product)\n");
        else
            printf ("no\n");

        printf ("  Process MSAVI - ");
        if (msavi_flag)
            printf ("yes (written to the VI output product)\n");
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

    /* Open the surface reflectance product, set up the input data structure,
       allocate memory for the data buffers, and read the associated metadata
       and attributes. */
    sr_input = open_input (sr_infile);
    if (sr_input == (Input_t *) NULL)
    {
        sprintf (errmsg, "Error opening/reading the surface reflectance file: "
            "%s\n",  sr_infile);
        error_handler (true, FUNC_NAME, errmsg);
        exit (ERROR);
    }

    /* Output some information from the input files if verbose */
    if (verbose)
    {
        printf ("  WRS path/row: %03d/%02d\n", sr_input->meta.path,
            sr_input->meta.row);
        printf ("  Number of lines/samples: %d/%d\n", sr_input->nlines,
            sr_input->nsamps);
        printf ("  Number of reflective bands: %d\n", sr_input->nrefl_band);
        printf ("  Pixel size: %f\n", sr_input->meta.pixsize);
        printf ("  Fill value: %d\n", sr_input->refl_fill);
        printf ("  Scale factor: %f\n", sr_input->refl_scale_fact);
        printf ("  Saturation value: %d\n", sr_input->refl_saturate_val);
    }

    /* Allocate memory for the NDVI */
    num_vi = 0;
    if (ndvi_flag)
    {
        ndvi = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (ndvi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NDVI");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        /* update SDS info for opening the VI product */
        vi_indx[SI_NDVI] = num_vi;
        strcpy (out_vi_sds_names[num_vi++], "NDVI");
    }

    /* Allocate memory for the EVI */
    if (evi_flag)
    {
        evi = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (evi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the EVI");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        /* update SDS info for opening the VI product */
        vi_indx[SI_EVI] = num_vi;
        strcpy (out_vi_sds_names[num_vi++], "EVI");
    }

    /* Allocate memory for the SAVI */
    if (savi_flag)
    {
        savi = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (savi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the SAVI");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        /* update SDS info for opening the VI product */
        vi_indx[SI_SAVI] = num_vi;
        strcpy (out_vi_sds_names[num_vi++], "SAVI");
    }

    /* Allocate memory for the MSAVI */
    if (msavi_flag)
    {
        msavi = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (msavi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the MSAVI");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        /* update SDS info for opening the VI product */
        vi_indx[SI_MSAVI] = num_vi;
        strcpy (out_vi_sds_names[num_vi++], "MSAVI");
    }

    /* Allocate memory for the NDMI */
    if (ndmi_flag)
    {
        ndmi = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (ndmi == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NDMI");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    /* Allocate memory for the NBR */
    if (nbr_flag)
    {
        nbr = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (nbr == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NBR");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    /* Allocate memory for the NBR2 */
    if (nbr2_flag)
    {
        nbr2 = (int16 *) calloc (PROC_NLINES*sr_input->nsamps, sizeof (int16));
        if (nbr2 == NULL)
        {
            sprintf (errmsg, "Error allocating memory for the NBR2");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    /* Get the projection and spatial information from the input surface
       reflectance product */
    retval = get_space_def_hdf (&space_def, sr_infile, hdf_grid_name);
    if (retval != SUCCESS)
    {
        sprintf (errmsg, "Error reading spatial metadata from the HDF file: "
            "%s", sr_infile);
        error_handler (true, FUNC_NAME, errmsg);
        close_input (sr_input);
        free_input (sr_input);
        exit (ERROR);
    }

    /* Pull the scene base name */
    find_scenename (sr_infile, dir_name, scene_base_name);

    /* Create and open the specified output HDF-EOS files */
    if (num_vi > 0)
    {   /* one overall VI file for NDVI, EVI, SAVI, and MSAVI */
        sprintf (vi_outfile, "%s%s-vi.hdf", dir_name, scene_base_name);
        if (create_output (vi_outfile) != SUCCESS)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        vi_output = open_output (vi_outfile, num_vi, out_vi_sds_names,
            sr_input->nlines, sr_input->nsamps);
        if (vi_output == NULL)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        /* Set up the buffers for each band of the VI product */
        if (ndvi_flag)
            vi_output->buf[vi_indx[SI_NDVI]] = ndvi;
        if (evi_flag)
            vi_output->buf[vi_indx[SI_EVI]] = evi;
        if (savi_flag)
            vi_output->buf[vi_indx[SI_SAVI]] = savi;
        if (msavi_flag)
            vi_output->buf[vi_indx[SI_MSAVI]] = msavi;
    }

    if (ndmi_flag)
    {
        sprintf (ndmi_outfile, "%s%s-ndmi.hdf", dir_name, scene_base_name);
        if (create_output (ndmi_outfile) != SUCCESS)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        strcpy (out_sds_names[0], "NDMI");
        ndmi_output = open_output (ndmi_outfile, NUM_OUT_SDS, out_sds_names,
            sr_input->nlines, sr_input->nsamps);
        if (ndmi_output == NULL)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
        ndmi_output->buf[0] = ndmi;
    }

    if (nbr_flag)
    {
        sprintf (nbr_outfile, "%s%s-nbr.hdf", dir_name, scene_base_name);
        if (create_output (nbr_outfile) != SUCCESS)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        strcpy (out_sds_names[0], "NBR");
        nbr_output = open_output (nbr_outfile, NUM_OUT_SDS, out_sds_names,
            sr_input->nlines, sr_input->nsamps);
        if (nbr_output == NULL)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
        nbr_output->buf[0] = nbr;
    }

    if (nbr2_flag)
    {
        sprintf (nbr2_outfile, "%s%s-nbr2.hdf", dir_name, scene_base_name);
        if (create_output (nbr2_outfile) != SUCCESS)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }

        strcpy (out_sds_names[0], "NBR2");
        nbr2_output = open_output (nbr2_outfile, NUM_OUT_SDS, out_sds_names,
            sr_input->nlines, sr_input->nsamps);
        if (nbr2_output == NULL)
        {   /* error message already printed */
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
        nbr2_output->buf[0] = nbr2;
    }

    /* Print the processing status if verbose */
    if (verbose)
    {
        printf ("  Processing %d lines at a time\n", PROC_NLINES);
        printf ("  Spectral indices -- %% complete: 0%%\r");
    }

    /* Loop through the lines and samples in the surface reflectance product
       computing the desired indices */
    nlines_proc = PROC_NLINES;
    k = 0;
    for (line = 0; line < sr_input->nlines; line += PROC_NLINES)
    {
        /* Do we have nlines_proc left to process? */
        if (line + nlines_proc >= sr_input->nlines)
            nlines_proc = sr_input->nlines - line;

        /* Update processing status? */
        if (verbose && (100 * line / sr_input->nlines > k))
        {
            k = 100 * line / sr_input->nlines;
            if (k % 10 == 0)
            {
                printf ("  Spectral indices -- %% complete: %d%%\r", k);
                fflush (stdout);
            }
        }

        /* Read the current lines from the surface reflectance file for each
           of the surface reflectance bands */
        for (band = 0; band < sr_input->nrefl_band; band++)
        {
            if (get_input_refl_lines (sr_input, band, line, nlines_proc) !=
                SUCCESS)
            {
                sprintf (errmsg, "Error reading %d lines from band %d of the "
                    "surface reflectance file starting at line %d",
                    nlines_proc, band, line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }  /* end for band */

        /* Compute the NDVI and write to output HDF file
           NDVI = (nir - red) / (nir + red) */
        if (ndvi_flag)
        {
            make_spectral_index (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[2] /*b3*/, sr_input->refl_fill,
                sr_input->refl_saturate_val, nlines_proc, sr_input->nsamps,
                ndvi);

            if (put_output_line (vi_output, vi_indx[SI_NDVI], line, nlines_proc)
                != SUCCESS)
            {
                sprintf (errmsg, "Writing output NDVI data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the EVI and write to output HDF file
           EVI = (nir - red) / (nir + C1 * red - C2 * blue + L) */
        if (evi_flag)
        {
            make_evi (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[2] /*b3*/, sr_input->refl_buf[0] /*b1*/,
                sr_input->refl_scale_fact, sr_input->refl_fill,
                sr_input->refl_saturate_val, nlines_proc, sr_input->nsamps,
                evi);

            if (put_output_line (vi_output, vi_indx[SI_EVI], line, nlines_proc)
                != SUCCESS)
            {
                sprintf (errmsg, "Writing output EVI data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the SAVI and write to output HDF file
           SAVI = ((nir - red) / (nir + red + L)) * (1 + L), where L is a
           constant 0.5. */
        if (savi_flag)
        {
            make_savi (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[2] /*b3*/, sr_input->refl_scale_fact,
                sr_input->refl_fill, sr_input->refl_saturate_val,
                nlines_proc, sr_input->nsamps, savi);

            if (put_output_line (vi_output, vi_indx[SI_SAVI], line, nlines_proc)
                != SUCCESS)
            {
                sprintf (errmsg, "Writing output SAVI data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the MSAVI (modified SAVI) and write to output HDF file
           MSAVI = (2 * nir + 1) - SQRT (SQR (2 * nir + 1) - (8 * (nir - red)))
                    * L
           where L is the soil brightness correction factor of 0.5*/
        if (msavi_flag)
        {
            make_modified_savi (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[2] /*b3*/, sr_input->refl_scale_fact,
                sr_input->refl_fill, sr_input->refl_saturate_val,
                nlines_proc, sr_input->nsamps, msavi);

            if (put_output_line (vi_output, vi_indx[SI_MSAVI], line,
                nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output MSAVI data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the NDMI and write to output HDF file
           NDMI = (nir - mir) / (nir + mir) */
        if (ndmi_flag)
        {
            make_spectral_index (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[4] /*b5*/, sr_input->refl_fill,
                sr_input->refl_saturate_val, nlines_proc, sr_input->nsamps,
                ndmi);

            if (put_output_line (ndmi_output, 0, line, nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NDMI data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the NBR and write to output HDF file
           NBR = (nir - swir) / (nir + swir) */
        if (nbr_flag)
        {
            make_spectral_index (sr_input->refl_buf[3] /*b4*/,
                sr_input->refl_buf[5] /*b7*/, sr_input->refl_fill,
                sr_input->refl_saturate_val, nlines_proc, sr_input->nsamps,
                nbr);

            if (put_output_line (nbr_output, 0, line, nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NBR data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }

        /* Compute the NBR2 and write to output HDF file
           NBR2 = (mir - swir) / (mir + swir) */
        if (nbr2_flag)
        {
            make_spectral_index (sr_input->refl_buf[4] /*b5*/,
                sr_input->refl_buf[5] /*b7*/, sr_input->refl_fill,
                sr_input->refl_saturate_val, nlines_proc, sr_input->nsamps,
                nbr2);

            if (put_output_line (nbr2_output, 0, line, nlines_proc) != SUCCESS)
            {
                sprintf (errmsg, "Writing output NBR2 data to HDF for line %d",
                    line);
                error_handler (true, FUNC_NAME, errmsg);
                close_input (sr_input);
                free_input (sr_input);
                exit (ERROR);
            }
        }
    }  /* end for line */

    /* Print the processing status if verbose */
    if (verbose)
        printf ("  Spectral indices -- %% complete: 100%%\n");

    /* Write the output metadata for each HDF file */
    if (num_vi > 0)
    {
        if (ndvi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_NDVI]],
                "normalized difference vegetation index");
        if (evi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_EVI]],
                "enhanced vegetation index");
        if (savi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_SAVI]],
                "soil adjusted vegetation index");
        if (msavi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_MSAVI]],
                "modified soil adjusted vegetation index");

        strcpy (short_name, "VI");
        if (put_metadata (vi_output, num_vi, short_name, out_vi_sds_names,
            &sr_input->meta) != SUCCESS)
        {
            sprintf (errmsg, "Error writing metadata to the output VI HDF "
                "file");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    if (ndmi_flag)
    {
        strcpy (short_name, "NDMI");
        strcpy (out_sds_names[0], "normalized difference moisture index");
        if (put_metadata (ndmi_output, NUM_OUT_SDS, short_name, out_sds_names,
            &sr_input->meta) != SUCCESS)
        {
            sprintf (errmsg, "Error writing metadata to the output NDMI HDF "
                "file");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    if (nbr_flag)
    {
        strcpy (short_name, "NBR");
        strcpy (out_sds_names[0], "normalized burn ratio");
        if (put_metadata (nbr_output, NUM_OUT_SDS, short_name, out_sds_names,
            &sr_input->meta) != SUCCESS)
        {
            sprintf (errmsg, "Error writing metadata to the output NBR HDF "
                "file");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    if (nbr2_flag)
    {
        strcpy (short_name, "NBR2");
        strcpy (out_sds_names[0], "normalized burn ratio 2");
        if (put_metadata (nbr2_output, NUM_OUT_SDS, short_name, out_sds_names,
            &sr_input->meta) != SUCCESS)
        {
            sprintf (errmsg, "Error writing metadata to the output NBR2 HDF "
                "file");
            error_handler (true, FUNC_NAME, errmsg);
            close_input (sr_input);
            free_input (sr_input);
            exit (ERROR);
        }
    }

    /* Close the output spectral indices products */
    if (num_vi > 0)
    {
        close_output (vi_output);
        free_output (vi_output);
    }
    if (ndmi_flag)
    {
        close_output (ndmi_output);
        free_output (ndmi_output);
    }
    if (nbr_flag)
    {
        close_output (nbr_output);
        free_output (nbr_output);
    }
    if (nbr2_flag)
    {
        close_output (nbr2_output);
        free_output (nbr2_output);
    }

    /* Write the spatial information, after the file has been closed, along
       with the associated ENVI header file */
    for (band = 0; band < MAX_OUT_SDS; band++)
        out_vi_sds_types[band] = DFNT_INT16;
    for (band = 0; band < NUM_OUT_SDS; band++)
        out_sds_types[band] = DFNT_INT16;

    if (num_vi > 0)
    {
        if (ndvi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_NDVI]], "NDVI");
        if (evi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_EVI]], "EVI");
        if (savi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_SAVI]], "SAVI");
        if (msavi_flag)
            strcpy (out_vi_sds_names[vi_indx[SI_MSAVI]], "MSAVI");

        if (put_space_def_hdf (&space_def, vi_outfile, num_vi,
            out_vi_sds_names, out_vi_sds_types, hdf_grid_name) != SUCCESS)
        {
            sprintf (errmsg, "Error writing spatial metadata to the output "
                "VI HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        sprintf (ehdr_file, "%s.hdr", vi_outfile);
        if (write_envi_hdr (ehdr_file, sr_input, &space_def) == ERROR)
        {
            sprintf (errmsg, "Error writing the ENVI header for the VI HDF "
                "file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }

    if (ndmi_flag)
    {
        strcpy (out_sds_names[0], "NDMI");
        if (put_space_def_hdf (&space_def, ndmi_outfile, NUM_OUT_SDS,
            out_sds_names, out_sds_types, hdf_grid_name) != SUCCESS)
        {
            sprintf (errmsg, "Error writing spatial metadata to the output "
                "NDMI HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        sprintf (ehdr_file, "%s.hdr", ndmi_outfile);
        if (write_envi_hdr (ehdr_file, sr_input, &space_def) == ERROR)
        {
            sprintf (errmsg, "Error writing the ENVI header for the "
                "NDMI HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }

    if (nbr_flag)
    {
        strcpy (out_sds_names[0], "NBR");
        if (put_space_def_hdf (&space_def, nbr_outfile, NUM_OUT_SDS,
            out_sds_names, out_sds_types, hdf_grid_name) != SUCCESS)
        {
            sprintf (errmsg, "Error writing spatial metadata to the output "
                "NBR HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        sprintf (ehdr_file, "%s.hdr", nbr_outfile);
        if (write_envi_hdr (ehdr_file, sr_input, &space_def) == ERROR)
        {
            sprintf (errmsg, "Error writing the ENVI header for the "
                "NBR HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }

    if (nbr2_flag)
    {
        strcpy (out_sds_names[0], "NBR2");
        if (put_space_def_hdf (&space_def, nbr2_outfile, NUM_OUT_SDS,
            out_sds_names, out_sds_types, hdf_grid_name) != SUCCESS)
        {
            sprintf (errmsg, "Error writing spatial metadata to the output "
                "NBR2 HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }

        sprintf (ehdr_file, "%s.hdr", nbr2_outfile);
        if (write_envi_hdr (ehdr_file, sr_input, &space_def) == ERROR)
        {
            sprintf (errmsg, "Error writing the ENVI header for the "
                "NBR2 HDF file");
            error_handler (true, FUNC_NAME, errmsg);
            exit (ERROR);
        }
    }

    /* Close the reflectance product */
    close_input (sr_input);
    free_input (sr_input);

    /* Free the filename pointers */
    if (sr_infile != NULL)
        free (sr_infile);

    /* Free the mask pointers */
    if (ndvi != NULL)
        free (ndvi);
    if (ndmi != NULL)
        free (ndmi);
    if (nbr != NULL)
        free (nbr);
    if (nbr2 != NULL)
        free (nbr2);
    if (savi != NULL)
        free (savi);
    if (msavi != NULL)
        free (msavi);
    if (evi != NULL)
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

NOTES:
******************************************************************************/
void usage ()
{
    printf ("spectral_indices produces the desired spectral index products "
            "for the input surface reflectance scene. The options include "
            "NDVI, EVI, SAVI, MSAVI, NDMI (also known as NDWI or NDII), NBR, "
            "and NBR2. The user may specify one, some, or all of the supported "
            "indices for output.\n");
    printf ("The vegetation indices (if specified) will be written to one "
            "combined output file, where as the other indices will be written "
            "to single band output files.\n\n");
    printf ("usage: spectral_indices "
            "--sr=input_surface_reflectance_Landsat_filename "
            "[--ndvi] [--evi] [--savi] [--msavi] [--ndmi] [--nbr] [--nbr2] "
            "[--verbose]\n");

    printf ("\nwhere the following parameters are required:\n");
    printf ("    -sr: name of the input Landsat surface reflectance file to "
            "be processed (HDF)\n");

    printf ("\nwhere the following parameters are optional:\n");
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
            "--sr=lndsr.LT50400331995173AAA02.hdf "
            "--ndvi --ndmi --nbr --evi "
            "--verbose\n");
}


/******************************************************************************
MODULE:  find_scenename

PURPOSE:  Determines the scene name of the input surface reflectance scene

RETURN VALUE:
Type = None

HISTORY:
Date        Programmer       Reason
--------    ---------------  -------------------------------------
4/6/2013    Gail Schmidt     Original Development

NOTES:
******************************************************************************/
void find_scenename
(
    char *sr_filename,   /* I: Input surface reflectance filename */
    char *dir_name,      /* O: Output directory name */
    char *scene_name     /* O: Output scene name */
)
{
    char filename[STR_SIZE];  /* copy of the input filename */
    char basename[STR_SIZE];  /* base filename */
    char *tokenptr = NULL;    /* pointer to the desired token */

    /* Copy the input filename */
    strcpy (filename, sr_filename);

    /* Find the end of the directory and grab the directory name */
    tokenptr = strrchr (filename, '/');
    if (tokenptr != NULL)
    {
        tokenptr++;

        /* save the base filename */
        strcpy (basename, tokenptr);

        /* strip the filename after the closing '/' to obtain the directory
           name */
        *tokenptr = '\0';
        strcpy (dir_name, filename);
    }
    else
    {
        /* no directory path exists in the filename */
        strcpy (dir_name, "./");

        /* save the base name */
        strcpy (basename, filename);
    }

    /* Strip the extension from the basename */
    tokenptr = strrchr (basename, '.');
    if (tokenptr != NULL)
        *tokenptr = '\0';

    strcpy (scene_name, basename);
}
