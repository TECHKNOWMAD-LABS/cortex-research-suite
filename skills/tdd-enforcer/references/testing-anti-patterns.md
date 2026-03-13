# Testing Anti-Patterns Reference Guide

Complete documentation of all 12 anti-patterns with examples, detection strategies, and fixes.

## 1. Mocked-to-Death

### Description
Test setup is >70% mocks and stubs; actual behavior of the system under test (SUT) is not validated. Tests become brittle, closely coupled to implementation, and provide false confidence.

### Problem
- Mock setup drowns out actual assertions
- When mocks change, tests break even if behavior is correct
- Tests validate mock configuration, not real functionality
- Maintenance burden increases as mocks must be updated

### Detection
- Line count analysis: mock lines / total lines > 0.70
- Keywords: `MagicMock`, `Mock`, `patch`, `@patch`, `mock_`
- Pattern: More mock setup than actual test logic

### Bad Example
```python
def test_user_creation(self):
    # 50 lines of mock configuration...
    mock_db = MagicMock()
    mock_db.save.return_value = True
    mock_db.query.return_value = [user1, user2]
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_email = MagicMock()
    mock_email.send.return_value = True
    mock_cache = MagicMock()
    mock_cache.set.return_value = None
    mock_config = MagicMock()
    mock_config.get.return_value = "value"

    # 2 lines of actual test
    user = UserService(mock_db, mock_logger, mock_email, mock_cache, mock_config)
    user.create_user("john@example.com")

    # Testing the mock, not the UserService
    mock_db.save.assert_called_once()
```

### Good Alternative
```python
def test_user_creation_saves_valid_user(self):
    """Test that valid user data is persisted."""
    # Use real database or minimal test double
    db = InMemoryUserDatabase()
    service = UserService(db)

    user = service.create_user("john@example.com", "John Doe")

    assert user.id is not None
    assert user.email == "john@example.com"
    assert db.get_user(user.id).email == "john@example.com"
```

### Fix Strategy
1. Replace mocks with real implementations where feasible
2. Use stubs (minimal implementations) instead of mocks
3. Mock only external dependencies (HTTP, database)
4. Keep mock setup to <30% of test code
5. Assert on real behavior, not mock calls

---

## 2. Assertion-Free

### Description
Test executes code but never asserts anything. Test always passes regardless of whether the code works. Provides zero value.

### Problem
- Test passes no matter what
- Detects no regressions
- Provides no documentation of expected behavior
- Waste of CI/CD resources

### Detection
- AST analysis: count `assert` statements
- Pattern: `try` blocks without `AssertionError`
- Keywords: no `assert`, `assertEqual`, `assertTrue`, etc.

### Bad Example
```python
def test_api_endpoint(self):
    response = requests.get("/api/users")
    # No assertion! Test passes whether response is 200, 404, 500, or anything

def test_database_connection(self):
    db = connect_to_database()
    # No assertion about connection success

def test_calculate_sum(self):
    result = calculate(5, 3)
    # No verification of result
```

### Good Alternative
```python
def test_api_endpoint_returns_users(self):
    response = requests.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_database_connection_succeeds(self):
    db = connect_to_database()
    assert db.is_connected()

def test_calculate_sum_returns_correct_total(self):
    result = calculate(5, 3)
    assert result == 8
```

### Fix Strategy
1. Add at least one assertion per test
2. Ideal: 2-3 assertions per test
3. Assert on business-meaningful values
4. Document why each assertion matters

---

## 3. Giant Test

### Description
Single test method >50 lines; tests multiple behaviors; hard to debug when it fails; takes too long to run; difficult to understand intent.

### Problem
- Failure diagnosis is difficult (which behavior failed?)
- Slow to execute
- Hard to understand test intent
- Often multiple test cases mixed together
- Maintenance burden increases

### Detection
- Line count analysis: test method length > 50 lines
- Pattern: Multiple `assert` statements with different contexts
- Keywords: lots of setup, multiple behaviors tested

### Bad Example
```python
def test_user_workflow(self):
    # Test 1: Create user (20 lines)
    user = User("john@example.com", "John Doe")
    assert user.is_valid()
    # ... 15 more lines of validation ...

    # Test 2: Update user (20 lines)
    user.update(email="john.doe@example.com")
    assert user.email == "john.doe@example.com"
    # ... 15 more lines of update verification ...

    # Test 3: Delete user (20 lines)
    user.delete()
    assert not user.exists()
    # ... 15 more lines of deletion verification ...
    # Total: 75 lines in one test
```

