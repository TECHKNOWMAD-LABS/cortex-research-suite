# Security Audit Severity Matrix and Remediation Guide

## Severity Classification Framework

| Severity | CVSS Score Range | Impact | Exploitability | Remediati Time | Definition |
|----------|------------------|--------|-----------------|-----------------|------------|
| Critical | 9.0-10.0 | Complete system compromise possible | Easy to very easy | Immediate (within hours) | Vulnerabilities allowing remote code execution, authentication bypass, or complete data exposure with minimal requirements |
| High | 7.0-8.9 | Significant functionality compromise | Moderate to easy | Urgent (within 24 hours) | Vulnerabilities enabling privilege escalation, SQL injection, cross-site scripting, or significant data exposure |
| Medium | 4.0-6.9 | Partial compromise or restricted access | Moderate | Within one week | Vulnerabilities requiring specific conditions, user interaction, or authenticated access to exploit |
| Low | 0.1-3.9 | Minimal impact under standard conditions | Difficult | Within one month | Vulnerabilities with limited impact, requiring unusual configurations or user action |
| Info | 0 | No security impact | N/A | As resources permit | Code quality issues, deprecated usage patterns, or configuration warnings without security implications |

## CWE-to-Severity Mapping

### Critical Severity

| CWE ID | CWE Title | Risk Description | Common Contexts |
|--------|-----------|------------------|-----------------|
| CWE-78 | Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection') | Attackers inject arbitrary commands through unsanitized input to operating system shells | subprocess calls, shell execution, system commands |
| CWE-89 | Improper Neutralization of Special Elements used in an SQL Query ('SQL Injection') | Attackers inject SQL statements through unsanitized input to modify database queries | Dynamic SQL construction, ORM misuse, prepared statement bypasses |
| CWE-94 | Improper Control of Generation of Code ('Code Injection') | Attackers inject code through eval, exec, or equivalent functions | Dynamic code execution, template rendering, pickle deserialization |
| CWE-502 | Deserialization of Untrusted Data | Unmarshalling untrusted data can lead to arbitrary code execution | Pickle, YAML, XML, Java serialization, messagepack |
| CWE-798 | Use of Hard-Coded Credentials | Static credentials embedded in source code enable direct account compromise | API keys, database passwords, SSH keys, tokens in code |
| CWE-259 | Use of Hard-Coded Password | Similar to CWE-798; static passwords in code or configuration | Hard-coded passwords in authentication logic, default credentials |

### High Severity

| CWE ID | CWE Title | Risk Description | Common Contexts |
|--------|-----------|------------------|-----------------|
| CWE-79 | Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Attackers inject scripts executed in victim's browser | Template injection, DOM XSS, stored XSS, reflected XSS |
| CWE-327 | Use of a Broken or Risky Cryptographic Algorithm | Weak or deprecated algorithms provide insufficient protection | MD5, SHA1 for hashing passwords, DES, RC4 for encryption |
| CWE-295 | Improper Certificate Validation | Missing or improper SSL/TLS certificate validation enables MITM attacks | Disabled certificate verification, ignoring hostname mismatches |
| CWE-306 | Missing Authentication for Critical Function | Critical functions accessible without authentication | Unprotected admin endpoints, password reset without verification |
| CWE-352 | Cross-Site Request Forgery (CSRF) | Attackers perform unauthorized actions on behalf of authenticated users | Missing CSRF tokens, token not properly validated |
| CWE-434 | Unrestricted Upload of File with Dangerous Type | Uploaded files can execute code or compromise system | Executable uploads, script uploads without validation |

### Medium Severity

