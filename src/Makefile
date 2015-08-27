#------------------------------------------------------------------------------
# Makefile
#
# For building spectral indices
#------------------------------------------------------------------------------
.PHONY: check-environment

BIN_INSTALL_PATH = $(PREFIX)/$(ESPA_PROJECT)/bin

# Set up compile options
CC = gcc
RM = rm -f
EXTRA = -Wall -g -O2

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

install: check-environment $(EXE)
	install -d $(BIN_INSTALL_PATH)
	install -m 755 $(EXE) $(BIN_INSTALL_PATH)

clean:
	$(RM) *.o $(EXE)

$(OBJ): $(INC)

.c.o:
	$(CC) $(NCFLAGS) -c $<

check-environment:
ifndef PREFIX
    $(error PREFIX is undefined)
endif
ifndef ESPA_PROJECT
    $(error ESPA_PROJECT is undefined)
endif

