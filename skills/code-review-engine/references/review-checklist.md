# Code Review Checklist

Complete checklist for two-stage code review: Spec Compliance (Stage 1) and Code Quality (Stage 2).

## Stage 1: SPEC COMPLIANCE REVIEW

Use this checklist to validate that implementation matches the approved specification.

### 1.1 Requirements Coverage

- [ ] All functional requirements from spec are implemented
- [ ] Implementation covers all use cases mentioned in spec
- [ ] All acceptance criteria are satisfied
- [ ] Required features are not missing or incomplete
- [ ] Feature flags or conditional logic match spec description

**Example Check**:
```
Spec says: "User must be able to reset password via email link"
Code check: Verify password_reset module sends email, generates token, validates token
```

### 1.2 Function Signatures and APIs

- [ ] Function names match specification
- [ ] Parameter names and types match spec
- [ ] Return types match specification
- [ ] Exception types match spec error handling
- [ ] Method visibility (public/private) matches spec

**Example Check**:
```
Spec: def authenticate_user(email: str, password: str) -> Dict[str, str]
Code: Verify signature matches, not authenticate(username) or def login()
```

### 1.3 Edge Cases and Error Handling

- [ ] All edge cases mentioned in spec are handled
- [ ] Error paths from spec are implemented
- [ ] Timeout handling as specified is present
- [ ] Boundary conditions are validated (e.g., min/max)
- [ ] Fallback behavior matches specification

**Example Check**:
```
Spec says: "Handle timeout after 5 seconds with TimeoutError"
Code check: Verify timeout is 5s, not 10s; proper exception raised
```

### 1.4 Data Structures and Configuration

- [ ] Data structures match spec (field names, types)
- [ ] Configuration parameters as specified are supported
- [ ] Constants match values in specification
- [ ] Enums or allowed values match spec

**Example Check**:
```
Spec: status field has values: pending, active, completed
Code: Verify enum or validation accepts only these values
```

### 1.5 Dependencies and Integrations

- [ ] External dependencies match specification
- [ ] API integrations use specified endpoints
- [ ] Database schema matches spec requirements
- [ ] Third-party service usage as specified

**Example Check**:
```
Spec: "Use PostgreSQL 14+ with async driver"
Code: Verify postgres version, not MySQL; confirm async driver used
```

### 1.6 Performance Requirements

- [ ] Performance targets from spec are met
- [ ] Scalability requirements are addressed
- [ ] Response times meet specification
- [ ] Throughput requirements are achievable

**Example Check**:
```
Spec: "Handle 1000 concurrent users with <100ms response"
Code: Review caching, db queries, connection pooling
```

### 1.7 Security Requirements

- [ ] Security requirements from spec are implemented
- [ ] Authentication method matches spec
- [ ] Authorization model matches spec
- [ ] Data protection as specified is in place
- [ ] Audit logging as specified is present

**Example Check**:
```
Spec: "Require JWT token in Authorization header, validate signature"
Code: Verify JWT parsing, signature validation, not simple string check
```

## Stage 2: CODE QUALITY REVIEW

Use this checklist for analyzing code across five quality dimensions.

## 2.1 Correctness

Focus on logic errors, safety, and proper error handling.

### Logic and Algorithms

- [ ] Off-by-one errors in loops and indexing
- [ ] Correct loop bounds (should this be < or <=?)
- [ ] Proper initialization of variables
- [ ] Correct order of operations
- [ ] Boolean logic is correct (not inverted conditions)

**Example Issues**:
```python
# WRONG: Off-by-one error
for i in range(len(items)):
    process(items[i+1])  # IndexError on last item

# CORRECT
for i in range(len(items) - 1):
    process(items[i+1])

# WRONG: Inverted logic
if not user.is_authenticated:
    grant_access()  # Logic is backwards

# CORRECT
if user.is_authenticated:
    grant_access()
```

### Null/None Safety

- [ ] Null checks before dereferencing
- [ ] Optional types handled properly
- [ ] Default values for missing data
- [ ] No assumptions about input not being None

**Example Issues**:
```python
# WRONG: No null check
user = find_user(id)
return user.email  # Crashes if user is None

# CORRECT
user = find_user(id)
if user is None:
    raise ValueError(f"User {id} not found")
return user.email
```

### Resource Management

- [ ] Files are closed properly (use with statement)
- [ ] Database connections released
- [ ] Network connections closed
- [ ] Memory not leaked (no circular references in Python)
- [ ] Cleanup in exception handlers

