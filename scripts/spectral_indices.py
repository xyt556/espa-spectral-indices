#! /usr/bin/env python
'''
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
'''
import sys
import os
import argparse
import logging
import commands
import metadata_api


def get_logger():
    # Setup the Logger with the proper configuration
    logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                ' %(levelname)-8s'
                                ' %(filename)s:%(lineno)d:'
                                '%(funcName)s -- %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


class Cmd:  # #################################################################
    '''Builds and executes command line statements

    Description:
        Encompasses all of the functions associated with building and
        executing command line arguments. By using this class with each script
        it ensures consistency in the way that that command line is produced.
    Usage:
        # __init__(SCRIPTNAME, DIRECTORY)
        cmdScript = Cmd('my_script_name')
        # add_param(PARAMERTER_NAME,PARAMETER_VALUE)
        cmdScript.add_param('xml', 'my_xml.xml')
        # Will use commands.getstatusoutput to execute built cmd-line
        cmdScript.execute()
    '''

    class EXECUTE_ERROR(Exception):
        def __init__(self, message, *args):
            self.message = message
            Exception.__init__(self, message, *args)

    class INVALID_SCRIPT(Exception):
        def __init__(self, script_name, *args):
            self.script_name = script_name
            Exception.__init__(self, script_name, *args)
        pass

    def __init__(self, script_name, basedir=''):
        '''Setup the base of the cmdline with required directory and script name.

        Parameters:
            script_name: Name of the executable
            basedir: Location of the executable
        Raises:
            INVALID_SCRIPT
        '''
        try:
            self.cmdline = [os.path.join(basedir, script_name)]
        except AttributeError:
            raise Cmd.INVALID_SCRIPT(script_name)

    def get_help(self):
        '''Creates and execute 'script_name --help', and ignores errors.'''
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
        '''Combine the script name (and path) with the arguments'''
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


class ScriptArgParser(argparse.ArgumentParser):  # ############################
        class HELP_REQUESTED(Exception):
            '''Indicates that -h or --help has been parsed

            See argparse.ArgumentParser.print_help()
            '''
            pass

        class INVALID_ARGUMENT(Exception):
            '''Indicates ArgParse has detected an error

            See argparse.ArgumentParser.error()
            '''
            pass

        def print_help(self, outfile=None):
            raise ScriptArgParser.HELP_REQUESTED

        def error(self, message):
            raise ScriptArgParser.INVALID_ARGUMENT(message)


