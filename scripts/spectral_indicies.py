'''
Created on Jun 4, 2015

@author: ngenetzky@usgs.gov


Possible future additions:
    1. Allow use of use BIN environment variable as the location of application.
    2. Allow a log file to be specified.
'''

import sys
import os
import argparse
import logging
import commands
try:
    import metadata_api
except:
    pass

class Cmd:
    """Cmd is a class that encompasses all of the functions 
    associated with building and executing command line arguments. 
    By using this class with each script it ensures consistency in 
    the way that that command line is produced.
    Usage:
    __init__(SCRIPTNAME, DIRECTORY)
    addParam(PARAMERTER_NAME,PARAMETER_VALUE)
    execute()
    """
    # Script Names
    def __init__(self,script_name,basedir=''):
        self.cmdline = [basedir+script_name]

    def addParam(self,name,arg1=''):
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
        output = ''
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
    ARG_XML = (['var','xml_filename'],
                   ['help','The XML metadata file to use'],
                   ['short','f'],
                   ['long','xml']   )
    def __init__(self):
        self.logger = ScriptHelper.getLogger()
        self.args = None
        self.cmd = None
        self.title = 'Title Not Defined' #Should be defined by sub-class
        self.programName = 'Program Name not defined' #Should be defined by sub-class
    def main(self):
        self.parse_arguments()
        if(self.check_prereq()):
            self.build_cmd_line()
            self.execute()
            sys.exit(ScriptHelper.SUCCESS())
        else:
            sys.exit(ScriptHelper.FAILURE())
        
    @staticmethod
    def isLansat8(xml_filename):
        '''
        Reads XML file for satellite and instrument type and determines the configuration.
        Output: Lzrd.CONFIG (enum-like) of base type (string)
        Expects the following contents in the xml:
        "...
        <global_metadata>
            ...
            <satellite>LANDSAT_8</satellite>
            <instrument>OLI_TIRS</instrument>
            ...
        ..."
        '''
        #xml = metadata_api.parse(xml_filename, silence=True)
        #global_metadata = xml.get_global_metadata()
        #satellite = global_metadata.get_satellite()
            #instrument = global_metadata.get_instrument()
        satellite = 'LANSAT_8'
        if (satellite == 'LANSAT_8'):
            return True
        else:
            return False
    @staticmethod
    def getLogger():
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
    def parseCommonArgs(parser, xml=True, debug=False, verbose=False):
        if(xml):
            parser.add_argument('--xml',
                action='store', dest='xml_filename', required=True,
                help='The XML metadata file to use', metavar='FILE')
        if(debug):
            parser.add_argument('--debug',
                            action='store_true', dest='debug',
                            required=False, default=False,
                            help="Keep any debugging data")
        if(verbose):
            parser.add_argument('--verbose',
                            action='store_true', dest='verbose',
                            required=False, default=False,
                            help=("Should intermediate messages be printed?"
                                  " (default value is False)"))
        return parser
    
    def checkCommonPreReq(self):
        # Verify that the XML filename provided is not an empty string
        if self.args.xml_filename == '':
            self.logger.fatal("No XML metadata filename provided.")
            self.logger.fatal("Error processing LST.  Processing will terminate.")
            sys.exit(self.FAILURE())
            
    @staticmethod
    def getBINdir():
        # get the BIN dir environment variable
        bin_dir = os.environ.get('BIN')
        bin_dir = bin_dir + '/'
        # msg = 'BIN environment variable: %s' % bin_dir
        # logIt (msg, log_handler)
        return bin_dir
    def get_execute_header(self):
        print('''{0} is processing Landsat file ({1}).
        The command line argument:{2} 
        ''' .format(self.title,
                    self.args.xml_filename,
                    self.cmd.getCmdline()
                    ))
        
    def execute(self):
        header = self.get_execute_header();
        self.logger.info(header)
        print(header)
        output = ''
        try:
            output = self.cmd.execute()
        except Exception, e:
            self.logger.exception("Error running {0}.  Processing will terminate.".format(self.title))
            sys.exit(ScriptHelper.FAILURE())
        finally:
            if len(output) > 0:
                self.logger.info("STDOUT/STDERR Follows: {0}".format(output))
        self.logger.info("Completion of {0}".format(self.title))
            
    # Not Implemented.
    def check_prereq(self):
        return True
    def parse_arguments(self):
        pass
    def build_cmd_line(self):
        pass
        
