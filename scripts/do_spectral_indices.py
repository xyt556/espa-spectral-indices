#! /usr/bin/env python
import sys
import os
import re
import commands
import datetime
from optparse import OptionParser

ERROR = 1
SUCCESS = 0

############################################################################
# Description: logIt logs the information to the logfile (if valid) or to
# stdout if the logfile is None.
#
# Inputs:
#   msg - message to be printed/logged
#   log_handler - log file handler; if None then print to stdout
#
# Returns: nothing
#
# Notes:
############################################################################
def logIt (msg, log_handler):
    if log_handler == None:
        print msg
    else:
        log_handler.write (msg + '\n')


#############################################################################
# Created on March 27, 2013 by Gail Schmidt, USGS/EROS
# Created Python script to run the spectral indices algorithms based on the
# desired indices specified by the user.
#
# History:
#   Updated on May 9, 2013 by Gail Schmidt, USGS/EROS
#   Added support for modified SAVI (MSAVI)
#   Updated on February 13, 2014 by Gail Schmidt, USGS/EROS
#   Added support for ESPA internal file format
#   Added support for TOA processing
#
#   Updated on May 9, 2013 by Gail Schmidt, USGS/EROS
#   Added a check to make sure that at least one of the spectral index products
#     was specified for processing.  Otherwise don't process.
#
# Usage: do_spectral_indices.py --help prints the help message
############################################################################
class SpectralIndices():

    def __init__(self):
        pass


    ########################################################################
    # Description: runSi will use the parameters passed for the input/output
    # files, logfile, and usebin.  If input/output files are None (i.e. not
    # specified) then the command-line parameters will be parsed for this
    # information.  The spectral indices application is then executed to
    # generate the desired indices on the specified input file.  If a log
    # file was specified, then the output from this application will be
    # logged to that file.
    #
    # Inputs:
    #   xml_infile - name of the input XML file
    #   logfile - name of the logfile for logging information; if None then
    #       the output will be written to stdout
    #   usebin - this specifies if the spectral indices exe resides in the
    #       $BIN directory; if None then the spectral indices exe is
    #       expected to be in the PATH
    #
    # Returns:
    #     ERROR - error running the DEM and SCA applications
    #     SUCCESS - successful processing
    #
    # Notes:
    #   1. The script obtains the path of the XML file and changes
    #      directory to that path for running the spectral indices application.
    #      If the XML file directory is not writable, then this script
    #      exits with an error.
    #   2. If the XML file is not specified and the information is
    #      going to be grabbed from the command line, then it's assumed all
    #      the parameters will be pulled from the command line.
    #######################################################################
    def runSi (self, xml_infile=None, toa=False, ndvi=False, ndmi=False, \
        nbr=False, nbr2=False, savi=False, msavi=False, evi=False, \
        logfile=None, \
        usebin=None):
        # if no parameters were passed then get the info from the
        # command line
        if xml_infile == None:
            # get the command line argument for the XML file
            parser = OptionParser()
            parser.add_option ("-i", "--xml_infile", type="string",
                dest="xml_infile",
                help="name of XML file", metavar="FILE")
            parser.add_option ("--toa", dest="toa", default=False,
                action="store_true",
                help="process TOA bands instead of surface reflectance bands")
            parser.add_option ("--ndvi", dest="ndvi", default=False,
                action="store_true",
                help="process NDVI (normalized difference vegetation index")
            parser.add_option ("--ndmi", dest="ndmi", default=False,
                action="store_true",
                help="process NDMI (normalized difference moisture index")
            parser.add_option ("--nbr", dest="nbr", default=False,
                action="store_true",
                help="process NBR (normalized burn ratio")
            parser.add_option ("--nbr2", dest="nbr2", default=False,
                action="store_true",
                help="process NBR2 (normalized burn ratio2")
            parser.add_option ("--savi", dest="savi", default=False,
                action="store_true",
                help="process SAVI (soil adjusted vegetation index")
            parser.add_option ("--msavi", dest="msavi", default=False,
                action="store_true",
                help="process modified SAVI (soil adjusted vegetation index")
            parser.add_option ("--evi", dest="evi", default=False,
                action="store_true",
                help="process EVI (enhanced vegetation index")
            parser.add_option ("--usebin", dest="usebin", default=False,
                action="store_true",
                help="use BIN environment variable as the location of spectral indices application")
            parser.add_option ("-l", "--logfile", type="string", dest="logfile",
                help="name of optional log file", metavar="FILE")
            (options, args) = parser.parse_args()
    
            # validate the command-line options
            usebin = options.usebin          # should $BIN directory be used
            logfile = options.logfile        # name of the log file

            # XML input file
            xml_infile = options.xml_infile
            if xml_infile == None:
                parser.error ("missing input XML file command-line argument");
                return ERROR

            # spectral indices options
            toa = options.toa
            ndvi = options.ndvi
            ndmi = options.ndmi
            nbr = options.nbr
            nbr2 = options.nbr2
            savi = options.savi
            msavi = options.msavi
            evi = options.evi
        
        # open the log file if it exists; use line buffering for the output
        log_handler = None
        if logfile != None:
            log_handler = open (logfile, 'w', buffering=1)
        msg = 'Spectral indices processing of Landsat file: %s' % xml_infile
        logIt (msg, log_handler)
        
        # should we expect the spectral indices application to be in the PATH
        # or in the BIN directory?
        if usebin:
            # get the BIN dir environment variable
            bin_dir = os.environ.get('BIN')
            bin_dir = bin_dir + '/'
            msg = 'BIN environment variable: %s' % bin_dir
            logIt (msg, log_handler)
        else:
            # don't use a path to the spectral indices application
            bin_dir = ""
            msg = 'Spectral indices executable expected to be in the PATH'
            logIt (msg, log_handler)
        
        # make sure the XML file exists
        if not os.path.isfile(xml_infile):
            msg = "Error: XML file does not exist or is not accessible: " + xml_infile
            logIt (msg, log_handler)
            return ERROR

        # use the base XML filename and not the full path.
        base_xmlfile = os.path.basename (xml_infile)
        msg = 'Processing XML file: %s' % base_xmlfile
        logIt (msg, log_handler)
        
        # get the path of the XML file and change directory to that location
        # for running this script.  save the current working directory for
        # return to upon error or when processing is complete.  Note: use
        # abspath to handle the case when the filepath is just the filename
        # and doesn't really include a file path (i.e. the current working
        # directory).
        mydir = os.getcwd()
        xmldir = os.path.dirname (os.path.abspath (xml_infile))
        if not os.access(xmldir, os.W_OK):
            msg = 'Path of XML file is not writable: %s.  Script needs write access to the XML directory.' % xmldir
            logIt (msg, log_handler)
            return ERROR
        msg = 'Changing directories for spectral indices processing: %s' % xmldir
        logIt (msg, log_handler)
        os.chdir (xmldir)

        # make sure there is something to do
        if not ndvi and not ndmi and not nbr and not nbr2 and not savi and \
            not msavi and not evi:
            msg = "Error: no spectral index product specified to be processed"
            logIt (msg, log_handler)
            return ERROR

        # run spectral indices algorithm, checking the return status.  exit
        # if any errors occur.
        toa_opt_str = ""
        ndvi_opt_str = ""
        ndmi_opt_str = ""
        nbr_opt_str = ""
        nbr2_opt_str = ""
        savi_opt_str = ""
        msavi_opt_str = ""
        evi_opt_str = ""

        if toa:
            toa_opt_str = "--toa "
        if ndvi:
            ndvi_opt_str = "--ndvi "
        if ndmi:
            ndmi_opt_str = "--ndmi "
        if nbr:
            nbr_opt_str = "--nbr "
        if nbr2:
            nbr2_opt_str = "--nbr2 "
        if savi:
            savi_opt_str = "--savi "
        if msavi:
            msavi_opt_str = "--msavi "
        if evi:
            evi_opt_str = "--evi "

        cmdstr = "%sspectral_indices --xml=%s %s%s%s%s%s%s%s%s--verbose" % \
            (bin_dir, xml_infile, toa_opt_str, ndvi_opt_str, ndmi_opt_str, \
             nbr_opt_str, nbr2_opt_str, savi_opt_str, msavi_opt_str, \
             evi_opt_str)
#        print 'DEBUG: spectral_indices command: %s' % cmdstr
        (status, output) = commands.getstatusoutput (cmdstr)
        logIt (output, log_handler)
        exit_code = status >> 8
        if exit_code != 0:
            msg = 'Error running spectral_indices.  Processing will terminate.'
            logIt (msg, log_handler)
            os.chdir (mydir)
            return ERROR
        
        # successful completion.  return to the original directory.
        os.chdir (mydir)
        msg = 'Completion of spectral indices.'
        logIt (msg, log_handler)
        if logfile != None:
            log_handler.close()
        return SUCCESS

######end of Sca class######

if __name__ == "__main__":
    sys.exit (SpectralIndices().runSi())
