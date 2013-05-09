#include <getopt.h>
#include "si.h"

/******************************************************************************
MODULE:  get_args

PURPOSE:  Gets the command-line arguments and validates that the required
arguments were specified.

RETURN VALUE:
Type = int
Value           Description
-----           -----------
ERROR           Error getting the command-line arguments or a command-line
                argument and associated value were not specified
SUCCESS         No errors encountered

PROJECT:  Land Satellites Data System Science Research and Development (LSRD)
at the USGS EROS

HISTORY:
Date          Programmer       Reason
----------    ---------------  -------------------------------------
4/6/2013      Gail Schmidt     Original Development
5/9/2013      Gail Schmidt     Modified to support MSAVI

NOTES:
  1. Memory is allocated for the input file.  This should be character a
     pointer set to NULL on input.  The caller is responsible for freeing the
     allocated memory upon successful return.
******************************************************************************/
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
    bool *msavi,          /* O: flag to process MSAVI */
    bool *evi,            /* O: flag to process EVI */
    bool *verbose         /* O: verbose flag */
)
{
    int c;                           /* current argument index */
    int option_index;                /* index for the command-line option */
    static int verbose_flag=0;       /* verbose flag */
    static int ndvi_flag=0;          /* process NDVI flag */
    static int ndmi_flag=0;          /* process NDMI flag */
    static int nbr_flag=0;           /* process NBR flag */
    static int nbr2_flag=0;          /* process NBR2 flag */
    static int savi_flag=0;          /* process SAVI flag */
    static int msavi_flag=0;         /* process MSAVI flag */
    static int evi_flag=0;           /* process EVI flag */
    char errmsg[STR_SIZE];           /* error message */
    char FUNC_NAME[] = "get_args";   /* function name */
    static struct option long_options[] =
    {
        {"verbose", no_argument, &verbose_flag, 1},
        {"ndvi", no_argument, &ndvi_flag, 1},
        {"ndmi", no_argument, &ndmi_flag, 1},
        {"nbr", no_argument, &nbr_flag, 1},
        {"nbr2", no_argument, &nbr2_flag, 1},
        {"savi", no_argument, &savi_flag, 1},
        {"msavi", no_argument, &msavi_flag, 1},
        {"evi", no_argument, &evi_flag, 1},
        {"sr", required_argument, 0, 'i'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    /* Initialize the flags to false */
    *verbose = false;
    *ndvi = false;
    *ndmi = false;
    *nbr = false;
    *nbr2 = false;
    *savi = false;
    *msavi = false;
    *evi = false;

    /* Loop through all the cmd-line options */
    opterr = 0;   /* turn off getopt_long error msgs as we'll print our own */
    while (1)
    {
        /* optstring in call to getopt_long is empty since we will only
           support the long options */
        c = getopt_long (argc, argv, "", long_options, &option_index);
        if (c == -1)
        {   /* Out of cmd-line options */
            break;
        }

        switch (c)
        {
            case 0:
                /* If this option set a flag, do nothing else now. */
                if (long_options[option_index].flag != 0)
                    break;
     
            case 'h':  /* help */
                usage ();
                return (ERROR);
                break;

            case 'i':  /* input file */
                *sr_infile = strdup (optarg);
                break;
     
            case '?':
            default:
                sprintf (errmsg, "Unknown option %s", argv[optind-1]);
                error_handler (true, FUNC_NAME, errmsg);
                usage ();
                return (ERROR);
                break;
        }
    }

    /* Make sure the surface reflectance infile was specified */
    if (*sr_infile == NULL)
    {
        sprintf (errmsg, "Input file is a required argument");
        error_handler (true, FUNC_NAME, errmsg);
        usage ();
        return (ERROR);
    }

    /* Check the spectral index flags */
    if (ndvi_flag)
        *ndvi = true;
    if (ndmi_flag)
        *ndmi = true;
    if (nbr_flag)
        *nbr = true;
    if (nbr2_flag)
        *nbr2 = true;
    if (savi_flag)
        *savi = true;
    if (msavi_flag)
        *msavi = true;
    if (evi_flag)
        *evi = true;

    /* Check the verbose flag */
    if (verbose_flag)
        *verbose = true;

    return (SUCCESS);
}