**Example Issues**:
```python
# WRONG: File not closed on error
f = open("data.txt")
data = json.load(f)  # If this fails, file not closed
return data

# CORRECT
with open("data.txt") as f:
    data = json.load(f)  # File closed automatically
return data
```

### Type Safety

- [ ] Type consistency (not mixing strings and numbers)
- [ ] Proper type conversions
- [ ] Generic types used correctly
- [ ] No unsafe casts or assumptions

**Example Issues**:
```python
# WRONG: Type inconsistency
count = "5"
total = count + 10  # String + int

# CORRECT
count = int("5")
total = count + 10
```

## 2.2 Performance

Look for inefficient algorithms, unnecessary allocations, and bottlenecks.

### Algorithmic Complexity

- [ ] Algorithm is O(n) or better where possible
- [ ] Not O(n²) where O(n) is achievable
- [ ] Not recalculating values in loops
- [ ] Efficient data structures used (dict vs list for lookup)

**Example Issues**:
```python
# WRONG: O(n²) for simple task
def find_all_matches(haystack, needles):
    matches = []
    for needle in needles:
        for item in haystack:  # Loops through haystack each time
            if item == needle:
                matches.append(item)
    return matches

# CORRECT: O(n + m)
def find_all_matches(haystack, needles):
    haystack_set = set(haystack)
    return [n for n in needles if n in haystack_set]
```

### Memory Usage

- [ ] Not creating unnecessary copies of data
- [ ] Not loading entire files/databases into memory
- [ ] Proper use of generators for large datasets
- [ ] Not accumulating unbounded lists

**Example Issues**:
```python
# WRONG: Creates copy for each filter
data = load_large_file()
filtered = [x for x in data]  # Copy
filtered = [x for x in filtered if valid(x)]  # Another copy

# CORRECT: Single pass
def process_large_file(path):
    for line in open(path):  # Single copy, streaming
        if valid(line):
            yield line
```

### Database Queries

- [ ] No N+1 query patterns
- [ ] Queries use indexes
- [ ] Batch operations where possible
- [ ] Not querying in loops

**Example Issues**:
```python
# WRONG: N+1 queries
users = db.query(User).all()  # 1 query
for user in users:
    posts = db.query(Post).filter(author=user).all()  # N more queries

# CORRECT: Eager loading
users = db.query(User).options(joinedload(User.posts)).all()  # 1 query
```

### Caching and Memoization

- [ ] Expensive computations are cached
- [ ] Cache invalidation is correct
- [ ] Cache keys are unique
- [ ] Cache size is bounded

## 2.3 Security

Identify vulnerabilities and unsafe patterns.

### Input Validation

- [ ] All user input is validated
- [ ] Expected data types are enforced
- [ ] String length limits are enforced
- [ ] Numeric ranges are validated
- [ ] Whitelist validation preferred over blacklist

**Example Issues**:
```python
# WRONG: No validation
user_id = request.args.get('id')
user = db.query(User).filter(id=user_id).first()

# CORRECT: Validate input
user_id = request.args.get('id')
if not isinstance(user_id, int) or user_id <= 0:
    raise ValueError("Invalid user ID")
user = db.query(User).filter(id=user_id).first()
```

### SQL Injection

- [ ] Using parameterized queries/prepared statements
- [ ] Not concatenating user input into SQL
- [ ] No string formatting in queries
- [ ] ORM properly escapes values

**Example Issues**:
```python
# WRONG: SQL injection vulnerability
query = f"SELECT * FROM users WHERE email='{email}'"
db.execute(query)

# CORRECT: Parameterized query
query = "SELECT * FROM users WHERE email=?"
db.execute(query, (email,))
```

### Credential Management

- [ ] No hardcoded passwords or keys
- [ ] No credentials in source code
- [ ] Secrets loaded from environment
- [ ] Keys not logged or exposed in errors

**Example Issues**:
```python
# WRONG: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
password = "super_secret_password"

# CORRECT: Load from environment
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not set in environment")
```

### Dangerous Functions

- [ ] No eval() or exec() usage
- [ ] No pickle of untrusted data
- [ ] Dangerous library functions used safely
- [ ] System commands properly escaped

**Example Issues**:
```python
# WRONG: Code injection via eval
user_code = request.args.get('code')
result = eval(user_code)  # Executes arbitrary code!

# CORRECT: Use safe alternative
import ast
user_code = request.args.get('code')
node = ast.parse(user_code)
result = ast.literal_eval(node)
```

