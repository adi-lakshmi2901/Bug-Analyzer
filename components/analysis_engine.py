"""Core analysis engine using Pydantic AI for bug categorization."""

import logging
from typing import List, Optional
from pydantic_ai import Agent
from pydantic_ai.models import Model

from models import RequirementDocument, Issue, AnalysisResult, BugCategory

logger = logging.getLogger(__name__)


class BugAnalysisEngine:
    """Core engine for AI-powered bug analysis and categorization."""
    
    def __init__(self, model_name: str = "openai:gpt-4o-mini"):
        """Initialize the analysis engine with specified AI model."""
        self.model_name = model_name
        self._agent = None
        self._init_agent()
        
    def _init_agent(self):
        """Initialize the Pydantic AI agent with analysis instructions."""
        system_prompt = """
You are an expert software analyst specializing in requirement analysis and issue categorization.

Your task is to analyze reported issues against product requirements and categorize them into exactly one of these 15 categories:

1. **Change Request (CR)** - Requests to modify existing functionality or behavior
2. **New Requirement (Feature Addition)** - Completely new features or capabilities not previously specified
3. **Requirement Modification** - Changes to existing requirements that affect scope or behavior
4. **Clarification Request** - Need for additional detail or explanation of existing requirements
5. **Gap / Missing Requirement** - Identified missing requirements that should have been specified
6. **Conflict / Inconsistency** - Contradicting requirements or specifications that need resolution
7. **Out of Scope Request** - Requests that fall outside the defined project boundaries
8. **Non-Functional Requirement (NFR)** - Performance, security, usability, or other quality attributes
9. **Bug / Spec Mismatch** - Implementation doesn't match what was specified in requirements
10. **Dependency Introduction** - New dependencies on external systems, libraries, or components
11. **Assumption Exposure** - Previously hidden assumptions that need to be made explicit
12. **Trade-off Decision** - Decisions requiring balancing competing priorities or constraints
13. **Risk Identification** - Potential issues or risks that need mitigation strategies
14. **KPI / Success Metric** - Measurements or metrics needed to track success
15. **Scope Reduction / De-scoping** - Suggestions to reduce scope or remove features

Analysis Guidelines:
- Compare the issue against product requirements context when available
- Choose the PRIMARY category that best fits (only one category per issue)
- Provide confidence as percentage (0-100%) based on clarity and evidence
- Give detailed reasoning explaining why this category was chosen
- Reference specific requirements when applicable
- Consider the business impact and technical implications

Output Format: You MUST return a structured AnalysisResult object with category, confidence, and reasoning.
"""

        try:
            self._agent = Agent(
                model=self.model_name,
                output_type=AnalysisResult,
                system_prompt=system_prompt.strip()
            )
            logger.info(f"Initialized analysis agent with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {e}")
            raise
    
    def analyze_issue(
        self, 
        issue: Issue, 
        requirements: List[RequirementDocument]
    ) -> Optional[AnalysisResult]:
        """Analyze a single issue and return categorization result."""
        try:
            # Build context from requirements
            context_text = self._build_context(requirements)
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(issue, context_text)
            
            # Run AI analysis
            logger.debug(f"Analyzing issue #{issue.number}: {issue.text[:100]}...")
            
            result = self._agent.run_sync(analysis_prompt)
            
            # Extract result and add issue number
            analysis_result = result.output
            analysis_result.issue_number = issue.number
            
            logger.info(
                f"Issue #{issue.number} categorized as {analysis_result.category} "
                f"(confidence: {analysis_result.confidence}%)"
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing issue #{issue.number}: {e}")
            return None
    
    def _build_context(self, requirements: List[RequirementDocument]) -> str:
        """Build context string from requirement documents."""
        if not requirements:
            return "No product requirements available for context."
            
        context_parts = ["=== PRODUCT REQUIREMENTS CONTEXT ==="]
        
        for req_doc in requirements:
            context_parts.append(f"\n--- {req_doc.filename} ---")
            # Truncate very long documents to avoid token limits
            content = req_doc.content
            if len(content) > 2000:
                content = content[:2000] + "...[truncated]"
            context_parts.append(content)
            
        context_parts.append("\n=== END CONTEXT ===")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, issue: Issue, context: str) -> str:
        """Create the analysis prompt for the AI agent."""
        prompt = f"""
{context}

=== BUG TO ANALYZE ===
Issue #{issue.number}: {issue.text}

Please analyze this bug report and categorize it into one of the 8 standard categories:
Functional, Interface, Performance, Security, Compatibility, Usability, Integration, or Configuration.

Consider the product requirements context when making your decision.
Provide your confidence level (0-100%) and detailed reasoning for the categorization.
"""
        return prompt.strip()
    
    def analyze_multiple_issues(
        self, 
        issues: List[Issue], 
        requirements: List[RequirementDocument]
    ) -> List[AnalysisResult]:
        """Analyze multiple issues and return list of results."""
        results = []
        
        logger.info(f"Starting analysis of {len(issues)} issues")
        
        for i, issue in enumerate(issues, 1):
            try:
                logger.info(f"Processing issue {i}/{len(issues)} (#{issue.number})")
                
                result = self.analyze_issue(issue, requirements)
                if result:
                    results.append(result)
                else:
                    logger.warning(f"Failed to analyze issue #{issue.number}")
                    
            except Exception as e:
                logger.error(f"Error processing issue #{issue.number}: {e}")
                continue
        
        logger.info(f"Successfully analyzed {len(results)} out of {len(issues)} issues")
        return results
    
    def get_model_info(self) -> dict:
        """Get information about the current AI model."""
        return {
            "model_name": self.model_name,
            "agent_initialized": self._agent is not None,
            "supported_categories": [category.value for category in BugCategory]
        }