| CWE ID | CWE Title | Risk Description | Common Contexts |
|--------|-----------|------------------|-----------------|
| CWE-200 | Exposure of Sensitive Information to an Unauthorized Actor | Information disclosure through error messages, logs, or responses | Verbose error messages, stack traces in production, debug output |
| CWE-330 | Use of Insufficiently Random Values | Weak randomness enables prediction or brute force of security tokens | Math.random(), weak RNG, predictable nonces |
| CWE-400 | Uncontrolled Resource Consumption | Resource exhaustion attacks can cause denial of service | Unbounded loops, no rate limiting, no request size limits |
| CWE-676 | Use of Potentially Dangerous Function | Functions with known security issues or unsafe characteristics | strcpy, gets, system(), eval, assert in production |
| CWE-703 | Improper Check or Handling of Exceptional Conditions | Missing or inadequate error handling | Unhandled exceptions, silent failures, assertions in production code |
| CWE-706 | Use of Incorrectly-Resolved Name | Reference to wrong object or function due to name shadowing | Variable name shadowing, incorrect import scope |
| CWE-863 | Incorrect Authorization | Authorization logic fails to properly restrict access | Missing permission checks, bypassable access controls |

### Low Severity

| CWE ID | CWE Title | Risk Description | Common Contexts |
|--------|-----------|------------------|-----------------|
| CWE-404 | Improper Resource Shutdown or Release | Resource leaks or incomplete cleanup | Unclosed file handles, unreleased database connections, memory leaks |
| CWE-477 | Use of Obsolete Function | Deprecated functions with limited support | deprecated library functions, superseded APIs |
| CWE-617 | Reachable Assertion | Assertion statements in production code can be triggered to crash application | assert statements, failed assertions in user paths |
| CWE-1007 | Hard-Coded Constant in Comparable Logic | Hard-coded values in conditional logic reduce flexibility | Magic numbers without explanation, hard-coded limits |

### Info Severity

| CWE ID | CWE Title | Risk Description | Common Contexts |
|--------|-----------|------------------|-----------------|
| CWE-2 | 7PK - Environment | Environmental configuration issues | Debug mode enabled, verbose logging, test code in production |
| CWE-1022 | Use of Web Link to Untrusted Target with window.opener Access | Linked pages can modify opener window | Links with target="_blank" without rel="noopener" |

## Remediation Priority Matrix

The priority score (1-5) combines severity and exploitability to guide remediation sequencing.

| Severity | Easy Exploit | Moderate Exploit | Difficult Exploit |
|----------|--------------|------------------|-------------------|
| Critical | Priority 1 (0-2 hours) | Priority 1 (0-4 hours) | Priority 1 (within 24 hours) |
| High | Priority 2 (4-24 hours) | Priority 2 (1-2 days) | Priority 3 (within 1 week) |
| Medium | Priority 3 (1-2 days) | Priority 4 (within 1 week) | Priority 4 (within 2 weeks) |
| Low | Priority 4 (within 1 week) | Priority 5 (within 1 month) | Priority 5 (within 1 month) |
| Info | Priority 5 (as time permits) | Priority 5 (as time permits) | Priority 5 (as time permits) |

## Bandit Test ID to CWE Mapping

