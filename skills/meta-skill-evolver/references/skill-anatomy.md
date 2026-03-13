# Skill Anatomy - Technical Reference

This document defines the structure, requirements, and best practices for well-formed Claude Code skills. It serves as the blueprint for skill generation, validation, and evolution.

## Directory Structure

A compliant skill has this exact structure:

```
skill-name/
├── SKILL.md                          # Main skill definition (required)
├── scripts/                          # Python automation (required)
│   └── main_implementation.py        # Primary script (~500 lines)
└── references/                       # Technical documentation (required)
    └── technical-reference.md        # Supporting docs
```

**Requirements:**

- Skill directory named in kebab-case (lowercase, hyphens for word separation)
- All three top-level components required: SKILL.md, scripts/, references/
- At least one .py file in scripts/ directory
- At least one .md file in references/ directory
- No hidden files except .gitignore
- No __pycache__ or compiled artifacts

## SKILL.md Frontmatter Rules

The SKILL.md file begins with YAML frontmatter delimited by `---` on separate lines.

### Allowed Fields (ONLY 2)

**name** (required, string)
- Kebab-case identifier for the skill
- Must match parent directory name
- Example: `code-formatter`, `json-processor`, `batch-renamer`
- Used for CLI invocation and registry lookup

**description** (required, string)
- Concise description of what the skill does
- MUST use `>` block scalar syntax for multi-line text
- Use active verbs: "generates", "transforms", "filters", "validates"
- Include 3-5 activation keywords that trigger the skill
- Example with proper formatting:

```yaml
---
name: csv-processor
description: >
  Transforms and filters CSV data with aggregation support.
  Activates on "process CSV", "filter data", "aggregate columns",
  "csv transformation", or "data processing" requests.
---
```

### Forbidden Fields

These fields MUST NOT appear in frontmatter:

- `tags` or `tag`
- `version` (tracked in registry instead)
- `author` or `created_by`
- `license`
- `metadata`
- Custom fields of any kind

**Why this restriction?** Minimal frontmatter ensures:
- Consistent parsing across all skills
- No version conflicts or metadata sprawl
- Clear separation: SKILL.md for instructions, registry for metadata

## SKILL.md Content Structure

After frontmatter, the SKILL.md file should follow this section hierarchy:

### H1: Skill Title

```markdown
# Skill Title
```

The title is typically the skill name in title case. It should be the only H1 in the document.

### H2: Core Sections

**Overview/Introduction**
- One paragraph explaining the skill's purpose
- Link to what problem it solves
- Expected use cases

**Usage Patterns**
- List 3-5 keywords/phrases that activate the skill
- Format: "Activate when user says: *'keyword'*"
- Include both common and specific triggers

**Features**
- Bulleted list of 3-5 key capabilities
- Focus on unique or powerful features
- Keep descriptions brief (one line each)

**Examples**
- At least 3 representative use cases
- Each example should show:
  - What the user would ask
  - What the skill does
  - What the expected output looks like
- Format: ### Example 1, ### Example 2, etc.

**Integration**
- List related or complementary skills
- Explain how this skill works with others
- Mention dependencies if any

**Troubleshooting**
- Common issues and solutions
- Error messages and fixes
- Performance tips

**Advanced Usage** (optional)
- Non-obvious applications
- Customization options
- Performance tuning

### Heading Hierarchy Rules

```markdown
# Skill Name                    (H1 - only one)
## Section 1                    (H2 - major sections)
### Subsection 1.1              (H3 - detail within sections)
#### Detail 1.1.1               (H4 - if needed, but avoid)
```

**Rules:**

- Use H2 for major sections only
- Use H3 for subsections and examples
- Avoid H4 and deeper nesting (indicates poor organization)
- Don't skip levels (don't jump from H1 to H3)
- Each H2 section should be substantive (at least 100 words)

## Python Script Conventions

### File Location and Naming

- Primary script: `scripts/skill_name.py` (matches skill name, underscores replace hyphens)
- Secondary scripts (optional): `scripts/helper_*.py`
- Must be executable: `chmod 755 scripts/*.py`

### Script Structure

Every script should follow this template:

