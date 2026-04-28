"""Output writer for adding ANALYSIS blocks to markdown files."""

import os
import re
import shutil
from pathlib import Path
from typing import List
from datetime import datetime
import logging

from models import AnalysisResult, BugReport

logger = logging.getLogger(__name__)


class OutputWriter:
    """Handles writing analysis results back to markdown files."""
    
    def __init__(self, create_backup: bool = True):
        """Initialize OutputWriter with backup option."""
        self.create_backup = create_backup
    
    def write_analysis_to_file(
        self, 
        bugs_file_path: str, 
        analysis_results: List[AnalysisResult]
    ) -> bool:
        """Write analysis results to the bugs.md file."""
        try:
            file_path = Path(bugs_file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Bugs file not found: {bugs_file_path}")
            
            # Create backup if requested
            if self.create_backup:
                self._create_backup(file_path)
            
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Process content with analysis blocks
            updated_content = self._insert_analysis_blocks(original_content, analysis_results)
            
            # Write updated content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"Successfully wrote {len(analysis_results)} analysis results to {bugs_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing analysis to file {bugs_file_path}: {e}")
            return False
    
    def _create_backup(self, file_path: Path):
        """Create a backup of the original file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".{timestamp}.backup")
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _insert_analysis_blocks(
        self, 
        content: str, 
        analysis_results: List[AnalysisResult]
    ) -> str:
        """Insert ANALYSIS blocks after corresponding numbered issues."""
        lines = content.split('\n')
        result_lines = []
        
        # Create lookup for analysis results by issue number
        analysis_lookup = {result.issue_number: result for result in analysis_results}
        
        i = 0
        while i < len(lines):
            line = lines[i]
            result_lines.append(line)
            
            # Check if this line starts a numbered issue
            match = re.match(r'^(\d+)[.)]\s+(.+)$', line.strip())
            if match:
                issue_number = int(match.group(1))
                
                # If we have analysis for this issue, add it
                if issue_number in analysis_lookup:
                    analysis = analysis_lookup[issue_number]
                    
                    # Skip forward to find the end of this issue text
                    j = i + 1
                    while j < len(lines) and not self._is_next_item_or_analysis(lines[j]):
                        result_lines.append(lines[j])
                        j += 1
                    
                    # Add the analysis block
                    analysis_block = self._format_analysis_block(analysis)
                    result_lines.extend(analysis_block)
                    
                    # Skip the lines we already processed
                    i = j - 1
            
            i += 1
        
        return '\n'.join(result_lines)
    
    def _is_next_item_or_analysis(self, line: str) -> bool:
        """Check if line starts next numbered item or analysis block."""
        line = line.strip()
        
        # Check for numbered item
        if re.match(r'^\d+[.)]', line):
            return True
            
        # Check for existing analysis block
        if line.startswith('```ANALYSIS'):
            return True
            
        return False
    
    def _format_analysis_block(self, analysis: AnalysisResult) -> List[str]:
        """Format an AnalysisResult into ANALYSIS block lines."""
        block_lines = [
            "",  # Empty line before block
            "```ANALYSIS",
            f"Category: {analysis.category.value}",
            f"Confidence: {analysis.confidence}%",
            f"Reasoning: {analysis.reasoning}",
            "```",
            ""  # Empty line after block
        ]
        
        return block_lines
    
    def update_single_analysis(
        self, 
        bugs_file_path: str, 
        analysis_result: AnalysisResult
    ) -> bool:
        """Update analysis for a single issue."""
        return self.write_analysis_to_file(bugs_file_path, [analysis_result])
    
    def remove_analysis_blocks(self, bugs_file_path: str, issue_numbers: List[int]) -> bool:
        """Remove existing analysis blocks for specified issues."""
        try:
            file_path = Path(bugs_file_path)
            
            # Create backup if requested
            if self.create_backup:
                self._create_backup(file_path)
            
            # Read and process content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated_content = self._remove_analysis_for_issues(content, issue_numbers)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"Removed analysis blocks for issues: {issue_numbers}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing analysis blocks: {e}")
            return False
    
    def _remove_analysis_for_issues(self, content: str, issue_numbers: List[int]) -> str:
        """Remove analysis blocks for specific issue numbers."""
        lines = content.split('\n')
        result_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a numbered issue
            match = re.match(r'^(\d+)[.)]\s+(.+)$', line.strip())
            if match:
                issue_number = int(match.group(1))
                result_lines.append(line)
                
                # If this issue should have its analysis removed
                if issue_number in issue_numbers:
                    i += 1
                    # Copy issue text lines
                    while i < len(lines) and not lines[i].strip().startswith('```ANALYSIS'):
                        if not self._is_next_item_or_analysis(lines[i]):
                            result_lines.append(lines[i])
                        else:
                            break
                        i += 1
                    
                    # Skip the analysis block if found
                    if i < len(lines) and lines[i].strip().startswith('```ANALYSIS'):
                        # Skip until end of block
                        while i < len(lines) and not lines[i].strip() == '```':
                            i += 1
                        i += 1  # Skip the closing ```
                        
                        # Skip empty lines after block
                        while i < len(lines) and lines[i].strip() == '':
                            i += 1
                        i -= 1  # Back up one for main loop increment
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
            
            i += 1
        
        return '\n'.join(result_lines)