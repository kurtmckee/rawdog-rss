# runtests.py - Run unit tests against the rawdog rss.py plugin
# Copyright (C) 2009 Kurt McKee <contactme@kurtmckee.org>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from os.path import abspath, dirname, join, splitext
import sys
import unittest
import xml.sax

from rawdoglib.rawdog import main

basedir = dirname(abspath(__file__))

class Handler(xml.sax.handler.ContentHandler, xml.sax.handler.ErrorHandler):
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self.errors = False
    def warning(self, exception):
        self.errors = True
        return
    error = warning
    fatalError = warning

class TestCases(unittest.TestCase):
    def setUp(self):
        # Rawdog changes the current working directory
        global basedir
        os.chdir(basedir)
        # The output directory needs to be clean
        path = join(basedir, 'output/')
        
        for r, d, filenames in os.walk(path):
            for filename in filenames:
                if filename != "config":
                    os.remove(join(path, filename))
            # There should be no need to traverse any other directories
            break
    def tearDown(self):
        pass

    def worker(self, testfile):
        global basedir
        # Create output files for comparison
        testpath = join(basedir, 'tests/')
        outpath = join(basedir, 'output/')
        if 'feed' in testfile:
            main(['-d', outpath, '-c', join(testpath, testfile), '-uw'])
        else:
            main(['-d', outpath, '-c', join(testpath, testfile), '-w'])
        # Parse the files and make sure they don't throw errors
        for f in ('foafroll.xml', 'opml.xml', 'rss20.xml'):
            handler = Handler()
            parser = xml.sax.make_parser()
            parser.setContentHandler(handler)
            parser.setErrorHandler(handler)
            parser.parse(join(outpath, f))
            self.assertFalse(handler.errors)

def make_testcase(testfile):
    # HACK: Only necessary in order to ensure that `evals` is evaluated
    # for every testcase, not just for the last one in the loop below
    # (where, apparently, `lambda` would cause it to be evaluated only
    # once at the end of the loop, containing the final testcase' values).
    return lambda self: self.worker(testfile)

testpath = join(basedir, 'tests/')
# files contains a list of relative paths to test files
# HACK: replace() is only being used because os.path.relpath()
# was only added to Python in version 2.6
files = (join(r, f).replace(testpath, '', 1)
            for r, d, files in os.walk(testpath)
            for f in files if f.endswith('.ini'))
for testfile in files:
    description = ''
    evals = []
    openfile = open(join(testpath, testfile))
    for line in openfile:
        line = line.strip()
        if not line.startswith('#'):
            break
        if 'Description:' in line:
            description = line.split('Description:')[1].strip()
        if 'Eval:' in line:
            evals.append(line.split('Eval:')[1].strip())
    openfile.close()
    if not description:
        raise ValueError("Description not found in test %s" % testfile)
    #if not evals:
    #    raise ValueError("No Eval found in test %s" % testfile)
    else:
        testcase = make_testcase(testfile)
        testcase.__doc__ = '%s: %s' % (testfile, description)
        setattr(TestCases, 'test_%s' % splitext(testfile)[0], testcase)

testsuite = unittest.TestLoader().loadTestsFromTestCase(TestCases)
unittest.TextTestRunner(verbosity=2).run(testsuite)
