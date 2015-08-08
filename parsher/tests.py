import os
import unittest
from parsher import BashScript
import sys


class test_all(unittest.TestCase):
    def prep(self, string):
        self.maxDiff = None
        path = './test_data'
        f = open(path, 'w')
        f.write(string)
        f.close()
        return BashScript(path)

    def test_simple_token(self):
        string = "somecommand"
        bashScript = self.prep(string)
        self.assertEquals([string], bashScript.commands)

    def test_multiple_tokens(self):
        string = "somecommand some@arg.with/symbols/foo.bar"
        bashScript = self.prep(string)
        self.assertEquals([string], bashScript.commands)

    def test_variable_assignment_no_command(self):
        string = "VAR=VALUE"
        bashScript = self.prep(string)
        self.assertEquals([string.split('=')], bashScript.vars)

    def test_variable_export(self):
        string = "export VAR=VALUE"
        bashScript = self.prep(string)
        self.assertEquals([['VAR', 'VALUE']], bashScript.vars)
        self.assertEquals([], bashScript.commands)

    def test_variable_export_multiple(self):
        string = "export VAR1=VAL1\nexport VAR2=VAL2\nexport VAR3=VAL3"
        bashScript = self.prep(string)
        self.assertEquals([['VAR1', 'VAL1'], ['VAR2', 'VAL2'], ['VAR3', 'VAL3']], bashScript.vars)
        self.assertEquals([], bashScript.commands)

    def test_variable_export_mutliple_with_command(self):
        string = "export VAR1=VAL1\nexport VAR2=VAL2\nexport VAR3=VAL3\nSomeCommand"
        bashScript = self.prep(string)
        self.assertEquals([['VAR1', 'VAL1'], ['VAR2', 'VAL2'], ['VAR3', 'VAL3']], bashScript.vars)
        self.assertEquals(['export', 'export', 'export', 'SomeCommand'], bashScript.commands)

    def test_variable_export_mutliple_with_command(self):
        string = "VAR1=VAL1 VAR2=VAL2 VAR3=VAL3 SomeCommand"
        bashScript = self.prep(string)
        self.assertEquals([['VAR1', 'VAL1'], ['VAR2', 'VAL2'], ['VAR3', 'VAL3']], bashScript.vars)
        self.assertEquals(['SomeCommand'], bashScript.commands)

    def test_semicolons_and_lstrip(self):
        string = "export VAR1=VAL1;; export VAR2=VAL2;\n\nexport VAR3=VAL3;SomeCommand"
        bashScript = self.prep(string)
        self.assertEquals([['VAR1', 'VAL1'], ['VAR2', 'VAL2'], ['VAR3', 'VAL3']], bashScript.vars)
        self.assertEquals(['SomeCommand'], bashScript.commands)

    def test_spaces_in_quoted_vars(self):
        string = 'export MAVEN_ARGS="-Dgpg.skip=true ' + \
                 '-Dmaven.javadoc.skip=true ' + \
                 '-DaltSnapshotDeploymentRepository=SomeCompany-SomeNexus::default::https://this.was.a/url/to/nexus/snapshots ' + \
                 '-DaltDeploymentRepository=SomeCompany-Nexus::default::https://another.nexus.url/nexus/content/repositories/snapshots" ' + \
                 'export SOME_ENV_VAR="SOME QUOTED VAL" ' + \
                 'someCommand'
        bashScript = self.prep(string)
        self.assertEquals([['MAVEN_ARGS', '"-Dgpg.skip=true ' + \
                            '-Dmaven.javadoc.skip=true ' + \
                            '-DaltSnapshotDeploymentRepository=SomeCompany-SomeNexus::default::https://this.was.a/url/to/nexus/snapshots ' + \
                            '-DaltDeploymentRepository=SomeCompany-Nexus::default::https://another.nexus.url/nexus/content/repositories/snapshots"'],
                           ['SOME_ENV_VAR', '"SOME QUOTED VAL"']], bashScript.vars)

        self.assertEquals(['someCommand'], bashScript.commands)

    def test_escaped_newlines(self):
        string = 'VAR=VALUE \\\n somecommand'
        bashScript = self.prep(string)
        self.assertEquals([['VAR', 'VALUE']], bashScript.vars)
        self.assertEquals(['somecommand'], bashScript.commands)

    def test_inside_function(self):
        string = 'somefun () {\n var="quoted_value"\n} \nVAR2=VALUE'
        bashScript = self.prep(string)
        self.assertEquals([["VAR2","VALUE"]], bashScript.vars)
        self.assertEquals(['somefun () {\n var="quoted_value"\n}'], bashScript.commands)


if __name__ == '__main__':
    unittest.main()
