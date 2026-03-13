# Repository Publication Checklist

This checklist serves as a manual verification reference for the repo-publisher skill. Use this to ensure repositories meet publication standards before pushing to GitHub.

## Pre-Publish Checklist

### Structure Validation

- [ ] README.md exists and is non-empty
- [ ] LICENSE file exists (MIT, Apache-2.0, BSD, GPL-3.0, or equivalent)
- [ ] .gitignore exists and covers language-specific patterns
- [ ] No orphaned files in root (temp files, .DS_Store, __pycache__, *.pyc)
- [ ] Directory structure is logical and documented
- [ ] CHANGELOG.md present (recommended for versioned projects)
- [ ] CONTRIBUTING.md present for open-source projects (recommended)
- [ ] No build artifacts in committed files (dist/, build/, node_modules/)
- [ ] src/ or equivalent source directory is clearly organized

### Security Checks

- [ ] No hardcoded secrets, API keys, tokens, or passwords
- [ ] No .env files with real values committed
- [ ] No private keys (RSA, EC, PGP) in the repository
- [ ] No database connection strings with credentials
- [ ] No AWS/GCP/Azure credentials or service account keys
- [ ] subprocess calls use list form, not shell=True
- [ ] No eval/exec with user input
- [ ] No pickle.loads on untrusted data
- [ ] Dependencies pinned to specific versions (requirements.txt, package-lock.json, Cargo.lock)
- [ ] No known vulnerable dependency versions
- [ ] No commented-out code containing credentials
- [ ] Configuration files do not expose internal infrastructure

### Writing Quality

- [ ] README has clear project title and one-line description
- [ ] README has installation and setup instructions
- [ ] README has at least one usage example with actual code
- [ ] README references the license and provides link to LICENSE file
- [ ] No emoji in markdown headers or body text
- [ ] No hyperbolic marketing language or hype
- [ ] No generic filler phrases ("In today's rapidly evolving world...", "cutting-edge")
- [ ] Technical claims are specific and verifiable, not vague
- [ ] Consistent heading hierarchy (no skipped heading levels)
- [ ] All internal links are valid and resolve correctly
- [ ] Code examples are accurate and executable
- [ ] No broken Markdown syntax
- [ ] Tables render correctly if present
- [ ] Lists are properly formatted

### Git Hygiene

- [ ] No merge conflict markers in any file
- [ ] No TODO, FIXME, or HACK comments in shipped code
- [ ] Commit messages are descriptive (not "fix bug", "update")
- [ ] No giant binary files in commit history
- [ ] .gitignore prevents build artifacts from being committed
- [ ] Working branch is clean (no uncommitted changes)
- [ ] No stray temporary files (*.swp, *.tmp, *.bak)
- [ ] All commits are signed (optional but recommended)

### GitHub Metadata

- [ ] Repository description is set (concise, specific, no buzzwords)
- [ ] Topics/tags are relevant and follow GitHub conventions
- [ ] Website URL is set if applicable
- [ ] Default branch is 'main' (not 'master')
- [ ] README renders correctly on GitHub (no broken images or links)
- [ ] GitHub Pages is configured if documentation site is present
- [ ] Repository visibility is set correctly (public/private/internal)
- [ ] Branch protection rules are configured for main branch

### For Skills Specifically

- [ ] SKILL.md exists at repository root
- [ ] SKILL.md has valid YAML frontmatter
- [ ] Frontmatter includes: name, description
- [ ] Description is a single paragraph with no line breaks
- [ ] scripts/ directory exists if SKILL.md references scripts
- [ ] references/ directory exists if SKILL.md references references
- [ ] All referenced files in SKILL.md actually exist in the repository
- [ ] All referenced scripts are executable
- [ ] Trigger conditions cover common phrasings and use cases
- [ ] Example prompts work correctly when tested

## Verification Process

### Automated Checks
The repo-publisher skill performs these checks automatically:
- Structure validation
- Security scanning
- Dependency vulnerability checks
- Markdown syntax verification

### Manual Review Items
The following require manual verification:
- Writing quality and consistency
- Technical accuracy of examples
- Appropriateness of commit message history
- Relevance of repository metadata
- Completeness of documentation

## Publication Approval Criteria

A repository is ready for publication when:
1. All structure validation checks pass
2. All security checks pass
3. Writing quality review is complete with no issues
4. Git history contains no sensitive data
5. GitHub metadata is complete and accurate
6. For skills: SKILL.md is valid and all referenced files exist
7. Repository has been tested in the target environment

## Post-Publication

After publishing to GitHub:
- [ ] Verify repository appears in GitHub search
- [ ] Test repository clone and initial setup
- [ ] Confirm all links in README work correctly
- [ ] Check that GitHub Actions workflows (if any) pass
- [ ] Monitor for any missed issues in first 24 hours
