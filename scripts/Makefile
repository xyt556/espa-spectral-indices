#-----------------------------------------------------------------------------
# Makefile
#
# Simple makefile for installing the scripts.
#-----------------------------------------------------------------------------
.PHONY: all install clean

# Inherit from upper-level make.config
TOP = ..
include $(TOP)/make.config

#-----------------------------------------------------------------------------
all:

#-----------------------------------------------------------------------------
install:
	install -d $(link_path)
	install -d $(bin_install_path)
	install -m 755 spectral_indices.py $(bin_install_path)
	ln -sf $(link_source_path)/spectral_indices.py $(link_path)/spectral_indices.py

#-----------------------------------------------------------------------------
clean:

