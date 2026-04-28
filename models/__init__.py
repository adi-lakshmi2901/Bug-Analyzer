"""Core data models for the Bug Analysis Agent."""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class BugCategory(str, Enum):
    """15 comprehensive bug/requirement categories for analysis."""
    CHANGE_REQUEST = "Change Request (CR)"
    NEW_REQUIREMENT = "New Requirement (Feature Addition)"
    REQUIREMENT_MODIFICATION = "Requirement Modification"
    CLARIFICATION_REQUEST = "Clarification Request"
    GAP_MISSING_REQUIREMENT = "Gap / Missing Requirement"
    CONFLICT_INCONSISTENCY = "Conflict / Inconsistency"
    OUT_OF_SCOPE_REQUEST = "Out of Scope Request"
    NON_FUNCTIONAL_REQUIREMENT = "Non-Functional Requirement (NFR)"
    BUG_SPEC_MISMATCH = "Bug / Spec Mismatch"
    DEPENDENCY_INTRODUCTION = "Dependency Introduction"
    ASSUMPTION_EXPOSURE = "Assumption Exposure"
    TRADE_OFF_DECISION = "Trade-off Decision"
    RISK_IDENTIFICATION = "Risk Identification"
    KPI_SUCCESS_METRIC = "KPI / Success Metric"
    SCOPE_REDUCTION = "Scope Reduction / De-scoping"


class RequirementDocument(BaseModel):
    """Represents a product requirement document."""
    filename: str = Field(..., description="Name of the requirement document file")
    content: str = Field(..., description="Full text content of the document")
    file_path: str = Field(..., description="Full path to the document file")
    last_modified: Optional[datetime] = Field(default=None, description="Last modification time")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.endswith('.md'):
            raise ValueError("Filename must be a valid markdown file (.md)")
        return v


class Issue(BaseModel):
    """Represents a single issue/bug from a numbered list."""
    number: int = Field(..., ge=1, description="Issue number from the list")
    text: str = Field(..., min_length=3, description="Full text of the issue")
    has_existing_analysis: bool = Field(default=False, description="True if ANALYSIS block already exists")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Issue text cannot be empty")
        return v.strip()


class BugReport(BaseModel):
    """Represents a bugs.md file with numbered issues."""
    file_path: str = Field(..., description="Full path to the bugs.md file")
    content: str = Field(..., description="Full content of the bugs.md file")
    issues: List[Issue] = Field(default_factory=list, description="Parsed list of issues")
    last_modified: Optional[datetime] = Field(default=None, description="Last modification time")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.endswith('.md'):
            raise ValueError("Bug report must be a markdown file")
        return v


class AnalysisResult(BaseModel):
    """Represents the AI analysis result for a single bug."""
    issue_number: int = Field(default=0, ge=0, description="Issue number being analyzed (set after AI returns)")
    category: BugCategory = Field(..., description="Categorized bug type")
    confidence: int = Field(..., ge=0, le=100, description="Confidence percentage (0-100)")
    reasoning: str = Field(..., min_length=10, description="Explanation for the categorization")
    
    @validator('reasoning')
    def validate_reasoning(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Reasoning must be at least 10 characters long")
        return v.strip()


class ProcessingResult(BaseModel):
    """Overall processing result for a bugs.md file."""
    bugs_file_path: str = Field(..., description="Path to the processed bugs.md file")
    total_issues: int = Field(..., ge=0, description="Total number of issues found")
    analyzed_issues: int = Field(..., ge=0, description="Number of issues analyzed")
    skipped_issues: int = Field(..., ge=0, description="Number of issues skipped (had existing analysis)")
    analysis_results: List[AnalysisResult] = Field(default_factory=list, description="All analysis results")
    processing_time_seconds: float = Field(..., ge=0, description="Total processing time")
    success: bool = Field(default=True, description="Overall success status")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")
    
    @validator('analyzed_issues', 'skipped_issues')
    def validate_issue_counts(cls, v, values):
        if 'total_issues' in values and v < 0:
            raise ValueError("Issue counts cannot be negative")
        return v