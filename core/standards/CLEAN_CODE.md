# Clean Code Principles

When writing or refactoring code in this repo, strictly follow these principles.
This file is read by agents before coding — defer to it, and to `PROJECT.md` for
anything repo-specific (stack, validation commands, existing patterns).

This is a {{PROJECT_STACK}} codebase. The examples below are illustrative;
apply the idea, not the Java syntax.

## Foundational Rules

1. **Code without tests is not clean.** Write the test first, or alongside.
2. **Clean code reads like well-written prose** — simple, direct, expressive.
3. **The three things that matter most:** reduced duplication, high expressiveness,
   tiny abstractions. When something is done over and over, something in the design
   is not yet well expressed.

## Hard Limits

| Rule | Limit |
|------|-------|
| **File length** | ~300 lines. Split before it grows past that. |
| **Function size** | 2–4 lines ideal, rarely >20 |
| **Max indent depth** | 1–2 levels |
| **Function arguments** | 0–2 ideal, never 3+ (wrap groups into a named object) |
| **Flag (boolean) arguments** | Never — a bool parameter means the function does two things; split it |
| **Return points** | Multiple returns are fine in a small function; prefer early-return to nesting |

These are guidelines, not laws — but exceeding one is a prompt to ask "is there another
unit hiding in here?", and the answer is usually yes.

## Naming

- **Intent-revealing.** The name answers why it exists and what it does. The problem
  is never simplicity — it's implicitness.
- **Classes/types are nouns** (`Customer`, `Account`, `AddressParser`), never verbs.
  Avoid `Manager`, `Processor`, `Data`, `Info` — weasel words that hide an unfocused
  responsibility.
- **Functions are verbs** (`postPayment`, `deletePage`, `save`). Accessors get
  `get`/`set`; predicates get `is`/`has`.
- **Pick one word per concept.** Don't mix `fetch`, `retrieve`, and `get` for the same
  operation across the codebase.
- **Don't pun.** Don't reuse one word for two meanings (`add` for arithmetic vs. `add`
  for list insertion — the second is `append`/`insert`).
- **No noise words.** `ProductData` vs `Product` is a distinction without a difference.
  `nameString` is not better than `name`.
- **Searchable and pronounceable.** Single-letter names only as loop counters in tiny
  scopes. Name length should match scope size.
- **No type encodings.** No Hungarian notation, no `I` prefix on interfaces.
- **Add meaningful context** with a well-named type, not a prefix on a loose variable —
  an `Address` type beats a bare `state` variable. But don't add gratuitous context.

## Functions

- **Do ONE thing, at ONE level of abstraction.** If you can extract a function whose
  name is not just a restatement of the body, the original did more than one thing.
- **Command–Query Separation.** A function either *does* something or *answers*
  something — never both. Changing state and returning a value is two jobs.
- **No hidden side effects.** If the name promises X, it must not secretly do Y.
  `checkPassword` must not also initialize the session. If a temporal coupling is
  unavoidable, put it in the name.
- **Prefer exceptions to error codes.** A function that handles errors does only that —
  extract the `try`/`catch` bodies into their own functions.
- **DRY.** Duplication is the root of most maintenance evil.

### One Level of Abstraction Per Function

Every line in a function should sit at the same "distance from the problem domain":

| Level | Example | Meaning |
|-------|---------|---------|
| High | "Register user" | Business intent |
| Medium | "Validate email" | Domain operation |
| Low | `if (email.includes("@"))` | Implementation detail |
| Very low | `s.charAt(3)` | Mechanical detail |

Mixing them forces the reader to keep switching gears ("mental stack pollution").

**Bad — mixed levels:**
```ts
async function registerUser(req: HttpRequest) {
  const email = req.body.email;                 // low-level access
  if (!email.includes("@")) throw new Error();  // low-level validation
  const user = { email, status: "ACTIVE" };     // domain construction
  await db.insert("users", user);               // persistence
  await sendWelcome(email);                      // side effect
}
```

**Good — single level:**
```ts
async function registerUser(req: RegisterUserRequest) {
  const user = createUser(req);
  await saveUser(user);
  await notifyUser(user);
}
```
Every line answers one question: "what does registering a user mean?" Details drop one
level down, into `createUser` / `saveUser` / `notifyUser`.