class ScriptHelper:  # ########################################################
    '''Parse arguments, check conditions and execute the proper executable.

    Description:
        General functions and properties inherent to all scripts.
        Should never be directly instantiated, but instead should
        be a base class for other script classes.

    To-Do list to properly subclass:
        extend __init__ and define self.title and self.exe_filename
            super.__init__() should be called at the beginning
            exe_filename can be set to none if a function is defined
            called get_exe_filename()
        override parse_arguments(). See parse_common_args().
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
                exe_filename: filename of executable to be called
        Instance Variables:
            Logger: logs info, error, fatal and other messages (from logging).
            args: defined by parse_arguments().
            cmd: defined by build_cmd_line()
            config: defined by get_config_from_xml()
            parser: created by setup() and should be used
                by subclass's parse_arguments()

        Instance Variables defined by subprogram:
            title: A title that describes all executables in the class.
            exe_filename: Should be defined in __init__() if possible.
                Otherwise a function get_exe_filename should be defined
                that will determine which exe will be used.
            description: A description for all executables in the class.
        '''
        self.logger = logging.getLogger(__name__)
        self.args = None
        self.cmd = None
        self.config = None
        # Should be defined by sub-class
        self.title = 'Title Not Defined'
        self.exe_filename = 'Program Name not defined'
        self.description = 'Description not defined'
        # Attempt to Pre-Parse XML so satellite can be used in logic

    class NO_ACTION_REQUESTED(Exception):
        pass

    class INVALID_FILE(Exception):
        def __init__(self, name, recieved, *args):
            self.name = name
            self.recieved = recieved
            Exception.__init__(self, name, recieved, *args)

    class INVALID_SATELLITE_XML(Exception):
        '''Parsed file parameter does not meet specified format'''
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
        ''' Stores desired information into config(dict) from xml file

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
        # self.check_common_prereq(check_xml=True) Handled in metadata_api
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
            raise ScriptHelper.INVALID_SUBCLASS('is_landsat8 must be called'
                                                ' after get_config_from_xml')

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
    def parse_common_args(parser, xml=False, debug=False, verbose=False,
                          version=False):
        '''Allows common arguments to be added to the parser.

        Description:
            Should be used by subclass when overriding build_parser()
        Precondition:
            parser must be a valid argparse.ArgumentParser
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
        ''' Will only parse --xml XML_FILENAME from cmdline.

        See get_config_from_xml() and  get_exe_filename()
        Precondition:
            '--xml FILENAME' exists in command line arguments
        Postcondition:
            self.args.xml_filename exists
        '''

        # Try to parse out the XML so the exe can be determined
        parse_xml = ScriptArgParser(add_help=False)
        parse_xml = self.parse_common_args(parse_xml, xml=True)
        (temp, extra_args) = parse_xml.parse_known_args()

        if(list_ignored):
            print 'The following arguments were ignored:' + ''.join(extra_args)
        try:
            if(self.args is None):
                self.args = temp  # Args are empty. thus overwrite
            else:
                self.args.xml_filename = temp.xml_filename
        except:
            raise

        self.get_config_from_xml(self.args.xml_filename)
        self.get_exe_filename()
        return self.args.xml_filename

    def print_custom_help(self):
        ''' Used to override default help so underlying exe's help can be shown

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
            # Print only for ScriptHelper
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
            (1) self.get_exe_filename() returns a string that is the name of a
                script in the current working directory.
            (2) application exits with success
        Postcondition:
            returns output if (2) is met
            returns '' if (2) is failed
        Raises
            Cmd.INVALID_SCRIPT if (1) is failed
            Cmd.EXECUTE_ERROR if (2) is failed
        '''
        try:
            cmd = Cmd(self.get_exe_filename())
            cmd.add_param('--version')
            version_msg = cmd.execute()
            return version_msg
        except Cmd.INVALID_SCRIPT:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR:
            #  print('Application returned error when requesting --version')
            return ''  # If version can't be obtained then leave it empty
        else:
            raise

    # Error Cause
    def get_executables_help(self):
        '''Will execute 'exe_filename --help' and return response.

        Precondition:
            (1) self.get_exe_filename() returns a string that is the name of a
                script in the current working directory.
            (2) application exits with success
        Postcondition:
            returns output if (2) is met
            returns '' if (2) is failed
        Raises
            Cmd.INVALID_SCRIPT if (1) is failed
            Cmd.EXECUTE_ERROR if (2) is failed
        '''
        try:
            cmd = Cmd(self.get_exe_filename())
            help_msg = cmd.get_help()
            return help_msg
        except Cmd.INVALID_SCRIPT:
            raise ScriptHelper.EXECUTABLE_NOT_DEFINED
        except Cmd.EXECUTE_ERROR as e:
            #  print('Application returned error when requesting --help')
            return e.args[0]  # Message should contain Stdout, but also Stderr
        else:
            raise

    def check_common_prereq(self, check_xml=True):
        '''Allow easy way to check conditions that are commonly required for a script.

        Description:
        Raises:
            INVALID_FILE (Filetype/Description, received filename)
        '''
        if check_xml:
            # Verify that the XML filename provided is not an empty string
            if not os.path.isfile(self.args.xml_filename):
                raise Cmd.INVALID_FILE(name='XML', recieved=
                                       self.args.xml_filename
                                       )
        return True

    def get_execute_header(self):
        '''Return String describing action taken by execute().

        Precondition:
            self.args.xmlfilename exists
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

    def build_parser(self):
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

    def parse_arguments(self):  # SubClass should override.
        '''Stores arguments specified in build_parser() to self.args

            If '--help' or '-h' is specified as an argument the request is
            handled here. Invalid arguments will also show help along with
            error message.
        '''
        try:
            self.args = self.parser.parse_args()
        except ScriptArgParser.INVALID_ARGUMENT as e:
            self.print_custom_help()
            self.logger.error(e.args[0])  # Error message from ArgParse
            exit(1)
        except ScriptArgParser.HELP_REQUESTED:
            self.print_custom_help()
            exit(0)

    def get_exe_filename(self):  # SubClass should override.
        '''Should return a the name of the script.

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
        Understood exceptions:
            Any Exception class defined in ScriptHelper directly
        Return:
            exceptionHandled: returns False if the exception was not understood
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


