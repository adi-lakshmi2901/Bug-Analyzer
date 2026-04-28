# Bug Analysis Agent

AI-powered bug categorization system that reads product requirements, analyzes bugs from markdown files, and writes structured analysis back to the files using Pydantic AI.

## 🎯 Overview

The Bug Analysis Agent automatically:
1. **Reads** product requirements from a `product-requirements-specs/` folder
2. **Parses** numbered bug lists from `bugs.md` files  
3. **Analyzes** each bug using AI to categorize into 8 standard categories
4. **Writes** `ANALYSIS` blocks back to the markdown file with category, confidence, and reasoning
5. **Skips** bugs that already have analysis to avoid duplication

## 🏷️ Issue Categories

The system categorizes issues into 15 comprehensive categories for thorough analysis:

**Requirements & Scope:**
- **Change Request (CR)** - Requests to modify existing functionality or behavior
- **New Requirement (Feature Addition)** - Completely new features or capabilities not previously specified
- **Requirement Modification** - Changes to existing requirements that affect scope or behavior
- **Clarification Request** - Need for additional detail or explanation of existing requirements
- **Gap / Missing Requirement** - Identified missing requirements that should have been specified
- **Conflict / Inconsistency** - Contradicting requirements or specifications that need resolution
- **Out of Scope Request** - Requests that fall outside the defined project boundaries

**Technical & Quality:**
- **Non-Functional Requirement (NFR)** - Performance, security, usability, or other quality attributes
- **Bug / Spec Mismatch** - Implementation doesn't match what was specified in requirements
- **Dependency Introduction** - New dependencies on external systems, libraries, or components

**Process & Management:**
- **Assumption Exposure** - Previously hidden assumptions that need to be made explicit
- **Trade-off Decision** - Decisions requiring balancing competing priorities or constraints
- **Risk Identification** - Potential issues or risks that need mitigation strategies
- **KPI / Success Metric** - Measurements or metrics needed to track success
- **Scope Reduction / De-scoping** - Suggestions to reduce scope or remove features

## 🚀 Quick Start

### 1. Setup

```bash
# Clone or download the project
cd analyze-it

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AI Model

Set up your AI API key (OpenAI example):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Setup Project Structure

```
your-project/
├── product-requirements-specs/     # Put requirement docs here
│   ├── feature-requirements.md
│   ├── user-stories.md
│   └── technical-specs.md
├── bugs.md                        # Your numbered bug list
└── analyze-it/                    # This tool
    ├── cli.py
    └── ...
```

### 4. Create Your Bug List

Create a `bugs.md` file with numbered issues:

```markdown
# Bug Report

1. Login button doesn't respond when clicked on mobile devices
2. Search results load very slowly with large datasets
3. User dashboard crashes when displaying more than 100 items
4. Email notifications are not being sent to users
5. Payment form shows error with valid credit card numbers
```

### 5. Run Analysis

```bash
# Analyze all bugs in bugs.md
python cli.py bugs.md

# Analyze with custom requirements folder
python cli.py bugs.md --requirements-folder ./my-specs

# Analyze only issue #3
python cli.py bugs.md --single-issue 3

# Use different AI model
python cli.py bugs.md --model openai:gpt-4
```

### 6. Review Results

The tool adds `ANALYSIS` blocks after each bug:

```markdown
1. Login button doesn't respond when clicked on mobile devices

```ANALYSIS
Category: Interface
Confidence: 85%
Reasoning: This is clearly a user interface issue where a UI element (button) is not responding to user interaction on a specific platform (mobile). The problem is with the user interface responsiveness rather than core functionality.
```

2. Search results load very slowly with large datasets

```ANALYSIS
Category: Performance
Confidence: 90%  
Reasoning: The issue describes slow loading times when handling large amounts of data, which is a classic performance problem related to system response time and scalability.
```
```

## 📋 Usage Options

### Command Line Interface

```bash
# Basic usage
python cli.py bugs.md

# All available options
python cli.py bugs.md \
  --requirements-folder ./specs \
  --model openai:gpt-4 \
  --no-backup \
  --log-level DEBUG \
  --log-file analysis.log

# Utility commands
python cli.py --validate-setup    # Check configuration
python cli.py --status           # Show agent status
```

### Programmatic Usage

```python
from bug_analysis_agent import BugAnalysisAgent

