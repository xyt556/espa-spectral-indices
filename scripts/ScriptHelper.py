#! /usr/bin/env python
'''
Script Helper
-----     -----     -----     -----     -----     -----     -----     -----
Author: ngenetzky@usgs.gov
        Underlying scripts' author are described with the class documentation
Version:
License: NASA Open Source Agreement 1.3
USGS Designation: EROS Science Processing Architecture (ESPA)

Classes:
    Cmd
    ScriptArgParser
    ScriptHelper (Version:0.0.1)
    SI: Spectral Indices (Version:2.1.0)
    SWE: Surface Water Extent
    Cfmask: Cloud Function Mask
    SR: Surface Reflectance
-----     -----     -----     -----     -----     -----     -----     -----
SI
-----     -----     -----     -----     -----     -----     -----     -----
Project Name: SI (Spectral Indices)
Source: https://github.com/USGS-EROS/espa-spectral-indices
License: NASA Open Source Agreement 1.3
USGS Designation: EROS Science Processing Architecture (ESPA)
Description:
    Spectral Indices produces the desired spectral index products for the
    input surface reflectance or TOA reflectance bands. The options
    include: NDVI, EVI, SAVI, MSAVI, NDMI (also known as NDWI or NDII),
    NBR, and NBR2. The user may specify one, some, or all of the
    supported indices for output.

Classes:
    Cmd
    ScriptArgParser
    ScriptHelper (Version:0.0.1)
    SI: Spectral Indices

Script:
    File: spectral_indices.py
    Author: ngenetzky@usgs.gov
    Purpose: Master script for creating spectral indices products.
    Help/Usage/Version: See "spectral_indices.py --help"
    Note: Script is based on source code from: do_spectral_indices.py
        From the project: github.com/USGS-EROS/espa-spectral-indices/
        Written by: gschmidt@usgs.gov

Executables:
    File: spectral_indices
    Author:  gschmidt@usgs.gov
    Help/Usage/Version: See "spectral_indices.py --help"
-----     -----     -----     -----     -----     -----     -----     -----
'''
import sys
import os
import argparse
import logging
import metadata_api
from Cmd import Cmd


def get_logger():

    # Setup the Logger with the proper configuration
    logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                ' %(levelname)-8s'
                                ' %(filename)s:%(lineno)d:'
                                '%(funcName)s -- %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


class ScriptArgParser(argparse.ArgumentParser):  # ############################
        '''Functions that exit during parse_args() will instead raise exception.

        Raises:
            HELP_REQUESTED: Indicates that the user would like help.
            INVALID_ARGUMENT: Indicates that the user's command line arguments
                are invalid.
        '''
        class HELP_REQUESTED(Exception):
            '''Indicates that -h or --help has been parsed

            See print_help()
            '''
            pass

        class INVALID_ARGUMENT(Exception):
            '''Indicates ArgParse has detected an error

            See error()
            '''
            pass

        def print_help(self, outfile=None):
            '''Raise exception instead of printing help and exiting

            argparse.ArgumentParser.print_help() originally would print a
            message defined by format_help() and then sys.exit(SUCCESS)
            format_help(): Return a string containing a help message,
            including the program usage and information about the arguments
            registered with the ArgumentParser.

            Raises: ScriptArgParser.HELP_REQUESTED
            '''
            raise ScriptArgParser.HELP_REQUESTED

        def error(self, message):
            '''Raise exception instead of printing message and exiting

            argparse.ArgumentParser.error() is called when the argument parser
            encounters an unrecognized argument or when it has read all the
            arguments but has not found one of the required arguments.
            Originally error() would print the message to sterr and then
            terminate program with status code of 2.

            Raises: ScriptArgParser.INVALID_ARGUMENT(message)
            '''
            raise ScriptArgParser.INVALID_ARGUMENT(message)


