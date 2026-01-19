<!-- file: docs/intelligent-issue-labeling.md -->
<!-- version: 1.0.1 -->
<!-- guid: 1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e -->
<!-- last-edited: 2026-01-19 -->

# Intelligent Issue Labeling

Automatically analyze GitHub issues and apply appropriate labels using machine learning patterns and
AI fallback for complex cases.

## Overview

The Intelligent Issue Labeling system analyzes issue content (title, body, comments) and
automatically suggests and applies relevant labels from your repository's comprehensive label
taxonomy. It uses:

1. **Pattern-based analysis** for fast, reliable labeling
2. **Machine learning techniques** for content analysis
3. **AI fallback (OpenAI)** for complex edge cases
4. **Confidence scoring** to ensure quality

## Features

- **Comprehensive Analysis**: Analyzes issue title, body, and metadata
- **Technology Detection**: Automatically detects programming languages and frameworks
- **Module Classification**: Identifies which modules/components are affected
- **Priority Assessment**: Suggests appropriate priority levels
- **Workflow Integration**: Identifies CI/CD, automation, and deployment issues
- **AI-Powered Fallback**: Uses OpenAI GPT-4 for complex labeling decisions
- **Batch Processing**: Efficiently processes multiple issues
- **Dry-Run Mode**: Test changes without applying them
- **Configurable**: Customize confidence thresholds and behavior

## Configuration

### Basic Configuration

```yaml
jobs:
  intelligent-labeling:
    uses: jdfalk/ghcommon/.github/workflows/reusable-intelligent-issue-labeling.yml@main
    with:
      enabled: true
      dry_run: false
      batch_size: 10
      confidence_threshold: 0.7
      max_labels_per_issue: 8
    secrets: inherit
```

### Advanced Configuration

```yaml
jobs:
  intelligent-labeling:
    uses: jdfalk/ghcommon/.github/workflows/reusable-intelligent-issue-labeling.yml@main
    with:
      # Core settings
      enabled: true
      dry_run: false
      batch_size: 15

      # AI configuration
      use_ai_fallback: true
      confidence_threshold: 0.75
      max_labels_per_issue: 6
      preserve_existing_labels: true

      # Custom configuration
      label_config_path: '.github/custom-labeling.yml'
      python_version: '3.11'
    secrets:
      github-token: ${{ secrets.JF_CI_GH_PAT }}
```

## Label Categories Detected

### Issue Types

- `bug` - Error reports and broken functionality
- `enhancement` - New features and improvements
- `documentation` - Documentation updates and fixes
- `question` - Support requests and clarifications

### Priority Levels

- `priority-high` - Urgent issues requiring immediate attention
- `priority-medium` - Standard priority issues
- `priority-low` - Nice-to-have improvements

### Technology Stack

- `tech:go` - Go programming language
- `tech:python` - Python programming language
- `tech:javascript` - JavaScript/Node.js
- `tech:typescript` - TypeScript
- `tech:protobuf` - Protocol Buffer definitions
- `tech:docker` - Docker containerization
- `tech:kubernetes` - Kubernetes orchestration
- `tech:shell` - Shell scripting

### Module Classification

- `module:auth` - Authentication and authorization
- `module:cache` - Caching systems
- `module:config` - Configuration management
- `module:database` - Database operations
- `module:metrics` - Monitoring and metrics
- `module:queue` - Message queuing
- `module:web` - Web services and APIs
- `module:ui` - User interface

### Workflow Types

- `workflow:automation` - Automation scripts and tools
- `workflow:github-actions` - GitHub Actions workflows
- `workflow:ci-cd` - CI/CD pipelines
- `workflow:deployment` - Deployment processes

### Special Categories

- `security` - Security vulnerabilities and concerns
- `performance` - Performance optimization
- `breaking-change` - Breaking changes
- `good first issue` - Beginner-friendly issues
- `help wanted` - Issues needing community help
- `dependencies` - Dependency updates

## How It Works

### 1. Pattern-Based Analysis

The system uses keyword matching and pattern recognition to identify:

```yaml
# Example patterns
bug:
  keywords: ['bug', 'error', 'fail', 'broken', 'crash']
  confidence: 0.8

tech:go:
  keywords: ['go', 'golang', '.go', 'gofmt']
  file_patterns: ['*.go', 'go.mod']
  confidence: 0.85
```

### 2. Content Analysis

- **Tokenization**: Breaks down text into meaningful tokens
- **Stop Word Removal**: Filters out common words
- **Lemmatization**: Reduces words to their base forms
- **TF-IDF Analysis**: Identifies important terms

### 3. Confidence Scoring

Each suggested label gets a confidence score (0.0-1.0):

- **0.9+**: Very high confidence (security issues, exact matches)
- **0.8+**: High confidence (technology detection, clear patterns)
- **0.7+**: Medium confidence (general categories)
- **0.6+**: Low confidence (default assignments)

### 4. AI Fallback

When pattern matching produces few or low-confidence suggestions, the system uses OpenAI's GPT-4 to
analyze the issue and suggest appropriate labels.