# Initialize agent
agent = BugAnalysisAgent(
    requirements_folder="product-requirements-specs",
    model_name="openai:gpt-4o-mini",
    create_backup=True
)

# Analyze entire file
result = agent.process_bugs_file("bugs.md")
print(f"Analyzed {result.analyzed_issues} issues in {result.processing_time_seconds:.2f}s")

# Analyze single issue
analysis = agent.analyze_single_issue("bugs.md", issue_number=5)
print(f"Issue #5: {analysis.category} ({analysis.confidence}%)")
```

## 🔧 Configuration

### Environment Variables

```bash
export REQUIREMENTS_FOLDER="./my-requirements"
export AI_MODEL_NAME="openai:gpt-4"
export CREATE_BACKUP="true"
export LOG_LEVEL="INFO"
export OPENAI_API_KEY="your-api-key"
```

### Supported AI Models

- **OpenAI**: `openai:gpt-4o-mini` (default), `openai:gpt-4`, `openai:gpt-3.5-turbo`
- **Anthropic**: `anthropic:claude-3-haiku`, `anthropic:claude-3-sonnet`
- **Google**: `google-genai:gemini-pro`
- **Groq**: `groq:llama-3.1-70b`, `groq:mixtral-8x7b`

## 📁 Project Structure

```
analyze-it/
├── models/                        # Data models
│   └── __init__.py               # BugCategory, Issue, AnalysisResult, etc.
├── components/                   # Core components  
│   ├── file_processor.py        # File reading and parsing
│   ├── analysis_engine.py       # AI-powered analysis
│   └── output_writer.py         # Writing results back to files
├── tests/                       # Test suite
│   └── test_basic.py           # Basic functionality tests
├── bug_analysis_agent.py       # Main orchestrator class
├── cli.py                      # Command line interface
├── config.py                   # Configuration and logging
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧪 Testing

```bash
# Run basic tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Manual testing
python cli.py --validate-setup
python tests/test_basic.py
```

## 🔍 Features

### Smart Analysis
- **Context-aware**: Uses product requirements for better categorization
- **Confidence scoring**: Provides 0-100% confidence for each analysis
- **Detailed reasoning**: Explains why each category was chosen

### File Management
- **Automatic backup**: Creates timestamped backups before modification
- **Skip existing**: Won't re-analyze bugs that already have ANALYSIS blocks
- **Preserves formatting**: Maintains original markdown structure

### Flexible Usage
- **Batch processing**: Analyze entire bug files at once
- **Single issue mode**: Target specific bug numbers
- **Multiple formats**: CLI tool and Python API
- **Configurable models**: Support for multiple AI providers

## 🔧 Troubleshooting

### Common Issues

**"Requirements folder does not exist"**
```bash
# Create the folder and add some requirement docs
mkdir product-requirements-specs
echo "# Requirements" > product-requirements-specs/requirements.md
```

**"API key not found"**  
```bash
# Set your API key for the chosen model
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

**"Pydantic AI import error"**
```bash
# Reinstall dependencies
pip install --upgrade pydantic-ai pydantic
```

### Debug Mode

```bash
# Enable detailed logging
python cli.py bugs.md --log-level DEBUG --log-file debug.log

# Check agent status
python cli.py --status

# Validate setup
python cli.py --validate-setup
```

### File Format Issues

The tool expects:
- **Numbered lists**: `1. Bug description` or `1) Bug description`  
- **Markdown files**: `.md` extension required
- **UTF-8 encoding**: Ensure files are saved with UTF-8 encoding

## 🔗 Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Analyze Bugs
  run: |
    python cli.py bugs.md --no-backup
    git add bugs.md
    git commit -m "Auto-update bug analysis"
```

### IDE Integration

The tool can be integrated with VS Code, IntelliJ, or other IDEs as an external tool for on-demand bug analysis.

## 📝 Learning More

- Review the `docs/` folder for detailed implementation documentation
- Check `tests/test_basic.py` for usage examples
- Examine `models/__init__.py` for data structures
- Look at `components/` for individual component implementations

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality in `tests/`
3. Update documentation for user-facing changes  
4. Use type hints and proper Pydantic validation
5. Follow the 8-category classification system

---

*Built with Pydantic AI for reliable, structured analysis results.*