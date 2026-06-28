# Fix Bug Command (Test-First)

Fix a bug using Test-Driven Development (TDD). Write a failing test first, then implement the fix.

**Usage:** `/fix-bug <bug-description>`

## CRITICAL: Test-First Approach

**YOU MUST write a failing test BEFORE writing any fix code.**

This is non-negotiable. The TDD cycle for bug fixes is:

1. **RED** - Write a test that reproduces the bug (test MUST fail)
2. **GREEN** - Write the minimal fix to make the test pass
3. **REFACTOR** - Clean up if needed (optional)

## Instructions

### Step 1: Understand the Bug

Based on the argument `$ARGUMENTS`:

1. Identify what the bug is and where it likely occurs
2. Search for related code using Grep/Glob
3. Read the relevant files to understand the current behavior
4. Identify the expected vs actual behavior

### Step 2: Find Existing Tests

1. Search for existing tests related to the buggy code
2. Understand the existing test patterns, runner, and conventions
3. Identify the test file where the new test should go

### Step 3: Write a Failing Test (RED)

**This step is MANDATORY before any fix.**

Create a test that:
- Reproduces the exact bug scenario
- Fails with the current buggy code
- Clearly describes what should happen

```
describe("ComponentOrFunction", () => {
  it("should <expected-behavior> when <condition>", () => {
    // Arrange: Set up the bug scenario
    // Act: Trigger the buggy behavior
    // Assert: Verify the expected (correct) behavior
    // This assertion should FAIL with the current code
  });
});
```

**After writing the test, run it to confirm it fails** using the project's test command.

**If the test passes, STOP.** Either:
- The bug doesn't exist or was already fixed
- Your test doesn't correctly reproduce the bug
- Revise your test to actually catch the bug

### Step 4: Implement the Fix (GREEN)

Only after confirming the test fails:

1. Make the **minimal** change to fix the bug
2. Don't refactor or "improve" unrelated code
3. Don't add features - just fix the bug
4. Run the test again to confirm it passes

### Step 5: Run Full Test Suite

Ensure no regressions:
```bash
{{TEST_CMD}}
```

If any tests fail, fix them before proceeding.

### Step 6: Verify Build

```bash
{{BUILD_CMD}}
```

### Step 7: Commit

Create an atomic commit with the test and fix together:

```bash
git add -A && git commit -m "fix: <brief-description>

<explanation-of-root-cause-and-fix>

{{COAUTHOR_LINE}}"
```

## Test Patterns for Common Bug Types

### Validation Bug
```
it("should reject invalid input", () => {
  const result = validateFunction({ /* problematic input */ });
  expect(result.success).toBe(false);
});
```

### State Bug
```
it("should maintain correct state after <action>", () => {
  // trigger the action, then assert the resulting state
});
```

### Edge Case Bug
```
it("should handle empty/null/undefined input", () => {
  expect(() => myFunction(null)).not.toThrow();
  expect(myFunction(null)).toBe(expectedDefault);
});
```

## Anti-Patterns - DO NOT

- Write the fix first, then add tests
- Skip the failing test step
- Write tests that pass immediately
- Fix multiple bugs in one commit
- Refactor while fixing
- Add features while fixing

## Why Test-First for Bug Fixes?

1. **Proves the bug exists** - You can't fix what you can't reproduce
2. **Documents the bug** - Future developers understand what was broken
3. **Prevents regression** - The bug can never silently return
4. **Minimal fix** - You only change what's needed to pass the test
5. **Confidence** - You know the fix actually works
