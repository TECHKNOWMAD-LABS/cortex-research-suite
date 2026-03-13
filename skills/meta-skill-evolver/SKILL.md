---
name: meta-skill-evolver
description: >
  Autonomous skill lifecycle engine that generates, validates, tests, packages,
  and evolves skills. Detects workflow patterns and auto-generates skills from
  them. Use when "create a skill", "meta-skill-evolver", "skill from pattern",
  "evolve skill", "auto-generate skill", "improve this skill", or any skill
  creation/evolution request is mentioned.
---

# Meta-Skill Evolver

The Meta-Skill Evolver is an autonomous engine designed to orchestrate the complete lifecycle of Claude Code skills: generation, validation, testing, packaging, and recursive evolution. It detects repeated workflow patterns and automatically transforms them into reusable, well-documented skills.

## Core Concepts

### Skill Lifecycle Stages

1. **Pattern Detection** — Analyzes conversation history and tool usage logs to identify repeated workflows that merit automation.
2. **Skill Scaffolding** — Generates a complete skill structure with compliant SKILL.md, Python scripts, and reference documentation.
3. **Validation Gate** — Ensures YAML integrity, directory structure compliance, Python syntax correctness, and documentation quality.
4. **Testing Gate** — Auto-generates and runs test cases based on skill examples and specifications.
5. **Packaging Gate** — Cleans artifacts, creates distributable .skill archive, and verifies integrity.
6. **Evolution Phase** — Analyzes performance metrics, identifies improvement opportunities, and automatically generates improved versions.

### Key Features

- **Pattern-Driven Generation**: Detects repeated tool calls, command sequences, and workflow patterns in conversation logs. Extracts common parameters, error handling strategies, and decision trees.
- **Compliant Scaffolding**: Generates SKILL.md with only `name` and `description` fields in frontmatter (no tags, version, or author fields). Includes Python automation scripts and supporting references.
- **Automated Validation**: Validates YAML schema, directory structure, Python syntax, and Markdown quality before allowing progression.
- **Comprehensive Testing**: Auto-generates test cases from skill examples, runs scripts against fixture data, and verifies expected outputs.
- **Recursive Evolution**: Tracks performance metrics, identifies improvement opportunities, generates enhanced versions, and A/B tests old vs. new implementations.
- **Skill Registry**: Maintains centralized inventory of all generated skills with version history, dependencies, and performance scores. Detects overlap and suggests optimizations.

## Usage Patterns

The meta-skill-evolver activates in these scenarios:

- User says: *"Create a skill for this workflow"*
- User says: *"Turn this pattern into a skill"*
- User says: *"Evolve/improve this skill"*
- User says: *"Auto-generate a skill from my logs"*
- System detects: Repeated tool sequences or command patterns
- User says: *"meta-skill-evolver"* (direct invocation)

## Skill Generation Pipeline

### Pattern Detection

The evolver analyzes conversation history to extract:

- **Tool Call Sequences**: Which tools are invoked together, in what order, with what parameters
- **Command Patterns**: Repeated shell commands, Python operations, or file manipulations
- **Error Recovery**: How failures are handled, what retries are attempted, what fallbacks are used
- **Parameter Trends**: Common values, ranges, defaults, and dependencies between parameters
- **Decision Trees**: Conditional logic based on tool output, file content, or system state

Example: If logs show repeated `read_file → search → edit_block` sequences, the evolver extracts this as a "Find and Replace" skill pattern.

### Skill Scaffolding

Once patterns are detected, the evolver generates:

1. **Directory Structure**:
   ```
   skill-name/
   ├── SKILL.md          (frontmatter + instructions)
   ├── scripts/
   │   └── main_script.py (automation implementation)
   └── references/
       └── supporting-docs.md
   ```

2. **SKILL.md Template**:
   - Frontmatter with only `name` and `description` fields
   - Usage instructions based on detected triggers
   - Examples section with representative scenarios
   - Step-by-step workflow description
   - Integration notes

3. **Python Scripts**:
   - Standalone, stdlib-only implementation
   - Command-line interface with clear argument handling
   - Error handling and logging
   - Output in JSON or human-readable formats
   - ~500 lines for typical skills

4. **Reference Documentation**:
   - Technical background and rationale
   - Advanced options and customization
   - Troubleshooting guide
   - Related skills and cross-references

