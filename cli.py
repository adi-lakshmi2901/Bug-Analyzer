"""Command Line Interface for Bug Analysis Agent."""

import argparse
import sys
import logging
from pathlib import Path

from bug_analysis_agent import BugAnalysisAgent
from config import Config, LoggingConfig

logger = logging.getLogger(__name__)


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-powered Bug Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze bugs.md in current directory
  python cli.py bugs.md

  # Analyze with custom requirements folder
  python cli.py bugs.md --requirements-folder ./specs

  # Use different AI model
  python cli.py bugs.md --model openai:gpt-4

  # Analyze single issue number
  python cli.py bugs.md --single-issue 5

  # Validate setup only
  python cli.py --validate-setup
        """
    )
    
    parser.add_argument(
        "bugs_file",
        nargs="?",
        default="bugs.md",
        help="Path to bugs.md file (default: bugs.md in current directory)"
    )

    parser.add_argument(
        "--requirements-folder", "-r",
        default=".",
        help="Path to product requirements folder (default: current directory)"
    )

    parser.add_argument(
        "--model", "-m",
        default= "google-gla:gemini-2.5-flash",
        help="AI model to use (default: google-gla:gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup files"
    )
    
    parser.add_argument(
        "--single-issue", "-s",
        type=int,
        help="Analyze only a specific issue number"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log to file (default: console only)"
    )
    
    parser.add_argument(
        "--validate-setup",
        action="store_true",
        help="Validate setup and configuration only"
    )
    
    parser.add_argument(
        "--status",
        action="store_true", 
        help="Show agent status and configuration"
    )
    
    return parser


def validate_args(args):
    """Validate command line arguments."""
    errors = []
    
    # If not just validating setup or status, check the bugs file exists
    if not args.validate_setup and not args.status:
        if not Path(args.bugs_file).exists():
            errors.append(f"Bugs file not found: {args.bugs_file}")

    return errors


def run_analysis(agent, args):
    """Run the main bug analysis."""
    print(f"\n🔍 Analyzing bugs file: {args.bugs_file}")
    print(f"📁 Requirements folder: {args.requirements_folder}")
    print(f"🤖 AI Model: {args.model}")
    
    if args.single_issue:
        print(f"🎯 Single issue mode: #{args.single_issue}")
        result = agent.analyze_single_issue(args.bugs_file, args.single_issue)
        
        if result:
            print(f"\n✅ Issue #{args.single_issue} Analysis:")
            print(f"   Category: {result.category}")
            print(f"   Confidence: {result.confidence}%")
            print(f"   Reasoning: {result.reasoning}")
            return True
        else:
            print(f"\n❌ Failed to analyze issue #{args.single_issue}")
            return False
    else:
        print("🚀 Full file analysis mode")
        result = agent.process_bugs_file(args.bugs_file)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Total Issues: {result.total_issues}")
        print(f"   Analyzed: {result.analyzed_issues}")
        print(f"   Skipped (existing): {result.skipped_issues}")
        print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
        print(f"   Success: {'✅ Yes' if result.success else '❌ No'}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        if result.analysis_results:
            print("\n🏷️ Categories Found:")
            categories = {}
            for analysis in result.analysis_results:
                cat = analysis.category.value
                categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in sorted(categories.items()):
                print(f"   {category}: {count}")
        
        return result.success


def show_status(agent):
    """Show agent status and configuration."""
    print("\n📋 Bug Analysis Agent Status")
    print("=" * 40)
    
    status = agent.get_status()
    
    print(f"Requirements Folder: {status['requirements_folder']}")
    print(f"Folder Exists: {'✅ Yes' if status['requirements_folder_exists'] else '❌ No'}")
    print(f"AI Model: {status['model_name']}")
    print(f"Create Backup: {'✅ Yes' if status['create_backup'] else '❌ No'}")
    
    engine_info = status['engine_info']
    print(f"AI Agent Ready: {'✅ Yes' if engine_info['agent_initialized'] else '❌ No'}")
    print(f"Supported Categories: {len(engine_info['supported_categories'])}")


def validate_setup(agent):
    """Validate agent setup."""
    print("\n🔧 Validating Setup...")
    print("=" * 30)
    
    validation = agent.validate_setup()
    
    print(f"Requirements Folder Exists: {'✅ Yes' if validation['requirements_folder_exists'] else '❌ No'}")
    print(f"Requirements Loaded: {validation['requirements_count']}")
    print(f"AI Agent Initialized: {'✅ Yes' if validation['ai_agent_initialized'] else '❌ No'}")
    print(f"Overall Setup Valid: {'✅ Yes' if validation['setup_valid'] else '❌ No'}")
    
    if validation['errors']:
        print("\n❌ Errors Found:")
        for error in validation['errors']:
            print(f"   - {error}")
        return False
    else:
        print("\n✅ Setup validation passed!")
        return True


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    LoggingConfig.setup_logging(
        level=args.log_level,
        log_file=args.log_file
    )
    
    # Validate arguments
    arg_errors = validate_args(args)
    if arg_errors:
        print("❌ Argument errors:")
        for error in arg_errors:
            print(f"   - {error}")
        sys.exit(1)
    
    try:
        # Create agent
        agent = BugAnalysisAgent(
            requirements_folder=args.requirements_folder,
            model_name=args.model,
            create_backup=not args.no_backup
        )
        
        # Handle different modes
        if args.validate_setup:
            success = validate_setup(agent)
            sys.exit(0 if success else 1)
        
        elif args.status:
            show_status(agent)
            sys.exit(0)
        
        else:
            # Run analysis
            success = run_analysis(agent, args)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()