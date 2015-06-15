#! /usr/bin/env python
'''
-----     -----     -----     -----     -----     -----     -----     -----
Author: ngenetzky@usgs.gov
License: NASA Open Source Agreement 1.3
USGS Designation: EROS Science Processing Architecture (ESPA)


Classes:
    Cmd
    ScriptHelper (Version: 0.0.1 June 2015)
    SI: Spectral Indices

SI    :    Spectral Indices
    FILE: spectral_indices.py
    SOURCE: https://github.com/USGS-EROS/espa-spectral-indices
    PURPOSE: Master script for creating spectral indices products.
    USAGE: See "spectral_indices.py --help"
    Dependencies: spectral_indices
    Description:
-----     -----     -----     -----     -----     -----     -----     -----
'''
import sys
import os
import argparse
import logging
import commands
import metadata_api


def exit_with_error():
    exit(1)


def get_logger():
    # Setup the Logger with the proper configuration
    logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                ' %(levelname)-8s'
                                ' %(filename)s:%(lineno)d:'
                                '%(funcName)s -- %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


class Cmd:
    '''Builds and executes command line statements

    Description:
        Encompasses all of the functions associated with building and
        executing command line arguments. By using this class with each script
        it ensures consistency in the way that that command line is produced.
    Usage:
        # __init__(SCRIPTNAME, DIRECTORY)
        cmdScript = Cmd('my_script_name')
        # addParam(PARAMERTER_NAME,PARAMETER_VALUE)
        cmdScript.addParam('xml', my_xml.xml)
        # Will use commands.getstatusoutput to execute built cmd-line
        cmdScript.execute()
    '''

    def __init__(self, script_name, basedir=''):
        '''Setup the base of the cmdline with required directory and script name.

        Parameters:
            script_name: Name of the executable
            basedir: Location of the executable
        '''
        self.cmdline = [os.path.join(basedir, script_name)]

    def addParam(self, name, *args):
        '''Allows a parameter to be added; optionally with list of arguments

        Parameters:
            name: Name of argument preceeded with "--" or "-" if desired.
            args: Additional arguments to place after name
        '''
        self.cmdline.append(name)
        self.cmdline.append(' '.join(args))

    def __str__(self):
        '''Combine the script name (and path) with the arguments'''
        return ' '.join(self.cmdline)

    def getCmdline(self):
        '''See __str__'''
        return self.__str__()

    def execute(self):
        ''' Execute a command line and return the terminal output

        Raises:
            Exception('EXECUTE_ERROR', message): where message
                contains Stout/Stderr
        Returns:
            output:The stdout and/or stderr from the executed command.
        '''
        cmd_string = str(self)
        (status, output) = commands.getstatusoutput(cmd_string)

        if status < 0:
            message = "Application terminated by signal [%s]" % cmd_string
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception('EXECUTE_ERROR', message)

        if status != 0:
            message = "Application failed to execute [%s]" % cmd_string
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception('EXECUTE_ERROR', message)

        if os.WEXITSTATUS(status) != 0:
            message = ("Application [%s] returned error code [%d]"
                       % (cmd_string, os.WEXITSTATUS(status)))
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Exception('EXECUTE_ERROR', message)

        return output


