#! /usr/bin/env python
'''
-----     -----     -----     -----     -----     -----
@author: ngenetzky@usgs.gov
Classes:
    Cmd
    ScriptHelper
    SI : Spectral Indices
    SWE : Surface Water Extent
Required Executable:
LICENSE: NASA Open Source Agreement 1.3

DSWE    :    Spectral Indices
    FILE: do_dynamic_surface_water_extent.py
    PURPOSE: Master script for running scene-based surface water algorithm.
    USAGE: See 'do_dynamic_surface_water_extent.py --help'
    DEPENDENCIES: dswe
SI    :    Surface Water Extent
    FILE: do_dynamic_surface_water_extent.py
    PURPOSE: Master script for running scene-based surface water algorithm.
    USAGE: See 'do_dynamic_surface_water_extent.py --help
    DEPENDENCIES: spectral_indices
-----     -----     -----     -----     -----     -----
'''

import sys
import os
import argparse
import logging
try:
    import commands
except:
    pass  # Py3.x import subprocess
try:
    import metadata_api
except:
    pass


class Cmd:
    """
    Cmd is a class that encompasses all of the functions
    associated with building and executing command line arguments.
    By using this class with each script it ensures consistency in
    the way that that command line is produced.
    Usage:
    # __init__(SCRIPTNAME, DIRECTORY)
    cmdScript = Cmd('my_script_name')
    # addParam(PARAMERTER_NAME,PARAMETER_VALUE)
    cmdScript.addParam('xml', my_xml.xml)
    # Will use commands.getstatusoutput to execute built cmd-line
    cmdScript.execute()
    """
    # Script Names
    def __init__(self, script_name, basedir=''):
        self.cmdline = [basedir+script_name]

    def addParam(self, name, arg1=''):
        self.cmdline.append(name)
        self.cmdline.append(arg1)

    def getCmdline(self):
        return ' '.join(self.cmdline)

    def execute(self):
        '''
        Description:
          Execute a command line and return the terminal output or raise an
          exception
        Returns:
            output - The stdout and/or stderr from the executed command.
        '''
        cmd = self.getCmdline()
        (status, output) = commands.getstatusoutput(cmd)

        if status < 0:
            message = "Application terminated by signal [%s]" % cmd
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception(message)

        if status != 0:
            message = "Application failed to execute [%s]" % cmd
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception(message)
        return output