### Good Alternative
```python
def test_user_creation_with_valid_email(self):
    """Test: valid email accepted."""
    user = User("john@example.com", "John Doe")
    assert user.is_valid()

def test_user_creation_validates_email_format(self):
    """Test: invalid email rejected."""
    with self.assertRaises(ValueError):
        User("invalid", "John Doe")

def test_user_email_update_changes_email(self):
    """Test: updating email changes stored value."""
    user = User("john@example.com", "John Doe")
    user.update(email="john.doe@example.com")
    assert user.email == "john.doe@example.com"

def test_user_deletion_removes_from_storage(self):
    """Test: deleted user no longer exists."""
    user = User("john@example.com", "John Doe")
    user.delete()
    assert not user.exists()
```

### Fix Strategy
1. Split one giant test into multiple focused tests
2. One test = one behavior
3. Keep tests <30 lines (strict guideline: <50 lines)
4. Each test should have clear, single assertion
5. Use descriptive test names to explain intent

---

## 4. Flickering/Flaky

### Description
Test results are non-deterministic. Sometimes passes, sometimes fails. Often caused by timing issues, concurrency, or external dependencies.

### Problem
- Unreliable CI/CD signals
- Difficult to diagnose failures
- Team loses confidence in tests
- Wasted time re-running tests

### Detection
- Run test suite 10+ times; check for inconsistent results
- Look for: `time.sleep()`, threading, external API calls
- Pattern: Date/time-dependent assertions, timing-sensitive code

### Bad Example
```python
def test_concurrent_user_creation(self):
    """Flaky: timing-dependent."""
    import time
    results = []
    for i in range(10):
        results.append(expensive_api_call())
        time.sleep(0.1)  # Timing-dependent; may fail under load

    # May pass when fast, fail when slow
    assert len(results) == 10

def test_cache_expiration(self):
    """Flaky: time-dependent."""
    cache = Cache(ttl=100)
    cache.set("key", "value")
    time.sleep(101)  # Hard to predict actual timing
    assert cache.get("key") is None
```

### Good Alternative
```python
def test_concurrent_user_creation_completes(self):
    """Deterministic: no timing dependencies."""
    from unittest.mock import patch

    with patch('expensive_api_call') as mock_call:
        mock_call.return_value = {"id": 123, "status": "created"}
        results = [expensive_api_call() for _ in range(10)]
        assert len(results) == 10

def test_cache_expiration_after_ttl(self):
    """Deterministic: mock time."""
    from unittest.mock import patch
    import time

    cache = Cache(ttl=100)
    cache.set("key", "value")

    with patch('time.time') as mock_time:
        mock_time.return_value = time.time() + 101
        assert cache.get("key") is None
```

### Fix Strategy
1. Mock external dependencies (HTTP, file system, system time)
2. Replace `time.sleep()` with `unittest.mock.patch`
3. Use fake clocks for time-dependent code
4. Remove random delays, retry logic in tests
5. Make tests deterministic and repeatable

---

## 5. Tautological

### Description
Test logic is a tautology; assertion always true, can never fail. Provides no value.

### Problem
- Test can never fail
- No regression detection
- False confidence
- Waste of CI/CD resources

### Detection
- Pattern: comparing variable to itself
- Pattern: comparing constant to identical constant
- Pattern: logic that always evaluates to True

### Bad Example
```python
def test_two_plus_two(self):
    result = 2 + 2
    assert result == 2 + 2  # Always true; 4 == 4

def test_list_not_empty(self):
    items = [1, 2, 3]
    assert items == items  # Always true; redundant

def test_user_name(self):
    user = User("John")
    name = user.get_name()
    assert name == user.get_name()  # Always true; same call twice

def test_string_concatenation(self):
    text = "hello" + "world"
    assert text == "helloworld"  # Testing Python, not code
```

### Good Alternative
```python
def test_addition_of_two_and_two(self):
    result = add(2, 2)
    assert result == 4

def test_list_contains_expected_items(self):
    items = populate()
    assert len(items) == 3
    assert items[0] == "first"
    assert items[1] == "second"

def test_user_name_matches_constructor(self):
    user = User("John")
    assert user.get_name() == "John"

def test_concatenate_strings(self):
    result = concatenate("hello", "world")
    assert result == "helloworld"
```

