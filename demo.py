"""Demo script showing Bug Analysis Agent functionality without requiring API keys."""

import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_file_processing():
    """Demonstrate file processing without AI analysis."""
    print("🔍 Bug Analysis Agent Demo")
    print("=" * 50)
    
    # Import our components (skip AI for demo)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from components.file_processor import FileProcessor
    
    # Setup paths
    examples_dir = Path(__file__).parent / "examples"
    requirements_dir = examples_dir / "product-requirements-specs" 
    bugs_file = examples_dir / "bugs.md"
    
    print(f"\n📁 Requirements folder: {requirements_dir}")
    print(f"🐛 Bugs file: {bugs_file}")
    
    # Initialize file processor
    processor = FileProcessor(str(requirements_dir))
    
    # Load requirements
    print("\n📋 Loading Requirements:")
    try:
        requirements = processor.load_requirements()
        for req in requirements:
            print(f"   ✓ {req.filename} ({len(req.content)} chars)")
    except Exception as e:
        print(f"   ❌ Error loading requirements: {e}")
        return
    
    # Parse bugs file
    print("\n🐛 Parsing Bugs File:")
    try:
        bug_report = processor.parse_bugs_file(str(bugs_file))
        print(f"   ✓ Found {len(bug_report.issues)} issues")
        
        for issue in bug_report.issues:
            status = "📝 New" if not issue.has_existing_analysis else "✅ Has analysis"
            print(f"   {issue.number}. {issue.text[:50]}... [{status}]")
            
    except Exception as e:
        print(f"   ❌ Error parsing bugs: {e}")
        return
    
    # Show what AI analysis would look like
    print("\n🤖 Simulated AI Analysis Results:")
    print("   (This is what the AI would produce with proper API keys)")
    
    sample_analyses = [
        ("Issue #1", "Bug / Spec Mismatch", 85, "Mobile login button should work as specified in requirements but fails on touch devices"),
        ("Issue #2", "Non-Functional Requirement (NFR)", 90, "Search performance violates the 2-second requirement - this is an NFR issue"),  
        ("Issue #3", "Bug / Spec Mismatch", 95, "Payment validation allows invalid CVV codes, violating security requirements in spec"),
        ("Issue #4", "New Requirement (Feature Addition)", 75, "Admin password reset bypass appears to be requesting new security feature not in requirements"),
        ("Issue #5", "Bug / Spec Mismatch", 80, "Safari rendering issue violates cross-browser compatibility requirements")
    ]
    
    for issue, category, confidence, reasoning in sample_analyses:
        print(f"\n   {issue}:")
        print(f"   ```ANALYSIS")
        print(f"   Category: {category}")
        print(f"   Confidence: {confidence}%")
        print(f"   Reasoning: {reasoning}")
        print(f"   ```")
    
    print("\n✅ Demo Complete!")
    print("\n💡 To run with real AI analysis:")
    print("   1. Set OPENAI_API_KEY environment variable")
    print("   2. Run: python cli.py examples/bugs.md --requirements-folder examples/product-requirements-specs")

if __name__ == "__main__":
    demo_file_processing()