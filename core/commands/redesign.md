# Redesign Command

Explore alternative, innovative UI designs for a page or view, generating 5 distinct design concepts.

**Usage:** `/redesign <page-or-view-name>`

## CRITICAL: Use the Frontend Design Skill

**YOU MUST** use the `frontend-design:frontend-design` skill (if available) for each
design variant. This ensures production-grade, distinctive interfaces that avoid
generic AI aesthetics.

## Instructions

### Step 1: Understand the Target

Based on the argument `$ARGUMENTS`:

1. Identify the page/view to redesign
2. Read the current implementation thoroughly (all components, styles, data flow)
3. Read the project's design-system reference if one exists (e.g. a style guide,
   design-tokens file, or `globals.css`/theme config)
4. Read `CLAUDE.md` for project conventions and any component-guidelines doc
   (e.g. `REACT_COMPONENTS.md`)
5. Understand what data the page works with and what user actions it supports

### Step 2: Analyze the Current Design

Before creating alternatives, understand what exists:

- What is the page's primary purpose?
- What data does it display?
- What user interactions does it support?
- What are the current pain points or areas for improvement?
- What works well that should be preserved?

### Step 3: Create the Design Exploration Routes

Create 5 self-contained design variants in a **temporary exploration location** that
suits the project's stack and does NOT touch existing pages — for example:

- Next.js App Router → `app/design-lab/design-1/` … `design-5/`
- Other frameworks → an equivalent throwaway route, story, or component set

### Step 4: Generate 5 Distinct Designs

For each design, invoke the `frontend-design:frontend-design` skill. Each design MUST be:

- **Creative and unique** from all other variants and from the existing design
- **Fully functional** — not a mockup, but real interactive code
- **Mobile-first** — designed for mobile screens first, enhanced for desktop
- **On-brand** — uses the project's design tokens (colors, typography, shadows, radii)
- **User-focused** — enhances clarity, trust, simplicity, and transparency

#### Design Direction Guidelines

Push the limits of your design capabilities. Each design should explore a
fundamentally different approach:

**Design 1 — Bold & Immersive**: Full-bleed hero sections, dramatic typography scale, cinematic transitions, rich visual hierarchy with layered depth effects.

**Design 2 — Minimal & Refined**: Maximized whitespace, subtle micro-interactions, elegant typography, information density through clever progressive disclosure.

**Design 3 — Data-Forward & Functional**: Information-dense dashboard-style layout, clear data visualization, scannable metrics, power-user efficiency.

**Design 4 — Warm & Conversational**: Friendly, approachable tone, card-based conversational layout, progress storytelling, emotional design touches.

**Design 5 — Magazine & Editorial**: Editorial-quality layout with asymmetric grids, feature imagery areas, pull-quotes, typographic rhythm, premium print-inspired feel.

#### Required Elements for Each Design

Each design must:
- **Use the project's design-system tokens** as the foundation — read the project's
  style guide / theme / tokens and build every variant on top of it
- Import and reuse existing UI primitives and shared components where applicable
- Use the project's icon components/library rather than inline SVGs
- Include realistic placeholder data that reflects the page's actual data shape
- Be responsive (mobile + desktop)
- Include hover states, transitions, and micro-animations
- Have a self-contained component (no modifications to existing pages)

### Step 5: Create an Index Page

Create a design-lab index that links to all 5 variants with:
- A preview description of each design direction
- Links to each variant
- The name of the page being redesigned

### Step 6: Verify

```bash
{{BUILD_CMD}}    # Ensure all designs compile
```

### Step 7: Present Results

Report to the user:
- The page being redesigned
- A brief description of each design's approach
- Links/paths to view each design
- Suggest the user view them side by side to compare

## Design Principles

When generating designs, focus on elements that enhance the user experience:

- **Clarity** — Information hierarchy should be immediately scannable
- **Trust** — Design should communicate reliability and professionalism
- **Simplicity** — Remove friction, reduce cognitive load
- **Transparency** — Make status, pricing, and next steps crystal clear
- **Delight** — Add moments of surprise through animation, color, and interaction

## Technical Constraints

- **The project's design system is the single source of truth** for visual design —
  always read it first and reuse its documented patterns for colors, typography,
  spacing, shadows, radii, buttons, cards, forms, badges, and animations
- Reuse existing shared components rather than reinventing them
- Do NOT use scoped inline `<style>` blocks — use the project's styling convention
- Do NOT modify any existing pages or components
- Do NOT add new dependencies
- Use realistic mock data that matches the page's actual data shape
- Each design variant should be self-contained

## Cleanup

After the user has chosen a design direction:
- The chosen design can be adapted into the actual page
- The temporary design-lab location can be deleted
- Run `/clean` on the final implementation