| Bandit ID | Test Name | CWE ID | Severity | Risk Description |
|-----------|-----------|--------|----------|------------------|
| B101 | assert_used | CWE-703 | Medium | Assertion used in code that reaches production |
| B102 | exec_used | CWE-94 | Critical | Use of exec() function |
| B103 | set_bad_file_permissions | CWE-276 | High | File created with world-readable permissions |
| B104 | hardcoded_sql_expressions | CWE-89 | Critical | Hard-coded SQL strings (suggests injection risk) |
| B105 | hardcoded_sql_expressions | CWE-89 | Critical | Hard-coded SQL in string format |
| B106 | hardcoded_sql_expressions | CWE-89 | Critical | Hard-coded SQL with parameterization issues |
| B107 | hardcoded_temp_file | CWE-377 | Medium | Temporary file in insecure location |
| B108 | hardcoded_tmp_directory | CWE-377 | Medium | Hard-coded /tmp reference |
| B109 | password_config_option_not_found | CWE-259 | Critical | Password found in configuration |
| B110 | try_except_pass | CWE-703 | Medium | Bare except clause silently catches all exceptions |
| B111 | execute_with_run_as_root_equals_true | CWE-94 | High | Code execution with root privileges |
| B112 | request_with_no_cert_validation | CWE-295 | High | SSL/TLS verification disabled |
| B113 | unverified_context | CWE-295 | High | Unverified SSL context |
| B201 | flask_debug_true | CWE-489 | High | Flask debug mode enabled in production |
| B202 | tarfile_unsafe_members | CWE-94 | Critical | Tar extraction without member validation |
| B203 | unverified_jsonschema | CWE-94 | Medium | JSONSchema validation not properly applied |
| B301 | pickle_load | CWE-502 | Critical | Use of pickle.load() with untrusted data |
| B302 | marshal_load | CWE-502 | Critical | Use of marshal.load() with untrusted data |
| B303 | md2_is_broken | CWE-327 | High | MD2 hash algorithm is broken |
| B304 | md4_is_broken | CWE-327 | High | MD4 hash algorithm is broken |
| B305 | md5_is_broken | CWE-327 | High | MD5 hash algorithm is broken for security |
| B306 | mktemp_q_is_insecure | CWE-377 | Medium | mktemp() is insecure |
| B307 | random_is_insecure | CWE-330 | Medium | random module is not cryptographically secure |
| B308 | mark_safe | CWE-79 | High | Django mark_safe() disables auto-escaping |
| B309 | httpsconnection | CWE-295 | High | HTTPSConnection without certificate validation |
| B310 | urllib_urlopen | CWE-295 | Medium | urllib.urlopen() without verification |
| B311 | random_random | CWE-330 | Medium | random.random() is not cryptographically secure |
| B312 | telnetlib | CWE-295 | High | telnetlib lacks encryption |
| B313 | xml_bad_etree | CWE-827 | High | XML entity expansion vulnerability |
| B314 | xml_bad_pulldom | CWE-827 | High | XML entity expansion in pulldom |
| B315 | xml_bad_sax | CWE-827 | High | XML entity expansion in sax parser |
| B316 | xml_bad_expat | CWE-827 | High | XML entity expansion in expat parser |
| B317 | yaml_load | CWE-502 | Critical | yaml.load() with untrusted data |
| B318 | using_element_tree | CWE-827 | Medium | XML parser vulnerable to entity expansion |
| B319 | using_xml_sax | CWE-827 | Medium | XML sax parser vulnerable to entity expansion |
| B320 | using_xmlrpc | CWE-502 | High | xmlrpc can deserialize untrusted data |
| B321 | ftplib | CWE-295 | High | FTP connection lacks encryption |
| B322 | input_builtin | CWE-94 | Critical | input() function used (evaluates input as Python) |
| B323 | unverified_context | CWE-295 | High | Unverified SSL context |
| B324 | probable_insecure_hash_functions | CWE-327 | Medium | Possibly insecure hash function |
| B325 | tempnam_is_insecure | CWE-377 | Medium | tempnam() is insecure |
| B401 | telnetlib | CWE-295 | High | Telnet import |
| B402 | ftplib | CWE-295 | High | FTP import |
| B403 | import_pickle | CWE-502 | Medium | pickle import (high risk if used) |
| B404 | import_subprocess | CWE-78 | Medium | subprocess import (high risk if misused) |
| B405 | import_xml_etree | CWE-827 | Medium | XML etree import (XXE risk) |
| B406 | import_xml_sax | CWE-827 | Medium | XML sax import (XXE risk) |
| B407 | import_xml_expat | CWE-827 | Medium | XML expat import (XXE risk) |
| B408 | import_xmlrpc | CWE-502 | Medium | xmlrpc import |
| B409 | import_httpd | CWE-295 | Low | Simple HTTP server import |
| B410 | import_wsgiref | CWE-2 | Low | WSGI ref server import |
| B411 | import_telnetlib | CWE-295 | High | telnetlib import |
| B413 | import_pycrypto | CWE-327 | Medium | PyCrypto is deprecated (use cryptography) |
| B501 | request_with_no_cert_validation | CWE-295 | High | requests without certificate validation |
| B502 | ssl_with_bad_version | CWE-327 | High | SSL/TLS with deprecated protocol version |
| B503 | ssl_with_bad_defaults | CWE-327 | High | SSL/TLS with weak cipher suites |
| B504 | ssl_with_no_version | CWE-327 | High | SSL/TLS without explicit version |
| B505 | weak_cryptographic_key | CWE-326 | High | Cryptographic key too short |
| B506 | yaml_load_all | CWE-502 | Critical | yaml.load_all() with untrusted data |
| B507 | ssh_no_host_key_verification | CWE-295 | High | SSH connection without host key verification |
| B601 | paramiko_calls | CWE-295 | High | Paramiko call without security options |
| B602 | shell_injection | CWE-78 | Critical | Potential shell injection |
| B603 | subprocess_without_shell | CWE-78 | Medium | subprocess.Popen() used |
| B604 | any_other_function_with_shell_equals_true | CWE-78 | Critical | Function called with shell=True |
| B605 | start_process_with_a_shell | CWE-78 | Critical | Process started with shell |
| B606 | process_with_path_injection | CWE-78 | High | Process name includes path variable |
| B607 | partial_parameterized_query | CWE-89 | High | Partially parameterized SQL query |
| B608 | hardcoded_sql_expressions | CWE-89 | Critical | Hard-coded SQL expression |
| B609 | wildcard_injection | CWE-78 | High | Wildcard used in function call |
| B610 | sql_expression_string_formatting | CWE-89 | Critical | SQL string formatting (injection risk) |
| B611 | sql_expression_string_concatenation | CWE-89 | Critical | SQL string concatenation (injection risk) |
| B701 | jinja2_autoescape_false | CWE-79 | High | Jinja2 template with autoescape=False |
| B702 | mako_templates | CWE-79 | High | Mako templates allow code execution |
| B703 | django_mark_safe | CWE-79 | High | Django mark_safe() disables escaping |