### Fix Strategy
1. Assert on expected values, not variable re-comparison
2. Test function return values, not the function itself
3. Compare actual vs. expected constants
4. Use clear, business-meaningful assertions
5. Review logic: assertion should have potential to fail

---

## 6. Logic in Tests

### Description
Test code contains conditional logic (if/else, loops). Logic should be in implementation code, tested directly. Tests should be linear and transparent.

### Problem
- Test logic itself may have bugs
- Hard to understand test intent
- Logic duplication (test vs. implementation)
- Difficult to debug test failures

### Detection
- AST analysis: find `if`, `elif`, `else`, `for`, `while` in test methods
- Pattern: conditional branches based on test parameters

### Bad Example
```python
def test_user_by_type(self, user_type):
    """Anti-pattern: conditional logic in test."""
    user = User(user_type)
    if user_type == "admin":
        assert user.has_permission("delete")
    elif user_type == "user":
        assert user.has_permission("read")
    else:
        assert not user.has_permission("write")

def test_calculate_discount(self, amount):
    """Anti-pattern: test logic duplicates implementation logic."""
    discount = calculate_discount(amount)
    if amount > 1000:
        expected = amount * 0.2
    elif amount > 100:
        expected = amount * 0.1
    else:
        expected = 0
    assert discount == expected  # Test logic = implementation logic
```

### Good Alternative
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

def test_large_purchase_receives_20_percent_discount(self):
    discount = calculate_discount(1500)
    assert discount == 300  # 1500 * 0.2

def test_medium_purchase_receives_10_percent_discount(self):
    discount = calculate_discount(500)
    assert discount == 50  # 500 * 0.1

def test_small_purchase_receives_no_discount(self):
    discount = calculate_discount(50)
    assert discount == 0
```

### Fix Strategy
1. Remove all conditional logic from tests
2. Create separate test methods for each condition
3. Keep tests linear and easy to follow
4. Test logic belongs in implementation, assertions in tests
5. One behavior per test method

---

## 7. Magic Numbers

### Description
Unexplained numeric constants in assertions. Intent unclear. Hard to understand why that specific number.

### Problem
- Maintenance difficulty: why is this number important?
- Error-prone: future developer may not understand threshold
- Non-portable: magic numbers often depend on environment
- Documentation missing

### Detection
- Pattern: numeric constants in assertions (2+ digit numbers)
- Pattern: no descriptive constant name nearby
- Pattern: numbers without comments

### Bad Example
```python
def test_user_age_validation(self):
    user = User(age=15)
    assert user.can_register() == False  # Why 15? Why not 16 or 18?

def test_password_strength(self):
    password = "abc"
    assert not validate_password(password)  # Why 3? What makes it weak?

def test_api_rate_limit(self):
    for i in range(101):  # Why 101? Is 100 the limit?
        response = call_api()
    assert response.status_code == 429  # Magic numbers everywhere

def test_timeout_handling(self):
    start = time.time()
    result = long_operation()
    elapsed = time.time() - start
    assert elapsed < 5000  # 5000 what? Milliseconds? Seconds?
```

### Good Alternative
```python
def test_user_under_minimum_age_cannot_register(self):
    MINIMUM_REGISTRATION_AGE = 18
    user = User(age=MINIMUM_REGISTRATION_AGE - 1)
    assert not user.can_register()

def test_user_at_minimum_age_can_register(self):
    MINIMUM_REGISTRATION_AGE = 18
    user = User(age=MINIMUM_REGISTRATION_AGE)
    assert user.can_register()

def test_password_too_short_is_weak(self):
    MINIMUM_PASSWORD_LENGTH = 8
    short_password = "abc"
    assert not validate_password(short_password)

def test_password_sufficient_length_is_strong(self):
    MINIMUM_PASSWORD_LENGTH = 8
    strong_password = "MyP@ssw0rd123"
    assert validate_password(strong_password)

def test_api_rate_limit_enforced_at_threshold(self):
    RATE_LIMIT = 100  # requests per minute
    for i in range(RATE_LIMIT):
        response = call_api()
        assert response.status_code == 200

    # 101st request hits limit
    response = call_api()
    assert response.status_code == 429  # Too Many Requests

