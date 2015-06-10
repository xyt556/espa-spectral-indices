#! /usr/bin/env python
'''
-----     -----     -----     -----     -----     -----
@author: ngenetzky@usgs.gov
LICENSE: NASA Open Source Agreement 1.3
CLASSES:
    Cmd
    ScriptHelper
    SI : Spectral Indices

SI    :    Spectral Indices
    FILE: spectral_indices.py
    SOURCE: https://github.com/USGS-EROS/espa-spectral-indices
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

    def __init__(self, script_name, basedir=''):
        'Cmd object must know location and name of script'
        self.cmdline = [basedir+script_name]

    def addParam(self, name, *args):
        'Allows parameter to be named as well as a list of arguments'
        self.cmdline.append(name)
        self.cmdline.append(' '.join(args))

    def getCmdline(self):
        'Combines the script name (and path) with the arguments'
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
        if os.WEXITSTATUS(status) != 0:
            message = "Application [%s] returned error code [%d]" \
                      % (cmd, os.WEXITSTATUS(status))
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception(message)
        return output


class ScriptHelper:
    '''
    General functions and properties inherent to all scripts.
    Should never be directly instantiated, but instead should
    be a base class for other script classes.
    '''
    # Possible future additions:
    # 1. Allow use of use BIN env. variable as the location of executable.
    # 2. Allow a log file to be specified.
    # 3. Create a more robust getConfigFromXml to replace "is_landsat8()"
    def __init__(self):
        '''
        A valid script should have a title, of its module, and exe_filename,
        which should be the name of the executable. Logger is from logging.
        args and cmd will be defined by parse_arguments and build_cmd_line.
        '''
        self.logger = ScriptHelper._get_logger()
        self.args = None
        self.cmd = None
        # Should be defined by sub-class
        self.title = 'Title Not Defined'
        self.exe_filename = 'Program Name not defined'

    @staticmethod
    def is_landsat8(xml_filename):
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
    def _get_logger():
        '''
        Obtain Logger object from logging module.
        setup the default logger format and level. log to STDOUT.
        '''
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
    def get_bin_dir():
        'Returns the BIN dir environment variable.'
        bin_dir = os.environ.get('BIN')
        bin_dir = bin_dir + '/'
        return bin_dir

    @staticmethod
    def parse_common_args(parser, xml=False, debug=False, verbose=False):
        '''
        Allows common arguments to be added to the parser.
        Any of the following can be specified: xml, debug and verbose.
        Default is None.
        '''
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

    def check_common_prereq(self, checkXml=True):
        '''
        Checks conditions that must be true for any script.
        Not required that each sub class uses any of them.
        '''
        if checkXml:
            # Verify that the XML filename provided is not an empty string
            if self.args.xml_filename == '':
                self.logger.fatal("\n\tNo XML metadata filename provided.")
                self.logger.fatal("\n\tError processing LST.     \
                                   Processing will terminate.")
                sys.exit(self.FAILURE())
        return True

    def get_execute_header(self):
        '''
        Defines the String that will appear in the log
        when execute() is called.
        '''
        return '''{0} is processing Landsat data associated with xml file ({1}). \
Using the command line:{2}
        ''' .format(self.title,
                    self.args.xml_filename,
                    self.cmd.getCmdline()
                    )

    def execute(self):
        header = self.get_execute_header()
        self.logger.info('\n\t'+header)
        # print(header)
        output = ''
        try:
            output = self.cmd.execute()
        except Exception:
            self.logger.exception("\n\tError running {0}.                  \
                                  Processing will terminate."
                                  .format(self.title))
            sys.exit(ScriptHelper.FAILURE())
        finally:
            if len(output) > 0:
                self.logger.info("\n\tSTDOUT/STDERR Follows: \
                                 {0}".format(output))
        self.logger.info("\n\tCompletion of {0}".format(self.title))

    def parse_arguments(self):  # SubClass should implement.
        'Should parse command line arguments using argparse module.'
        pass

    def check_prereq(self):  # SubClass should implement.
        'Should check conditions that must be for the script to execute.'
        return True

    def build_cmd_line(self):  # SubClass should implement.
        'Should use Cmd to build a command line argument.'
        pass


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
        'Create a command line argument parser. Accept arguments from cmdline.'
        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        parser = ScriptHelper.parse_common_args(parser, xml=True)
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
        parser = ScriptHelper.parse_common_args(parser,
                                                debug=False, verbose=True)
        # Parse the command line parameters
        self.args = parser.parse_args()

    def check_prereq(self):
        'Checks conditions that should be true in order execute script'
        # make sure there is something to do
        if (not self.args.ndvi and not
                self.args.ndmi and not
                self.args.nbr and not
                self.args.nbr2 and not
                self.args.savi and not
                self.args.msavi and not
                self.args.evi):
            self.logger.error("\n\tError:no spectral index product"
                              "specified to be processed")
            return False
        else:
            return True

    def build_cmd_line(self):
        'Builds a Cmd object that can be executed to run the executable.'
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
    script = SI()
    script.parse_arguments()
    if(script.check_prereq()):
        script.build_cmd_line()
        script.execute()
        sys.exit(0)
    else:
        sys.exit(1)