class SWE(ScriptHelper):  # ###################################################
    '''Parse request, check conditions, execute appropriate executable

    SWE: Surface Water Extent
    Author: rdilley@usgs.gov
    File: surface_water_extent.py
    Source: https://github.com/USGS-EROS/espa-surface-water-extent
    Purpose: Master script for running scene-based surface water algorithm.
    Usage: See "do_dynamic_surface_water_extent.py --help"
    Dependencies: dswe
    Description:
    '''
    __title__ = 'Surface-Water-Extent'
    __version__ = '0.0.1 (June 2015)'

    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = 'dswe'
        self.title = 'Surface Water Extent'
        self.description = ("Build the command line and then kick-off the"
                            "Dynamic Surface Water Extent application")

    def build_parser(self):
        '''See ScriptHelper.build_parser() for more details'''
        self.parser = ScriptArgParser(description=self.description,
                                      add_help=True)
        # Required parameters
        self.parser = ScriptHelper.parse_common_args(self.parser, xml=True)
        self.parser.add_argument('--dem', action='store', dest='dem_filename',
                                 required=True,
                                 help="The DEM metadata file to use")
        # Additional parameters
        self.parser = ScriptHelper.parse_common_args(self.parser,
                                                     debug=True, verbose=True)

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
        self.cmd = Cmd(self.exe_filename)
        self.cmd.add_param("--xml", self.args.xml_filename)
        self.cmd.add_param("--dem", self.args.dem_filename)
        if self.args.verbose:
            self.cmd.add_param("--verbose")


class SI(ScriptHelper):  # ####################################################
    '''Parse request, check conditions, execute appropriate executable

    SI: Spectral Indices
    Author:  gschmidt@usgs.gov
    File: spectral_indices.py
    Source: https://github.com/USGS-EROS/espa-spectral-indices
    Purpose: Master script for creating spectral indices products.
    Usage: See "spectral_indices.py --help"
    Dependencies: spectral_indices
    Description:
        spectral_indices produces the desired spectral index products for the
        input surface reflectance or TOA reflectance bands. The options
        include: NDVI, EVI, SAVI, MSAVI, NDMI (also known as NDWI or NDII),
        NBR, and NBR2. The user may specify one, some, or all of the
        supported indices for output.
    '''
    __title__ = 'Spectral Indices'
    __version__ = '2.1.0'

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

    def build_parser(self):
        '''See ScriptHelper.build_parser() for more details'''
        self.parser = ScriptArgParser(description=self.description,
                                      add_help=True)
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

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
        # TODO - Replace with argparse group
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

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See ScriptHelper.handle_exception() for more details.
        See sys.exc_info() = [type,value,traceback]
        Description:
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        e_type = sys.exc_info()[0]
        # e = sys.exc_info()[1]
        if e_type is ScriptHelper.NO_ACTION_REQUESTED:
            self.logger.warning('NO_ACTION_REQUESTED:No SI product specified.')
            self.print_custom_help()
            return True
        return ScriptHelper.handle_exception(self)

    def get_executables_version(self):
        return '2.1.0'  # Hardcode Version
        # return ScriptHelper.get_executables_version(self)