def test_operation_completes_within_timeout(self):
    MAX_OPERATION_TIME_SECONDS = 5
    start = time.time()
    result = long_operation()
    elapsed = time.time() - start
    assert elapsed < MAX_OPERATION_TIME_SECONDS
```

### Fix Strategy
1. Extract magic numbers into named constants
2. Place constants at top of test class or file
3. Add comments explaining why the number matters
4. Use descriptive constant names (MINIMUM_AGE, RATE_LIMIT, TIMEOUT_MS)
5. Consider moving constants to application configuration

---

## 8. Test-Per-Method

### Description
Mechanical 1:1 test-to-method ratio. Each method gets a test that just calls it. Tests don't verify behavior; they verify the method exists.

### Problem
- Tests don't verify behavior
- Over-testing trivial getters/setters
- Under-testing complex business logic
- Low-value test coverage

### Detection
- Count tests vs. methods
- Pattern: test names match method names exactly
- Pattern: tests just call method and assert return value

### Bad Example
```python
# Mechanical testing of getters
def test_get_name(self):
    user = User("John")
    assert user.get_name() == "John"

def test_get_age(self):
    user = User(age=30)
    assert user.get_age() == 30

def test_get_email(self):
    user = User("john@example.com")
    assert user.get_email() == "john@example.com"

def test_is_active(self):
    user = User()
    assert user.is_active() == True

def test_get_created_at(self):
    user = User()
    assert user.get_created_at() is not None
```

### Good Alternative
```python
# Test behavior: user creation with full profile succeeds
def test_user_creation_with_complete_profile(self):
    user = User("John", age=30, email="john@example.com")
    assert user.id is not None
    assert user.is_valid()

# Test behavior: incomplete profile is invalid
def test_user_without_email_is_invalid(self):
    user = User("John", age=30)
    assert not user.is_valid()

# Test behavior: new user is active by default
def test_new_user_is_active(self):
    user = User("John")
    assert user.is_active()

# Test behavior: inactive user cannot access system
def test_inactive_user_cannot_access_system(self):
    user = User("John")
    user.deactivate()
    with self.assertRaises(PermissionError):
        user.access_dashboard()
```

### Fix Strategy
1. Test behaviors and use cases, not individual methods
2. Write tests from user perspective ("I want to create a user")
3. Skip trivial getters/setters (focus on behavior-changing methods)
4. Group tests by feature or workflow
5. Test integration of multiple methods to verify behavior

---

## 9. Shared Mutable State

### Description
Tests share state via class variables or globals. Test order matters. Tests interfere with each other. Cleanup missing.

### Problem
- Tests are order-dependent
- Difficult to run tests in isolation
- Flaky tests (pass sometimes, fail other times)
- Hard to debug failures
- Cleanup logic is fragile

### Detection
- Pattern: class-level mutable variables
- Pattern: static test data modified across tests
- Pattern: missing setUp/tearDown
- Pattern: tests pass only when run together

### Bad Example
```python
class TestUserService(unittest.TestCase):
    users = []  # ANTI-PATTERN: shared state

    def test_add_user_1(self):
        user = User("john@example.com")
        self.users.append(user)  # Modifies class-level list
        assert len(self.users) == 1

    def test_add_user_2(self):
        user = User("jane@example.com")
        self.users.append(user)
        # Depends on previous test! Fails if run in different order
        assert len(self.users) == 2

class TestDatabase(unittest.TestCase):
    db = None  # Shared database connection

    def test_insert_record(self):
        self.db = Database.connect()
        self.db.insert("users", {"name": "John"})

    def test_query_records(self):
        # Depends on previous test inserting data
        results = self.db.query("users")
        assert len(results) > 0
```

### Good Alternative
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
        # Fresh state from setUp; no dependencies on other tests
        user = self.service.create_user("jane@example.com")
        self.users.append(user)
        assert len(self.users) == 1

    def tearDown(self):
        """Clean up after each test."""
        self.service.cleanup()
        self.users = []

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Fresh database connection for each test."""
        self.db = Database.connect(":memory:")  # In-memory, isolated

    def tearDown(self):
        """Close connection after test."""
        self.db.close()

    def test_insert_record(self):
        self.db.insert("users", {"name": "John"})
        assert self.db.record_count("users") == 1

    def test_query_records(self):
        # Independent of other tests; has fresh data
        self.db.insert("users", {"name": "John"})
        results = self.db.query("users")
        assert len(results) == 1
```

