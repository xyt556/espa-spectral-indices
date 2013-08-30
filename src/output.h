#ifndef OUTPUT_H
#define OUTPUT_H

#include "mystring.h"
#include "input.h"
#include "space.h"

/* Define the order of vegetation products to be written to the vegetation
   index file */
typedef enum {SI_NDVI=0, SI_EVI, SI_SAVI, SI_MSAVI, NUM_VI} Myvi_list_t;

/* Define the number of SDS that will be output to the HDF-EOS file.  The
   actual SDS names are defined in spectral_indices.c.  Maximum is currently
   the count in the vegetation index products. */
#define MAX_OUT_SDS NUM_VI
#define NUM_OUT_SDS 1

/* Define some of the constants to use in the output data products */
#define FILL_VALUE -9999
#define SATURATE_VALUE 20000
#define FLOAT_TO_INT 10000.0
#define SCALE_FACTOR 0.0001

/* Structure for the 'output' data type */
typedef struct {
  char *file_name;      /* Output file name */
  bool open;            /* Flag to indicate whether output file is open 
                           for access; 'true' = open, 'false' = not open */
  int nband;            /* Number of output image bands */
  Img_coord_int_t size; /* Output image size */
  int32 sds_file_id;    /* SDS file id */
  Myhdf_sds_t sds[MAX_OUT_SDS]; /* SDS data structures for image data */
  int16 *buf[MAX_OUT_SDS]; /* Output data buffer */
} Output_t;

/* Prototypes */
int create_output
(
    char *file_name    /* I: name of HDF file to be created */
);

Output_t *open_output
(
    char *file_name,                /* I: name of output HDF file */
    int nband,                      /* I: number of image bands (SDSs) to be
                                          created */
    char sds_names[][STR_SIZE],     /* I: array of SDS names for each band */
    int nlines,                     /* I: number of lines in image */
    int nsamps                      /* I: number of samples in image */
);

int close_output
(
    Output_t *this    /* I/O: Output data structure to close */
);

int free_output
(
    Output_t *this    /* I/O: Output data structure to free */
);

int put_output_line
(
    Output_t *this,    /* I: Output data structure; buf contains the line to
                             be written */
    int iband,         /* I: current band to be written (0-based) */
    int iline,         /* I: current line to be written (0-based) */
    int nlines         /* I: number of lines to be written */
);

int put_metadata
(
    Output_t *this,           /* I: Output data structure */
    int nband,                /* I: number of bands to write */
    char product_id[STR_SIZE], /* I: short band name to write */
    char band_names[MAX_OUT_SDS][STR_SIZE],  /* I: band names to write */
    Input_meta_t *meta        /* I: metadata to be written */
);

void generate_short_name
(
    char *sat,           /* I: satellite type */
    char *inst,          /* I: instrument type */
    char *product_id,    /* I: ID for the current band */
    char *short_name     /* O: short name produced */
);

#endif