### Content Generation

The evolver writes comprehensive instructions including:

- **Activation Triggers**: Keywords and phrases that invoke the skill
- **Input Specification**: What data the skill expects (file paths, parameters, formats)
- **Processing Logic**: Step-by-step explanation of how the skill processes inputs
- **Output Specification**: What the skill produces and in what format
- **Error Handling**: How the skill responds to edge cases, missing data, or invalid inputs
- **Examples**: At least 3-5 representative use cases with inputs and expected outputs

### Script Generation

Python scripts follow these patterns:

- **Minimal Dependencies**: Use only Python standard library (json, re, pathlib, etc.)
- **CLI Interface**: `python3 script.py [command] [options]`
- **Structured Output**: JSON for programmatic use, human-readable text for interactive use
- **Error Handling**: Try-except blocks with informative error messages
- **Logging**: Debug-level logging to help troubleshoot failures
- **Testing Hooks**: Fixture data paths, test runner integration

### Reference Generation

Supporting documentation includes:

- **Skill Anatomy**: Explanation of SKILL.md structure and frontmatter requirements
- **Advanced Usage**: Non-obvious ways to combine the skill with others
- **Performance Tuning**: How to optimize for speed, memory, or accuracy
- **Troubleshooting**: Common errors and solutions
- **Related Skills**: Links to complementary or dependent skills

## Skill Validation Gate

### Schema Validation

- **Frontmatter Check**: Only `name` and `description` fields allowed. No tags, version, author, or custom fields.
- **Description Validation**: Must use `>` block scalar syntax for multi-line descriptions. Must be descriptive and actionable.
- **YAML Syntax**: Must parse without errors. Must be valid YAML 1.2.

### Directory Structure Validation

- Skill directory exists with correct naming (kebab-case)
- SKILL.md file exists at root
- scripts/ directory exists with at least one Python file
- references/ directory exists with at least one markdown file
- No hidden files (starting with .) except .gitignore
- No __pycache__ directories

### Python Syntax Verification

- All .py files compile without syntax errors (py_compile)
- No import errors for stdlib modules
- Scripts have proper error handling (try-except blocks)
- Scripts include `if __name__ == '__main__'` entry point

### Script Size Checks

- Main scripts should be 300-800 lines for typical skills
- Avoid monolithic 1000+ line scripts (break into modules)
- Avoid trivial <100 line scripts (reconsider skill value)
- Flag unusually large or small scripts for review

### Markdown Quality

- SKILL.md has proper heading hierarchy (H1 → H2 → H3)
- Code blocks are properly fenced with language tags
- At least 3-5 examples provided
- All sections are substantive (not placeholder text)
- External links use proper markdown syntax

## Skill Testing Gate

### Auto-Generated Test Cases

The evolver generates tests by parsing the skill's SKILL.md examples section:

- Extract input/output pairs from examples
- Create fixture files based on example data
- Generate test assertions for expected outputs
- Create edge case tests (empty inputs, missing files, invalid parameters)

### Fixture Data Management

- Fixture files stored in `tests/fixtures/` directory
- Sample data files represent realistic use cases
- Includes both happy-path and error-case examples
- Minimal fixtures (< 1 MB total)

### Test Execution

- Run main script against all fixtures
- Capture stdout, stderr, exit codes
- Compare against documented expected outputs
- Verify script completes in reasonable time (< 30 seconds typical)
- Check for unhandled exceptions

### Test Reporting

- Summary: passed/failed/skipped counts
- Details: which fixtures passed/failed and why
- Performance: execution times for each test
- Coverage: which code paths were exercised
- Recommendations: fix failing tests or update documentation

## Skill Packaging Gate

### Pre-Package Cleanup

- Remove all __pycache__ directories
- Remove all .pyc and .pyo files
- Remove hidden files (except intentional .gitignore)
- Remove temporary files (*~, *.bak)
- Remove large artifacts (test outputs > 10 MB)

### Zip Creation

- Create .skill archive (zip format with .skill extension)
- Preserve directory structure within archive
- Include SKILL.md, scripts/, references/
- Set appropriate file permissions (755 for scripts)
- Add optional README.txt with installation instructions

### Integrity Verification

