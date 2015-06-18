#! /usr/bin/env python
'''
-----     -----     -----     -----     -----     -----     -----     -----
Author: ngenetzky@usgs.gov
License: NASA Open Source Agreement 1.3
USGS Designation: EROS Science Processing Architecture (ESPA)
Version: 0.0.1 (June 2015)

Classes:
    Cmd
    ScriptArgParser
    ScriptHelper
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
from distutils.tests.setuptools_build_ext import if_dl


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
        # add_param(PARAMERTER_NAME,PARAMETER_VALUE)
        cmdScript.add_param('xml', my_xml.xml)
        # Will use commands.getstatusoutput to execute built cmd-line
        cmdScript.execute()
    '''

    class EXECUTE_ERROR(Exception):
        def __init__(self, message, *args):
            self.message = message
            Exception.__init__(self, message, *args)
        pass

    def __init__(self, script_name, basedir=''):
        '''Setup the base of the cmdline with required directory and script name.

        Parameters:
            script_name: Name of the executable
            basedir: Location of the executable
        '''
        self.cmdline = [os.path.join(basedir, script_name)]

    def get_help(self):
        '''
        TODO
        '''
        self.add_param('--help')
        cmd_string = self.__str__()
        (status, output) = commands.getstatusoutput(cmd_string)
        return output

    def add_param(self, name, *args):
        '''Allows a parameter to be added; optionally with list of arguments

        Parameters:
            name: Name of argument preceeded with "--" or "-" if desired.
            args: Additional arguments to place after name
        '''
        self.cmdline.append(name)
        # Will only add an argument of the list if it is truthy
        self.cmdline.append(' '.join(arg for arg in args if arg))

    def __repr__(self):
        '''Combine the script name (and path) with the arguments'''
        return ' '.join(self.cmdline)

    def __str__(self):
        '''See __repr__'''
        return ' '.join(self.cmdline)

    def execute(self):
        ''' Execute a command line and return the terminal output

        Raises:
            EXECUTE_ERROR (Stdout/Stderr)
        Returns:
            output:The stdout and/or stderr from the executed command.
        '''
        cmd_string = self.__str__()
        (status, output) = commands.getstatusoutput(cmd_string)

        if status < 0:
            message = "Application terminated by signal [%s]" % cmd_string
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Cmd.EXECUTE_ERROR(message)

        if status != 0:
            message = "Application failed to execute [%s]" % cmd_string
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Cmd.EXECUTE_ERROR(message)

        if os.WEXITSTATUS(status) != 0:
            message = ("Application [%s] returned error code [%d]"
                       % (cmd_string, os.WEXITSTATUS(status)))
            if len(output) > 0:
                message = ' Stdout/Stderr is: '.join([message, output])
            raise Cmd.EXECUTE_ERROR(message)

        return output


