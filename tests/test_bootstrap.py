from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch, call
from tools import bootstrap


def process(rc=0, stdout=''):
    return subprocess.CompletedProcess([],rc,stdout,'')


class BootstrapSafetyTests(unittest.TestCase):
    @patch('tools.bootstrap.maybe_install')
    @patch('tools.bootstrap.git_run')
    def test_existing_origin_is_never_replaced(self, g, tools):
        tools.return_value = 'git'
        g.side_effect = [process(0, str(bootstrap.ROOT)), process(0, 'git@github.com:example/existing.git')]
        bootstrap.ensure_github()
        self.assertEqual(tools.call_count,1)  # Does not even need gh
        self.assertEqual(g.call_count,2)

    @patch('tools.bootstrap.maybe_install')
    @patch('tools.bootstrap.git_run')
    def test_nested_git_repo_does_not_modify_parent(self, g, tools):
        tools.return_value = 'git'
        g.return_value = process(0, str(bootstrap.ROOT.parent))
        bootstrap.ensure_github()
        self.assertEqual(g.call_count,1)

    @patch('tools.bootstrap.gh_output')
    @patch('tools.bootstrap.run')
    @patch('tools.bootstrap.maybe_install')
    @patch('tools.bootstrap.git_run')
    def test_account_mismatch_cannot_publish(self, g, tools, tool_run, gh_output):
        tools.side_effect = ['git','gh']
        g.side_effect = [process(1), process(0), process(1)]
        tool_run.return_value = process(0)
        gh_output.return_value = 'unexpected-account'
        bootstrap.ensure_github()
        self.assertEqual(g.call_count,3)
        self.assertFalse(any('repo' in str(x.args) and 'create' in str(x.args) for x in tool_run.call_args_list))

    def test_start_files_present(self):
        self.assertTrue((bootstrap.ROOT/'URUCHOM_AUCTIONHAMMER.bat').is_file())
        self.assertTrue((bootstrap.ROOT/'launch_auctionhammer.py').is_file())
        self.assertTrue((bootstrap.ROOT/'AUCTIONHAMMER_MASTER.md').is_file())

if __name__=='__main__':
    unittest.main()
