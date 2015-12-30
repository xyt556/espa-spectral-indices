#-----------------------------------------------------------------------------
# Makefile
#
# Project Name: spectral indicies
# Makefile that will invoke subsequent Makefiles in subdirectories.
#-----------------------------------------------------------------------------
.PHONY: check-environment all install clean

include make.config

#-----------------------------------------------------------------------------
all:
	echo "make all in scripts"; \
        (cd scripts; $(MAKE) all);
	echo "make all in src"; \
        (cd src; $(MAKE) all);

#-----------------------------------------------------------------------------
install: check-environment
	echo "make install in scripts"; \
        (cd scripts; $(MAKE) install);
	echo "make install in src"; \
        (cd src; $(MAKE) install);

#-----------------------------------------------------------------------------
clean:
	echo "make clean in scripts"; \
        (cd scripts; $(MAKE) clean);
	echo "make clean in src"; \
        (cd src; $(MAKE) clean);

#-----------------------------------------------------------------------------
check-environment:
ifndef PREFIX
    $(error Environment variable PREFIX is not defined)
endif

