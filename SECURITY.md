# Security Policy

## Supported Versions

| Version | Status |
|---------|--------|
| main    | Supported |
| < 1.0   | Not Supported |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing admin@techknowmad.ai instead of using the public issue tracker.

Include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Any suggested fixes (optional)

## Response Timeline

- **48 hours**: Acknowledgment of receipt
- **7 days**: Security assessment and initial response
- **30 days**: Target resolution or mitigation plan

## Disclosure Policy

We follow a coordinated disclosure approach. Please allow 90 days from initial report for us to develop and release a fix before public disclosure. This window may be extended by mutual agreement.

## Scope

### In Scope
- Code vulnerabilities in the cortex repository
- Dependency vulnerabilities affecting the project
- Authentication and authorization issues
- Data handling and encryption concerns

### Out of Scope
- Social engineering or phishing
- Physical security concerns
- DoS attacks on infrastructure
- Vulnerabilities in third-party services
- Issues already publicly disclosed

## Trilogy integration security (v1.3.0)

### mindspider-connector
- SQL queries use parameterised placeholders (pymysql %s) — never f-strings or string concatenation
- Database URL read from environment variable only — never hardcoded, never logged
- Connection timeout: 10 seconds. Query timeout: 30 seconds.
- Demo mode (--source demo) generates synthetic data with no external connections

### intelligence-query
- All external source data passes through validate_topics() deduplication before LLM injection
- Input truncated to 50,000 characters maximum before any API call
- No raw external data passed to LLM prompts without length capping and HTML stripping

### multimodal-analyst
- Content-type detection runs BEFORE any analysis — prevents misclassification attacks
- Image URLs are not fetched client-side in any CLI script — only passed as references to the API
- hallucination_warnings field in output flags any claims that could not be grounded in input

### forum-intelligence
- Thread data sanitised (HTML stripped, length capped at 50,000 chars) before LLM prompt injection
- coordination_detected flag uses statistical heuristics only — no false positive tolerance for "coordinated"
- Minority viewpoint extraction does not conflate "minority" with "incorrect"

### scenario-simulator
- Agent personas are system-generated from LLM analysis, not user-supplied
- All simulation outputs include disclaimer: "Simulated outcomes for analytical purposes only"
- Seed report input capped at 3,000 characters
- No persistent state between simulation runs (each run is independent)

### GraphRAG knowledge store
- Graph stored as JSON (json.dump) — never pickle (pickle deserialization = arbitrary code execution)
- Triple extraction uses string operations and compiled regex — never eval() or exec()
- Graph file created with standard permissions (no world-writable)
- No external network calls during graph operations

### Browser Skill Arena (skill_arena_demo.html)
- API keys stored in sessionStorage only (cleared on tab close) — never localStorage
- Content Security Policy restricts script sources to self and cdnjs.cloudflare.com
- Auto-run capped at 20 experiments with re-confirmation required
- SKILL.md content truncated to 8,000 characters before API prompt injection
- No eval(), Function(), or innerHTML on API response content
- All diff rendering uses explicit HTML escaping