class ScriptHelper:  # ########################################################
    '''Parse arguments, check conditions and execute the proper executable.

    Description:
        General functions and properties inherent to all scripts.
        Should never be directly instantiated, but instead should
        be a base class for other script classes.

    To-Do list to properly subclass:
        extend __init__. super.__init__() should be called at the beginning
        override build_parser(). See add_common_args().
        extend setup(). See check_common_prereq(). (optional)
            super.setup() should be called at the beginning
        override build_cmd_line(). See build_cmd_line().
        extend handle_exception(). (optional)
    '''
    __title__ = 'Script Helper'
    __version__ = '0.0.1 (July 2015)'

    def __init__(self):
        '''Create an instance of Script Helper

        To-Do for subclass:
            Extend. super.__init__() should be called at the beginning
            define the following instance variables:
                title: title of its module to be used in log statements
                exe_filename:

        Instance Variables:
            Logger: logs info, error, fatal and other messages (from logging).
            args: defined by parse_arguments().
            cmd: defined by build_cmd_line()
            config: defined by get_config_from_xml()
            parser: defined by build_parser()

        Instance Variables defined by subprogram:
            title: A title that describes all executables in the class.
            exe_filename: filename of executable to be called should be
                defined in __init__() if possible. Otherwise a function
                get_exe_filename should be defined that will determine
                which exe will be used.
            description: A description for all executables in the class.
        '''
        self.logger = logging.getLogger(__name__)
        self.args = None
        self.cmd = None
        self.config = None
        # Should be defined by sub-class
        self.title = None
        self.exe_filename = None
        self.description = None
        # Attempt to Pre-Parse XML so satellite can be used in logic

    class NO_ACTION_REQUESTED(Exception):
        pass

    class INVALID_FILE(Exception):
        def __init__(self, name, recieved, *args):
            self.name = name
            self.recieved = recieved
            Exception.__init__(self, name, recieved, *args)

    class INVALID_SATELLITE_XML(Exception):
        '''Parsed xml file does not meet specified format'''
        def __init__(self, sat_name, *args):
            self.sat_name = sat_name
            Exception.__init__(self, sat_name, *args)

    class INVALID_SUBCLASS(Exception):
        '''Subclass failed a requirements for a subclasses of ScriptHelper'''
        pass

    class EXECUTABLE_NOT_DEFINED(Exception):
        '''exe_filename has been requested before being defined.

        Should either be defined in __init__() or in get_exe_filename()
        '''
        pass

    def get_config_from_xml(self, xml_filename):
        '''Stores desired information into config(dict) from xml file

        Description:
            Provides access to information from xml file.
        Precondition:
            xml_filename is a string that refers to a xmlfile in the current
                working directory
            XML contains the following item:
                <global_metadata><satellite>
        Postcondition:
            'satellite' is in dictionary self.config
        '''

        self.config = {}  # Empty dictionary
        xml = metadata_api.parse(xml_filename, silence=True)
        global_metadata = xml.get_global_metadata()
        self.config['satellite'] = global_metadata.get_satellite()
        # self.config['instrument'] = global_metadata.get_instrument()
        # self.config['date'] = xml_filename[9:16]
        del global_metadata  # Explicitly release memory from xml object
        del xml  # Explicitly release memory from xml object

    def is_landsat8(self, config):
        '''Reads config dictionary for satellite name, checks if L8.
        Precondition:
            (1) 'satellite' is in config
            (2) config['satellite'] is in
                ['LANDSAT_4','LANDSAT_5','LANDSAT_7','LANDSAT_8']
        Postcondition:
            returns is_landsat8
        Raises:
            INVALID_SUBCLASS if fail Precondition (1)
            INVALID_SATELLITE_XML if fail Precondition (2)
        '''
        try:
            if config['satellite'] in ['LANDSAT_8']:
                return True
            elif config['satellite'] in ['LANDSAT_4',
                                         'LANDSAT_5',
                                         'LANDSAT_7']:
                return False
            else:
                raise ScriptHelper.INVALID_SATELLITE_XML(config['satellite'])
        except TypeError:
            raise
            # In one scenario TypeError is raised for this particular issue:
            # raise ScriptHelper.INVALID_SUBCLASS('is_landsat8 must be called'
            #                                    ' after get_config_from_xml')

    @staticmethod
    def str_to_bool(string):
        '''Converts common boolean-like string to boolean value

        Supported Strings:['true', '1', 't', 'yes']
                          ['false', '0', 'f', 'no']
        Note: Strings are not Case Sensitive
        '''
        if(string.lower() in ['true', '1', 't', 'yes']):
            return True
        elif(string.lower() in ['false', '0', 'f', 'no']):
            return False

    @staticmethod
    def add_common_args(parser, xml=False, debug=False, verbose=False,
                        version=False):
        '''Allows common arguments to be added to the parser.

        Description:
            Should be used by subclass when overriding build_parser()
        Precondition:
            parser must be a valid argparse.ArgumentParser or subclass
        Arguments to add to ArgumentParser (Default is False):
            xml==True: add argument "--xml XML_FILENAME"
            debug==True: add argument "--debug"
            verbose==True: add argument "--verbose"
            version==True: add argument "--version"
        Postcondition:
            returns parser: A valid argparse.ArgumentParser object with equal
             or more arguments specified than the parser passed in.
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
                                help=('Should version message'
                                      ' be printed? (default is False)'))
        return parser

    def parse_only_xml(self, list_ignored=False):
        '''Will only parse --xml XML_FILENAME from cmdline.

        See get_config_from_xml() and  get_exe_filename() for additional
            pre and post conditions.

        Precondition:
            '--xml FILENAME' exists in command line arguments
        Postcondition:
            self.args.xml_filename exists

        '''

        # Try to parse out the XML so the exe can be determined
        parse_xml = ScriptArgParser(add_help=False)
        parse_xml = self.add_common_args(parse_xml, xml=True)
        (temp, extra_args) = parse_xml.parse_known_args()

        try:
            if(self.args is None):
                self.args = temp  # Args are empty. thus overwrite
            else:
                self.args.xml_filename = temp.xml_filename
        except:
            raise

    def print_custom_help(self):
        '''Used to override default help so underlying exe's help can be shown

        Format
        If the exe_filename can be determined at the time of execution:
            SCRIPT_TITLE SCRIPT_VERSION
            USAGE
            DESCRIPTION
            ARGUMENTS

            ----     EXE_TITLE EXE_VERSION     -----

            Help from executables under this script:
            EXE_HELP_OUTPUT

        Otherwise:
            SCRIPT_TITLE SCRIPT_VERSION
            USAGE
            DESCRIPTION
            ARGUMENTS

            For additional help specify the xml with the help parameter
        '''
        try:
            self.parse_only_xml()
            self.get_config_from_xml(self.args.xml_filename)
            self.get_exe_filename()
            msg = (('{2} {3}\n{4}'
                    '\n\n-----     {0} {1}     -----\n'
                    'Help from executables under this script:\n\n{5}'
                    ).format(
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
        except ScriptArgParser.INVALID_ARGUMENT:  # Implies xml is missing

            # Print only the help for the script not underlying executables.
            msg = ('{0} {1}\n{2}\nFor additional help specify the xml with'
                   ' the help parameter').format(
                                             # Name of the Sub Class
                                             self.__class__.__title__,
                                             # Version of the Sub Class
                                             self.__class__.__version__,
                                             self.parser.format_help())
        print msg

    def get_executables_version(self):
        '''Will execute 'exe_filename --version' and return response.

        Precondition:
            (1) self.get_exe_filename() returns a string that is the name of an
                executable that exists in the path
            (2) application exits with success
        Postcondition:
            If (2) fails : returns standard output
            If (2) passes: returns ''
        Raises
            Cmd.INVALID_EXECUTABLE if (1) is failed
        '''
        try:
            cmd = Cmd(self.get_exe_filename())
            cmd.add_param('--version')
            version_msg = cmd.execute()
            return version_msg
        except Cmd.INVALID_EXECUTABLE:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR:
            return ''  # If version can't be obtained then leave it empty
        else:
            raise

    def get_executables_help(self):
        '''Will execute 'exe_filename --help' and return response.

        Precondition:
            (1) self.get_exe_filename() returns a string that is the name of an
                executable that exists in the path
            (2) application exits with success
        Postcondition:
            If (2) fails : returns standard output and error
            If (2) passes: returns standard output
        Raises
            Cmd.INVALID_EXECUTABLE if (1) is failed
        '''
        try:
            cmd = Cmd(self.get_exe_filename())
            help_msg = cmd.get_help()
            return help_msg
        except Cmd.INVALID_EXECUTABLE:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR as e:
            return e.args[0]  # Message should contain Stdout, but also Stderr
        else:
            raise

    def check_common_prereq(self, check_xml=True):
        '''Helper method to check conditions commonly required for executables.

        Description:
        Raises:
            INVALID_FILE (Filetype/Description, received filename)
        '''
        if check_xml:

            # Verify that the XML filename provided is not an empty string
            # and that the file can be accessed
            if not os.path.isfile(self.args.xml_filename):
                raise Cmd.INVALID_FILE(name='XML',
                                       recieved=self.args.xml_filename)
        return True

    def get_execute_header(self):
        '''Return String describing action taken by execute().

        Precondition:
            self.args.xml_filename exists
            self.cmd is valid Cmd object
        Postcondition:
            returns string that introduces the operations of the execution.
            '''
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

    def build_parser(self):  # SubClass should override.
        '''Should parse command line arguments using argparse module.

        To-Do for subclass:
            Override. Create argparse.ArgumentParser object.
                argparse.ArgumentParser(description=self.description)
        SubClass Note:
            If this method is not overridden it will raise exception.
        Raises:
            INVALID_SUBCLASS
        '''
        raise ScriptHelper.INVALID_SUBCLASS

    def parse_arguments(self):
        '''Stores arguments specified in build_parser() to self.args

            If '--help' or '-h' is specified as an argument the request is
            handled here by printing according to print_custom_help().
            Invalid arguments will also show help along with error message.
        '''
        try:
            self.args = self.parser.parse_args()
        except ScriptArgParser.INVALID_ARGUMENT as e:
            self.print_custom_help()
            self.logger.error(e.args[0])  # Error message from ArgParse
            sys.exit(1)
        except ScriptArgParser.HELP_REQUESTED:
            self.print_custom_help()
            sys.exit(0)

    def get_exe_filename(self):  # SubClass should override.
        '''Should return the name of the executable.

        Precondition:
            self.exe_filename exists
        Postcondition:
            returns self.exe_filename
        To-Do for subclass:
            Override if exe_filename can not be determined before parsing
                arguments
        Raises:
            EXECUTABLE_NOT_DEFINED
        '''
        if self.exe_filename:
            return self.exe_filename
        else:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED

    def build_cmd_line(self):  # SubClass should override.
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

        See sys.exc_info() = [type,value,traceback]
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
        Precondition:
            Called within the except block of a try/except.
        Postcondition:
            Returns: False if the exception was not understood
        '''

        # Gets the exception type of exception being handled (class object)
        e_type = sys.exc_info()[0]

        # Gets the exception parameter (the second argument to raise)
        e = sys.exc_info()[1]
        print(str(e.__class__)+' Exception:'+str(e))

        if e_type is ScriptHelper.NO_ACTION_REQUESTED:
            self.logger.fatal("NO_ACTION_REQUESTED")
            try:
                self.logger.fatal(e.args[0])
            except NameError:
                pass
            raise

        elif e_type is ScriptHelper.INVALID_FILE:
            try:
                self.logger.fatal("Error: {0} file ({1}) does not exist or"
                                  " is not accessible."
                                  .format(e.name, e.recieved))
            except NameError:
                pass
            raise

        elif e_type is ScriptHelper.INVALID_SATELLITE_XML:
            try:
                self.logger.fatal("Error: XML specifies invalid satellite({0})"
                                  .format(e.sat_name))
            except NameError:
                pass
            raise

        elif e_type is ScriptHelper.INVALID_SUBCLASS:
            self.logger.fatal("Script Helper was improperly subclassed")
            raise
        else:

            # Return False because Script Helper does not understand Exception
            return False

    def run(self):
        '''Generic use of class's functions to obtained executables output'''
        try:
            self.build_parser()
            self.parse_arguments()
            self.build_cmd_line()
            self.execute()
            sys.exit(0)
        except Exception:

            # Exceptions that were raised by the executable
            #  Handle any exceptions understood by script
            #  handle_exception may exit with error and not return.
            if not self.handle_exception():
                raise   # Unhandled/Unexpected exceptions will not be masked