class ScriptHelper:
    '''Parse arguments, check conditions and execute the proper executable.

    Description:
        General functions and properties inherent to all scripts.
        Should never be directly instantiated, but instead should
        be a base class for other script classes.

    To-Do list to properly subclass:
        extend __init__ and define self.title and self.exe_filename
            super.__init__() should be called at the beginning
        override parse_arguments(). See parse_common_args().
        override check_prereq(). See check_common_prereq(). (optional)
        override build_cmd_line(). See build_cmd_line().
        extend handle_exception(). (optional)
    Understood Exceptions:
        NO_ACTION_REQUESTED,
        INVALID_FILE: (Type of file, filename given),
        INVALID_SATELLITE_XML,
        INVALID_SUBCLASS,
        INVALID_FILE_PARAM : (Expected format, filename given)
    '''
    # Possible future additions:
    # 1. Allow use of use BIN env. variable as the location of executable.
    # 2. Allow a log file to be specified.

    def __init__(self):
        '''Create an instance of Script Helper

        To-Do for subclass:
            Extend. super.__init__() should be called at the beginning
            define the following instance variables:
                title: title of its module to be used in log statements
                exe_filename: filename of executable to be called
        Instance Variables:
            Logger: logs info, error, fatal and other messages (from logging).
            args: will be defined by parse_arguments.
            cmd: will be defined by build_cmd_line
        '''
        self.logger = ScriptHelper._get_logger()
        self.args = None
        self.cmd = None
        self.config = None
        # Should be defined by sub-class
        self.title = 'Title Not Defined'
        self.exe_filename = 'Program Name not defined'

    def get_config_from_xml(self, xml_filename):
        ''' Stores desired information into dictionary from xml file

        Description:
            Provides information from xml file used by other functions.
        Functions that require config:
            is_landsat8()
        Expects the following contents in the xml:
        "
        <global_metadata>
            <satellite>LANDSAT_8</satellite>
            <instrument>OLI_TIRS</instrument>
        "
        '''
        self.config = {}  # Empty dictionary
        xml = metadata_api.parse(xml_filename, silence=True)
        global_metadata = xml.get_global_metadata()
        self.config['satellite'] = global_metadata.get_satellite()
        self.config['instrument'] = global_metadata.get_instrument()
        self.config['date'] = xml_filename[9:16]
        del xml  # Explicitly release memory from xml object

    @staticmethod
    def is_landsat8(config):
        '''Reads config dictionary for satellite name, checks if L8.
        Parameter:
            Config dictionary from ScriptHelper.get_config_from_xml()
        Raises:
            NotImplementedError('INVALID_SATELLITE_XML')
        '''
        if config['satellite'] is 'LANSAT_8':
            return True
        elif config['satellite'] in ['LANSAT_4', 'LANSAT_5', 'LANSAT_7']:
            return False
        else:
            raise NotImplementedError('INVALID_SATELLITE_XML')

    @staticmethod
    def str_to_bool(string):
        '''Converts common boolean-like string to boolean value

        Supported Strings:['true', '1', 't', 'yes']
                          ['false', '0', 'f', 'no']
        '''
        if(string.lower() == ['true', '1', 't', 'yes']):
            return True
        elif(string.lower() in ['false', '0', 'f', 'no']):
            return False

    @staticmethod
    def _get_logger():
        '''Obtain Logger object from logging module

        Pre-Condition: The configuration must already be set.
        '''
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def get_bin_dir():
        '''Returns the BIN dir environment variable.'''
        bin_dir = os.environ.get('BIN')
        bin_dir = bin_dir + '/'
        return bin_dir

    @staticmethod
    def parse_common_args(parser, xml=False, debug=False, verbose=False):
        '''Allows common arguments to be added to the parser.

        Description:
            Should be used by subclass overriding parse_common_args()
        Parameters:
            parser: A valid argparse.ArgumentParser object.
        Arguments to add to ArgumentParser (Default is False):
            xml==True: add argument "--xml XML_FILENAME"
            debug==True: add argument "--debug"
            verbose==True: add argument "--verbose"
        Returns:
            parser: A valid "argparse.ArgumentParser" object with equal or
             more arguments specified than the parser passed in.
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
                                help=('Should intermediate messages'
                                      ' be printed? (default value is False)'))
        return parser

    def check_common_prereq(self, check_xml=True):
        '''Allow easy way to check conditions that are commonly required for a script.

        Description:
            Should be used by subclass overriding check_prereq()
        Raises:
            ValueError('INVALID_FILE_PARAM', expected format, xml_filename)

        '''
        if check_xml:
            # Verify that the XML filename provided is not an empty string
            if '.xml' not in self.args.xml_filename:
                raise ValueError('INVALID_FILE_PARAM', '*.xml*',
                                 self.args.xml_filename)
            if not os.path.isfile(self.args.xml_filename):
                raise ValueError('INVALID_FILE', 'XML',
                                 self.args.xml_filename)
        return True

    def get_execute_header(self):
        '''Return String describing action taken by execute().'''
        return ("{0} is processing Landsat data associated with xml file"
                " ({1}). Using the command line:{2}"
                ).format(self.title,
                         self.args.xml_filename,
                         self.cmd.getCmdline()
                         )

    def execute(self):
        '''Print the execute header, execute cmdline and print output

        Description:
            Uses get_execute_header() to know what to print before execution
            Executes line built with build_cmd_line()
        '''
        header = self.get_execute_header()
        self.logger.info(header)

        output = self.cmd.execute()

        if len(output) > 0:
            script.logger.info("STDOUT/STDERR Follows:"
                               "{0}".format(output))
        script.logger.info("Completion of {0}".format(script.title))

    def parse_arguments(self):  # SubClass should implement.
        '''Should parse command line arguments using argparse module.

        To-Do for subclass:
            Override. Create argparse.ArgumentParser object.
                argparse.ArgumentParser(description=self.description)
            Add additional parameters by using Cmd.addParam()
            Must put arguments into self.args
                self.args = parser.parse_args()
        SubClass Note:
            If this method is not overridden it will raise exception.
        Raises:
            NotImplementedError('INVALID_SUBCLASS')
        '''
        raise NotImplementedError('INVALID_SUBCLASS')

    def check_prereq(self):  # SubClass should implement.
        '''Should check conditions that must be for the script to execute.

        To-Do for subclass:
            Optionally Override. Check conditions that must be
            true in order for the executable to be executed.
            This function would be a valid time to set the the executable
            if it depends on the arguments passed in.
        Note:
            If a condition is failed it can raise exception or return false
            which will skip execution of script.
        SubClass Note:
            If this method is not overridden it will always return True.
        '''
        return True

    def build_cmd_line(self):  # SubClass should implement.
        '''Builds a Cmd object that can be executed to run the executable.

        To-Do for subclass:
            Override. Create Cmd object and store in self.cmd
            Add additional parameters by using Cmd.addParam()
        SubClass Note:
            If this method is not overridden it will raise exception.
        Raises:
            NotImplementedError('INVALID_SUBCLASS')
        '''
        raise NotImplementedError('INVALID_SUBCLASS')

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See sys.exc_info() for access to exception information
        See ScriptHelper.__doc__ for Understood Exceptions
        Description:
            Typically the method will log a message related to the exception
            and then exit with error.
        To-Do for subclass:
            Optionally Extend. Subclass should return False if the
            exception was not understood.
        SubClass Note:
            Consider effects of calling super.handle_exception at beginning or
            end of the method that extends this method.
        Understood exceptions:
            See class.__doc__
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        # gets the exception type of exception being handled (class object)
        e_type = sys.exc_info()[0]
        # gets the exception parameter (the second argument to raise)
        e = sys.exc_info()[1]
        if e_type is ValueError:
            if(e.args[0] == 'NO_ACTION_REQUESTED'):
                exit_with_error()  # NO_ACTION_REQUESTED
            elif(e.args[0] == 'CANT_OPEN_FILE'):
                if(e.args[1] == 'CANT_READ_XML'):
                    logger.fatal("Error: XML file ({1})does not exist or is"
                                 "not accessible.".format(e.args[1]))
                exit_with_error()  # INVALID_XML

            elif(e.args[0] == 'INVALID_FILE_PARAM'):
                logger.error("Error: Expecting file parameter of format ({0})"
                             " but found ({1})".format(e.args[1]), e.args[2])
                exit_with_error()  # INVALID_FILE_PARAM

        elif e_type is NotImplementedError:
            if(e.args[0] == 'INVALID_SATELLITE_XML'):
                logger.fatal("Error: XML specifies invalid satellite")
                exit_with_error()  # INVALID_SATELLITE_XML

            elif(e.args[0] == 'INVALID_SUBCLASS'):
                logger.fatal("Script Helper was improperly subclassed")
                exit_with_error()  # INVALID_SUBCLASS

        else:
            if(e.args[0] == 'MISSING_ENV_VARIABLE'):
                logger.fatal("Error: Missing environment Variable")
                exit_with_error()  # INVALID_SATELLITE_XML

        return False


class SI(ScriptHelper):
    '''Parse request, check conditions, execute appropriate executable

    Description:
    Executables: spectral_indices
        Authors:
    Understood Exceptions:
        See ScriptHelper.__doc__ for more Understood Exceptions.
    '''
    # Compared to do_spectral_indices:
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
        supported indices for output.
        ''')

    def parse_arguments(self):
        '''See ScriptHelper.parse_arguments() for more details'''

        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        parser = ScriptHelper.parse_common_args(parser, xml=True)
        # Additional parameters
        parser.add_argument("--toa", dest="toa", default=False,
                            action="store_true",
                            help="process TOA bands"
                                 "instead of surface reflectance bands")

        parser.add_argument("--ndvi", dest="ndvi", default=False,
                            action="store_true",
                            help="process NDVI"
                                 "(normalized difference vegetation index")

        parser.add_argument("--ndmi", dest="ndmi", default=False,
                            action="store_true",
                            help="process NDMI"
                                 "(normalized difference moisture index")

        parser.add_argument("--nbr", dest="nbr", default=False,
                            action="store_true",
                            help=("process NBR"
                                  "(normalized burn ratio"))

        parser.add_argument("--nbr2", dest="nbr2", default=False,
                            action="store_true",
                            help="process NBR2"
                                 "(normalized burn ratio2")

        parser.add_argument("--savi", dest="savi", default=False,
                            action="store_true",
                            help="process SAVI"
                                 "(soil adjusted vegetation index)")

        parser.add_argument("--msavi", dest="msavi", default=False,
                            action="store_true",
                            help="process modified SAVI"
                                 "(soil adjusted vegetation index)")

        parser.add_argument("--evi", dest="evi", default=False,
                            action="store_true",
                            help="process EVI"
                                 "(enhanced vegetation index")
        # Common command line arguments
        parser = ScriptHelper.parse_common_args(parser,
                                                debug=False, verbose=True)
        # Parse the command line parameters
        self.args = parser.parse_args()

    def check_prereq(self):
        '''Checks that a product was specified

        See ScriptHelper.build_cmd_line() for more details
        Raises:
            ValueError('NO_ACTION_REQUESTED', message)
        '''
        run = self.check_common_prereq(check_xml=True)
        # make sure there is something to do
        if (not self.args.ndvi and
                not self.args.ndmi and
                not self.args.nbr and
                not self.args.nbr2 and
                not self.args.savi and
                not self.args.msavi and
                not self.args.evi):
            self.logger.error("Error:no spectral index product"
                              " specified to be processed")
            raise ValueError('NO_ACTION_REQUESTED', 'No spectral index product'
                                                    'specified to be processed'
                             )
            return False
        return run

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
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
    logger = get_logger()
    try:
        script = SI()

        script.parse_arguments()
        if(script.check_prereq()):
            script.build_cmd_line()
            script.execute()
    except Exception as e:
        # Exceptions that were raised by the executable
        if(e.args[0] == 'EXECUTE_ERROR'):
            logger.exception(("Error running {0}."
                              "Processing will terminate."
                              ).format(script.title))
            exit_with_error()  # EXECUTE_ERROR

        #  Handle any exceptions understood by script
        #  handle_exception may exit with error and not return.
        if(script.handle_exception() is False):
            raise  # Unhandled/Unexpected exceptions will not be masked