```python
#!/usr/bin/env python3
"""Module docstring describing the skill."""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class SkillImplementation:
    """Core skill logic."""

    def __init__(self):
        """Initialize the skill."""
        pass

    def process(self, **kwargs) -> Dict[str, Any]:
        """Main processing method."""
        try:
            # Core logic here
            result = self._execute(**kwargs)
            return {'status': 'success', 'result': result}
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _execute(self, **kwargs) -> Any:
        """Implementation details."""
        pass


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description='Skill description')
    parser.add_argument('--input', help='Input data')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--json', action='store_true', help='JSON output')

    args = parser.parse_args()
    skill = SkillImplementation()
    result = skill.process(input=args.input, output=args.output)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Result: {result}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
```

### Requirements

**Imports:**
- Use ONLY Python standard library
- No pip packages or external dependencies
- Common modules: json, re, pathlib, logging, subprocess, tempfile

**Entry Point:**
- Must have `if __name__ == '__main__':` block
- `main()` function for CLI
- argparse for argument handling

**Error Handling:**
- All operations in try-except blocks
- Return structured error responses: `{'status': 'error', 'message': '...'}`
- Use logging for debug information, never print stack traces

**Return Values:**
- Consistent JSON structure: `{'status': 'success'/'error', 'result'/'message': ...}`
- Structured output for programmatic use
- Human-readable fallback text output

**Logging:**
- Use logging module, not print statements
- Log at INFO level for normal operations
- Log at ERROR level for failures
- Set level in main(): `logging.basicConfig(level=logging.INFO)`

### Size Guidelines

- **Minimum:** 50 lines (too trivial for a skill)
- **Optimal:** 300-800 lines (most skills)
- **Maximum:** 1500 lines (consider breaking into modules)

Larger scripts should be broken into multiple modules in the scripts/ directory.

## Reference Documentation Format

Reference files (in `references/`) should follow this structure:

### File Naming

- `technical-reference.md` (required)
- `advanced-usage.md` (optional, for complex skills)
- `performance-tuning.md` (optional, for computationally intensive skills)
- `troubleshooting-guide.md` (optional, for error-prone skills)

### Content Structure

**technical-reference.md must include:**

1. **Architecture Overview** — High-level description of how the skill works
2. **Core Components** — Breakdown of major classes/functions
3. **Input Specifications** — Data formats, schemas, constraints
4. **Output Specifications** — Result formats, structure, units
5. **Algorithm Explanation** — For complex processing logic
6. **Performance Characteristics** — Speed, memory, scalability
7. **Error Handling** — How failures are managed and reported
8. **Dependencies** — List of related skills or utilities
9. **Version History** — Changes between versions
10. **Contributing** — How to improve the skill

### Markdown Quality Criteria

- **Headings:** Proper hierarchy (H1 → H2 → H3)
- **Code blocks:** Always use triple backticks with language tag
  ```python
  # Good: Proper language tag
  def example():
      pass
  ```
  ```
  # Bad: No language tag
  ```
- **Lists:** Use consistent formatting (- or *)
- **Links:** Use markdown format: `[text](url)`
- **Length:** Minimum 500 characters, maximum 5000 characters per file
- **Clarity:** Technical accuracy without unnecessary jargon

## Packaging Requirements

### Pre-Packaging Cleanup

Before creating the .skill archive:

1. **Remove build artifacts:**
   - `__pycache__` directories
   - `*.pyc` and `*.pyo` files
   - `*.egg-info` directories

2. **Remove temporary files:**
   - `*~` (backup files)
   - `*.bak` (backup copies)
   - `*.tmp` (temporary files)
   - `.DS_Store` (macOS)

3. **Remove test artifacts:**
   - Test output files > 1 MB
   - Coverage reports
   - Debug logs

### Archive Format

- **Format:** ZIP file with .skill extension
- **Name:** `skill-name.skill` (matches skill directory name)
- **Structure:** Preserve full directory tree from skill root
- **Permissions:** Scripts remain executable (755)

### Archive Integrity Checks

- Zip file must be readable without errors
- All expected files present: SKILL.md, at least one .py, at least one reference .md
- SKILL.md and main script must be valid
- Archive size between 5 KB and 10 MB

## Validation Checklist

Use this checklist when validating a skill:

### Frontmatter
- [ ] Frontmatter delimited by `---` on lines 1 and 3+
- [ ] Contains ONLY `name` and `description` fields
- [ ] No forbidden fields (tags, version, author, etc.)
- [ ] Description uses `>` block scalar syntax
- [ ] Name matches directory name in kebab-case

