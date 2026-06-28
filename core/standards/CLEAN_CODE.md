# Clean Code Principles

When writing code, strictly follow these Clean Code principles.

## Foundational Rules

1. **Code without tests is not clean** - Always write tests first or alongside production code
2. **Clean code reads like well-written prose** - Make it simple, direct, and expressive
3. **Focus on three key aspects**:
   - Reduced duplication (DRY principle)
   - High expressiveness (meaningful names, clear intent)
   - Tiny abstractions (small, focused units)

## Hard Limits

| Rule | Limit |
|------|-------|
| **File length** | ~250 lines — split if approaching |
| **Function size** | 2-4 lines ideal, rarely >20 lines |
| **Max indent depth** | 1-2 levels |
| **Function arguments** | 0-2 ideal, never 3+ |
| **Flag (boolean) arguments** | Never — split into two functions |

## Naming Conventions

- Use **intent-revealing names** - the name should answer why it exists, what it does, and how it's used
- **Classes**: Use nouns or noun phrases (e.g., Customer, Account, AddressParser)
- **Methods**: Use verbs or verb phrases (e.g., postPayment, deletePage, save)
- Make names **pronounceable and searchable**
- **Pick one word per concept** - don't mix fetch, retrieve, and get for the same operation
- **No noise words** - `ProductData` vs `Product` is a meaningless distinction

## Functions

- **Functions should be small** - ideally 2-4 lines, rarely more than 20 lines
- **Do ONE thing** - functions should do one thing, do it well, and do it only
- **Ideal argument count: 0-2** - avoid 3+ arguments
- **Never use flag arguments** (boolean parameters)
- **Command Query Separation** - functions should either do something OR answer something, not both
- **No side effects** - if a function promises X, it shouldn't secretly do Y
- **Don't Repeat Yourself (DRY)** - eliminate duplication

### One Level of Abstraction Per Function

**A function should do one thing at one level of abstraction.** Think in terms of "distance from the problem domain":

| Level    | Example                      | Meaning               |
| -------- | ---------------------------- | --------------------- |
| High     | "Register user"              | Business intent       |
| Medium   | "Validate email"             | Domain operation      |
| Low      | `if (email.contains("@"))`   | Implementation detail |
| Very Low | `charAt(3)`                  | Mechanical detail     |

**Mixing these levels in one function is problematic** - your brain keeps switching gears (Uncle Bob calls this "mental stack pollution").

**Bad example (mixed levels):**
```java
void registerUser(HttpRequest request) {
    String email = request.getBody().get("email");  // Low-level HTTP detail
    if (!email.contains("@")) { throw new IllegalArgumentException(); }  // Low-level validation
    User user = new User(email, Status.ACTIVE);     // Domain construction
    userRepository.save(user);                      // Persistence detail
}
```

**Good example (single level):**
```java
void registerUser(RegisterUserRequest request) {
    User user = createUser(request);
    saveUser(user);
    notifyUser(user);
}
```
Every line answers: "What does registering a user mean?" - no sudden drops into implementation detail.

### The Step-Down Rule

**Code should read like a top-down narrative.** We want to read the program as a set of TO paragraphs:

- **Top level:** "TO register the user..."
- **Next level:** "TO create the user... TO save the user... TO notify the user..."
- **Next level:** "TO validate email... TO construct value objects..."

**You step down gradually—never abruptly.** Each function should be followed by those at the next level of abstraction.

**Quick tests for abstraction violations:**
1. "Does any line feel like it belongs in a different function?"
2. "Would I explain this line to a junior developer using different vocabulary?"

If yes → abstraction leak.

**One-sentence takeaway:** A function should tell one story, using one vocabulary, at one zoom level.

## General Rules

- **Follow the Boy Scout Rule**: Leave the code cleaner than you found it
- **Avoid over-engineering**: Only make changes that are directly requested or clearly necessary
- **No premature optimization**: Don't add configurability, abstractions, or helpers for hypothetical future needs
- **Trust internal code**: Only validate at system boundaries (user input, external APIs)
- **Three similar lines are better than a premature abstraction**
- **Delete unused code completely** - no backwards-compatibility hacks
- **Don't comment bad code, rewrite it**

## Test Standards

- TDD: write a failing test first, then the minimal fix
- One concept per test, minimize asserts per concept
- F.I.R.S.T.: Fast, Independent, Repeatable, Self-validating, Timely