## Usage Examples

### Daily Batch Processing

```yaml
name: Daily Issue Labeling

on:
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM

jobs:
  label-issues:
    uses: jdfalk/ghcommon/.github/workflows/reusable-intelligent-issue-labeling.yml@main
    with:
      batch_size: 20
      confidence_threshold: 0.7
    secrets: inherit
```

### Real-time Labeling

```yaml
name: Real-time Issue Labeling

on:
  issues:
    types: [opened, edited]

jobs:
  label-new-issue:
    uses: jdfalk/ghcommon/.github/workflows/reusable-intelligent-issue-labeling.yml@main
    with:
      batch_size: 1
      use_ai_fallback: true
    secrets: inherit
```

### Testing Configuration

```yaml
name: Test Labeling Rules

on:
  workflow_dispatch:

jobs:
  test-labeling:
    uses: jdfalk/ghcommon/.github/workflows/reusable-intelligent-issue-labeling.yml@main
    with:
      dry_run: true
      batch_size: 5
      confidence_threshold: 0.5
    secrets: inherit
```

## Integration with Unified Automation

The intelligent labeling system integrates seamlessly with the unified automation workflow:

```yaml
jobs:
  unified-automation:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-automation.yml@main
    with:
      operation: 'all' # Includes intelligent labeling

      # Intelligent labeling configuration
      il_enabled: true
      il_batch_size: 15
      il_use_ai_fallback: true
      il_confidence_threshold: 0.7
    secrets: inherit
```

## Configuration File

Create `.github/intelligent-labeling.yml` to customize behavior:

```yaml
global:
  confidence_threshold: 0.7
  max_labels_per_issue: 8
  preserve_existing_labels: true

patterns:
  issue_types:
    bug:
      keywords: ['bug', 'error', 'broken']
      confidence: 0.8

  technology:
    tech:python:
      keywords: ['python', '.py', 'pip']
      file_patterns: ['*.py', 'requirements.txt']
      confidence: 0.85

ai_fallback:
  enabled: true
  model: 'gpt-4o-mini'
  trigger_conditions:
    few_suggestions: 3
```

## Environment Variables

### Required

- `GITHUB_TOKEN` - GitHub token with issues:write permission

### Optional

- `OPENAI_API_KEY` - OpenAI API key for AI fallback functionality

## Best Practices

### 1. Start with Dry Run

```yaml
with:
  dry_run: true
  batch_size: 5
```

### 2. Adjust Confidence Threshold

- Start with `0.7` (moderate confidence)
- Increase to `0.8+` for stricter labeling
- Decrease to `0.6` for more aggressive labeling

### 3. Use AI Fallback Selectively

```yaml
with:
  use_ai_fallback: true
  confidence_threshold: 0.8 # Only use AI for uncertain cases
```

### 4. Monitor Performance

```yaml
with:
  batch_size: 10 # Start small, increase as needed
  max_labels_per_issue: 6 # Prevent over-labeling
```

## Troubleshooting

### Common Issues

**No labels applied:**

- Check confidence threshold (try lowering to 0.6)
- Verify repository has the expected labels
- Enable AI fallback for better coverage

**Too many labels applied:**

- Increase confidence threshold to 0.8+
- Reduce max_labels_per_issue
- Review and refine pattern configurations

**AI fallback not working:**

- Verify OPENAI_API_KEY is set in repository secrets
- Check OpenAI API quota and usage
- Review AI fallback trigger conditions

**Performance issues:**

- Reduce batch_size for large repositories
- Run during off-peak hours
- Consider splitting into multiple workflows

### Debugging

Enable detailed logging by setting:

```yaml
with:
  dry_run: true # See what would be applied without changes
```

Monitor workflow logs for:

- Pattern matching results
- Confidence scores
- AI fallback usage
- Applied labels

## Limitations

- **Rate Limits**: GitHub API and OpenAI API rate limits apply
- **Token Limits**: Large issues may be truncated for AI analysis
- **Language Support**: Optimized for English content
- **Pattern Accuracy**: Depends on keyword accuracy and maintenance

## Future Enhancements

- **Learning from Manual Labels**: Train on existing label patterns
- **Multi-language Support**: Support for non-English content
- **Custom Models**: Support for organization-specific AI models
- **Advanced Analytics**: Labeling accuracy metrics and reporting
- **Integration APIs**: REST API for external labeling requests

## Support

For issues, questions, or contributions:

1. Check existing issues in the [ghcommon repository](https://github.com/jdfalk/ghcommon/issues)
2. Create a new issue with the `intelligent-labeling` label
3. Include workflow logs and configuration for debugging
4. Provide example issues that aren't being labeled correctly

## License

This workflow is part of the ghcommon repository and follows the same license terms.

## Technology Stack

- `tech:go` - Go programming language
- `tech:python` - Python programming language
- `tech:javascript` - JavaScript/Node.js
- `tech:typescript` - TypeScript
- `tech:docker` - Docker containerization
- `tech:kubernetes` - Kubernetes orchestration
- `tech:shell` - Shell scripting