### The Step-Down Rule

Code reads like a top-down narrative: each function is followed by those one level below
it, so the file descends the abstraction ladder as you read down. To spot a violation,
ask while reading a line: *"does this belong in a different function?"* If yes, it's an
abstraction leak.

### Switch / large discriminated dispatch

A `switch` (or long `if/else` chain) on a type tag is hard to keep to one thing and
tends to reappear — `isPayDay`, `deliverPay`, `calculatePay` all switching on the same
`employeeType`. Prefer polymorphism: dispatch through a map or a discriminated-union
handler so the branching lives in exactly one place. Tolerable only if it appears once,
builds the polymorphic objects, and is hidden from the rest of the system.

## Objects vs. Data Structures

- **Objects** hide data behind abstractions and expose behavior. Easy to add new *types*
  without changing existing behavior; hard to add new *behavior*.
- **Data structures** (and DTOs) expose data and have little behavior. Easy to add new
  *behavior*; hard to add new *types*.

Neither is "better" — pick the one whose axis of change matches the feature. Convex docs
and DTOs are legitimately data structures; domain logic should hide its data.

**Law of Demeter — talk to friends, not strangers.** A function should only call methods
on: itself, objects it created, its arguments, and its own fields. Avoid
`a.getB().getC().doThing()` train-wrecks. If you're reaching through an object to pull
its data out and act on it, tell the object to do the thing instead.

## Design: Invariants, DIP, DI

- **Invariants** are rules that must always be true about a value for its whole life
  (e.g. an order total is never negative; a status is one of a fixed set). Make invalid
  states unrepresentable — enforce invariants at construction (a factory / smart
  constructor) rather than scattering defensive checks everywhere.
- **Dependency Inversion (DIP).** High-level policy must not depend on low-level detail;
  both depend on an abstraction. Business logic depends on a `PaymentProcessor`
  interface, never on `StripePaymentProcessor` directly.
- **Dependency Injection (DI).** Achieve DIP by passing dependencies in from the outside
  (constructor/parameter injection) rather than constructing them inside. The concrete
  choice is made at the edge — in a factory or the composition root — so the core stays
  testable and swappable. *Details are plugins to policy.*

## Classes / Modules

- **Small — measured by responsibilities, not just lines.** You should be able to
  describe the module in ~25 words without "and", "or", "but". If you can't name it
  concisely, it does too much.
- **Single Responsibility.** One reason to change. Three functions that all touch
  "version info" want to be a `Version` unit. High cohesion: a module whose every field
  is used by most of its functions is cohesive; when a subset of functions uses a subset
  of fields, another module is hiding inside.
- **Open for extension, closed for modification.** Add behavior by adding a unit, not by
  editing a working one.
- **Depend on abstractions to isolate from change.** A `Portfolio` that talks to a
  `StockExchange` interface can be tested with a stub; one wired directly to
  `TokyoStockExchange` cannot.
- **Get it working, then make it clean** — but don't skip the second step.

## Tests

- **TDD (three laws):** no production code without a failing test first; write only
  enough test to fail; write only enough production code to pass.
- **Tests are as important as production code.** Dirty tests are as bad as no tests,
  because they rot and you stop trusting them. Keep them readable above all.
- **One concept per test**, asserts per concept minimized. Given–When–Then.
- **F.I.R.S.T.** — Fast, Independent, Repeatable, Self-validating, Timely.
- **Never weaken, skip, or delete a test to make a change pass.** If a test encodes
  wrong behavior, escalate it with reasoning — don't quietly edit it green.

## General

- **Boy Scout Rule** — leave code cleaner than you found it, in small steps.
- **No over-engineering / no premature optimization.** No configurability, abstraction,
  or extension points for needs nobody has stated. Three similar lines beat a premature
  abstraction.
- **Trust internal code; validate only at boundaries** (user input, external APIs).
- **Delete dead code** — no backwards-compat hacks left lying around.
- **Don't comment bad code — rewrite it.** A comment explaining *what* usually marks
  code that should have been named better; comments earn their place explaining *why*.
