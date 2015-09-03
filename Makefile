#------------------------------------------------------------------------------
# Makefile
#
# Project Name: spectral indicies
# Makefile that will invoke subsequent Makefiles in subdirectories.
# Assumes the following make files exist:
#	scripts/Makefile
#	src/Makefile
#------------------------------------------------------------------------------
.PHONY: check-environment all install clean

include make.config

MAKEFILE_NAME = Makefile

all:
	echo "make all in scripts"; \
        (cd scripts; $(MAKE) all -f $(MAKEFILE_NAME));
	echo "make all in src"; \
        (cd src; $(MAKE) all -f $(MAKEFILE_NAME));

install: check-environment
	echo "make install in scripts"; \
        (cd scripts; $(MAKE) install -f $(MAKEFILE_NAME));
	echo "make install in src"; \
        (cd src; $(MAKE) install -f $(MAKEFILE_NAME));

clean:
	echo "make clean in scripts"; \
        (cd scripts; $(MAKE) clean -f $(MAKEFILE_NAME));
	echo "make clean in src"; \
        (cd src; $(MAKE) clean -f $(MAKEFILE_NAME));

check-environment:
ifndef PREFIX
    $(error Environment variable PREFIX is not defined)
endif