class DSWE(ScriptHelper):
    def __init__(self):
        ScriptHelper.__init__(self)
        self.programName= 'dswe'
        self.title = 'Surface Water Extent'
        self.description = ("Build the command line and then kick-off the Dynamic" 
                       " Surface Water Extent application")
    def parse_arguments(self):
        # Create a command line argument parser
        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        parser.add_argument('--dem',
            action='store', dest='dem_filename', required=True,
            help="The DEM metadata file to use")
        # Additional parameters
        parser.add_argument('--verbose',
            action='store_true', dest='verbose', default=False,
            help=("Should intermediate messages be printed?"
                  " (default value is False)"))
        # Common args
        parser = ScriptHelper.parseCommonArgs(parser, xml=True, debug=True, verbose=False)
        
        # Parse the command line parameters
        self.args = parser.parse_args()
        
    def build_cmd_line(self):
        self.cmd = Cmd(self.programName)
        self.cmd.addParam("--xml", self.args.xml_filename)
        self.cmd.addParam("--dem", self.args.dem_filename)   
        if(self.args.verbose==True):
             self.cmd.addParam("--verbose")
             
class SI(ScriptHelper):
    # Removed Log file argument
    # Removed usebin argument
    def __init__(self):
        ScriptHelper.__init__(self)
        self.programName__= 'spectral_indices'
        self.title = 'Spectral Indices'
        self.description = ("")
    def parse_arguments(self):
        # Create a command line argument parser
        parser = argparse.ArgumentParser(description=self.description)
        # Required parameters
        # Additional parameters
        parser.add_argument ("--toa", dest="toa", default=False,
            action="store_true",
            help="process TOA bands instead of surface reflectance bands")
        parser.add_argument ("--ndvi", dest="ndvi", default=False,
            action="store_true",
            help="process NDVI (normalized difference vegetation index")
        parser.add_argument ("--ndmi", dest="ndmi", default=False,
            action="store_true",
            help="process NDMI (normalized difference moisture index")
        parser.add_argument ("--nbr", dest="nbr", default=False,
            action="store_true",
            help="process NBR (normalized burn ratio")
        parser.add_argument ("--nbr2", dest="nbr2", default=False,
            action="store_true",
            help="process NBR2 (normalized burn ratio2")
        parser.add_argument ("--savi", dest="savi", default=False,
            action="store_true",
            help="process SAVI (soil adjusted vegetation index")
        parser.add_argument ("--msavi", dest="msavi", default=False,
            action="store_true",
            help="process modified SAVI (soil adjusted vegetation index")
        parser.add_argument ("--evi", dest="evi", default=False,
            action="store_true",
            help="process EVI (enhanced vegetation index")    
        # Common command line arguments
        parser = ScriptHelper.parseCommonArgs(parser, xml=True, debug=False, verbose=True)
        # Parse the command line parameters
        self.args = parser.parse_args()
        
    def build_cmd_line(self):
        self.cmd = Cmd(self.programName)
        self.cmd.addParam("--xml", self.args.xml_filename)
        self.cmd.addParam("--dem", self.args.dem_filename) 
        
        if(self.args.verbose==True):
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
    #script = DSWE()
    script = SI()
    
    script.parse_arguments()
    if(script.check_prereq()):
        script.build_cmd_line()
        script.execute()
        sys.exit(ScriptHelper.SUCCESS())
    else:
        sys.exit(ScriptHelper.FAILURE())