### Cryptography

- [ ] Hashing uses strong algorithms (bcrypt, argon2)
- [ ] Not using MD5 or SHA1 for passwords
- [ ] Proper key derivation functions used
- [ ] Random number generation is cryptographically secure

**Example Issues**:
```python
# WRONG: Weak hash for password
hash = hashlib.md5(password.encode()).hexdigest()

# CORRECT: Use proper password hashing
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)
```

## 2.4 Maintainability

Enable future developers to understand and modify code.

### Function Length

- [ ] Functions under 50 lines (general guideline)
- [ ] Single responsibility principle followed
- [ ] Complex logic extracted to helper functions
- [ ] Well-named functions explain their purpose

**Example Issues**:
```python
# WRONG: 150-line function doing many things
def process_user_data(user):
    # Validate input (20 lines)
    # Transform data (30 lines)
    # Save to database (20 lines)
    # Send email (40 lines)
    # Log activity (15 lines)
    # Update cache (25 lines)

# CORRECT: Smaller functions with clear purpose
def process_user_data(user):
    validate_user_input(user)
    transformed = transform_user_data(user)
    save_user(transformed)
    notify_user(user)
    log_user_action(user)
    update_user_cache(user)
```

### Cyclomatic Complexity

- [ ] Functions have complexity <= 10
- [ ] Excessive nesting (>3 levels) avoided
- [ ] Complex conditionals extracted to methods
- [ ] Switch statements over if-else chains

**Example Issues**:
```python
# WRONG: High complexity (6 paths)
def check_eligibility(user, age, income, credit_score):
    if user.is_active:
        if age >= 18:
            if income > 30000:
                if credit_score > 600:
                    if user.no_bankruptcy:
                        return True
    return False

# CORRECT: Extract logical checks
def check_eligibility(user, age, income, credit_score):
    return (
        user.is_active and
        is_legal_age(age) and
        has_sufficient_income(income) and
        has_good_credit(credit_score) and
        user.no_bankruptcy
    )
```

### Naming

- [ ] Variables have clear, descriptive names
- [ ] Single letter variables only for loop counters
- [ ] Function names describe what they do
- [ ] Class names are nouns, method names are verbs
- [ ] Avoid abbreviations except common ones (db, api)

**Example Issues**:
```python
# WRONG: Unclear names
def f(a, b):
    x = a * 2 + b
    if x > 100:
        return True
    return False

# CORRECT: Clear names
def is_total_above_threshold(base_amount, adjustment):
    total = base_amount * 2 + adjustment
    return total > 100
```

### Documentation

- [ ] Docstrings on public functions/classes
- [ ] Parameters and return types documented
- [ ] Complex algorithms explained with comments
- [ ] Why, not what (comments explain reasoning)

**Example Issues**:
```python
# WRONG: No documentation, redundant comment
def process(data):
    # Loop through data
    for item in data:
        x = item * 2  # Multiply by 2

# CORRECT: Clear documentation
def double_values(data: List[int]) -> List[int]:
    """
    Double all values in the input list.

    Args:
        data: List of integers to transform

    Returns:
        New list with all values doubled
    """
    return [x * 2 for x in data]
```

### DRY (Don't Repeat Yourself)

- [ ] No significant code duplication
- [ ] Common patterns extracted to utilities
- [ ] Shared logic in base classes or mixins
- [ ] Constants defined once

**Example Issues**:
```python
# WRONG: Duplicate validation logic
def create_user(name, email):
    if not name or len(name) < 2:
        raise ValueError("Invalid name")
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    # ... create user

def update_user(name, email):
    if not name or len(name) < 2:
        raise ValueError("Invalid name")
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    # ... update user

# CORRECT: Extract validation
def validate_user_input(name, email):
    if not name or len(name) < 2:
        raise ValueError("Invalid name")
    if not email or "@" not in email:
        raise ValueError("Invalid email")

def create_user(name, email):
    validate_user_input(name, email)
    # ... create user

def update_user(name, email):
    validate_user_input(name, email)
    # ... update user
```

## 2.5 Style and Conventions

Consistent code that follows language conventions.

### Language Standards (Python/PEP 8)

