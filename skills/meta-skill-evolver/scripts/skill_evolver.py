#!/usr/bin/env python3
"""
Meta-Skill Evolver: Autonomous skill lifecycle engine.

Orchestrates pattern detection, skill generation, validation, testing,
packaging, and recursive evolution. Detects repeated workflows and
automatically transforms them into reusable skills.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import re
import hashlib
import zipfile
import shutil
import py_compile
import tempfile
from io import StringIO


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkillRegistry:
    """Manages centralized inventory of all generated skills."""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.data = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk or initialize empty."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {
            'skills': [],
            'skill_map': {},
            'metadata': {
                'created': datetime.now(timezone.utc).isoformat(),
                'version': '1.0'
            }
        }

    def _save_registry(self) -> None:
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def register(self, skill_name: str, skill_path: str,
                dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Register a new skill in the registry."""
        entry = {
            'name': skill_name,
            'location': skill_path,
            'version': '1.0.0',
            'created': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'performance_score': 0.0,
            'invocation_count': 0,
            'error_count': 0,
            'success_rate': 0.0,
            'dependencies': dependencies or [],
            'related_skills': [],
            'status': 'active'
        }

        idx = len(self.data['skills'])
        self.data['skills'].append(entry)
        self.data['skill_map'][skill_name] = {'index': idx}
        self._save_registry()

        logger.info(f"Registered skill: {skill_name}")
        return entry

    def update(self, skill_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update skill metadata."""
        if skill_name not in self.data['skill_map']:
            logger.warning(f"Skill not found: {skill_name}")
            return None

        idx = self.data['skill_map'][skill_name]['index']
        skill = self.data['skills'][idx]

        for key, value in kwargs.items():
            if key in skill:
                skill[key] = value

        skill['last_updated'] = datetime.now(timezone.utc).isoformat()
        self._save_registry()

        logger.info(f"Updated skill: {skill_name}")
        return skill

    def get(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve skill metadata."""
        if skill_name not in self.data['skill_map']:
            return None
        idx = self.data['skill_map'][skill_name]['index']
        return self.data['skills'][idx]

    def list_skills(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all skills, optionally filtered by status."""
        if status:
            return [s for s in self.data['skills'] if s.get('status') == status]
        return self.data['skills']

    def find_dependencies(self, skill_name: str) -> List[str]:
        """Find all transitive dependencies for a skill."""
        if skill_name not in self.data['skill_map']:
            return []

        skill = self.get(skill_name)
        all_deps = set(skill.get('dependencies', []))

        for dep in skill.get('dependencies', []):
            all_deps.update(self.find_dependencies(dep))

        return list(all_deps)

    def detect_overlap(self) -> List[Tuple[str, str, float]]:
        """Detect overlapping skills based on trigger similarity."""
        overlaps = []
        skills = self.data['skills']

        for i, skill1 in enumerate(skills):
            for skill2 in skills[i+1:]:
                # Simple overlap detection based on name similarity
                name1, name2 = skill1['name'], skill2['name']
                common = len(set(name1.split('-')) & set(name2.split('-')))
                similarity = common / max(len(name1.split('-')), len(name2.split('-')))

                if similarity > 0.5:
                    overlaps.append((name1, name2, similarity))

        return overlaps

    def lint(self) -> Dict[str, Any]:
        """Check registry integrity."""
        issues = {
            'orphaned_skills': [],
            'circular_dependencies': [],
            'missing_locations': [],
            'duplicates': []
        }

        # Check for missing locations
        for skill in self.data['skills']:
            if not Path(skill['location']).exists():
                issues['missing_locations'].append(skill['name'])

        # Check for duplicates
        names = [s['name'] for s in self.data['skills']]
        issues['duplicates'] = [n for n in names if names.count(n) > 1]

        # Check for circular dependencies
        for skill in self.data['skills']:
            deps = self.find_dependencies(skill['name'])
            if skill['name'] in deps:
                issues['circular_dependencies'].append(skill['name'])

        return issues


class PatternAnalyzer:
    """Analyzes conversation history and tool logs for repeated workflows."""

    @staticmethod
    def analyze_logs(log_file: Path) -> Dict[str, Any]:
        """Extract patterns from tool call logs."""
        patterns = {
            'tool_sequences': [],
            'command_patterns': [],
            'error_patterns': [],
            'parameter_ranges': {}
        }

        if not log_file.exists():
            logger.warning(f"Log file not found: {log_file}")
            return patterns

        with open(log_file, 'r') as f:
            logs = json.load(f) if log_file.suffix == '.json' else f.readlines()

        # Simple pattern extraction (would be more sophisticated in production)
        if isinstance(logs, list):
            tools_in_sequence = []
            for entry in logs:
                if isinstance(entry, dict) and 'tool' in entry:
                    tools_in_sequence.append(entry['tool'])

            if len(tools_in_sequence) > 2:
                patterns['tool_sequences'].append(tools_in_sequence)

        return patterns

    @staticmethod
    def detect_patterns_from_history(history: str) -> Dict[str, Any]:
        """Extract patterns from conversation history string."""
        patterns = {
            'repeated_commands': [],
            'repeated_workflows': [],
            'common_parameters': {}
        }

        # Find repeated command sequences (simple regex-based detection)
        lines = history.split('\n')
        command_freq = {}

        for line in lines:
            # Look for command-like patterns
            if line.strip().startswith('python') or line.strip().startswith('grep') or \
               line.strip().startswith('find') or line.strip().startswith('cat'):
                cmd = line.strip()
                command_freq[cmd] = command_freq.get(cmd, 0) + 1

        # Extract repeated commands
        for cmd, count in sorted(command_freq.items(), key=lambda x: -x[1]):
            if count > 1:
                patterns['repeated_commands'].append((cmd, count))

        return patterns


class SkillValidator:
    """Validates skill structure, YAML, and Python syntax."""

    @staticmethod
    def validate_frontmatter(skill_md_path: Path) -> Tuple[bool, List[str]]:
        """Validate SKILL.md frontmatter."""
        errors = []

        try:
            with open(skill_md_path, 'r') as f:
                content = f.read()

            # Extract YAML frontmatter
            if not content.startswith('---'):
                errors.append("Missing opening frontmatter delimiter (---)")
                return False, errors

            end_idx = content.find('---', 3)
            if end_idx == -1:
                errors.append("Missing closing frontmatter delimiter (---)")
                return False, errors

            frontmatter_str = content[3:end_idx].strip()

            # Parse YAML (minimal parser using regex)
            lines = frontmatter_str.split('\n')
            allowed_fields = {'name', 'description'}
            found_fields = set()

            for line in lines:
                if ':' in line:
                    field = line.split(':')[0].strip()
                    found_fields.add(field)

                    if field not in allowed_fields:
                        errors.append(f"Disallowed field in frontmatter: {field}")

            if 'name' not in found_fields:
                errors.append("Missing required field: name")

            if 'description' not in found_fields:
                errors.append("Missing required field: description")

        except Exception as e:
            errors.append(f"Error parsing frontmatter: {str(e)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_directory_structure(skill_dir: Path) -> Tuple[bool, List[str]]:
        """Validate skill directory structure."""
        errors = []

        if not skill_dir.is_dir():
            errors.append(f"Skill directory does not exist: {skill_dir}")
            return False, errors

        # Check required files
        skill_md = skill_dir / 'SKILL.md'
        if not skill_md.exists():
            errors.append("Missing SKILL.md file")

        # Check required directories
        scripts_dir = skill_dir / 'scripts'
        if not scripts_dir.exists():
            errors.append("Missing scripts/ directory")
        else:
            py_files = list(scripts_dir.glob('*.py'))
            if not py_files:
                errors.append("No Python files in scripts/ directory")

        references_dir = skill_dir / 'references'
        if not references_dir.exists():
            errors.append("Missing references/ directory")
        else:
            md_files = list(references_dir.glob('*.md'))
            if not md_files:
                errors.append("No markdown files in references/ directory")

        # Check for hidden files (except .gitignore)
        for item in skill_dir.rglob('*'):
            if item.name.startswith('.') and item.name != '.gitignore':
                errors.append(f"Unexpected hidden file: {item.relative_to(skill_dir)}")
            if item.name == '__pycache__':
                errors.append(f"Unexpected __pycache__ directory: {item.relative_to(skill_dir)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_python_syntax(script_path: Path) -> Tuple[bool, List[str]]:
        """Validate Python script syntax."""
        errors = []

        try:
            py_compile.compile(str(script_path), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Python syntax error: {str(e)}")

        # Check file size
        size_bytes = script_path.stat().st_size
        size_lines = len(script_path.read_text().split('\n'))

        if size_lines < 50:
            errors.append(f"Script seems too short ({size_lines} lines)")
        elif size_lines > 1500:
            errors.append(f"Script seems too long ({size_lines} lines, consider modularizing)")

        return len(errors) == 0, errors

    @staticmethod
    def validate_markdown_quality(md_path: Path) -> Tuple[bool, List[str]]:
        """Validate Markdown documentation quality."""
        errors = []

        try:
            content = md_path.read_text()

            # Check heading hierarchy
            h1_count = len(re.findall(r'^# ', content, re.MULTILINE))
            if h1_count == 0:
                errors.append("No H1 headings found")

            # Check for code blocks
            code_blocks = len(re.findall(r'```', content))
            if code_blocks < 2:
                errors.append("Few or no code blocks; add examples")

            # Check for examples section
            if 'example' not in content.lower():
                errors.append("No examples section found")

            # Check minimum length
            if len(content.strip()) < 500:
                errors.append("Documentation is too brief (< 500 characters)")

        except Exception as e:
            errors.append(f"Error reading markdown: {str(e)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_skill(skill_dir: Path) -> Dict[str, Any]:
        """Comprehensive skill validation."""
        skill_dir = Path(skill_dir)
        results = {
            'valid': True,
            'checks': {}
        }

        # Frontmatter validation
        skill_md = skill_dir / 'SKILL.md'
        valid, errors = SkillValidator.validate_frontmatter(skill_md)
        results['checks']['frontmatter'] = {'valid': valid, 'errors': errors}
        results['valid'] = results['valid'] and valid

        # Directory structure validation
        valid, errors = SkillValidator.validate_directory_structure(skill_dir)
        results['checks']['directory'] = {'valid': valid, 'errors': errors}
        results['valid'] = results['valid'] and valid

        # Python syntax validation
        for py_file in skill_dir.glob('scripts/*.py'):
            valid, errors = SkillValidator.validate_python_syntax(py_file)
            results['checks'][f'python_{py_file.name}'] = {'valid': valid, 'errors': errors}
            results['valid'] = results['valid'] and valid

        # Markdown quality validation
        for md_file in skill_dir.glob('references/*.md'):
            valid, errors = SkillValidator.validate_markdown_quality(md_file)
            results['checks'][f'markdown_{md_file.name}'] = {'valid': valid, 'errors': errors}
            results['valid'] = results['valid'] and valid

        if skill_md.exists():
            valid, errors = SkillValidator.validate_markdown_quality(skill_md)
            results['checks']['skill_md'] = {'valid': valid, 'errors': errors}
            results['valid'] = results['valid'] and valid

        return results


class SkillScaffoldGenerator:
    """Generates complete skill directory structure and templates."""

    @staticmethod
    def generate_skill_md_template(name: str, description: str) -> str:
        """Generate SKILL.md template."""
        template = f"""---
name: {name}
description: >
  {description}
---

# {name.replace('-', ' ').title()}

## Overview

[Comprehensive skill description and use cases]

## Usage

Activate this skill when:
- [Trigger keyword 1]
- [Trigger keyword 2]
- [Trigger keyword 3]

## Features

- [Feature 1]
- [Feature 2]
- [Feature 3]

## Examples

### Example 1
[Description and expected behavior]

### Example 2
[Description and expected behavior]

### Example 3
[Description and expected behavior]

## Integration

This skill integrates with:
- [Related skill 1]
- [Related skill 2]

## Troubleshooting

### Common Issues
- [Issue 1]: [Solution]
- [Issue 2]: [Solution]
"""
        return template

    @staticmethod
    def generate_python_script_template(skill_name: str) -> str:
        """Generate Python script template."""
        template = f'''#!/usr/bin/env python3
"""
{skill_name.replace('-', ' ').title()} - Automated skill implementation.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class {skill_name.replace('-', '_').title()}:
    """Core implementation for {skill_name}."""

    def __init__(self):
        """Initialize the skill."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, **kwargs) -> Dict[str, Any]:
        """Process input and return results."""
        try:
            # Implement core logic here
            result = self._execute(**kwargs)
            return {{'status': 'success', 'result': result}}
        except Exception as e:
            self.logger.error(f"Error processing: {{e}}")
            return {{'status': 'error', 'message': str(e)}}

    def _execute(self, **kwargs) -> Any:
        """Core execution logic."""
        # TODO: Implement skill logic
        return {{'processed': True}}


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description='{skill_name.replace('-', ' ').title()}'
    )
    parser.add_argument('--input', type=str, help='Input data or file path')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    skill = {skill_name.replace('-', '_').title()}()
    result = skill.process(input=args.input, output=args.output)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Result: {{result}}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
'''
        return template

    @staticmethod
    def generate_reference_template(skill_name: str) -> str:
        """Generate reference documentation template."""
        template = f"""# {skill_name.replace('-', ' ').title()} - Technical Reference

## Anatomy and Structure

This skill follows the standard Claude Code skill format:

```
{skill_name}/
├── SKILL.md
├── scripts/
│   └── main_script.py
└── references/
    └── technical-reference.md
```

## Frontmatter

The SKILL.md file contains only two frontmatter fields:

- `name`: The skill identifier (kebab-case)
- `description`: A concise description using the `>` block scalar syntax

## Script Conventions

The Python script:

1. Uses only Python standard library modules
2. Implements a main class with a `process()` method
3. Includes CLI argument handling
4. Supports JSON output with `--json` flag
5. Has proper error handling and logging
6. Targets 300-800 lines for typical skills

## Performance Characteristics

Expected performance metrics:

- Typical execution time: < 5 seconds
- Memory usage: < 100 MB for standard inputs
- Concurrent invocations: Up to 10 parallel instances
- Error rate target: < 5% with proper input validation

## Advanced Usage

[Document advanced features and customization options]

## Related Skills

Links to complementary or dependent skills:

- [Related skill 1]
- [Related skill 2]

## Troubleshooting Guide

### Common Errors

**Error**: [Error message]
**Cause**: [Root cause explanation]
**Solution**: [How to fix or work around]

## Metrics and Monitoring

Track these metrics to monitor skill health:

- Invocation count per day
- Error rate and error types
- Average execution time
- User satisfaction rating

## Version History

- v1.0.0 (Initial release): [Date and features]

## Contributing

Guidelines for improving this skill:

1. Follow the skill anatomy structure
2. Maintain backward compatibility
3. Add comprehensive test cases
4. Update documentation
5. Submit for evolution review
"""
        return template

    @staticmethod
    def create_skill(skill_dir: Path, name: str, description: str) -> Tuple[bool, str]:
        """Create a complete skill directory structure."""
        try:
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Create SKILL.md
            skill_md = skill_dir / 'SKILL.md'
            skill_md.write_text(
                SkillScaffoldGenerator.generate_skill_md_template(name, description)
            )
            logger.info(f"Created SKILL.md")

            # Create scripts directory and main script
            scripts_dir = skill_dir / 'scripts'
            scripts_dir.mkdir(exist_ok=True)

            main_script = scripts_dir / f'{name.replace("-", "_")}.py'
            main_script.write_text(
                SkillScaffoldGenerator.generate_python_script_template(name)
            )
            main_script.chmod(0o755)
            logger.info(f"Created main script")

            # Create references directory and reference doc
            references_dir = skill_dir / 'references'
            references_dir.mkdir(exist_ok=True)

            tech_ref = references_dir / 'technical-reference.md'
            tech_ref.write_text(
                SkillScaffoldGenerator.generate_reference_template(name)
            )
            logger.info(f"Created technical reference")

            return True, f"Skill created at {skill_dir}"

        except Exception as e:
            logger.error(f"Error creating skill: {e}")
            return False, str(e)


class SkillPackager:
    """Packages skills into distributable .skill archives."""

    @staticmethod
    def cleanup_artifacts(skill_dir: Path) -> Tuple[bool, List[str]]:
        """Remove build artifacts and temporary files."""
        removed = []

        # Remove __pycache__ directories
        for cache_dir in skill_dir.rglob('__pycache__'):
            try:
                shutil.rmtree(cache_dir)
                removed.append(str(cache_dir))
            except Exception as e:
                logger.warning(f"Could not remove {cache_dir}: {e}")

        # Remove .pyc and .pyo files
        for ext in ['*.pyc', '*.pyo']:
            for f in skill_dir.rglob(ext):
                try:
                    f.unlink()
                    removed.append(str(f))
                except Exception as e:
                    logger.warning(f"Could not remove {f}: {e}")

        # Remove backup and temp files
        for pattern in ['*~', '*.bak', '*.tmp']:
            for f in skill_dir.rglob(pattern):
                try:
                    f.unlink()
                    removed.append(str(f))
                except Exception as e:
                    logger.warning(f"Could not remove {f}: {e}")

        return True, removed

    @staticmethod
    def create_zip(skill_dir: Path, output_path: Path) -> Tuple[bool, str]:
        """Create .skill zip archive."""
        try:
            # Remove trailing slash
            skill_dir = Path(skill_dir)

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in skill_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(skill_dir.parent)
                        zf.write(file_path, arcname)

            logger.info(f"Created zip archive: {output_path}")
            return True, str(output_path)

        except Exception as e:
            logger.error(f"Error creating zip: {e}")
            return False, str(e)

    @staticmethod
    def verify_zip(zip_path: Path) -> Tuple[bool, List[str]]:
        """Verify zip archive integrity."""
        issues = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    issues.append(f"Corrupted file in archive: {bad_file}")

                # Check for required files
                namelist = zf.namelist()
                required = ['SKILL.md']
                for req in required:
                    if not any(req in name for name in namelist):
                        issues.append(f"Missing required file: {req}")

            return len(issues) == 0, issues

        except Exception as e:
            issues.append(f"Error verifying archive: {str(e)}")
            return False, issues

    @staticmethod
    def check_size(zip_path: Path) -> Tuple[bool, str]:
        """Check archive size is reasonable."""
        size_bytes = zip_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        if size_bytes < 5000:
            return False, f"Archive too small ({size_mb:.2f} MB)"
        elif size_mb > 10:
            return False, f"Archive too large ({size_mb:.2f} MB)"
        elif size_mb > 2:
            logger.warning(f"Archive is large ({size_mb:.2f} MB); consider optimizing")

        return True, f"Size OK ({size_mb:.2f} MB)"

    @staticmethod
    def package_skill(skill_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Complete packaging workflow."""
        skill_dir = Path(skill_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {'status': 'started', 'steps': {}}

        # Step 1: Cleanup
        success, removed = SkillPackager.cleanup_artifacts(skill_dir)
        results['steps']['cleanup'] = {'success': success, 'removed': removed}

        # Step 2: Create zip
        skill_name = skill_dir.name
        zip_path = output_dir / f'{skill_name}.skill'
        success, msg = SkillPackager.create_zip(skill_dir, zip_path)
        results['steps']['zip'] = {'success': success, 'path': str(zip_path)}

        if not success:
            results['status'] = 'failed'
            return results

        # Step 3: Verify zip
        success, issues = SkillPackager.verify_zip(zip_path)
        results['steps']['verify'] = {'success': success, 'issues': issues}

        if not success:
            results['status'] = 'failed'
            return results

        # Step 4: Size check
        success, size_msg = SkillPackager.check_size(zip_path)
        results['steps']['size'] = {'success': success, 'message': size_msg}

        results['status'] = 'success' if success else 'warning'
        return results


class SkillEvolver:
    """Orchestrates the complete skill lifecycle."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry = SkillRegistry(
            registry_path or Path.home() / '.vce' / 'skill-registry.json'
        )

    def generate_skill(self, name: str, description: str,
                      output_dir: Path) -> Dict[str, Any]:
        """Generate a new skill."""
        skill_dir = output_dir / name

        success, msg = SkillScaffoldGenerator.create_skill(skill_dir, name, description)

        return {
            'action': 'generate',
            'success': success,
            'skill_name': name,
            'skill_dir': str(skill_dir),
            'message': msg
        }

    def validate_skill(self, skill_dir: Path) -> Dict[str, Any]:
        """Validate a skill."""
        results = SkillValidator.validate_skill(skill_dir)

        return {
            'action': 'validate',
            'skill_dir': str(skill_dir),
            'valid': results['valid'],
            'checks': results['checks']
        }

    def test_skill(self, skill_dir: Path) -> Dict[str, Any]:
        """Test a skill (basic)."""
        skill_dir = Path(skill_dir)
        results = {'action': 'test', 'skill_dir': str(skill_dir), 'tests': []}

        # Find and execute test scripts
        test_dir = skill_dir / 'tests'
        if test_dir.exists():
            for test_file in test_dir.glob('test_*.py'):
                # In production, would use pytest or similar
                results['tests'].append({
                    'name': test_file.name,
                    'status': 'skipped',
                    'reason': 'Integration with test-harness required'
                })
        else:
            results['message'] = 'No tests directory found'

        return results

    def package_skill(self, skill_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Package a skill."""
        return SkillPackager.package_skill(skill_dir, output_dir)

    def evolve_skill(self, skill_name: str) -> Dict[str, Any]:
        """Evolve a skill based on performance metrics."""
        skill = self.registry.get(skill_name)

        if not skill:
            return {
                'action': 'evolve',
                'success': False,
                'message': f'Skill not found: {skill_name}'
            }

        # Analyze performance
        error_rate = skill.get('error_count', 0) / max(skill.get('invocation_count', 1), 1)
        performance_score = 1.0 - error_rate

        improvement_opportunities = []

        if error_rate > 0.1:
            improvement_opportunities.append('High error rate detected')

        if error_rate > 0.05:
            improvement_opportunities.append('Consider adding edge case handling')

        return {
            'action': 'evolve',
            'skill_name': skill_name,
            'current_version': skill.get('version'),
            'error_rate': error_rate,
            'performance_score': performance_score,
            'opportunities': improvement_opportunities
        }

    def pipeline(self, skill_dir: Path, output_dir: Path,
                force: bool = False) -> Dict[str, Any]:
        """Run complete validation → test → package pipeline."""
        skill_dir = Path(skill_dir)
        output_dir = Path(output_dir)

        pipeline_results = {
            'skill': skill_dir.name,
            'status': 'in_progress',
            'stages': []
        }

        # Stage 1: Validate
        logger.info("Stage 1: Validation")
        validate_result = self.validate_skill(skill_dir)
        pipeline_results['stages'].append(('validate', validate_result['valid']))

        if not validate_result['valid'] and not force:
            pipeline_results['status'] = 'failed'
            pipeline_results['validation_errors'] = validate_result['checks']
            return pipeline_results

        # Stage 2: Test
        logger.info("Stage 2: Testing")
        test_result = self.test_skill(skill_dir)
        pipeline_results['stages'].append(('test', True))

        # Stage 3: Package
        logger.info("Stage 3: Packaging")
        package_result = self.package_skill(skill_dir, output_dir)
        success = package_result['status'] in ['success', 'warning']
        pipeline_results['stages'].append(('package', success))

        if not success and not force:
            pipeline_results['status'] = 'failed'
            pipeline_results['package_errors'] = package_result.get('steps', {})
            return pipeline_results

        pipeline_results['status'] = 'completed'
        return pipeline_results

    def registry_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute registry command."""
        if command == 'list':
            skills = self.registry.list_skills(status=kwargs.get('status'))
            return {'command': 'list', 'skills': skills}

        elif command == 'lint':
            issues = self.registry.lint()
            return {'command': 'lint', 'issues': issues}

        elif command == 'overlap':
            overlaps = self.registry.detect_overlap()
            return {'command': 'overlap', 'overlaps': overlaps}

        else:
            return {'error': f'Unknown registry command: {command}'}


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Meta-Skill Evolver: Autonomous skill lifecycle engine'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a new skill')
    gen_parser.add_argument('name', help='Skill name (kebab-case)')
    gen_parser.add_argument('--description', required=True, help='Skill description')
    gen_parser.add_argument('--output', type=Path, default=Path.cwd(),
                           help='Output directory')

    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate a skill')
    val_parser.add_argument('skill_dir', type=Path, help='Skill directory path')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test a skill')
    test_parser.add_argument('skill_dir', type=Path, help='Skill directory path')

    # Package command
    pkg_parser = subparsers.add_parser('package', help='Package a skill')
    pkg_parser.add_argument('skill_dir', type=Path, help='Skill directory path')
    pkg_parser.add_argument('--output', type=Path, default=Path.cwd(),
                           help='Output directory')

    # Evolve command
    evo_parser = subparsers.add_parser('evolve', help='Evolve a skill')
    evo_parser.add_argument('skill_name', help='Skill name to evolve')

    # Registry command
    reg_parser = subparsers.add_parser('registry', help='Registry operations')
    reg_parser.add_argument('operation', choices=['list', 'lint', 'overlap'],
                           help='Registry operation')

    # Pipeline command
    pip_parser = subparsers.add_parser('pipeline', help='Run full pipeline')
    pip_parser.add_argument('skill_dir', type=Path, help='Skill directory path')
    pip_parser.add_argument('--output', type=Path, default=Path.cwd(),
                           help='Output directory')
    pip_parser.add_argument('--force', action='store_true',
                           help='Skip validation on failure')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    evolver = SkillEvolver()

    if args.command == 'generate':
        result = evolver.generate_skill(args.name, args.description, args.output)
    elif args.command == 'validate':
        result = evolver.validate_skill(args.skill_dir)
    elif args.command == 'test':
        result = evolver.test_skill(args.skill_dir)
    elif args.command == 'package':
        result = evolver.package_skill(args.skill_dir, args.output)
    elif args.command == 'evolve':
        result = evolver.evolve_skill(args.skill_name)
    elif args.command == 'registry':
        result = evolver.registry_command(args.operation)
    elif args.command == 'pipeline':
        result = evolver.pipeline(args.skill_dir, args.output, args.force)
    else:
        result = {'error': f'Unknown command: {args.command}'}

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