- Zip file can be read without errors
- All expected files present in archive
- SKILL.md and main script are readable
- Archive size is reasonable (typical: 50 KB - 5 MB)

### Size Sanity Checks

- Reject archives > 10 MB (too large for typical skills)
- Reject archives < 5 KB (too small, likely incomplete)
- Warn if archive exceeds 2 MB (may be overweight)

## Skill Evolution (Recursive Improvement)

### Performance Metrics

The evolver tracks:

- **Success Rate**: Percentage of invocations that completed without errors
- **Execution Time**: Average time to run the skill (per invocation)
- **Error Frequency**: Count and types of errors encountered
- **User Ratings**: If available, user satisfaction/helpfulness ratings
- **Trigger Accuracy**: How often the skill is invoked correctly vs. false positives

### Improvement Opportunity Detection

The evolver identifies improvements when:

- **Missing Edge Cases**: Error logs show unhandled scenarios
- **Script Errors**: Repeated failures on specific inputs
- **Trigger Inaccuracy**: Skill invoked incorrectly > 10% of attempts
- **Performance Regression**: Execution time increasing over versions
- **Documentation Gaps**: User confusion based on error patterns

Examples:

- If the skill consistently fails on empty files, improve input validation
- If users invoke the skill for unrelated tasks, refine trigger descriptions
- If execution time exceeds 30 seconds on large inputs, optimize algorithms

### Version Generation

The evolver generates improved versions by:

1. **Analyzing Errors**: Parse error logs to understand failure modes
2. **Generating Fixes**: Improve error handling, edge case coverage, or documentation
3. **Code Optimization**: Improve performance or readability if needed
4. **Documentation Refinement**: Clarify descriptions and examples
5. **Create New Version**: Generate v2, v3, etc. with improvements

### A/B Testing

When a new version is ready:

1. Deploy both old and new versions
2. Route a percentage of invocations to each (e.g., 80% old / 20% new)
3. Track success rates and error frequencies for each
4. If new version succeeds, promote it and retire old version
5. If new version fails, rollback and iterate

### Auto-Promotion

The evolver automatically promotes improved versions when:

- New version has > 95% success rate
- New version outperforms old version by > 10% on key metrics
- New version handles edge cases that old version failed on
- User feedback indicates improvement

## Skill Registry

### Registry Structure

A JSON-based inventory of all generated skills:

```json
{
  "skills": [
    {
      "name": "file-batch-processor",
      "location": "/path/to/skill",
      "version": "1.2.3",
      "created": "2026-03-01T10:30:00Z",
      "last_updated": "2026-03-13T14:22:00Z",
      "performance_score": 0.94,
      "invocation_count": 156,
      "error_count": 9,
      "success_rate": 0.942,
      "dependencies": ["pattern-matcher", "data-validator"],
      "related_skills": ["csv-processor", "json-transformer"],
      "status": "active"
    }
  ],
  "skill_map": {
    "file-batch-processor": { "index": 0 }
  }
}
```

### Registry Operations

- **Register**: Add new skill entry with initial metadata
- **Update**: Modify skill status, version, performance scores
- **Query**: Find skills by name, dependencies, or status
- **Recommend**: Suggest skill merges/splits based on overlap
- **Lint**: Check for orphaned skills or broken dependencies

### Dependency Mapping

The registry tracks:

- **Direct Dependencies**: Which skills depend on which other skills
- **Transitive Dependencies**: All skills in the dependency chain
- **Circular Dependency Detection**: Prevent circular imports/invocations
- **Compatibility Tracking**: Which skill versions work together

### Redundancy Detection

The evolver identifies:

- **Overlapping Triggers**: Multiple skills with similar activation patterns
- **Code Duplication**: Shared logic between skill scripts
- **Functional Overlap**: Skills that perform similar transformations
- **Suggestions**: Recommend merging similar skills or creating shared utilities

## Pipeline Runner

The pipeline orchestrates the entire workflow:

```
Pattern Detection → Scaffolding → Validation ↘
                                    ↓
                              Testing ↘
                                    ↓
                              Packaging ↘
                                    ↓
                              Registry Update ↘
                                    ↓
                              Optional: Evolution
```

### Pipeline Execution

- **Sequential**: Each stage waits for previous stage to complete
- **Failure Handling**: Stop on validation/testing failure, allow override with `--force`
- **Reporting**: Human-readable summary of each stage
- **Rollback**: Option to revert to previous version if new version fails

