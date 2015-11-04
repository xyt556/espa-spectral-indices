#-----------------------------------------------------------------------------
# Makefile
#
# For building spectral indices
#-----------------------------------------------------------------------------
.PHONY: all install clean

# Inherit from upper-level make.config
TOP = ..
include $(TOP)/make.config

#-----------------------------------------------------------------------------
# Set up compile options
CC = gcc
RM = rm
EXTRA_OPTIONS = $(static_option) $(threading_options) $(profiling_options)
EXTRA   = -Wall -O2 $(EXTRA_OPTIONS)

# Define the include files
INC = common.h input.h output.h si.h

# Define the source code and object files
SRC = \
      get_args.c            \
      input.c               \
      make_spectral_index.c \
      output.c              \
      spectral_indices.c
OBJ = $(SRC:.c=.o)

# Define include paths
INCDIR  = -I. -I$(ESPAINC) -I$(XML2INC)
NCFLAGS = $(EXTRA) $(INCDIR)

# Define the object libraries and paths
EXLIB = -L$(ESPALIB) -l_espa_raw_binary -l_espa_common \
        -L$(XML2LIB) -lxml2 \
        -L$(LZMALIB) -llzma \
        -L${ZLIBLIB} -lz
MATHLIB = -lm
LOADLIB = $(EXLIB) $(MATHLIB)

# Define C executable
EXE = spectral_indices

#-----------------------------------------------------------------------------
all: $(EXE)

$(EXE): $(OBJ) $(INC)
	$(CC) $(EXTRA) -o $(EXE) $(OBJ) $(LOADLIB)

#-----------------------------------------------------------------------------
install: $(EXE)
	install -d $(link_path)
	install -d $(bin_install_path)
	install -m 755 $(EXE) $(bin_install_path)
	ln -sf $(link_source_path)/$(EXE) $(link_path)/$(EXE)

#-----------------------------------------------------------------------------
clean:
	$(RM) -f *.o $(EXE)

#-----------------------------------------------------------------------------
$(OBJ): $(INC)

.c.o:
	$(CC) $(NCFLAGS) -c $<