class ScriptHelper:
    '''
    General functions and properties inherent to all scripts.
    Should never be directly instantiated, but instead should
    ...be a base class for other script classes.
    ---Methods---
    main(): The actions that every script must perform to execute.
    isLansat8(): Looks at the XML file to determine if the satellite is L8.
    _getLogger(): Obtain Logger object from 'logging' module
    SUCCESS(): Constant to define value of "Success". (Set to 1)
    FAILURE(): Constant to define value of "Failure". (Set to 0)
    getBINdir(): Returns the environment variable bin. Assumed to be a path
                to the BIN directory
    parseCommonArgs(): Allows common arguments to be added to the parser.
                    Any of the following can be specified:
                    xml, debug and verbose. default is None.
    checkCommonPreReq(): Checks conditions that must be true for any script.
                        Not required that each sub class uses them.
    get_execute_header(): Defines the String that will appear in the log
                        when execute() is called.
    parse_arguments(): SubClass should implement. Should obtain any command
                    line arguments. Should use argparse module.
    check_prereq(): SubClass should implement. Should check conditions that
                    must be for the script to execute.
    build_cmd_line(): SubClass should implement.
    '''
    # Possible future additions:
    # 1. Allow use of use BIN env. variable as the location of executable.
    # 2. Allow a log file to be specified.
    ARG_XML = (['var', 'xml_filename'],
               ['help', 'The XML metadata file to use'],
               ['short', 'f'],
               ['long', 'xml'])

    def __init__(self):
        self.logger = ScriptHelper._getLogger()
        self.args = None
        self.cmd = None
        # Should be defined by sub-class
        self.title = 'Title Not Defined'
        self.exe_filename = 'Program Name not defined'

    def main(self):
        script.parse_arguments()
        if(script.check_prereq()):
            script.build_cmd_line()
            script.execute()
            sys.exit(ScriptHelper.SUCCESS())
        else:
            sys.exit(ScriptHelper.FAILURE())

    @staticmethod
    def isLansat8(xml_filename):
        '''
        Reads XML file for satellite and instrument type and determines
        the configuration. Expects the following contents in the xml:
        "...
        <global_metadata>
            ...
            <satellite>LANDSAT_8</satellite>
            <instrument>OLI_TIRS</instrument>
            ...
        ..."
        '''
        xml = metadata_api.parse(xml_filename, silence=True)
        global_metadata = xml.get_global_metadata()
        satellite = global_metadata.get_satellite()
        # instrument = global_metadata.get_instrument()
        if (satellite == 'LANSAT_8'):
            return True
        else:
            return False

    @staticmethod
    def getConfigFromXml(xml_filename):
        return "Not Implemented"

    @staticmethod
    def _getLogger():
        # setup the default logger format and level. log to STDOUT.
        logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                    ' %(levelname)-8s'
                                    ' %(filename)s:%(lineno)d:'
                                    '%(funcName)s -- %(message)s'),
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO)
        # get the logger
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def SUCCESS():
        return 1

    @staticmethod
    def FAILURE():
        return 0

    @staticmethod
    def getBINdir():
        # get the BIN dir environment variable
        bin_dir = os.environ.get('BIN')
        bin_dir = bin_dir + '/'
        # msg = 'BIN environment variable: %s' % bin_dir
        # logIt (msg, log_handler)
        return bin_dir

    @staticmethod
    def parseCommonArgs(parser, xml=False, debug=False, verbose=False):
        if(xml):
            parser.add_argument('--xml', action='store',
                                dest='xml_filename', required=True,
                                help='The XML metadata file to use',
                                metavar='FILE')
        if(debug):
            parser.add_argument('--debug',
                                action='store_true', dest='debug',
                                required=False, default=False,
                                help="Keep any debugging data")
        if(verbose):
            parser.add_argument('--verbose',
                                action='store_true', dest='verbose',
                                required=False, default=False,
                                help=("Should intermediate messages         \
                                      be printed? (default value is False)"))
        return parser

    def checkCommonPreReq(self):
        # Verify that the XML filename provided is not an empty string
        if self.args.xml_filename == '':
            self.logger.fatal("No XML metadata filename provided.")
            self.logger.fatal("Error processing LST.     \
                               Processing will terminate.")
            sys.exit(self.FAILURE())

    def get_execute_header(self):
        return '''
        {0} is processing Landsat data associated with xml file ({1}). \
        Using the command line:{2}
        ''' .format(self.title,
                    self.args.xml_filename,
                    self.cmd.getCmdline()
                    )

    def execute(self):
        header = self.get_execute_header()
        self.logger.info(header)
        print(header)
        output = ''
        try:
            output = self.cmd.execute()
        except Exception:
            self.logger.exception("Error running {0}.                  \
                                  Processing will terminate."
                                  .format(self.title))
            sys.exit(ScriptHelper.FAILURE())
        finally:
            if len(output) > 0:
                self.logger.info("STDOUT/STDERR Follows: {0}".format(output))
        self.logger.info("Completion of {0}".format(self.title))

    # Not Implemented.
    def parse_arguments(self):
        pass

    def check_prereq(self):
        return True

    def build_cmd_line(self):
        '''Sub classes'''
        pass


class SWE(ScriptHelper):

    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = 'dswe'
        self.title = 'Surface Water Extent'
        self.description = ("Build the command line and then kick-off the \
                            Dynamic Surface Water Extent application")

    def parse_arguments(self):
        # Create a command line argument parser
        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        parser = ScriptHelper.parseCommonArgs(parser, xml=True)
        parser.add_argument('--dem',
                            action='store', dest='dem_filename', required=True,
                            help="The DEM metadata file to use")
        # Additional parameters
        parser.add_argument('--verbose',
                            action='store_true', dest='verbose', default=False,
                            help=("Should intermediate messages be printed?"
                                  " (default value is False)"))
        # Common args
        parser = ScriptHelper.parseCommonArgs(parser,
                                              debug=True, verbose=False)

        # Parse the command line parameters
        self.args = parser.parse_args()

    def build_cmd_line(self):
        self.cmd = Cmd(self.exe_filename)
        self.cmd.addParam("--xml", self.args.xml_filename)
        self.cmd.addParam("--dem", self.args.dem_filename)
        if self.args.verbose:
            self.cmd.addParam("--verbose")