- [ ] Naming follows PEP 8 (snake_case for functions/variables)
- [ ] Line length under 100 characters
- [ ] 4-space indentation
- [ ] Spaces around operators: `x = 1`, not `x=1`
- [ ] Two blank lines between top-level functions

**Example Issues**:
```python
# WRONG: PEP 8 violations
myVariable = 5  # should be my_variable
def myFunction( ):  # Extra space, bad name
    x=myVariable*2  # No spaces around operators
    return x

# CORRECT: PEP 8 compliant
my_variable = 5

def calculate_doubled_value():
    return my_variable * 2
```

### Import Organization

- [ ] Standard library imports first
- [ ] Third-party imports second
- [ ] Local imports last
- [ ] Imports alphabetically sorted within groups
- [ ] No wildcard imports (except specific cases)

**Example Issues**:
```python
# WRONG: Unorganized imports
import my_module
import os
from third_party import something
import sys
from . import utils
import requests

# CORRECT: Organized imports
import os
import sys

import requests

from . import utils
from . import my_module
```

### Formatting Consistency

- [ ] Consistent quote style (single vs double)
- [ ] Consistent comment format
- [ ] No trailing whitespace
- [ ] Blank lines separate logical sections
- [ ] Consistent use of whitespace

**Example Issues**:
```python
# WRONG: Inconsistent quoting and spacing
name = "John"
email = 'john@example.com'
# This is a comment
x=5

# CORRECT: Consistent style
name = "John"
email = "john@example.com"
# This is a comment
x = 5
```

### Dead Code

- [ ] No unused variables or imports
- [ ] No commented-out code blocks
- [ ] No unreachable code
- [ ] No debug print statements left behind

**Example Issues**:
```python
# WRONG: Dead code
import unused_module
x = 5
x = 10  # x never used after this
# old_function()  # Commented out code
if False:  # Unreachable
    do_something()
print("DEBUG")  # Debug statement

# CORRECT: Clean code
x = 10
# Code is active, no debug statements
```

## Review Decision Matrix

Use this matrix to decide whether to request changes:

| Issue Type | CRITICAL | MAJOR | MINOR | INFO |
|-----------|----------|-------|-------|------|
| Spec Compliance | Blocks | Blocks | Can defer | Can defer |
| Security Vulnerability | Blocks | Depends | Can defer | Can defer |
| Logic Error | Blocks | Blocks | - | - |
| Performance Issue | Depends | Blocks | Can defer | Suggest |
| Style/Format | - | - | Can defer | Suggest |
| Documentation | - | - | Can defer | Suggest |

### Approval Criteria

- ✅ **APPROVED**: No critical issues, spec compliant, few/no major issues
- ⚠️ **APPROVED WITH SUGGESTIONS**: No critical issues, spec compliant, suggestions for improvement
- ❌ **CHANGES REQUESTED**: Critical issues present OR spec not compliant OR major issues blocking merge

## Tips for Effective Reviews

### For Reviewers

1. **Understand the context first** — Read the spec/requirements before reviewing code
2. **Run the code** — Don't just read; execute and test if possible
3. **Check the diffs carefully** — Focus on changes, not the entire file
4. **Be constructive** — Explain why, suggest how to fix
5. **Prioritize issues** — Focus on critical and major issues first
6. **Ask questions** — If logic is unclear, ask for clarification
7. **Appreciate good code** — Comment on well-written sections too

### For Authors

1. **Self-review first** — Find and fix obvious issues before requesting review
2. **Provide context** — Explain what changes and why
3. **Keep PRs small** — Easier to review, faster feedback
4. **Respond to feedback** — Engage with reviewer questions
5. **Don't argue needlessly** — Some issues are subjective; be pragmatic
6. **Test thoroughly** — Reviewer shouldn't find bugs; tests should

### Common Review Patterns

**Pattern 1: Logic seems off**
> "This condition looks inverted. Shouldn't it be `if not user.is_active:` instead of `if user.is_active:`?"

**Pattern 2: Potential performance issue**
> "This loops through the list for each item, making it O(n²). Consider using a set for O(n): `user_ids = set(users)` then `if user_id in user_ids:`"

**Pattern 3: Missing error handling**
> "What happens if this external API call fails? Consider wrapping in try/except and retrying."

**Pattern 4: Security concern**
> "This query uses f-string with user input. Use parameterized queries to prevent SQL injection: `db.execute(query, (user_input,))`"

**Pattern 5: Code quality improvement**
> "This function does several things. Consider extracting validation and transformation into separate functions."
