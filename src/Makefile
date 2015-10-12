#------------------------------------------------------------------------------
# Makefile
#
# For building spectral indices
#------------------------------------------------------------------------------
.PHONY: all install clean

# Inherit from upper-level make.config
TOP = ..
include $(TOP)/make.config

bin_install_path = $(espa_project_dir)/bin

# Set up compile options
CC = gcc
RM = rm -f
EXTRA = $(build_type) -Wall -g -O2

# Define the include files
INC = common.h input.h output.h si.h
INCDIR  = -I. -I$(XML2INC) -I$(ESPAINC)
NCFLAGS = $(EXTRA) $(INCDIR)

# Define the source code and object files
SRC = \
      get_args.c            \
      input.c               \
      make_spectral_index.c \
      output.c              \
      spectral_indices.c
OBJ = $(SRC:.c=.o)

# Define the object libraries
LIB   = -L$(ESPALIB) -l_espa_raw_binary -l_espa_common -L$(XML2LIB) -lxml2 \
        -L${ZLIBLIB} -lz -lm

# Define the executable
EXE = spectral_indices

# Target for the executable
all: $(EXE)

$(EXE): $(OBJ) $(INC)
	$(CC) $(EXTRA) -o $(EXE) $(OBJ) $(LIB)

install: $(EXE)
	install -d $(link_path)
	install -d $(bin_install_path)
	install -m 755 $(EXE) $(bin_install_path)
	ln -sf $(bin_install_path)/$(EXE) $(link_path)/$(EXE)
#	ln -sf ../$(project_name)/bin/$(EXE) $(link_path)/$(EXE)

clean:
	$(RM) *.o $(EXE)

$(OBJ): $(INC)

.c.o:
	$(CC) $(NCFLAGS) -c $<