""""Template for creating a subclass of ScriptHelper
class NameOfModule(ScriptHelper):
    '''Parse request, check conditions, execute appropriate executable

    Description:
    Executables:
        Authors:
    '''
    __title__ = 'Script_Template'
    __version__ = '0.0.1 (June 2015)'
    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = 'name_of_executable'  # None = determined later
        self.title = 'Title_Of_Executable'
        self.description = ('''description_of_executable''')

        # Insert_Code_After_Here

    def build_parser(self):
        '''See ScriptHelper.build_parser() for more details'''

        parser = argparse.ArgumentParser(description=self.description)

        # Required parameters
        parser = ScriptHelper.add_common_args(parser, xml=True)

        # Additional parameters
        parser.add_argument('--cmdline_name', dest='args_name', default=False,
                            action='store_true',
                            help='help'
                                 'even_more_help')

        # Common command line arguments
        parser = ScriptHelper.add_common_args(parser,
                                                debug=False, verbose=False)

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''

        self.cmd = Cmd(self.exe_filename)
        self.cmd.add_param('--argument_with_param', self.args.xml_filename)

        if self.args.boolean:
            self.cmd.add_param('--some_flag')

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See ScriptHelper.handle_exception() for more details.
        See sys.exc_info() for access to exception information
        Description:
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        return ScriptHelper.handle_exception(self)
"""

