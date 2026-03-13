---
name: tdd-enforcer
description: >
  Enforces test-driven development with mandatory RED-GREEN-REFACTOR cycles,
  anti-pattern detection, coverage gating, and test quality scoring. Blocks
  code that was written before tests. Use when "write tests first", "TDD",
  "tdd-enforcer", "test-driven", "RED-GREEN-REFACTOR", "test quality", or
  any testing enforcement request is mentioned.
---

# TDD Enforcer: Test-Driven Development Enforcement System

## Overview

The TDD Enforcer implements mandatory RED-GREEN-REFACTOR cycles with comprehensive anti-pattern detection, coverage gating, and test quality scoring. This skill enforces true test-driven development practices and prevents code quality degradation.

## RED-GREEN-REFACTOR Protocol (Non-Negotiable)

### 1. RED Phase: Write a Failing Test First
- Write test code **before** implementation code
- Test must fail when executed against nonexistent or incomplete implementation
- Test clearly documents expected behavior
- No exceptions to this rule

**Red Phase Checklist:**
- [ ] Test file exists with failing test
- [ ] Test name clearly describes behavior being tested
- [ ] Test uses meaningful assertions
- [ ] Implementation code does not exist (or incomplete)
- [ ] All team members can understand test intent

### 2. GREEN Phase: Write Minimal Code to Pass Test
- Write **only** the code necessary to make the test pass
- No speculation about future requirements
- No optimizations or refactoring yet
- All tests (new and existing) must pass