### CLI Commands

```bash
python3 skill_evolver.py generate [--from-pattern PATTERN_ID]
python3 skill_evolver.py validate [SKILL_PATH]
python3 skill_evolver.py test [SKILL_PATH]
python3 skill_evolver.py package [SKILL_PATH]
python3 skill_evolver.py evolve [SKILL_NAME]
python3 skill_evolver.py registry [list|query|lint]
python3 skill_evolver.py pipeline [SKILL_PATH]
```

## Integration Points

### With skill-validator

The evolver invokes the skill-validator skill for comprehensive validation checks beyond schema and syntax.

### With skill-test-harness

The evolver integrates with test-harness for test execution, fixture management, and reporting.

### With pre-package-pipeline

The evolver uses pre-package-pipeline to clean, verify, and prepare skills for distribution.

### With Pattern Logger

The evolver reads from a pattern logger that tracks tool invocations and command sequences across all sessions.

## Examples

### Example 1: Auto-Generate a CSV Processing Skill

User: *"I keep doing the same thing: read CSV, filter by date, sum a column, write output. Create a skill for this."*

The evolver:
1. Detects the pattern: `read_file → parse CSV → filter → sum → write_file`
2. Extracts parameters: column names, date ranges, output format
3. Generates skill: "csv-processor" with CLI for filtering and aggregation
4. Creates examples: filtering Q1 2026 data, summing revenue by region
5. Validates YAML and Python syntax
6. Tests against sample CSV files
7. Packages as csv-processor.skill
8. Registers in skill registry

### Example 2: Evolve a Skill Based on Error Patterns

Skill "json-transformer" has 15% error rate on deeply nested JSON structures.

The evolver:
1. Analyzes error logs: JSON depth > 10 levels causes recursion issues
2. Improves error handling: Add max depth check with informative error
3. Generates v1.1: Same interface, better error messages and edge case handling
4. Tests v1.1 against fixtures including deep JSON files
5. A/B tests: Routes 20% of invocations to v1.1
6. v1.1 succeeds on 98% of invocations (vs. 85% for v1.0)
7. Auto-promotes v1.1 to active, retires v1.0

### Example 3: Detect and Merge Overlapping Skills

Registry detects:
- Skill "csv-processor": filters and aggregates CSV data
- Skill "data-aggregator": filters and sums various data formats

The evolver:
1. Analyzes both skills: 80% code overlap
2. Suggests merge: Create "universal-data-processor" combining both
3. Generates merged version with unified CLI
4. Tests against fixtures from both original skills
5. Deprecates old skills, activates merged version
6. Updates registry: mark old skills as "deprecated", link to replacement

## Best Practices

1. **Skill Naming**: Use kebab-case (all lowercase, hyphens for word boundaries)
2. **Descriptions**: Be specific about what the skill does. Use verbs (generates, filters, transforms)
3. **Triggers**: Provide 3-5 activation keywords in description and examples
4. **Testing**: Always include at least 3 examples in SKILL.md
5. **Documentation**: Reference files should be substantial, not placeholder
6. **Versioning**: Semantic versioning (major.minor.patch) tracked in registry
7. **Dependencies**: Minimize external dependencies; prefer stdlib
8. **Performance**: Target < 30 seconds for typical invocations
9. **Error Handling**: Provide helpful error messages, not stack traces
10. **Compatibility**: Ensure new versions are backward compatible with old versions

## Troubleshooting

**Q: Skill validation fails on YAML frontmatter**
A: Ensure only `name` and `description` fields are present. Remove tags, version, author, and other custom fields. Use `>` for multi-line descriptions.

**Q: Python script has syntax errors**
A: Run `python3 -m py_compile script.py` to identify errors. Ensure all imports are from stdlib. Check indentation.

**Q: Tests fail on fixture data**
A: Verify fixture files match the input format expected by the script. Check script command-line arguments. Review error messages for clues.

**Q: Skill package is too large**
A: Remove large test files or sample data. Compress images if included. Consider splitting into multiple skills if functionality is diverse.

**Q: Evolution doesn't improve performance**
A: Review error logs for patterns. Ensure improvements address the root cause, not symptoms. Expand test coverage to include failing cases.
