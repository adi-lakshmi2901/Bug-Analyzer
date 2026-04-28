"""Main Bug Analysis Agent that coordinates all components."""

import time
import logging
from pathlib import Path
from typing import List, Optional

from models import (
    ProcessingResult, 
    RequirementDocument, 
    BugReport, 
    AnalysisResult,
    Issue
)
from components.file_processor import FileProcessor
from components.analysis_engine import BugAnalysisEngine
from components.output_writer import OutputWriter

logger = logging.getLogger(__name__)


class BugAnalysisAgent:
    """Main agent for automated bug analysis and categorization."""
    
    def __init__(
        self, 
        requirements_folder: str = "product-requirements-specs",
        model_name: str = "openai:gpt-4o-mini",
        create_backup: bool = True
    ):
        """Initialize the Bug Analysis Agent."""
        self.requirements_folder = requirements_folder
        self.model_name = model_name
        self.create_backup = create_backup
        
        # Initialize components
        self.file_processor = FileProcessor(requirements_folder)
        self.analysis_engine = BugAnalysisEngine(model_name)
        self.output_writer = OutputWriter(create_backup)
        
        logger.info("Bug Analysis Agent initialized")
        
    def process_bugs_file(self, bugs_file_path: str) -> ProcessingResult:
        """Process a bugs.md file completely - main entry point."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting processing of bugs file: {bugs_file_path}")
            
            # 1. Load requirements for context
            requirements = self._load_requirements()
            
            # 2. Parse bugs file
            bug_report = self._parse_bugs_file(bugs_file_path)
            
            # 3. Filter issues that need analysis (skip existing ones)
            issues_to_analyze = self._filter_issues_for_analysis(bug_report.issues)
            
            # 4. Analyze issues with AI
            analysis_results = self._analyze_issues(issues_to_analyze, requirements)
            
            # 5. Write results back to file
            write_success = self._write_results(bugs_file_path, analysis_results)
            
            # 6. Create processing result
            processing_time = time.time() - start_time
            result = ProcessingResult(
                bugs_file_path=bugs_file_path,
                total_issues=len(bug_report.issues),
                analyzed_issues=len(analysis_results),
                skipped_issues=len(bug_report.issues) - len(issues_to_analyze),
                analysis_results=analysis_results,
                processing_time_seconds=processing_time,
                success=write_success and len(analysis_results) > 0,
                error_message=None if write_success else "Failed to write results to file"
            )
            
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            logger.info(f"Total: {result.total_issues}, Analyzed: {result.analyzed_issues}, Skipped: {result.skipped_issues}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error during processing: {e}")
            
            return ProcessingResult(
                bugs_file_path=bugs_file_path,
                total_issues=0,
                analyzed_issues=0,
                skipped_issues=0,
                analysis_results=[],
                processing_time_seconds=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _load_requirements(self) -> List[RequirementDocument]:
        """Load product requirements for analysis context."""
        try:
            requirements = self.file_processor.load_requirements()
            logger.info(f"Loaded {len(requirements)} requirement documents")
            return requirements
        except Exception as e:
            logger.warning(f"Failed to load requirements: {e}")
            return []
    
    def _parse_bugs_file(self, bugs_file_path: str) -> BugReport:
        """Parse the bugs.md file."""
        try:
            bug_report = self.file_processor.parse_bugs_file(bugs_file_path)
            logger.info(f"Parsed {len(bug_report.issues)} issues from bugs file")
            return bug_report
        except Exception as e:
            logger.error(f"Failed to parse bugs file: {e}")
            raise
    
    def _filter_issues_for_analysis(self, issues: List[Issue]) -> List[Issue]:
        """Filter out issues that already have analysis blocks."""
        issues_to_analyze = [issue for issue in issues if not issue.has_existing_analysis]
        
        skipped_count = len(issues) - len(issues_to_analyze)
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} issues that already have analysis")
            
        return issues_to_analyze
    
    def _analyze_issues(
        self, 
        issues: List[Issue], 
        requirements: List[RequirementDocument]
    ) -> List[AnalysisResult]:
        """Analyze issues using AI engine."""
        if not issues:
            logger.info("No issues to analyze")
            return []
            
        try:
            analysis_results = self.analysis_engine.analyze_multiple_issues(issues, requirements)
            logger.info(f"Successfully analyzed {len(analysis_results)} issues")
            return analysis_results
        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            return []
    
    def _write_results(self, bugs_file_path: str, analysis_results: List[AnalysisResult]) -> bool:
        """Write analysis results back to the bugs file."""
        if not analysis_results:
            logger.info("No analysis results to write")
            return True
            
        try:
            success = self.output_writer.write_analysis_to_file(bugs_file_path, analysis_results)
            if success:
                logger.info(f"Successfully wrote {len(analysis_results)} analysis blocks to file")
            else:
                logger.error("Failed to write analysis results to file")
            return success
        except Exception as e:
            logger.error(f"Error writing results: {e}")
            return False
    
    def analyze_single_issue(
        self, 
        bugs_file_path: str, 
        issue_number: int
    ) -> Optional[AnalysisResult]:
        """Analyze a single specific issue."""
        try:
            # Load context
            requirements = self._load_requirements()
            
            # Parse bugs file
            bug_report = self._parse_bugs_file(bugs_file_path)
            
            # Find the specific issue
            target_issue = None
            for issue in bug_report.issues:
                if issue.number == issue_number:
                    target_issue = issue
                    break
            
            if not target_issue:
                logger.error(f"Issue #{issue_number} not found in bugs file")
                return None
            
            # Analyze single issue
            result = self.analysis_engine.analyze_issue(target_issue, requirements)
            
            if result:
                # Write result back to file
                self.output_writer.update_single_analysis(bugs_file_path, result)
                logger.info(f"Successfully analyzed and updated issue #{issue_number}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing single issue #{issue_number}: {e}")
            return None
    
    def get_status(self) -> dict:
        """Get current status and configuration of the agent."""
        return {
            "requirements_folder": self.requirements_folder,
            "model_name": self.model_name,
            "create_backup": self.create_backup,
            "requirements_folder_exists": Path(self.requirements_folder).exists(),
            "engine_info": self.analysis_engine.get_model_info()
        }
    
    def validate_setup(self) -> dict:
        """Validate the agent setup and return status."""
        validation_results = {
            "requirements_folder_exists": False,
            "requirements_count": 0,
            "ai_agent_initialized": False,
            "setup_valid": False,
            "errors": []
        }
        
        try:
            # Check requirements folder
            req_path = Path(self.requirements_folder)
            validation_results["requirements_folder_exists"] = req_path.exists()
            
            if req_path.exists():
                requirements = self._load_requirements()
                validation_results["requirements_count"] = len(requirements)
            else:
                validation_results["errors"].append(f"Requirements folder not found: {self.requirements_folder}")
            
            # Check AI agent
            engine_info = self.analysis_engine.get_model_info()
            validation_results["ai_agent_initialized"] = engine_info["agent_initialized"]
            
            if not engine_info["agent_initialized"]:
                validation_results["errors"].append("AI analysis engine not properly initialized")
            
            # Overall validation
            validation_results["setup_valid"] = (
                validation_results["ai_agent_initialized"] and
                len(validation_results["errors"]) == 0
            )
            
        except Exception as e:
            validation_results["errors"].append(f"Validation error: {e}")
        
        return validation_results