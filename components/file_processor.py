"""File processing component for reading requirements and parsing bug files."""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import logging

from models import RequirementDocument, BugReport, Issue

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles file I/O operations for requirements and bug analysis."""
    
    def __init__(self, requirements_folder: str = "product-requirements-specs"):
        """Initialize FileProcessor with requirements folder path."""
        self.requirements_folder = Path(requirements_folder)
        self.supported_extensions = ['.md', '.markdown']
        
    def load_requirements(self) -> List[RequirementDocument]:
        """Load all markdown files from requirements folder."""
        requirements = []
        
        if not self.requirements_folder.exists():
            logger.warning(f"Requirements folder not found: {self.requirements_folder}")
            return requirements
            
        try:
            for file_path in self.requirements_folder.rglob('*.md'):
                if file_path.is_file() and file_path.name != 'bugs.md':
                    requirement_doc = self._load_single_requirement(file_path)
                    if requirement_doc:
                        requirements.append(requirement_doc)
                        
            logger.info(f"Loaded {len(requirements)} requirement documents")
            return requirements
            
        except Exception as e:
            logger.error(f"Error loading requirements: {e}")
            raise
    
    def _load_single_requirement(self, file_path: Path) -> Optional[RequirementDocument]:
        """Load a single requirement document file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            return RequirementDocument(
                filename=file_path.name,
                content=content,
                file_path=str(file_path),
                last_modified=last_modified
            )
            
        except Exception as e:
            logger.error(f"Error loading requirement file {file_path}: {e}")
            return None
    
    def parse_bugs_file(self, bugs_file_path: str) -> BugReport:
        """Parse a bugs.md file and extract numbered issues."""
        file_path = Path(bugs_file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Bugs file not found: {bugs_file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            issues = self._extract_numbered_issues(content)
            
            return BugReport(
                file_path=str(file_path),
                content=content,
                issues=issues,
                last_modified=last_modified
            )
            
        except Exception as e:
            logger.error(f"Error parsing bugs file {bugs_file_path}: {e}")
            raise
    
    def _extract_numbered_issues(self, content: str) -> List[Issue]:
        """Extract numbered list items from markdown content."""
        issues = []
        
        # Pattern to match numbered list items: 1. Some text or 1) Some text
        number_pattern = r'^(\d+)[.)]\s+(.+)$'
        
        lines = content.split('\n')
        current_issue_number = None
        current_issue_text = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this line starts a new numbered item
            match = re.match(number_pattern, line)
            if match:
                # Save previous issue if it exists
                if current_issue_number is not None:
                    full_text = ' '.join(current_issue_text).strip()
                    if full_text:
                        has_analysis = self._has_existing_analysis(lines, current_issue_number)
                        issues.append(Issue(
                            number=current_issue_number,
                            text=full_text,
                            has_existing_analysis=has_analysis
                        ))
                
                # Start new issue
                current_issue_number = int(match.group(1))
                current_issue_text = [match.group(2)]
                
            elif current_issue_number is not None:
                # Continue current issue if we're in the middle of one
                # Stop current issue if we hit an ANALYSIS block or another numbered item
                if line.startswith('```ANALYSIS') or re.match(r'^\d+[.)]', line):
                    # Save current issue before breaking
                    full_text = ' '.join(current_issue_text).strip()
                    if full_text:
                        has_analysis = self._has_existing_analysis(lines, current_issue_number)
                        issues.append(Issue(
                            number=current_issue_number,
                            text=full_text,
                            has_existing_analysis=has_analysis
                        ))
                    current_issue_number = None
                    current_issue_text = []
                    
                    # If it's another numbered item, process it
                    match = re.match(number_pattern, line)
                    if match:
                        current_issue_number = int(match.group(1))
                        current_issue_text = [match.group(2)]
                        
                elif line and not line.startswith('#'):
                    current_issue_text.append(line)
        
        # Don't forget the last issue
        if current_issue_number is not None:
            full_text = ' '.join(current_issue_text).strip()
            if full_text:
                has_analysis = self._has_existing_analysis(lines, current_issue_number)
                issues.append(Issue(
                    number=current_issue_number,
                    text=full_text,
                    has_existing_analysis=has_analysis
                ))
        
        logger.info(f"Extracted {len(issues)} numbered issues")
        return issues
    
    def _has_existing_analysis(self, content_lines: List[str], issue_number: int) -> bool:
        """Check if an ANALYSIS block already exists for this issue number."""
        # Look for ANALYSIS block pattern after the issue
        analysis_pattern = r'```ANALYSIS'
        
        issue_found = False
        number_pattern = rf'^{issue_number}[.)]\s+'
        
        for i, line in enumerate(content_lines):
            # First, find the issue number
            if re.match(number_pattern, line.strip()):
                issue_found = True
                continue
                
            # Once we found our issue, look for ANALYSIS block before next issue
            if issue_found:
                if re.match(analysis_pattern, line.strip()):
                    return True
                # Stop at next numbered item
                if re.match(r'^\d+[.)]', line.strip()):
                    break
                    
        return False
    
    def detect_existing_analysis(self, bugs_file_path: str) -> List[int]:
        """Detect which issues already have ANALYSIS blocks."""
        try:
            bug_report = self.parse_bugs_file(bugs_file_path)
            existing_analysis = [
                issue.number for issue in bug_report.issues 
                if issue.has_existing_analysis
            ]
            
            logger.info(f"Found existing analysis for issues: {existing_analysis}")
            return existing_analysis
            
        except Exception as e:
            logger.error(f"Error detecting existing analysis: {e}")
            return []