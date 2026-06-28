# Clean Code Refactor Command

Apply clean code principles to the specified target, following the standards in the project's Clean Code standard (`.claude/standards/CLEAN_CODE.md` or the Clean Code section of `CLAUDE.md`).

**Usage:** `/clean <target>`

**Target options:**
- `unstaged` - Refactor all unstaged changes
- `<file-path>` - Refactor entire file (e.g., `src/admin/config.ts`)
- `<file-path>:<function-name>` - Refactor specific function (e.g., `src/utils.ts:formatDate`)
- `<file-path>:<ComponentName>` - Refactor specific component (e.g., `src/Header.tsx:Header`)

## Instructions

You are a clean code specialist. Your job is to refactor the target code following the Clean Code principles defined in the project's standards.

### Step 1: Identify Target

Based on the argument `$ARGUMENTS`:

1. If `unstaged` → Run `git diff` to get all unstaged changes and identify files to refactor
2. If file path → Read the entire file
3. If `file:function` → Read the file and locate the specific function/component

### Step 2: Read Standards

Read these files to understand the coding standards:
- `.claude/standards/CLEAN_CODE.md` (or the Clean Code section of `CLAUDE.md`)
- The project's component-guidelines doc (e.g. `REACT_COMPONENTS.md`) if refactoring UI code

### Step 3: Analyze Code

For each piece of code, check for violations:

**Naming:**
- [ ] Names reveal intent (why it exists, what it does, how it's used)
- [ ] Classes use nouns, methods use verbs
- [ ] Names are pronounceable and searchable
- [ ] One word per concept (don't mix fetch/retrieve/get)

**Functions:**
- [ ] Functions are small (ideally 2-20 lines)
- [ ] Functions do ONE thing only
- [ ] 0-2 arguments (avoid 3+)
- [ ] No boolean/flag parameters
- [ ] Command-Query Separation (do something OR return something, not both)
- [ ] DRY - no duplicate code
- [ ] **One level of abstraction per function** (see below — enforce strictly)

**One Level of Abstraction Per Function (CRITICAL — enforce strictly):**

A function should do one thing **at one level of abstraction**. Think in terms of
"distance from the problem domain":

| Level    | Example                      | Meaning               |
| -------- | ---------------------------- | --------------------- |
| High     | "Register user"              | Business intent       |
| Medium   | "Validate email"             | Domain operation      |
| Low      | `if (email.contains("@"))`   | Implementation detail |
| Very Low | `charAt(3)`                  | Mechanical detail     |

**Mixing these levels in one function is a violation** — your brain keeps switching
gears (Uncle Bob calls this "mental stack pollution"). Flag and fix it.

- [ ] **No function mixes high-level intent with low-level implementation detail.**
- [ ] Each line in a function answers the same question at the same zoom level.
- [ ] **Step-down rule:** code reads top-down as a narrative — each function is
  followed by helpers at the *next* level down, never an abrupt drop into mechanics.

Quick tests for an abstraction leak:
1. "Does any line feel like it belongs in a different function?"
2. "Would I explain this line to a junior developer using different vocabulary?"

If yes → extract that detail into a named helper one level down.

**Bad example (mixed levels):**
```
void registerUser(HttpRequest request) {
    String email = request.getBody().get("email");  // Low-level HTTP detail
    if (!email.contains("@")) { throw new IllegalArgumentException(); }  // Low-level validation
    User user = new User(email, Status.ACTIVE);     // Domain construction
    userRepository.save(user);                      // Persistence detail
}
```

**Good example (single level):**
```
void registerUser(RegisterUserRequest request) {
    User user = createUser(request);
    saveUser(user);
    notifyUser(user);
}
```
Every line answers: "What does registering a user mean?" — no sudden drops into
implementation detail.

**File Length (CRITICAL — enforce strictly):**
- [ ] **No file exceeds the project's file-length limit (~250 lines).** This is a hard limit, not a suggestion.
- [ ] If a file is over the limit, it MUST be split — extract hooks, sub-components, or utilities into separate files.
- [ ] When splitting, co-locate related files in the same directory.
- [ ] Measure lines AFTER refactoring and report per-file line counts in the summary.

**UI Components (if applicable):**
- [ ] Single Responsibility - one reason to change
- [ ] Props interface is minimal and focused
- [ ] Complex logic extracted to custom hooks/helpers
- [ ] No inline styles (use the project's styling convention)
- [ ] Uses shared/reusable components where applicable
- [ ] Uses shared constants and validators

**General:**
- [ ] No over-engineering (only requested changes)
- [ ] No premature abstractions
- [ ] Trust internal code (only validate at boundaries)
- [ ] Delete unused code completely

### Step 4: Refactor

Apply refactoring following established patterns in the codebase:

**For files approaching or exceeding the limit:**
1. Extract logic/state into a focused unit (hook, module, helper)
2. Split sub-components or sub-functions into their own files
3. Create a types file if needed
4. Create a barrel/index export where it fits the project's conventions
5. Reuse existing shared components, constants, and validators

**For functions:**
1. Extract to smaller, single-purpose functions
2. **Unify the abstraction level** — push low-level/implementation detail down into
   named helpers so the parent reads as one story at one zoom level (step-down rule)
3. Use descriptive names
4. Reduce arguments (use objects for 3+ params)
5. Remove flag parameters (split into separate functions)

### Step 5: Write Tests

Add or update tests following the project's existing test patterns and runner. Cover rendering/return values, interactions, and edge cases (empty/null data, loading/error states).

### Step 6: Verify

Run the project's checks:

```bash
{{TEST_CMD}}
{{TYPECHECK_CMD}}
{{BUILD_CMD}}
```

### Step 7: Report

Provide a summary:
- **Per-file line counts** — list every modified/created file with its line count. Flag any file still over the limit as a violation.
- Files modified/created
- Lines before → after (total and per-file)
- Tests added
- Key changes made

## Example Refactoring Patterns

### Extracting a unit of logic
```
// Before: One unit mixing state, logic, and presentation (200+ lines)
// After: Presentation calls a focused helper/hook that owns the logic
```

### Splitting a large file
```
// Before: 400-line file doing everything
// After: Composed from focused, single-responsibility files
```

## Do NOT:
- Add features beyond what's requested
- Create abstractions for one-time operations
- Add error handling for impossible scenarios
- Create documentation files
- Add comments unless logic is non-obvious
- Leave backwards-compatibility hacks