class SR(ScriptHelper):  # ####################################################
    '''Parse request, check conditions, execute appropriate executable

    SR: Surface Reflectance
    Author:  gschmidt@usgs.gov
    File: surface-reflectance.py
    Purpose: https://github.com/USGS-EROS/espa-surface-reflectance
    PURPOSE: Master script for creating surface reflectance products.
    USAGE: See "surface-reflectance.py --help"
    Dependencies: do_ledaps.py, do_l8_sr.py
    Description:
    '''
    __title__ = 'Surface-Reflectance'
    __version__ = '0.0.1 (June 2015)'

    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = None  # Determined later in get_exe_filename()
        self.title = 'Surface Reflectance'
        self.description = ('''description_of_executable''')

    def build_parser(self):
        '''See ScriptHelper.build_parser() for more details'''
        self.parser = ScriptArgParser(description=self.description,
                                      add_help=True)
        # Required parameters
        self.parser = ScriptHelper.parse_common_args(self.parser, xml=True)
        # Additional parameters
        msg = ('Process the surface reflectance products; True or False'
               '(default is True) If False, then processing will halt after'
               'the TOA reflectance products are complete.')
        self.parser.add_argument('--process_sr', action='store',
                                 type=ScriptHelper.str_to_bool,
                                 dest='process_sr',
                                 required=True, help=msg, metavar='BOOL')
        try:
            self.parse_only_xml()
        except ScriptArgParser.INVALID_ARGUMENT:
            self.print_custom_help()

        if(self.get_exe_filename() == Cfmask.L8_exe):
            self.parser.add_argument('--write_toa',
                                     action='store_true', dest='write_toa',
                                     required=False, default=False,
                                     help="Write top of atmosphere"
                                     "")
        # Common command line arguments
        self.parser = ScriptHelper.parse_common_args(self.parser,
                                                     debug=False,
                                                     verbose=False)

    def get_exe_filename(self):
        ''' Uses get_config_from_xml to determine which exe to use.

        See ScriptHelper.get_exe_filename() for more details
        '''
        if self.args.xml_filename is None:
            self.parse_only_xml()
            print('self.args.xml_filename is None')
        if self.config is None:
            # Obtain Config from XML to know if satellite is L8 or not
            self.get_config_from_xml(self.args.xml_filename)
            print('self.config is None')

        if(ScriptHelper.is_landsat8(self.config)):
            self.exe_filename = 'do_l8_sr.py'
        else:
            self.exe_filename = 'do_ledaps.py'

        return self.exe_filename

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
        # self.args.process_sr = ScriptHelper.str_to_bool(self.args.process_sr)

        try:
            self.cmd = Cmd(self.get_exe_filename())
        except(Cmd.INVALID_SCRIPT):  # If exe_filename==None
            self.get_config_from_xml(self.args.xml_filename)
            self.get_exe_filename()
            self.cmd = Cmd(self.get_exe_filename())

        self.cmd.add_param("--xml", self.args.xml_filename)

        # Format of boolean depends on the recieving script.
        if self.args.process_sr:
            self.cmd.add_param("--process_sr", "True")
        else:
            self.cmd.add_param("--process_sr", "False")

        if(self.get_exe_filename() == Cfmask.L8_exe):
            if self.args.write_toa:
                self.cmd.add_param("--write_toa")

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See ScriptHelper.handle_exception() for more details.
        See sys.exc_info() for access to exception information.
        Description:
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        return ScriptHelper.handle_exception(self)