## Secret Detection and Severity Classification

### Secret Type Severity Matrix

| Secret Type | Exposure Risk | Authentication Scope | Default Severity | Remediati Priority |
|-------------|---------------|--------------------|------------------|--------------------|
| Private Keys (RSA, DSA, EC) | Very High | System/application-wide access | Critical | Immediate revocation |
| Database Credentials | Very High | Full database access | Critical | Immediate revocation |
| API Keys (AWS, GCP, Azure) | Very High | Cloud infrastructure access | Critical | Immediate revocation |
| OAuth Tokens / Bearer Tokens | Very High | Bearer token access scope | Critical | Immediate revocation |
| Encryption Keys (master keys) | Very High | All encrypted data access | Critical | Immediate rotation |
| SSH Keys | Very High | Server authentication | Critical | Immediate revocation |
| SQL Connection Strings | High | Database server access | Critical | Immediate rotation |
| MongoDB Connection Strings | High | Database access | Critical | Immediate rotation |
| Passwords (general) | High | Account access | Critical | Immediate change |
| JWT Tokens | High | Token scope dependent | Critical | Immediate revocation |
| Slack/Discord Webhooks | High | Service-specific actions | High | Immediate rotation |
| Third-party API Keys | High | Service-specific scope | High | Immediate rotation |
| NPM/PyPI tokens | High | Package repository access | High | Immediate rotation |
| GitHub tokens | High | Repository access | High | Immediate rotation |
| AWS Access Keys | Critical | AWS account access | Critical | Immediate rotation |
| Service Principal Keys (Azure) | Critical | Azure service access | Critical | Immediate rotation |
| PagerDuty Tokens | Medium | Incident management | Medium | Within 24 hours |
| Stripe Keys | High | Payment processing | High | Immediate rotation |
| SendGrid API Keys | Medium | Email service | Medium | Within 24 hours |
| Basic Auth Credentials | High | HTTP authentication | High | Immediate rotation |

### Secret Detection Patterns

**High-Confidence Detection** (Critical severity if found):
- Private keys with standard headers (BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY, etc.)
- AWS access keys (AKIA followed by 16 alphanumeric characters)
- Azure connection strings with SharedAccessKey
- Database connection strings with passwords
- OAuth tokens and Bearer tokens with sufficient entropy
- Encrypted private key blobs with correct format
- Asymmetric key material in PEM format