**Green Phase Checklist:**
- [ ] New test passes
- [ ] All existing tests still pass
- [ ] Code is intentionally simplistic
- [ ] No extra features beyond test requirements
- [ ] Implementation could be improved (that's next phase)

### 3. REFACTOR Phase: Clean Up While Tests Stay Green
- Improve code quality, readability, maintainability
- Extract methods, consolidate duplicates, clarify naming
- Tests serve as safety net—must stay green throughout
- Coverage must not decrease

**Refactor Phase Checklist:**
- [ ] All tests still pass
- [ ] Code is cleaner, more maintainable
- [ ] No functional changes
- [ ] Coverage maintained or improved
- [ ] Commit message references refactoring intent

### Enforcement Rules

**BLOCKING VIOLATIONS:**
- Code found without corresponding test → BLOCK commit
- Coverage drops below minimum thresholds → BLOCK commit
- Critical path uncovered → BLOCK commit
- Multiple high-severity anti-patterns detected → BLOCK commit

**WARNING VIOLATIONS:**
- Single anti-pattern instance → FLAG for fix
- Coverage approaching threshold → FLAG for improvement
- Test-to-code ratio suspiciously low → FLAG for review

## Test Anti-Pattern Detection (12 Patterns)

### 1. Mocked-to-Death
**Problem:** Test setup is >70% mocks/stubs; actual behavior not tested.

**Bad Example:**
```python
def test_user_creation(self):
    mock_db = MagicMock()
    mock_logger = MagicMock()
    mock_email = MagicMock()
    mock_cache = MagicMock()
    # 50 lines of mock configuration...
    user = UserService(mock_db, mock_logger, mock_email, mock_cache)
    user.create_user("john@example.com")
    mock_db.save.assert_called_once()  # Actually testing mock, not UserService
```

**Good Alternative:**
```python
def test_user_creation_saves_valid_user(self):
    """Test that valid user data is persisted."""
    service = UserService()
    user = service.create_user("john@example.com", "John")
    assert user.id is not None
    assert user.email == "john@example.com"
```

### 2. Assertion-Free
**Problem:** Test runs but never asserts anything; passes vacuously.

**Bad Example:**
```python
def test_api_endpoint(self):
    response = requests.get("/api/users")
    # No assertion! Test passes no matter what response is
```

**Good Alternative:**
```python
def test_api_endpoint_returns_users(self):
    response = requests.get("/api/users")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert all("id" in user for user in response.json())
```

### 3. Giant Test
**Problem:** Single test method >50 lines; tests too much; hard to debug failures.

**Bad Example:**
```python
def test_user_workflow(self):
    # 80 lines testing user creation, validation, update, deletion, etc.
    user = User("john@example.com")
    # ... 20 lines of setup ...
    assert user.is_valid()
    # ... 30 lines testing updates ...
    assert user.email_verified
    # ... 15 lines testing deletion ...
    assert not user.exists()
```

**Good Alternative:**
```python
def test_user_creation_with_valid_email(self):
    user = User("john@example.com")
    assert user.is_valid()

def test_user_email_verification_marks_verified(self):
    user = User("john@example.com")
    user.verify_email()
    assert user.email_verified

def test_user_deletion_removes_from_storage(self):
    user = User("john@example.com")
    user.delete()
    assert not user.exists()
```

### 4. Flickering/Flaky
**Problem:** Test results are non-deterministic; sometimes passes, sometimes fails randomly.

**Bad Example:**
```python
def test_concurrent_access(self):
    import time
    results = []
    for i in range(10):
        results.append(expensive_operation())
    # Timing-dependent; may fail under load, pass under low load
    assert len(results) == 10
```

**Good Alternative:**
```python
def test_concurrent_access_completes(self):
    """Test handles concurrent access with explicit synchronization."""
    from unittest.mock import patch
    with patch('time.sleep'):  # Avoid timing dependencies
        results = concurrent_operation(5)
        assert len(results) == 5
```

### 5. Tautological
**Problem:** Test can never fail; logic is a tautology.

**Bad Example:**
```python
def test_two_plus_two(self):
    result = 2 + 2
    assert result == 2 + 2  # Always true; doesn't test function

def test_list_not_empty(self):
    items = [1, 2, 3]
    assert items == items  # Redundant
```

**Good Alternative:**
```python
def test_addition_result(self):
    result = add(2, 2)
    assert result == 4

def test_populate_fills_list(self):
    items = populate()
    assert len(items) == 3
    assert items[0] == "expected_value"
```

### 6. Logic in Tests
**Problem:** Test code contains conditional logic (if/else); logic should be tested, not part of test.

**Bad Example:**
```python
def test_user_by_type(self, user_type):
    user = User(user_type)
    if user_type == "admin":
        assert user.has_permission("delete")
    elif user_type == "user":
        assert user.has_permission("read")
    else:
        assert not user.has_permission("write")
```

**Good Alternative:**
```python
def test_admin_can_delete(self):
    user = User("admin")
    assert user.has_permission("delete")

def test_regular_user_can_read_only(self):
    user = User("user")
    assert user.has_permission("read")
    assert not user.has_permission("delete")

def test_guest_cannot_write(self):
    user = User("guest")
    assert not user.has_permission("write")
```

### 7. Magic Numbers
**Problem:** Unexplained constants in assertions; unclear intent.

**Bad Example:**
```python
def test_user_age_validation(self):
    user = User(age=15)
    assert user.can_register() == False  # Why 15? Why not 16 or 18?
```

**Good Alternative:**
```python
def test_user_under_minimum_age_cannot_register(self):
    MINIMUM_AGE = 18
    user = User(age=MINIMUM_AGE - 1)
    assert not user.can_register()

def test_user_at_minimum_age_can_register(self):
    MINIMUM_AGE = 18
    user = User(age=MINIMUM_AGE)
    assert user.can_register()
```

### 8. Test-Per-Method
**Problem:** Mechanical 1:1 test-to-method ratio; tests behaviors instead of implementation details.

**Bad Example:**
```python
# Testing method names, not actual behavior
def test_get_name(self):
    user = User("John")
    assert user.get_name() == "John"

def test_get_age(self):
    user = User(age=30)
    assert user.get_age() == 30

def test_get_email(self):
    user = User("john@example.com")
    assert user.get_email() == "john@example.com"
```

**Good Alternative:**
```python
# Test behavior: creating user with valid data succeeds
def test_user_creation_with_complete_profile(self):
    user = User("John", age=30, email="john@example.com")
    assert user.id is not None
    assert user.is_valid()

# Test behavior: user validation fails with incomplete data
def test_user_validation_fails_without_email(self):
    user = User("John", age=30)
    assert not user.is_valid()
```

### 9. Shared Mutable State
**Problem:** Tests share state via class variables or globals; test order matters; tests interfere.

**Bad Example:**
```python
class TestUserService(unittest.TestCase):
    users = []  # Shared state!

    def test_add_user(self):
        user = User("john@example.com")
        self.users.append(user)  # Modifies class-level state
        assert len(self.users) == 1

    def test_add_another_user(self):
        user = User("jane@example.com")
        self.users.append(user)
        assert len(self.users) == 2  # Fails if test_add_user hasn't run
```

**Good Alternative:**
```python
class TestUserService(unittest.TestCase):
    def setUp(self):
        """Fresh state for each test."""
        self.service = UserService()
        self.users = []

    def test_add_user(self):
        user = self.service.create_user("john@example.com")
        self.users.append(user)
        assert len(self.users) == 1

    def test_add_another_user(self):
        # Fresh state from setUp, independent of other tests
        user = self.service.create_user("jane@example.com")
        self.users.append(user)
        assert len(self.users) == 1
```

### 10. Slow Test
**Problem:** Individual test takes >5 seconds; slows CI/CD feedback loop.

**Bad Example:**
```python
def test_data_processing(self):
    """This test takes 30 seconds to run."""
    results = []
    for i in range(100):
        results.append(real_api_call())  # Actual HTTP requests
        time.sleep(0.3)
    assert len(results) == 100
```

**Good Alternative:**
```python
def test_data_processing_handles_batch(self):
    """Fast test using mocked API."""
    from unittest.mock import patch
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        results = process_batch([1, 2, 3])
        assert len(results) == 3
        assert mock_get.call_count == 3
```

### 11. Caught Exception
**Problem:** Test catches exceptions silently; errors not asserted; test passes whether exception occurs or not.

**Bad Example:**
```python
def test_user_creation(self):
    try:
        user = User("invalid")
        assert user.email == "invalid"
    except ValueError:
        pass  # Silent catch; test passes if exception or not
```

**Good Alternative:**
```python
def test_user_creation_with_invalid_email_raises(self):
    """Explicitly test that invalid email raises ValueError."""
    with self.assertRaises(ValueError):
        User("invalid")

def test_user_creation_with_valid_email_succeeds(self):
    """Test successful creation separately."""
    user = User("john@example.com")
    assert user.email == "john@example.com"
```

### 12. Over-Specification
**Problem:** Test asserts on implementation details (private methods, internal state) instead of public behavior.

**Bad Example:**
```python
def test_caching_logic(self):
    """Testing internal implementation instead of behavior."""
    service = UserService()
    user = service.get_user("john")
    # Over-specified: testing internal cache structure
    assert service._cache["john"] == user
    assert service._cache_hit_count == 1
    assert service._last_access_time is not None
```

**Good Alternative:**
```python
def test_repeated_user_retrieval_is_efficient(self):
    """Test behavior: repeated calls are faster."""
    service = UserService()

    import time
    start = time.time()
    user1 = service.get_user("john")
    first_call_time = time.time() - start

    start = time.time()
    user2 = service.get_user("john")
    second_call_time = time.time() - start

    assert user1 == user2
    assert second_call_time < first_call_time  # Cached call is faster
```

## Coverage Gating

Coverage thresholds enforce quality baseline and prevent regressions:

### Minimum Coverage Thresholds
- **Line Coverage:** 80% (overall), 90% (new code)
- **Branch Coverage:** 70% (overall), 85% (new code)
- **Function Coverage:** 90% (overall), 95% (new code)

### Coverage Delta Rules
- New code must have >= 90% coverage
- Coverage cannot decrease (comparing against base branch)
- Critical paths (main, init, error handlers) must be 100% covered

### Critical Paths Requiring 100% Coverage
- Authentication/authorization paths
- Error handling paths
- Input validation logic
- Security-sensitive operations

## Test Quality Score (0-100)

Composite score calculated from:

### Scoring Components
1. **Anti-Pattern Count** (negative scoring)
   - Each pattern reduces score proportionally
   - Severe patterns (Assertion-Free, Over-Specification) have higher penalty
   - Score floor: 0 (all thresholds exceeded)

2. **Coverage Percentage** (weighted heavily)
   - 80%+ coverage: full points
   - 70-80%: partial points
   - <70%: significant penalty
   - Weight: 35% of total score

3. **Test-to-Code Ratio**
   - Ideal: 1 test file per module, 3-5 test methods per function
   - Too few tests: warning
   - Too many tests (over-specification): warning
   - Weight: 20% of total score

4. **Assertion Density**
   - Ideal: 2-3 assertions per test method
   - <1 assertion: major red flag
   - >10 assertions: usually indicates giant test
   - Weight: 20% of total score

5. **Edge Case Coverage**
   - Boundary values tested (min, max, 0, -1, etc.)
   - Null/None handling
   - Error path testing
   - Permission/authorization boundaries
   - Weight: 15% of total score

6. **Test Organization**
   - Clear test naming convention followed
   - Proper use of setUp/tearDown
   - Logical test grouping
   - Weight: 10% of total score

### Score Interpretation
- **90-100:** Excellent - production-ready test suite
- **75-89:** Good - acceptable with minor improvements
- **60-74:** Fair - significant anti-patterns present
- **40-59:** Poor - multiple quality issues
- **<40:** Critical - test suite unreliable

## Usage

### Integration with Development Workflow

**Before Code Review:**
```bash
python3 scripts/tdd_enforcer.py scan --target tests/ --threshold 75
```

**In CI/CD Pipeline:**
```bash
python3 scripts/tdd_enforcer.py scan --target tests/ \
  --threshold 85 \
  --coverage coverage.xml \
  --blocking-mode
```

**Developer Feedback Loop:**
```bash
python3 scripts/tdd_enforcer.py scan --target tests/ \
  --target-code src/ \
  --quality-report
```

### Expected Output
- Per-file anti-pattern findings
- Coverage report with delta analysis
- Composite quality score
- Blocking violations (if any)
- Actionable improvement recommendations

## Skill Activation

Use this skill when any of these terms appear:
- "write tests first"
- "TDD" or "test-driven development"
- "tdd-enforcer"
- "test-driven"
- "RED-GREEN-REFACTOR"
- "test quality"
- "testing enforcement"
- "code coverage gating"
- "anti-pattern detection"
