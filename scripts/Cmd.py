'''
Author: ngenetzky@usgs.gov
    Based on code from execute_cmd() by rdilley@usgs.gov
'''
import commands
import os


class Cmd:  # #################################################################
    '''Builds and executes command line statements

    Description:
        Encompasses all of the functions associated with building and
        executing command line arguments. By using this class with each script
        it ensures consistency in the way that that command line is produced.
    Usage:
        # __init__(EXECUTABLE_NAME, DIRECTORY)
        cmdExecutable = Cmd('my_executable_name')
        # add_param(PARAMERTER_NAME,PARAMETER_VALUE)
        cmdExecutable.add_param('--xml', 'my_xml.xml')
        # Will use commands.getstatusoutput to execute built cmd-line
        cmdExecutable.execute()
    '''

    class EXECUTE_ERROR(Exception):
        def __init__(self, message, *args):
            self.message = message
            Exception.__init__(self, message, *args)

    class INVALID_EXECUTABLE(Exception):
        def __init__(self, executable_name, *args):
            self.executable_name = executable_name
            Exception.__init__(self, self.executable_name, *args)
        pass

    def __init__(self, executable_name, basedir=''):
        '''Setup the base of the cmdline with required directory and script name.

        Parameters:
            executable_name: Name of the executable
            basedir: Location of the executable
        Raises:
            INVALID_EXECUTABLE
        '''
        try:
            self.cmdline = [os.path.join(basedir, executable_name)]
        except AttributeError:
            raise Cmd.INVALID_EXECUTABLE(executable_name)

    def get_help(self):
        '''Create and execute 'executable_name --help', and ignore errors.'''
        cmd_string = self.cmdline[0] + ' --help'
        (status, output) = commands.getstatusoutput(cmd_string)
        return output

    def add_param(self, name, *arg):
        '''Allows a parameter to be added; optionally with an argument

        Parameters:
            name: Name of argument preceeded with "--" or "-" if desired.
            args: Additional argument to place after name
        '''
        self.cmdline.append(name)
        self.cmdline.append(arg)

        # to support multiple args: ' '.join(arg for arg in args if arg)

    def __repr__(self):
        '''Combine the executable name (and path) with the arguments'''
        return ' '.join(self.cmdline)

    def __str__(self):
        '''Combine the executable name (and path) with the arguments'''
        return self.__repr__()

    def execute(self):
        '''Execute a command line and return the terminal output

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