### Structure
- [ ] SKILL.md exists at skill root
- [ ] scripts/ directory exists with at least one .py file
- [ ] references/ directory exists with at least one .md file
- [ ] No hidden files except .gitignore
- [ ] No __pycache__ directories
- [ ] Directory naming is kebab-case

### SKILL.md Content
- [ ] Single H1 heading (skill name)
- [ ] H2 sections are substantive (100+ words each)
- [ ] At least 3-5 examples provided
- [ ] Usage patterns section included
- [ ] Proper heading hierarchy (no gaps, no excessive depth)
- [ ] Code blocks have language tags
- [ ] Minimum 500 characters total

### Python Scripts
- [ ] Syntax valid (py_compile.compile succeeds)
- [ ] Has `if __name__ == '__main__':` block
- [ ] Has proper error handling (try-except blocks)
- [ ] Uses logging, not print for messages
- [ ] Imports are stdlib only
- [ ] Has argparse for CLI arguments
- [ ] Returns structured JSON responses
- [ ] 50-1500 lines (optimal 300-800)
- [ ] Executable permissions set (755)

### Reference Files
- [ ] At least 500 characters
- [ ] Proper markdown formatting
- [ ] No placeholder text
- [ ] Heading hierarchy correct
- [ ] Contains technical depth

### Packaging
- [ ] No build artifacts
- [ ] No temporary files
- [ ] Archive is 5 KB - 10 MB
- [ ] Zip file integrity verified
- [ ] All required files present in archive

## Integration Points

### With skill-validator
The validation skill provides comprehensive checks beyond this basic framework. It performs:
- YAML schema validation
- File permissions checking
- Code quality analysis
- Documentation completeness assessment

### With skill-test-harness
The test-harness skill:
- Auto-generates test cases from examples
- Manages fixture data
- Executes tests and reports coverage
- Benchmarks performance

### With pre-package-pipeline
The packaging skill:
- Orchestrates cleanup
- Creates archives
- Verifies integrity
- Manages distribution

## Examples

### Example: Simple Text Processor Skill

**Directory structure:**
```
text-formatter/
├── SKILL.md
├── scripts/
│   └── text_formatter.py
└── references/
    └── technical-reference.md
```

**SKILL.md frontmatter:**
```yaml
---
name: text-formatter
description: >
  Formats and transforms text content with support for case conversion,
  whitespace normalization, and pattern replacement. Use when "format text",
  "clean up text", "normalize whitespace", "convert case", or
  "standardize formatting" is mentioned.
---
```

**Script structure:**
- Main class: `TextFormatter`
- Main method: `process(input_text, format_type)`
- CLI: `python3 text_formatter.py --input FILE --format TYPE --json`
- Output: JSON with formatted text

**References:**
- Algorithm explanation
- Supported format types
- Performance notes
- Troubleshooting common issues

## Best Practices Summary

1. **Naming:** Kebab-case everywhere (directories, scripts, references)
2. **Simplicity:** Minimal frontmatter, clear content structure
3. **Consistency:** Follow conventions for scripts and documentation
4. **Quality:** Substantive content, proper markdown, tested code
5. **Modularity:** Single skill = single purpose
6. **Documentation:** Comprehensive but concise
7. **Testing:** At least 3 examples in SKILL.md
8. **Compatibility:** Backward compatible versions when possible
9. **Performance:** Target < 30 seconds for typical usage
10. **Maintenance:** Track versions and improvements in registry

## Troubleshooting

### Q: Validation fails on frontmatter?
**A:** Ensure frontmatter is wrapped in `---` delimiters and contains ONLY `name` and `description`. Remove any other fields.

### Q: Script has import errors?
**A:** Use only Python standard library. Check that all imports (json, re, pathlib, etc.) are from stdlib.

### Q: Tests fail on fixture data?
**A:** Verify that fixture files match the format expected by the script. Check argparse arguments and error handling.

### Q: Archive is too large?
**A:** Remove test files > 1 MB, compression output, or sample datasets. Consider splitting into multiple skills.

### Q: Heading hierarchy validation fails?
**A:** Use H2 for major sections, H3 for subsections. Don't skip levels (no H1 → H3). Keep H4+ minimal.

## Related Documents

- **SKILL.md Format Guide:** Details on frontmatter and content structure
- **Python Script Standards:** Conventions for skill automation code
- **Validation Framework:** Complete validation rules and error messages
- **Testing Strategy:** Auto-generating and running test cases
- **Packaging Pipeline:** Steps for creating distributable .skill archives