class Cfmask(ScriptHelper):  # ################################################
    '''Parse request, check conditions, execute appropriate executable

    CFMASK: Cloud Function Mask
    Author: rdilley@usgs.gov
    File: cfmask.py
    Source: https://github.com/USGS-EROS/espa-cloud-masking
    Purpose: Master script for creating cloud masking products.
    Usage: See "cfmask.py --help"
    Dependencies: cfmask, l8cfmask fillminima.py run_fillminima.py
    Description:
        Fmask identify the cloud, shadow, snow, water and clear pixels
        using the input Landsat scene (top of atmosphere (TOA)
        reflection and brightness temperature (BT) for band 10) output
        from LEDAPS
    '''
    __title__ = 'Cloud Function Mask'
    __version__ = '0.0.1 (June 2015)'

    L8_exe = 'l8cfmask'
    L457_exe = 'cfmask'

    def __init__(self):
        ScriptHelper.__init__(self)
        self.exe_filename = None  # Determined later in get_exe_filename()
        self.title = 'Cloud Function Mask'
        self.description = ('''Fmask identify the cloud, shadow, snow, water and clear pixels using
        the input Landsat scene (top of atmosphere (TOA) reflection and
        brightness temperature (BT) for band 6) output from LEDAPS''')

    def build_parser(self):
        '''See ScriptHelper.build_parser() for more details'''
        self.parser = ScriptArgParser(description=self.description,
                                      add_help=True)
        # Required parameters
        self.parser = ScriptHelper.parse_common_args(self.parser, xml=True)
        # Additional parameters
        self.parser.add_argument('--prob', action='store',
                                 dest='prob',
                                 required=False,
                                 help='cloud_probability',
                                 )
        self.parser.add_argument('--cldpix', action='store',
                                 dest='cldpix',
                                 required=False,
                                 help='cloud_pixel_buffer for image dilate',
                                 )
        self.parser.add_argument('--sdpix', action='store',
                                 dest='sdpix',
                                 required=False,
                                 help='cloud_pixel_buffer for image dilate',
                                 )
        self.parser.add_argument('--max_cloud_pixels', action='store',
                                 dest='max_cloud_pixels',
                                 required=False,
                                 help='maximum_cloud_pixel_number for cloud'
                                      ' division',
                                 )
        try:
            self.parse_only_xml()
        except ScriptArgParser.INVALID_ARGUMENT:
            self.print_custom_help()

        if(self.get_exe_filename() == Cfmask.L8_exe):
            msg = ("Should Landsat 8 QA band cirrus bit info be used in cirrus"
                   " cloud detection? (If not specified means Bonston"
                   " University's dynamic cirrus band static threshold will be"
                   " used)")
            self.parser.add_argument('--use_l8_cirrus', action='store_true',
                                     dest='use_l8_cirrus',
                                     required=False,
                                     help=msg
                                     )
        # Common command line arguments
        self.parser = ScriptHelper.parse_common_args(self.parser,
                                                     debug=False, verbose=True)

    def get_exe_filename(self):
        '''Uses config read from XML to determine executable

        Assumes: self.config exists from calling get_config_from_xml()
        Raises: ScriptHelper.EXECUTABLE_NOT_DEFINED
        '''
        if self.args.xml_filename is None:
            self.parse_only_xml()
            print('self.args.xml_filename is None')
        if self.config is None:
            # Obtain Config from XML to know if satellite is L8 or not
            self.get_config_from_xml(self.args.xml_filename)
            print('self.config is None')

        if(ScriptHelper.is_landsat8(self.config)):
            self.exe_filename = Cfmask.L8_exe
        else:
            self.exe_filename = Cfmask.L457_exe
        return self.exe_filename

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''
        if self.args.xml_filename is None:
            self.parse_only_xml()
        if self.config is None:
            self.get_config_from_xml(self.args.xml_filename)
        try:
            self.cmd = Cmd(self.get_exe_filename())
        except(Cmd.INVALID_SCRIPT):  # Will raise if exe_filename=None
            self.get_config_from_xml(self.args.xml_filename)
            self.get_exe_filename()
            self.cmd = Cmd(self.get_exe_filename())

        self.cmd.add_param("--xml", self.args.xml_filename)

        if self.args.prob is not None:
            self.cmd.add_param("--prob", self.args.prob)

        if self.args.cldpix is not None:
            self.cmd.add_param("--cldpix", self.args.cldpix)

        if self.args.sdpix is not None:
            self.cmd.add_param("--sdpix", self.args.sdpix)

        if self.args.max_cloud_pixels is not None:
            self.cmd.add_param("--max_cloud_pixels",
                               self.args.max_cloud_pixels)

        if self.get_exe_filename() is Cfmask.L8_exe:
            if self.args.use_l8_cirrus:
                self.cmd.add_param("--use_l8_cirrus", self.args.use_l8_cirrus)

        if self.args.verbose:
            self.cmd.add_param("--verbose")

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See ScriptHelper.handle_exception() for more details.
        See sys.exc_info() for access to exception information.
        Description:
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        return ScriptHelper.handle_exception(self)


def main():
    logger = get_logger()

    script = SI()
    try:
        script.run()
    except Cmd.EXECUTE_ERROR as e:
        logger.exception(("Error running {0}."
                          "Processing will terminate."
                          ).format(script.title))
        try:
            logger.info(e.args[0])
        except NameError:  # No Message
            pass
        raise


if __name__ == '__main__':
    main()


""" Template for creating a subclass of ScriptHelper
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
        parser = ScriptHelper.parse_common_args(parser, xml=True)
        # Additional parameters
        parser.add_argument("--cmdline_name", dest="args_name", default=False,
                            action="store_true",
                            help="help"
                                 "even_more_help")
        # Common command line arguments
        parser = ScriptHelper.parse_common_args(parser,
                                                debug=False, verbose=False)

    def build_cmd_line(self):
        '''See ScriptHelper.build_cmd_line() for more details'''

        self.cmd = Cmd(self.exe_filename)
        self.cmd.add_param("--argument_with_param", self.args.xml_filename)

        if self.args.boolean:
            self.cmd.add_param("--some_flag")

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

