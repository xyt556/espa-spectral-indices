#------------------------------------------------------------------------------
# Makefile
#
# Simple makefile for building and installing spectral indicies
# applications.
#------------------------------------------------------------------------------

all:
	echo "make all in scripts"; \
        (cd scripts; $(MAKE) all -f Makefile);

install:
	echo "make install in scripts"; \
        (cd scripts; $(MAKE) install -f Makefile);

clean:
	echo "make clean in scripts"; \
        (cd scripts; $(MAKE) clean -f Makefile);