**Medium-Confidence Detection** (High severity if found):
- Generic-looking API keys in context suggesting secrets
- Token-like strings with high entropy in source code
- SSH public key material (can indicate private key elsewhere)
- Configuration strings with embedded credentials

**Low-Confidence Detection** (Medium severity, requires review):
- Suspicious variable names with credential patterns (password, token, secret, key)
- Hard-coded configuration strings that might contain credentials
- Comments referencing credential locations

## Remediation Guidance by Vulnerability Type

### Critical Severity Remediation

**CWE-78 (OS Command Injection)**
- Replace shell execution with library functions or prepared command lists
- Never pass unsanitized user input to shell interpreters
- Use subprocess.run() with shell=False and list arguments
- Validate and whitelist all command parameters

**CWE-89 (SQL Injection)**
- Use parameterized queries / prepared statements for all database queries
- Employ ORMs with proper query builders
- Validate input against strict whitelist before use
- Never concatenate or format SQL strings with user input

**CWE-94 (Code Injection / eval)**
- Remove all eval(), exec(), and compile() calls on untrusted input
- Replace dynamic code generation with data-driven logic
- Use sandbox environments if dynamic code is unavoidable
- Implement strict input validation and whitelisting

**CWE-502 (Deserialization)**
- Deserialize only JSON from untrusted sources
- Avoid pickle, YAML, XML deserialization of untrusted data
- Use safe_load() for YAML if must be used
- Implement object type whitelisting for deserialization

**CWE-798/259 (Hard-Coded Credentials)**
- Remove all embedded credentials immediately
- Use environment variables or secure vaults for credentials
- Implement credential rotation policies
- Audit version control history and remove historical leaks
- Consider automated secret scanning in CI/CD

### High Severity Remediation

**CWE-79 (XSS)**
- Enable output encoding/escaping in all templating engines
- Use context-aware encoding (HTML, JS, CSS, URL contexts)
- Implement Content Security Policy headers
- Validate input against strict whitelist patterns

**CWE-327 (Broken Cryptography)**
- Replace MD5, SHA1, DES, RC4 with modern algorithms
- Use SHA-256+ for hashing, AES-256 for encryption
- Implement proper key derivation (PBKDF2, bcrypt, scrypt)
- Use cryptography library instead of PyCrypto

**CWE-295 (Insecure SSL/TLS)**
- Enable certificate validation in all HTTPS connections
- Implement proper hostname validation
- Use TLS 1.2 or higher, disable SSL 3.0/TLS 1.0/1.1
- Enforce strong cipher suites, disable weak algorithms

### Medium Severity Remediation

**CWE-330 (Insufficient Randomness)**
- Replace random.random() with secrets module or os.urandom()
- Use cryptographically secure random for tokens, nonces, IVs
- Ensure seed material has sufficient entropy
- Do not reuse random values

**CWE-400 (Resource Consumption)**
- Implement request rate limiting
- Set maximum request/response sizes
- Implement timeout controls
- Add resource quotas and monitoring

**CWE-703 (Error Handling)**
- Implement comprehensive try-except blocks
- Log detailed errors to secure locations
- Return generic error messages to users
- Never expose stack traces in production
- Gracefully handle all exception types

## Vulnerability Tracking and Reporting

When reporting vulnerabilities, use the following format for consistency:

```
Severity: [Critical | High | Medium | Low | Info]
CWE: CWE-XXXX [Title]
Bandit ID: B-XXX (if applicable)
Description: [Clear description of the issue]
Location: [File path and line number]
Affected Code: [Snippet of vulnerable code]
Recommendation: [Specific remediation steps]
Priority: [1-5 based on remediation matrix]
Exploitability: [Easy | Moderate | Difficult]
```

## Reference Standards

- OWASP Top 10 (2021)
- CWE/SANS Top 25 (2022)
- CVSS v3.1 Specification
- NIST Software Supply Chain Risk Management (SP 800-161)