### Fix Strategy
1. Move mutable state from class level to instance level
2. Implement `setUp()` to initialize fresh state
3. Implement `tearDown()` to clean up
4. Use isolated test databases (in-memory)
5. Run tests in random order to catch dependencies
6. Avoid singleton patterns in test code

---

## 10. Slow Test

### Description
Individual test takes >5 seconds. Slows CI/CD feedback loop. Reduces test frequency. Increases frustration.

### Problem
- Slows down development feedback loop
- Discourages frequent test runs
- CI/CD pipelines take longer
- Encourages skipping tests locally

### Detection
- Run test suite with timing; identify tests >5 seconds
- Look for: real I/O (file, network, database), sleeps
- Pattern: external API calls, database queries without mocks

### Bad Example
```python
def test_data_processing(self):
    """This test takes 30 seconds to run."""
    results = []
    for i in range(100):
        results.append(requests.get("https://api.example.com/data"))  # Real HTTP
        time.sleep(0.3)

    assert len(results) == 100

def test_file_upload(self):
    """This test takes 10 seconds."""
    large_file = create_1gb_file()  # Real I/O
    response = upload_file(large_file)
    assert response.status_code == 200
    cleanup_file(large_file)

def test_database_operations(self):
    """This test takes 8 seconds."""
    for i in range(1000):
        db.insert("users", {"name": f"User{i}"})  # Real database
    results = db.query("users")
    assert len(results) == 1000
```

### Good Alternative
```python
def test_data_processing_handles_batch(self):
    """Fast test using mocked API (10ms)."""
    from unittest.mock import patch

    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"id": 1, "data": "value"}
        results = [requests.get("https://api.example.com/data") for _ in range(100)]
        assert len(results) == 100

def test_file_upload_succeeds(self):
    """Fast test using fake file (5ms)."""
    from io import BytesIO

    fake_file = BytesIO(b"file contents")
    response = upload_file(fake_file)
    assert response.status_code == 200

def test_database_operations_batch_insert(self):
    """Fast test using in-memory database (50ms)."""
    db = InMemoryDatabase()  # Fast, isolated
    for i in range(1000):
        db.insert("users", {"name": f"User{i}"})
    results = db.query("users")
    assert len(results) == 1000
```

### Fix Strategy
1. Mock external dependencies (HTTP, file I/O, database)
2. Use in-memory databases for testing
3. Replace `time.sleep()` with mocked time
4. Batch operations instead of looping
5. Move integration tests to separate suite (slower, run less frequently)

---

## 11. Caught Exception

### Description
Test catches exceptions silently (empty `except` blocks). Exception may or may not occur; test passes either way. No verification of exception behavior.

### Problem
- Test doesn't verify exception handling
- Silent failures
- No documentation of expected exceptions
- Exception might never be raised

### Detection
- Pattern: `try`/`except` with `pass` or empty body
- Pattern: catching all exceptions with `except: pass`
- Pattern: exception handling without assertions

### Bad Example
```python
def test_user_creation(self):
    try:
        user = User("invalid")
        assert user.email == "invalid"
    except ValueError:
        pass  # Silent catch; test passes whether exception occurs or not

def test_file_parsing(self):
    try:
        parse_file("nonexistent.txt")
    except:
        pass  # Exception silently ignored

def test_api_call(self):
    try:
        response = api_call()
        result = response.json()  # Could raise exception
    except Exception:
        pass  # Covers up any error
```

### Good Alternative
```python
def test_user_creation_with_invalid_email_raises(self):
    """Explicitly verify that invalid email raises ValueError."""
    with self.assertRaises(ValueError):
        User("invalid")

def test_user_creation_with_valid_email_succeeds(self):
    """Successful case is separate test."""
    user = User("john@example.com")
    assert user.email == "john@example.com"

def test_file_parsing_missing_file_raises(self):
    """Explicitly verify that missing file raises FileNotFoundError."""
    with self.assertRaises(FileNotFoundError):
        parse_file("nonexistent.txt")

def test_api_call_returns_valid_json(self):
    """Verify successful API call."""
    response = api_call()
    data = response.json()
    assert isinstance(data, dict)
    assert "id" in data
```

### Fix Strategy
1. Remove `try`/`except` from tests (use `assertRaises`)
2. Explicitly test exception cases with `self.assertRaises(ExceptionType)`
3. Separate happy path and error path tests
4. Document expected exceptions in docstring
5. Test exception message/code if relevant

