#------------------------------------------------------------------------------
# Makefile for sample HDF code
#------------------------------------------------------------------------------

# Set up compile options
CC = gcc
RM = rm -f
EXTRA = -Wall -g

# Define the include files
INC = common.h input.h output.h si.h
INCDIR  = -I. -I$(XML2INC) -I$(ESPAINC)
NCFLAGS = $(EXTRA) $(INCDIR)

# Define the source code and object files
SRC = get_args.c          \
      input.c             \
      make_spectral_index.c \
      output.c            \
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
	install -d $(PREFIX)/bin
	install -m 755 $(EXE) $(PREFIX)/bin

clean:
	$(RM) *.o $(EXE)

$(OBJ): $(INC)

.c.o:
	$(CC) $(NCFLAGS) -c $<