class SI(ScriptHelper):
    # Removed Log file argument
    # Removed usebin argument
    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = 'spectral_indices'
        self.title = 'Spectral Indices'
        self.description = ('''
        spectral_indices produces the desired spectral index products for the
         input surface reflectance or TOA reflectance bands. The options
         include: NDVI, EVI, SAVI, MSAVI, NDMI (also known as NDWI or NDII),
         NBR, and NBR2. The user may specify one, some, or all of the
         supported indices for output.''')

    def parse_arguments(self):
        # Create a command line argument parser
        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        parser = ScriptHelper.parseCommonArgs(parser, xml=True)
        # Additional parameters
        parser.add_argument("--toa", dest="toa", default=False,
                            action="store_true",
                            help="process TOA bands             \
                            instead of surface reflectance bands")
        parser.add_argument("--ndvi", dest="ndvi", default=False,
                            action="store_true",
                            help="process NDVI                 \
                            (normalized difference vegetation index")
        parser.add_argument("--ndmi", dest="ndmi", default=False,
                            action="store_true",
                            help="process NDMI                 \
                            (normalized difference moisture index")
        parser.add_argument("--nbr", dest="nbr", default=False,
                            action="store_true",
                            help="process NBR                 \
                            (normalized burn ratio")
        parser.add_argument("--nbr2", dest="nbr2", default=False,
                            action="store_true",
                            help="process NBR2                 \
                            (normalized burn ratio2")
        parser.add_argument("--savi", dest="savi", default=False,
                            action="store_true",
                            help="process SAVI                 \
                            (soil adjusted vegetation index)")
        parser.add_argument("--msavi", dest="msavi", default=False,
                            action="store_true",
                            help="process modified SAVI         \
                            (soil adjusted vegetation index)")
        parser.add_argument("--evi", dest="evi", default=False,
                            action="store_true",
                            help="process EVI                    \
                            (enhanced vegetation index")
        # Common command line arguments
        parser = ScriptHelper.parseCommonArgs(parser,
                                              debug=False, verbose=True)
        # Parse the command line parameters
        self.args = parser.parse_args()

    def check_prereq(self):
        # make sure there is something to do
        if (not self.args.ndvi and not
                self.args.ndmi and not
                self.args.nbr and not
                self.args.nbr2 and not
                self.args.savi and not
                self.args.msavi and not
                self.args.evi):
            self.logger.error("Error:no spectral index product"
                              "specified to be processed")
            return False
        else:
            return True

    def build_cmd_line(self):
        self.cmd = Cmd(self.exe_filename)
        self.cmd.addParam("--xml", self.args.xml_filename)

        if self.args.verbose:
            self.cmd.addParam("--verbose")
        if self.args.toa:
            self.cmd.addParam("--toa")
        if self.args.ndvi:
            self.cmd.addParam("--ndvi")
        if self.args.ndmi:
            self.cmd.addParam("--ndmi")
        if self.args.nbr:
            self.cmd.addParam("--nbr")
        if self.args.nbr2:
            self.cmd.addParam("--nbr2")
        if self.args.savi:
            self.cmd.addParam("--savi")
        if self.args.msavi:
            self.cmd.addParam("--msavi")
        if self.args.evi:
            self.cmd.addParam("--evi")

if __name__ == '__main__':
    MyFileName = os.path.basename(__file__)
    print(MyFileName+"::"+"__main__")
    if(MyFileName in ['spectral_indicies.py', 'si.py']):
        script = SI()
    elif(MyFileName in ['surface_water_extent.py', 'dswe.py', 'swe.py']):
        script = SWE()
    else:
        script = SI()

    script.parse_arguments()
    if(script.check_prereq()):
        script.build_cmd_line()
        script.execute()
        sys.exit(ScriptHelper.SUCCESS())
    else:
        sys.exit(ScriptHelper.FAILURE())