---

## 12. Over-Specification

### Description
Test asserts on implementation details (private members, internal state, timing) instead of public behavior. Tests brittle to refactoring.

### Problem
- Tests break when implementation changes (even with same behavior)
- Discourages refactoring
- Tests know too much about internals
- Coupling between tests and implementation

### Detection
- Pattern: accessing private members (`_cache`, `_internal`)
- Pattern: testing internal state instead of behavior
- Pattern: assertion on method call counts to mocks
- Pattern: checking implementation details (private variables)

### Bad Example
```python
def test_caching_logic(self):
    """Over-specified: testing internal implementation."""
    service = UserService()
    user = service.get_user("john")

    # Testing internal cache structure (implementation detail)
    assert service._cache["john"] == user
    assert service._cache_hit_count == 1
    assert service._last_access_time is not None
    assert isinstance(service._cache, dict)

def test_api_retry_logic(self):
    """Over-specified: testing internal retry mechanism."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [ConnectionError(), {"data": "success"}]
        result = api_call_with_retry()

        # Testing internal implementation of retry (not behavior)
        assert mock_get.call_count == 2
        assert service._retry_count == 1
        assert service._last_retry_time is not None

def test_list_sorting(self):
    """Over-specified: testing implementation of sort."""
    items = [3, 1, 2]
    sorted_items = sort_items(items)

    # Implementation detail: is it using quicksort, mergesort, etc?
    assert sort_items.__name__ == 'quicksort'  # Over-specified
```

### Good Alternative
```python
def test_repeated_user_retrieval_is_efficient(self):
    """Test behavior: repeated calls are faster (caching works)."""
    service = UserService()

    import time
    start = time.time()
    user1 = service.get_user("john")
    first_call_time = time.time() - start

    start = time.time()
    user2 = service.get_user("john")
    second_call_time = time.time() - start

    assert user1 == user2
    assert second_call_time < first_call_time  # Caching makes it faster

def test_api_call_succeeds_after_transient_failure(self):
    """Test behavior: API call succeeds even if first attempt fails."""
    with patch('requests.get') as mock_get:
        # First attempt fails, second succeeds
        mock_get.side_effect = [ConnectionError(), {"data": "success"}]
        result = api_call_with_retry()

        assert result["data"] == "success"

def test_list_is_sorted_ascending(self):
    """Test behavior: items are in ascending order (not implementation)."""
    items = [3, 1, 2]
    sorted_items = sort_items(items)

    assert sorted_items == [1, 2, 3]
    assert all(sorted_items[i] <= sorted_items[i+1] for i in range(len(sorted_items)-1))
```

### Fix Strategy
1. Test public interface, not private implementation
2. Assert on behavior outcomes, not internal state
3. Mock external dependencies, not internal methods
4. Refactor tests when refactoring implementation (if behavior unchanged)
5. Focus on "does it work?" not "how does it work internally?"

---

## Summary: Anti-Pattern Detection Checklist

| Pattern | Detection Method | Severity | Fix |
|---------|-----------------|----------|-----|
| **Mocked-to-Death** | >70% mock lines | Warning | Use real objects, minimal mocks |
| **Assertion-Free** | 0 assertions | Critical | Add assertions |
| **Giant Test** | >50 lines | Warning | Split into focused tests |
| **Flaky** | Non-deterministic results | Critical | Mock external dependencies |
| **Tautological** | x == x pattern | Warning | Assert on actual values |
| **Logic in Tests** | if/else in tests | Warning | Separate tests per condition |
| **Magic Numbers** | Unexplained constants | Warning | Use named constants |
| **Test-Per-Method** | 1:1 test ratio | Warning | Test behaviors, not methods |
| **Shared Mutable State** | Class-level state | Critical | Use setUp/tearDown |
| **Slow Test** | >5 seconds | Warning | Mock I/O, use in-memory |
| **Caught Exception** | except: pass | Critical | Use assertRaises |
| **Over-Specification** | Private member asserts | Warning | Test behavior, not internals |

## Test Quality Standards

- Minimum test count: 1 test per feature/behavior
- Ideal assertion count: 2-3 per test
- Maximum test method length: 30-50 lines
- Minimum coverage: 80% overall, 90% new code
- Maximum test execution time: 5 seconds per test
- Anti-pattern count: 0-1 acceptable, 5+ blocking