class ScriptArgParser(argparse.ArgumentParser):
        class HELP_REQUESTED(Exception):
            pass

        class INVALID_ARGUMENT(Exception):
            pass

        def print_help(self, outfile=None):
            raise ScriptArgParser.HELP_REQUESTED

        def error(self, message):
            raise ScriptArgParser.INVALID_ARGUMENT(message)


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
        extend setup(). See check_common_prereq(). (optional)
        override build_cmd_line(). See build_cmd_line().
        extend handle_exception(). (optional)
    '''
    __title__ = 'Script Helper'
    __version__ = '0.0.1 (June 2015)'

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
        self.logger = logging.getLogger(__name__)
        self.args = None
        self.cmd = None
        self.config = None
        # Should be defined by sub-class
        self.title = 'Title Not Defined'
        self.exe_filename = 'Program Name not defined'
        self.description = 'Description not defined'
        self.parser = ScriptArgParser(description=
                                      self.description,
                                      add_help=True)

    class NO_ACTION_REQUESTED(Exception):
        pass

    class INVALID_FILE(Exception):
        def __init__(self, name, recieved, *args):
            self.name = name
            self.recieved = recieved
            Exception.__init__(name, recieved, *args)

    class INVALID_FILE_PARAM(Exception):  # (Expected format,received filename)
        def __init__(self, expected, recieved, *args):
            self.expected = expected
            self.recieved = recieved
            Exception.__init__(expected, recieved, *args)

    class INVALID_SATELLITE_XML(Exception):
        pass

    class INVALID_SUBCLASS(Exception):
        pass

    class MISSING_ENV_VARIABLE(Exception):
        pass

    class EXECUTABLE_NOT_DEFINED(Exception):
        pass

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
            INVALID_SATELLITE_XML
        '''
        if config['satellite'] is 'LANDSAT_8':
            return True
        elif config['satellite'] in ['LANDSAT_4', 'LANDSAT_5', 'LANDSAT_7']:
            return False
        else:
            raise ScriptHelper.INVALID_SATELLITE_XML

    @staticmethod
    def str_to_bool(string):
        '''Converts common boolean-like string to boolean value

        Supported Strings:['true', '1', 't', 'yes']
                          ['false', '0', 'f', 'no']
        '''
        if(string.lower() in ['true', '1', 't', 'yes']):
            return True
        elif(string.lower() in ['false', '0', 'f', 'no']):
            return False

    @staticmethod
    def parse_common_args(parser, xml=False, debug=False, verbose=False,
                          version=False):
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
                                help='Input XML metadata file',
                                metavar='FILE')
        if(debug):
            parser.add_argument('--debug',
                                action='store_true', dest='debug',
                                required=False, default=False,
                                help="Keep any debugging data"
                                     " (default is False)")
        if(verbose):
            parser.add_argument('--verbose',
                                action='store_true', dest='verbose',
                                required=False, default=False,
                                help=('Should intermediate messages'
                                      ' be printed? (default is False)'))
        if(version):
            parser.add_argument('--version',
                                action='store_true', dest='version',
                                required=False, default=False,
                                help=('Should intermediate messages'
                                      ' be printed? (default is False)'))
        return parser

    def parse_only_xml(self, list_ignored=False):
        '''
        TODO
        '''
        # Try to parse out the XML so the exe can be determined
        parse_xml = ScriptArgParser(add_help=False)
        parse_xml = self.parse_common_args(parse_xml, xml=True)
        (temp, extra_args) = parse_xml.parse_known_args()
        if(list_ignored):
            print 'The following arguments were ignored:' + ''.join(extra_args)
        self.args.xml_filename = temp.args.xml_filename
        return self.args.xml_filename

    def print_custom_help(self, this_module_help_only=True):
        '''
        TODO
        '''
        if(this_module_help_only):
            msg = '{0} {1}\n{2}'.format(
                                       # Name of the Sub Class
                                       self.__class__.__title__,
                                       # Version of the Sub Class
                                       self.__class__.__version__,
                                       self.parser.format_help(),
                                       )
        else:
            msg = ('{0} {1} was used by {2} {3} \n{4}\n'
                   'Help from executables under this script:\n{5}'
                   .format(
                           # Title of the module
                           self.title,
                           # Version of the underlying executable
                           self.get_executables_version(),
                           # Name of the Sub Class
                           self.__class__.__title__,
                           # Version of the Sub Class
                           self.__class__.__version__,
                           self.parser.format_help(),
                           self.get_executables_help()
                   ))
        print msg

    def get_executables_version(self):
        '''
        TODO
        '''
        try:
            cmd = Cmd(self.exe_filename)
            cmd.add_param('--version')
            version_msg = cmd.execute()
            return version_msg
        except NameError:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR:
            #  print('Application returned error when requesting --version')
            return ''  # If version can't be obtained then leave it empty
        else:
            raise

    # Error Cause
    def get_executables_help(self):
        '''
        TODO
        '''
        try:
            cmd = Cmd(self.exe_filename)
            help_msg = cmd.get_help()
            return help_msg
        except NameError:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR as e:
            print('Application returned error when requesting --help')
            return e.args[0]  # Message should contain Stdout, but also Stderr
        else:
            raise

    def check_common_prereq(self, check_xml=True):
        '''Allow easy way to check conditions that are commonly required for a script.

        Description:
            Should be used by subclass setup setup()
        Raises:
            INVALID_FILE_PARAM (Expected format, received filename)
            INVALID_FILE (Filetype/Description, received filename)
        '''
        if check_xml:
            # Verify that the XML filename provided is not an empty string
            if '.xml' not in self.args.xml_filename:
                raise ScriptHelper.INVALID_FILE_PARAM('*.xml*',
                                                      self.args.xml_filename)
            if not os.path.isfile(self.args.xml_filename):
                raise ScriptHelper.INVALID_FILE('XML',
                                                self.args.xml_filename)
        return True

    def get_execute_header(self):
        '''Return String describing action taken by execute().'''
        return ("{0} is processing Landsat data associated with xml file"
                " ({1}). Using the command line:{2}"
                ).format(self.title,
                         self.args.xml_filename,
                         str(self.cmd)
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
            self.logger.info("STDOUT/STDERR Follows:"
                             "{0}".format(output))
        self.logger.info("Completion of {0}".format(self.title))

    def parse_arguments(self):  # SubClass should implement.
        '''Should parse command line arguments using argparse module.

        To-Do for subclass:
            Override. Create argparse.ArgumentParser object.
                argparse.ArgumentParser(description=self.description)
            Add additional parameters by using Cmd.add_param()
            Must put arguments into self.args
                self.args = parser.parse_args()
        SubClass Note:
            If this method is not overridden it will raise exception.
        Raises:
            INVALID_SUBCLASS
        '''
        raise ScriptHelper.INVALID_SUBCLASS

    def get_exe_filename(self):  # SubClass should implement.
        '''Should parse command line arguments using argparse module.

        To-Do for subclass:
            Override. If exe_filename is defined as None in __init__
        Raises:
            EXECUTABLE_NOT_DEFINED
        '''
        if self.exe_filename:
            return self.exe_filename
        else:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED

    def setup(self):  # SubClass should implement.
        '''Should ensure the class is ready to build/execute the script

        To-Do for subclass:
            Optionally Extend. Check conditions that must be
            true in order for the executable to be executed.
            This function would be a valid time to set the the executable
            if it depends on the arguments passed in.
        '''
        try:
            self.args = self.parser.parse_args()

        except ScriptArgParser.HELP_REQUESTED:
            try:  # Assume XML is in arg list
                self.print_custom_help(this_module_help_only=False)
                exit(0)
            except NameError:
                # Then print extended help
                self.parse_only_xml()
                self.get_config_from_xml(self.args.xml_filename)
                self.get_exe_filename()
                self.print_custom_help(this_module_help_only=False)
                exit(0)
        except ScriptArgParser.INVALID_ARGUMENT as e:
            try:  # Then print extended help
                self.parse_only_xml()
                self.get_config_from_xml(self.args.xml_filename)
                self.get_exe_filename()
                self.print_custom_help(this_module_help_only=False)
                print('INVALID_ARGUMENT:'+e.args[0])
                exit(0)
            except ScriptArgParser.INVALID_ARGUMENT as exc:
                # Then print simple help
                self.print_custom_help(this_module_help_only=True)
                print('INVALID_ARGUMENT:'+exc.args[0])
                exit(0)

    def build_cmd_line(self):  # SubClass should implement.
        '''Builds a Cmd object that can be executed to run the executable.

        To-Do for subclass:
            Override. Create Cmd object and store in self.cmd
            Add additional parameters by using Cmd.add_param()
        SubClass Note:
            If this method is not overridden it will raise exception.
        Raises:
            INVALID_SUBCLASS
        '''
        raise ScriptHelper.INVALID_SUBCLASS

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
            Any Exception class defined in ScriptHelper directly
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        # Gets the exception type of exception being handled (class object)
        e_type = sys.exc_info()[0]
        # Gets the exception parameter (the second argument to raise)
        e = sys.exc_info()[1]

        if e_type is ScriptHelper.NO_ACTION_REQUESTED:
            self.logger.fatal("NO_ACTION_REQUESTED")
            try:
                self.logger.fatal(e.args[0])
            except NameError:
                pass
            exit_with_error()

        elif e_type is ScriptHelper.INVALID_FILE:
            try:
                self.logger.fatal("Error: {0} file ({1}) does not exist or"
                                  " is not accessible."
                                  .format(e.name, e.recieved))
            except NameError:
                pass
            exit_with_error()

        elif e_type is ScriptHelper.INVALID_FILE_PARAM:
            try:
                self.logger.error("Error: Expecting file parameter of"
                                  " format ({0}) but found ({1})"
                                  .format(e.expected, e.recieved))
            except NameError:
                pass
            exit_with_error()

        elif e_type is ScriptHelper.INVALID_SATELLITE_XML:
            self.logger.fatal("Error: XML specifies invalid satellite")
            exit_with_error()

        elif e_type is ScriptHelper.INVALID_SUBCLASS:
            self.logger.fatal("Script Helper was improperly subclassed")
            exit_with_error()

        elif e_type is ScriptHelper.MISSING_ENV_VARIABLE:
            self.logger.fatal("Error: Missing environment Variable")
            exit_with_error()  # MISSING_ENV_VARIABLE
        else:
            # Return False because Script Helper does not understand Exception
            return False


class SI(ScriptHelper):
    '''Parse request, check conditions, execute appropriate executable

    Description:
    Executables: spectral_indices
        Authors:
    Understood Exceptions:
        Those understood by ScriptHelper.
    '''
    __title__ = 'Spectral-Indices'
    __version__ = '0.0.1 (June 2015)'

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
        self.parser = ScriptHelper.parse_common_args(self.parser, xml=True)
        # Additional parameters
        self.parser.add_argument("--toa", dest="toa", default=False,
                                 action="store_true",
                                 help="process TOA bands"
                                 " instead of surface reflectance bands")

        self.parser.add_argument("--ndvi", dest="ndvi", default=False,
                                 action="store_true",
                                 help="process NDVI"
                                 "(normalized difference vegetation index)")

        self.parser.add_argument("--ndmi", dest="ndmi", default=False,
                                 action="store_true",
                                 help="process NDMI"
                                 "(normalized difference moisture index)")

        self.parser.add_argument("--nbr", dest="nbr", default=False,
                                 action="store_true",
                                 help=("process NBR"
                                       "(normalized burn ratio)"))

        self.parser.add_argument("--nbr2", dest="nbr2", default=False,
                                 action="store_true",
                                 help="process NBR2"
                                 "(normalized burn ratio2)")

        self.parser.add_argument("--savi", dest="savi", default=False,
                                 action="store_true",
                                 help="process SAVI"
                                 "(soil adjusted vegetation index)")

        self.parser.add_argument("--msavi", dest="msavi", default=False,
                                 action="store_true",
                                 help="process modified SAVI"
                                 "(soil adjusted vegetation index)")

        self.parser.add_argument("--evi", dest="evi", default=False,
                                 action="store_true",
                                 help="process EVI"
                                 "(enhanced vegetation index)")
        # Common command line arguments
        self.parser = ScriptHelper.parse_common_args(self.parser,
                                                     debug=False, verbose=True)

    def setup(self):
        '''Checks that a product was specified

        See ScriptHelper.setup() for more details
        Raises:
            NO_ACTION_REQUESTED(msg)
        '''
        ScriptHelper.setup(self)
        # make sure there is something to do
        if (not self.args.ndvi and
                not self.args.ndmi and
                not self.args.nbr and
                not self.args.nbr2 and
                not self.args.savi and
                not self.args.msavi and
                not self.args.evi):
            raise ScriptHelper.NO_ACTION_REQUESTED('No spectral indices'
                                                   ' product specified to'
                                                   ' be processed')

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
        self.cmd = Cmd(self.exe_filename)
        self.cmd.add_param("--xml", self.args.xml_filename)

        if self.args.verbose:
            self.cmd.add_param("--verbose")
        if self.args.toa:
            self.cmd.add_param("--toa")
        if self.args.ndvi:
            self.cmd.add_param("--ndvi")
        if self.args.ndmi:
            self.cmd.add_param("--ndmi")
        if self.args.nbr:
            self.cmd.add_param("--nbr")
        if self.args.nbr2:
            self.cmd.add_param("--nbr2")
        if self.args.savi:
            self.cmd.add_param("--savi")
        if self.args.msavi:
            self.cmd.add_param("--msavi")
        if self.args.evi:
            self.cmd.add_param("--evi")


if __name__ == '__main__':
    logger = get_logger()

    script = SI()

    try:
        script.parse_arguments()
        script.setup()
        script.build_cmd_line()

        try:
            script.execute()
        except Cmd.EXECUTE_ERROR as e:
            logger.exception(("Error running {0}."
                              "Processing will terminate."
                              ).format(script.title))
            try:
                logger.info(e.args[0])
            except NameError:  # No Message
                pass
            exit_with_error()
    except Exception as e:
        # Exceptions that were raised by the executable
        #  Handle any exceptions understood by script
        #  handle_exception may exit with error and not return.
        if(script.handle_exception() is False):
            raise  # Unhandled/Unexpected exceptions will not be masked

