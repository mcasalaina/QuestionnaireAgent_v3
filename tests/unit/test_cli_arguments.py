#!/usr/bin/env python3
"""
Unit tests for command line argument parsing in run_app.py
"""

import sys
import os
import unittest
from unittest.mock import patch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCLIArguments(unittest.TestCase):
    """Test command line argument parsing for run_app.py"""
    
    def test_parse_arguments_defaults(self):
        """Test that default arguments are set correctly."""
        from run_app import parse_arguments
        
        with patch('sys.argv', ['run_app.py']):
            args = parse_arguments()
            
            self.assertEqual(args.context, "Microsoft Azure AI")
            self.assertEqual(args.charlimit, 2000)
            self.assertIsNone(args.question)
            self.assertIsNone(args.spreadsheet)
    
    def test_parse_arguments_context(self):
        """Test parsing --context argument."""
        from run_app import parse_arguments
        
        with patch('sys.argv', ['run_app.py', '--context', 'Custom Context']):
            args = parse_arguments()
            
            self.assertEqual(args.context, "Custom Context")
            self.assertEqual(args.charlimit, 2000)  # default unchanged
    
    def test_parse_arguments_charlimit(self):
        """Test parsing --charlimit argument."""
        from run_app import parse_arguments
        
        with patch('sys.argv', ['run_app.py', '--charlimit', '3000']):
            args = parse_arguments()
            
            self.assertEqual(args.context, "Microsoft Azure AI")  # default unchanged
            self.assertEqual(args.charlimit, 3000)
    
    def test_parse_arguments_question(self):
        """Test parsing --question argument."""
        from run_app import parse_arguments
        
        with patch('sys.argv', ['run_app.py', '--question', 'What is Azure AI?']):
            args = parse_arguments()
            
            self.assertEqual(args.question, "What is Azure AI?")
            self.assertIsNone(args.spreadsheet)
    
    def test_parse_arguments_spreadsheet(self):
        """Test parsing --spreadsheet argument."""
        from run_app import parse_arguments
        
        with patch('sys.argv', ['run_app.py', '--spreadsheet', './tests/sample.xlsx']):
            args = parse_arguments()
            
            self.assertEqual(args.spreadsheet, "./tests/sample.xlsx")
            self.assertIsNone(args.question)
    
    def test_parse_arguments_all_options(self):
        """Test parsing all arguments together."""
        from run_app import parse_arguments
        
        with patch('sys.argv', [
            'run_app.py',
            '--context', 'Test Context',
            '--charlimit', '1500',
            '--question', 'Test Question'
        ]):
            args = parse_arguments()
            
            self.assertEqual(args.context, "Test Context")
            self.assertEqual(args.charlimit, 1500)
            self.assertEqual(args.question, "Test Question")
            self.assertIsNone(args.spreadsheet)
    
    def test_parse_arguments_spreadsheet_with_context(self):
        """Test parsing spreadsheet with context options."""
        from run_app import parse_arguments
        
        with patch('sys.argv', [
            'run_app.py',
            '--context', 'Azure Services',
            '--charlimit', '2500',
            '--spreadsheet', './tests/questionnaire.xlsx'
        ]):
            args = parse_arguments()
            
            self.assertEqual(args.context, "Azure Services")
            self.assertEqual(args.charlimit, 2500)
            self.assertEqual(args.spreadsheet, "./tests/questionnaire.xlsx")
            self.assertIsNone(args.question)


if __name__ == '__main__':
    unittest.main()
