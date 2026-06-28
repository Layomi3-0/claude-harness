# Commit Command

Create a well-structured git commit following best practices and conventional commit format.

**Usage:** `/commit [optional-description]`

## Instructions

### Step 1: Analyze Changes

Run these commands in parallel to understand the current state:

```bash
# See all changed/untracked files (never use -uall flag)
git status

# See staged and unstaged changes
git diff
git diff --cached

# See recent commits for style consistency
git log --oneline -5
```

### Step 2: Review Changes

1. **Identify what changed** - Group related changes together
2. **Check for secrets** - Never commit files that may contain secrets:
   - `.env`, `.env.*` files
   - `credentials.json`, `secrets.*`
   - Files containing API keys, tokens, passwords
   - If found, warn the user and exclude from commit
3. **Assess scope** - If changes span multiple unrelated concerns, suggest splitting into multiple commits

### Step 3: Run Verification

Before committing, ensure code quality:

```bash
{{TEST_CMD}}
{{BUILD_CMD}}
```

**If tests or build fail, STOP.** Fix the issues before committing.

### Step 4: Stage Files

```bash
# For all changes (most common)
git add -A

# Or stage specific files if splitting commits
git add <specific-files>
```

### Step 5: Create Commit Message

Follow **Conventional Commits** format:

```
<type>: <short-description>

<optional-body>

{{COAUTHOR_LINE}}
```

**Types:**
- `feat` - New feature or capability
- `fix` - Bug fix
- `refactor` - Code restructuring without behavior change
- `test` - Adding or updating tests
- `docs` - Documentation only
- `chore` - Maintenance, dependencies, tooling
- `style` - Formatting, whitespace (no code change)
- `perf` - Performance improvement

**Guidelines:**
- **Short description**: Imperative mood, lowercase, no period, max 50 chars
- **Body** (optional): Explain the "why" not the "what", wrap at 72 chars
- Focus on the intent and impact, not implementation details

### Step 6: Commit

Use HEREDOC for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
<type>: <short-description>

<optional-body-explaining-why>

{{COAUTHOR_LINE}}
EOF
)"
```

### Step 7: Verify

```bash
git log -1
git status
```

## Commit Message Examples

### Simple fix
```
fix: prevent NaN in order total when quantity empty
```

### Feature with context
```
feat: add Walmart product scraping support

Extends scraper to handle Walmart URLs using their JSON-LD
structured data. Falls back to Open Graph if JSON-LD unavailable.
```

### Refactoring
```
refactor: split payment client into focused modules

Break the 1200-line monolith into single-responsibility modules:
api, contacts, invoices, logger. Improves testability and
follows clean code principles.
```

## Safety Rules

**NEVER:**
- Commit with failing tests
- Commit with build errors
- Commit secrets or credentials
- Use `git commit --amend` on pushed commits
- Use `--force` push without explicit user request
- Use `-i` interactive flags
- Skip hooks with `--no-verify` unless explicitly requested

**ALWAYS:**
- Run tests before committing
- Run build before committing
- Include the Co-Authored-By line
- Use HEREDOC for multi-line messages
- Keep commits atomic and focused

## Handling Edge Cases

### No changes to commit
```
No changes detected. Nothing to commit.
```

### Mixed unrelated changes
Suggest splitting into separate, focused commits.

### Secrets detected
```
⚠️ Warning: Found potential secrets in staged files.
I cannot commit these. Please add them to .gitignore and
unstage with: git reset <file>
```

### Tests failing
```
❌ Tests are failing. Please fix before committing.
Would you like me to investigate the failures?
```

## Arguments

If the user provides `$ARGUMENTS`, use it as guidance for the commit message focus. For example:

- `/commit` - Analyze changes and generate appropriate message
- `/commit fix login redirect` - Focus message on the login redirect fix
- `/commit refactor auth` - Frame as a refactoring of auth system
