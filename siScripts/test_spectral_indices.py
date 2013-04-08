#! /usr/bin/env python

import sys
from do_spectral_indices import SpectralIndices

ERROR = 1
SUCCESS = 0

if __name__ == "__main__":
    status = SpectralIndices().runSi(sr_infile="/media/sf_Software_SandBox/Landsat/TM/lndsr.LT50400331995173AAA02.hdf", ndvi=True, evi=True, usebin=True)
    if status != SUCCESS:
        print "Error running spectral indices"
        sys.exit(ERROR)

    print "Success running spectral indices"
    sys.exit(SUCCESS)

