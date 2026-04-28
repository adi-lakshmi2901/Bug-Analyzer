"""Basic tests for Bug Analysis Agent."""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import BugCategory, Issue, RequirementDocument, AnalysisResult
from components.file_processor import FileProcessor


class TestFileProcessor(unittest.TestCase):
    """Test FileProcessor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = FileProcessor(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_numbered_issues(self):
        """Test parsing numbered issues from markdown."""
        content = """
# Bug Report

1. Login button doesn't work on mobile
2. Search results are slow
3. Dashboard crashes when loading large datasets

Some other text here.

4. Email notifications not sent
        """
        
        issues = self.processor._extract_numbered_issues(content)
        
        self.assertEqual(len(issues), 4)
        self.assertEqual(issues[0].number, 1)
        self.assertEqual(issues[0].text, "Login button doesn't work on mobile")
        self.assertEqual(issues[3].number, 4) 
        self.assertEqual(issues[3].text, "Email notifications not sent")
    
    def test_detect_existing_analysis(self):
        """Test detection of existing ANALYSIS blocks."""
        content = """
1. Login bug
```ANALYSIS
Category: Bug / Spec Mismatch
Confidence: 90%
Reasoning: Implementation doesn't match specification
```

2. UI issue without analysis

3. Another bug  
```ANALYSIS
Category: Clarification Request
Confidence: 85%
Reasoning: Unclear requirement specification
```
        """
        
        issues = self.processor._extract_numbered_issues(content)
        
        # Check that existing analysis is detected
        self.assertTrue(any(issue.has_existing_analysis for issue in issues))
        
        # Should have 3 issues
        self.assertEqual(len(issues), 3)


class TestDataModels(unittest.TestCase):
    """Test Pydantic data models."""
    
    def test_bug_category_enum(self):
        """Test BugCategory enum values."""
        categories = list(BugCategory)
        self.assertEqual(len(categories), 15)
        self.assertIn(BugCategory.CHANGE_REQUEST, categories)
        self.assertIn(BugCategory.NEW_REQUIREMENT, categories)
        self.assertIn(BugCategory.BUG_SPEC_MISMATCH, categories)
    
    def test_issue_model(self):
        """Test Issue model validation."""
        # Valid issue
        issue = Issue(number=1, text="Test bug description")
        self.assertEqual(issue.number, 1)
        self.assertEqual(issue.text, "Test bug description")
        self.assertFalse(issue.has_existing_analysis)
        
        # Test validation
        with self.assertRaises(ValueError):
            Issue(number=0, text="Invalid number")  # Should be >= 1
            
        with self.assertRaises(ValueError):
            Issue(number=1, text="")  # Empty text should fail
    
    def test_analysis_result_model(self):
        """Test AnalysisResult model."""
        result = AnalysisResult(
            issue_number=1,
            category=BugCategory.BUG_SPEC_MISMATCH,
            confidence=85,
            reasoning="This is a clear case where implementation doesn't match the specification"
        )
        
        self.assertEqual(result.issue_number, 1)
        self.assertEqual(result.category, BugCategory.BUG_SPEC_MISMATCH)
        self.assertEqual(result.confidence, 85)
        
        # Test confidence validation
        with self.assertRaises(ValueError):
            AnalysisResult(
                issue_number=1,
                category=BugCategory.BUG_SPEC_MISMATCH,
                confidence=150,  # Over 100%
                reasoning="Test"
            )


class TestOutputWriter(unittest.TestCase):
    """Test OutputWriter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        from components.output_writer import OutputWriter
        self.writer = OutputWriter(create_backup=False)
    
    def test_format_analysis_block(self):
        """Test formatting of analysis blocks."""
        result = AnalysisResult(
            issue_number=1,
            category=BugCategory.BUG_SPEC_MISMATCH,
            confidence=85,
            reasoning="Clear spec mismatch issue"
        )
        
        block_lines = self.writer._format_analysis_block(result)
        
        self.assertIn("```ANALYSIS", block_lines)
        self.assertIn("Category: Bug / Spec Mismatch", block_lines)
        self.assertIn("Confidence: 85%", block_lines)
        self.assertIn("Reasoning: Clear spec mismatch issue", block_lines)
        self.assertIn("```", block_lines)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_agent_initialization(self):
        """Test that BugAnalysisAgent initializes correctly."""
        # Skip this test if no API key is available
        import os
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("No API key available for testing")
            
        from bug_analysis_agent import BugAnalysisAgent
        
        # Should be able to create agent even without requirements folder
        agent = BugAnalysisAgent()
        self.assertIsNotNone(agent)
        
        # Should have all required components
        self.assertIsNotNone(agent.file_processor)
        self.assertIsNotNone(agent.analysis_engine)
        self.assertIsNotNone(agent.output_writer)
    
    def test_config_validation(self):
        """Test configuration validation."""
        from config import Config
        
        config = Config()
        errors = config.validate()
        
        # Should have error about missing requirements folder
        self.assertTrue(any("Requirements folder does not exist" in error for error in errors))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)