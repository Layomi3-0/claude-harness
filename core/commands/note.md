# Note Command

Add a learning note or summary to the project's dev documentation.

**Usage:** `/note <topic-or-summary>`

## Instructions

### Step 1: Read Current Notes

Read the notes file configured for this project:

```
{{NOTES_PATH}}
```

(If `{{NOTES_PATH}}` is unset, default to `docs/NOTES.md` and create it if missing.)

### Step 2: Understand the Topic

Based on `$ARGUMENTS`, determine:
1. **Topic** - What concept is being documented
2. **Context** - Any relevant context from the current conversation
3. **Section** - Where it fits in the existing structure (Terms, new section, etc.)

### Step 3: Format the Note

Structure the note clearly:
- Use a descriptive heading (## or ###)
- Keep explanations concise but complete
- Use tables for comparisons
- Use code blocks for examples
- Link related concepts if applicable

### Step 4: Add to File

Append or insert the note in the appropriate section of the notes file.

If the topic fits under an existing section (like Terms), add it there.
If it's a new category, create a new section.

### Step 5: Confirm

Tell the user what was added and where.

## Examples

### Simple term
```
/note webhook - an HTTP endpoint that receives callbacks from external services
```

### Detailed concept from conversation
```
/note summarize our discussion about authentication flows
```

### New topic
```
/note exchange rates - how we fetch and cache USD/NGN rates
```

## Guidelines

- Keep notes scannable (headers, bullets, tables)
- Focus on the "why" not just the "what"
- Include practical examples when relevant
- Link to related concepts in the codebase when helpful
