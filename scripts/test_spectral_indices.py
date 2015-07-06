#! /usr/bin/env python
'''
Created on Jun 25, 2015

@author: ngenetzky
'''
import unittest
import sys
import itertools
from Cmd import Cmd


class S:
    ''' String Resource Class
    '''
    MORE_HELP = 'For additional help specify the xml with the help parameter'
    EXE_HELP = 'Help from executables under this script:'
    SI_COMPLETE = 'Spectral indices processing complete'


def script_constructor():
    import spectral_indices
    return spectral_indices.SI()


def script_name():
    return "spectral_indices.py"


def verify_output(self, out, has_more_help=False, has_exe_help=False):
    if(has_more_help):
        assert S.MORE_HELP in out
    if(has_exe_help):
        assert S.EXE_HELP in out


class Test_prints_help_no_error(unittest.TestCase):
    def __init__(self):
        self.verify_output = verify_output

    def test_h(self):
        command = Cmd(script_name())
        command.add_param('-h')
        output = command.execute()
        self.verify_output(output, has_exe_help=True)

    def test_help(self):
        command = Cmd(script_name())
        command.add_param('--help')
        output = command.execute()
        self.verify_output(output, has_exe_help=True)


class Test_help_with_error(unittest.TestCase):
    def __init__(self):
        self.verify_output = verify_output

    def test_empty_cmdline(self):
        command = Cmd(script_name())
        with self.assertRaises(Cmd.EXECUTE_ERROR):
            output = command.execute()
            self.verify_output(output, has_exe_help=True)


class Test_SI_output_files(unittest.TestCase):
    def __init__(self):
        self.si_products = ['toa', 'ndvi', 'evi',
                            'savi', 'msavi', 'ndmi',
                            'nbr', 'nbr2']
        self.verify_output = verify_output

        self.product_comb = []
        for L in range(0, len(self.si_products)+1):
            for one_comb in itertools.combinations(self.si_products, L):
                self.product_comb.append(one_comb)

    def test_nbr(self):
        command = Cmd(script_name())
        command.add_param('--nbr')
        output = command.execute()
        assert '--nbr' in output


    def test_all_products(self):
        command = Cmd(script_name())
        for comb in self.product_comb:
            for item in comb:
                self.command.add_param(item)
            command.execute()

""" In progress:



class Test_cli_help(unittest.TestCase):
    ''' Does the script show the correct help message (simple or extended)?

    Purpose: Checks that the expected help message is displaying for various
     use cases that involve help.
    '''
    def setUp(self):
        import StringIO
        self.saved_stdout = sys.stdout
        self.saved_stderr = sys.stderr
        self.out = StringIO.StringIO()
        self.err = StringIO.StringIO()
        sys.stdout = self.out
        sys.stderr = self.err

    def get_script(self):
        ScriptHelper.SI()

    def check_help_xml(self, xml_filename):
        '''Test --help --xml xml_filename'''
        sys.argv[1:] = ['--help', '--xml', xml_filename]
        with self.assertRaises(SystemExit) as cm:
            ScriptHelper.main()

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)  # Exit with success

    def test_base_command(self):
        '''Test with no argv. 

        Expect error: --xml is required and  exit with error
        '''
        sys.argv[1:] = ['']
        with self.assertRaises(SystemExit) as cm:
            ScriptHelper.main()

        self.assertIn(S.MORE_HELP, self.out.getvalue())
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 1)  # Exit with error

    def test_h_command(self):
        '''script --help

        Ensures that MORE_HELP message is shown but EXE_HELP is not.
        '''
        sys.argv[1:] = ['-h']
        with self.assertRaises(SystemExit) as cm:
            ScriptHelper.main()
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)  # Exit with success

        self.assertIn(S.MORE_HELP, self.out.getvalue())
        self.assertNotIn(S.EXE_HELP, self.out.getvalue())

    def test_help_command(self):
        '''script --help

        Ensures that MORE_HELP message is shown but EXE_HELP is not.
        '''
        sys.argv[1:] = ['--help']
        with self.assertRaises(SystemExit) as cm:
            ScriptHelper.main()
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)  # Exit with success

        self.assertIn(S.MORE_HELP, self.out.getvalue())
        self.assertNotIn(S.EXE_HELP, self.out.getvalue())

    def test_help_xml_l5(self):
        '''Test --help --xml LT5*'''
        self.check_help_xml('LT50460282002298LGS01.xml')

    def test_help_xml_l8(self):
        '''Test --help --xml LC8*'''
        self.check_help_xml('LC80730112013165LGN00.xml')

    def tearDown(self):
        sys.stdout = self.saved_stdout
        sys.stderr = self.saved_stderr
"""

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

