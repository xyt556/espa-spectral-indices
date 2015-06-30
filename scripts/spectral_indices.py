#! /usr/bin/env python
'''
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
import commands
import metadata_api
from Cmd import Cmd
from ScriptHelper import ScriptHelper, ScriptArgParser


def get_logger():

    # Setup the Logger with the proper configuration
    logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                ' %(levelname)-8s'
                                ' %(filename)s:%(lineno)d:'
                                '%(funcName)s -- %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


class SI(ScriptHelper):  # ####################################################
    '''Parse request, build command line and return output from executable.
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
        self.parser = ScriptHelper.add_common_args(self.parser, xml=True)

        # Additional parameters
        self.parser.add_argument('--toa', dest='toa', default=False,
                                 action='store_true',
                                 help='process TOA bands'
                                 ' instead of surface reflectance bands')

        self.parser.add_argument('--ndvi', dest='ndvi', default=False,
                                 action='store_true',
                                 help='process NDVI'
                                 '(normalized difference vegetation index)')

        self.parser.add_argument('--ndmi', dest='ndmi', default=False,
                                 action='store_true',
                                 help='process NDMI'
                                 '(normalized difference moisture index)')

        self.parser.add_argument('--nbr', dest='nbr', default=False,
                                 action='store_true',
                                 help=('process NBR'
                                       '(normalized burn ratio)'))

        self.parser.add_argument('--nbr2', dest='nbr2', default=False,
                                 action='store_true',
                                 help='process NBR2'
                                 '(normalized burn ratio2)')

        self.parser.add_argument('--savi', dest='savi', default=False,
                                 action='store_true',
                                 help='process SAVI'
                                 '(soil adjusted vegetation index)')

        self.parser.add_argument('--msavi', dest='msavi', default=False,
                                 action='store_true',
                                 help='process modified SAVI'
                                 '(soil adjusted vegetation index)')

        self.parser.add_argument('--evi', dest='evi', default=False,
                                 action='store_true',
                                 help='process EVI'
                                 '(enhanced vegetation index)')

        # Common command line arguments
        self.parser = ScriptHelper.add_common_args(self.parser,
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
        self.cmd.add_param('--xml', self.args.xml_filename)

        if self.args.verbose:
            self.cmd.add_param('--verbose')
        if self.args.toa:
            self.cmd.add_param('--toa')
        if self.args.ndvi:
            self.cmd.add_param('--ndvi')
        if self.args.ndmi:
            self.cmd.add_param('--ndmi')
        if self.args.nbr:
            self.cmd.add_param('--nbr')
        if self.args.nbr2:
            self.cmd.add_param('--nbr2')
        if self.args.savi:
            self.cmd.add_param('--savi')
        if self.args.msavi:
            self.cmd.add_param('--msavi')
        if self.args.evi:
            self.cmd.add_param('--evi')

    def handle_exception(self):
        '''Will handle any exception that the ScriptHelper understands.

        See ScriptHelper.handle_exception() for more details.
        See sys.exc_info() = [type,value,traceback]
        Description:
        Return:
            exceptionHandled: returns False if the exception was not understood
        '''
        e_type = sys.exc_info()[0]
        if e_type is ScriptHelper.NO_ACTION_REQUESTED:
            self.print_custom_help()
            self.logger.warning('NO_ACTION_REQUESTED:No SI product specified.')
            return True
        return ScriptHelper.handle_exception(self)

    def get_executables_version(self):
        return SI.__version__  # Hardcode Version
        # return ScriptHelper.get_executables_version(self)


def main():
    logger = get_logger()

    script = SI()
    try:
        script.run()
    except Cmd.EXECUTE_ERROR as e:
        logger.exception(('Error running {0}.'
                          'Processing will terminate.'
                          ).format(script.title))
        try:
            logger.info(e.args[0])
        except NameError:  # No Message
            pass
        raise

script = None
if __name__ == '__main__':
    main()

