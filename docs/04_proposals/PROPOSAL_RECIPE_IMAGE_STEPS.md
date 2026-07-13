# Proposal — Recipe "Image" Steps Mode (C-4 add-on)

**Status:** ✅ **BUILT — 2026-06-25** (proposal + all §5 decisions + full
implementation shipped the same day; see `DORA_WORKLOG.md` 2026-06-25 and
`DORA_FOLLOWUPS_RESOLVED.md` FU-369). The 2026-07-01 proposals audit mistakenly
logged this as "not built" (FU-369) — corrected 2026-07-13.
· **Date drafted:** 2026-06-25 · *(proposal-as-written changed no code; the build landed the same day)*
**Scope:** Add a third recipe-steps mode — **image** — alongside the existing
**structured** and **freeform** modes. The user uploads ordered photos of their
recipe (a cookbook spread, a handwritten card, a printout) and Dora renders them
as the step content. **Not OCR.** Pictures are pictures. Ingredients stay
structured; the rest of the loop (cookability, pantry deduction, shopping list,
suggestions, search) is untouched.

> **Charter tie-break:** Effortless (P1) + Anti-creep (P10). The biggest barrier
> to seeding the cookbook with the user's *own* recipes is retyping steps from
> a physical source. Image mode removes that friction entirely without inviting
> OCR scope. Ingredients stay first-class so the recipe still participates in
> the loop — image-mode recipes are *not* dead bookmarks.

---

## 1. Current state (from live code)

Recipe instructions exist in **two shapes today**, with implicit detection:

- **Freeform** — `Recipe.instructions: str | None` ([recipe.py:39](dora_api/domain/entities/recipe.py:39)).
  Cook mode splits it on newlines and does fragile text-matched ingredient
  highlighting ([RecipeCookMode.vue](web_app/src/pages/RecipeCookMode.vue), `:356-363`, `:424-432`).
- **Structured** — `RecipeStep` rows ([recipe_step.py](dora_api/domain/entities/recipe_step.py))
  with `text`, optional `hint`, optional `parent_step_id` (one level of
  sub-steps), and association tables for `ingredient_refs[]` / `tool_refs[]`.
  Detected via `has_structured_steps_for_recipes` ([get_recipes.py:28](dora_api/features/recipes/get_recipes.py:28));
  a recipe is "structured" once it has step rows. Cook mode then renders the
  rich per-step UI (highlight, hint footer, per-step tools/timer).

There is **no explicit `steps_mode` field today** — the mode is inferred from
"does this recipe have step rows?" That implicit detection has been adequate
for two modes but won't extend to a third: an image-mode recipe could have
*zero* step rows *and* zero `instructions`, which today would render an empty
cook mode rather than a gallery.

There is also a `Recipe.image: bytes | None` column ([recipe.py:37](dora_api/domain/entities/recipe.py:37))
for the **dish hero image** (currently dead — wired up by Cookbook §2.3 / FU-039).
That's a *single* image of the finished dish. Step images are a separate
concern: ordered, plural, content-bearing.

---

## 2. The design

### 2.1 The third mode

Recipes gain an explicit, server-owned **`steps_mode`** enum
(R-003, R-010 — closed-set, validated at the boundary):

| `steps_mode` | Source of step content | Cook-mode rendering |
|---|---|---|
| `structured` | `RecipeStep` rows | Step-by-step nav, highlight, hint, per-step tools, per-step timer |
| `freeform` | `Recipe.instructions` text blob | One-step-per-line split, text-matched highlight (today's fallback) |
| **`image` (new)** | Ordered `RecipeStepImage` rows | **Scrollable image gallery; no step nav, no highlight, no timer, no per-step tools** |

The mode is the user's declared intent — the editor offers all three as
peers (a tabbed mode switch, like a Quasar `q-btn-toggle`). Switching modes
**does not destroy data in the other modes**: a recipe can carry freeform
text *and* structured rows *and* step images simultaneously; `steps_mode`
just declares which one cook mode and the detail page render. (Rationale: the
user may want to experiment with image mode but keep their typed steps as a
backup, and a destructive switch would feel unsafe — P1.)

> **Open decision** (§5.1): peer switch keeping all three payloads (proposed),
> vs. exclusive switch that prompts before clearing the other modes' data.

### 2.2 Model — `RecipeStepImage`

A new child table, parallel in spirit to `RecipeStep`:

```
RecipeStepImage
  id
  recipe_id    (FK)
  sequence     (int, ordered)
  image        (bytes)  -- the photo
  mime_type    (str)    -- 'image/jpeg' | 'image/png' | 'image/webp'
```

**Storage shape — bytes-in-db** matches the existing pattern for
`Recipe.image` and `User.image` (R-005: keep the data layer portable across
SQLite + Postgres without a separate blob store). The blob size pressure is
real but bounded — see §2.6.

**No caption / title / alt-text fields.** Image mode is deliberately the
*dumbest* mode; adding caption fields starts the slide toward OCR-lite. If
the user wants per-image notes, they should switch to structured (R-007:
scope discipline).

**No `parent_step_id`-style nesting.** Just a flat ordered list.

### 2.3 Editor (recipe detail page)

In the recipe detail page steps slot — driven by the `steps_mode` tab toggle —
**image mode** renders a new component **`RecipeStepImagesEditor.vue`**
(R-001: componentisation-first; do not inline this into the page):

- **Upload affordance** — multi-file file picker + drag-and-drop. On mobile,
  the file picker should `accept="image/*"` with `capture="environment"` so
  iOS/Android offer "Take Photo" directly (no native camera wrapper needed —
  the browser handles it).
- **Reorder** — drag-reorder, matching `RecipeStepsEditor` ergonomics
  (`vuedraggable` is already a dependency).
- **Remove** — per-image delete with the standard delete confirmation (A3 modal).
- **Preview** — each row shows the thumbnail at a comfortable size.

Save flow follows the existing recipe-save pattern (PATCH the recipe; the
image rows are written as part of the same transaction). Validation: at least
one image required if `steps_mode = image` (R-010 — server-side guard, with a
matching client check).

### 2.4 Cook mode rendering

Cook mode (`RecipeCookMode.vue`) branches on `steps_mode`. **Image mode**
renders a new component **`RecipeCookModeImageView.vue`**:

- **Vertical scroll** of the ordered images, each rendered full-width
  (responsive). Tap any image to **zoom** (existing pattern, or a minimal
  lightbox).
- **Ingredients panel** — unchanged from the other modes. The cook still sees
  the structured ingredient list, location grouping, B8 session-only
  substitute swaps, etc.
- **Finish-cooking flow (C-3 §2.1)** — unchanged. Per-item level checklist,
  meals-cooked counter, celebration, etc. all work the same. The recipe still
  *closes the loop*.
- **Disabled in image mode:**
  - Per-step navigation (no "Next step" / progress bar).
  - Per-step ingredient/tool highlight (no step → ingredient association).
  - Per-step timer auto-detection (no text to scan). The free-standing timer
    affordance (§2.7 of C-3 — sous-chef timer button) **stays available** as
    a manual control; the user can still set a timer when they need one.
  - Voice "next step" command (no steps to advance). Other voice commands
    that don't depend on steps (e.g. ingredient queries) keep working.
- **Serving auto-adjust (C-3 §2.2)** — unchanged. Scales the ingredients
  panel; images are not modified.

> **Open decision** (§5.2): vertical scroll (proposed) vs. swipe carousel.
> Scroll is simpler, friendlier for two-page-spread photos, and degrades to
> desktop trivially. Carousel feels app-like but adds a widget and obscures
> overall context.

### 2.5 Detail page rendering

The recipe detail page renders steps according to `steps_mode`. Image mode
renders the same `RecipeStepImagesViewer.vue` used inline (read-only variant
of the editor — thumbnail strip with tap-to-zoom).

### 2.6 Storage & size — the real constraint

Bytes-in-db is consistent (R-005) but step images can be large. Before saving,
the editor **client-side resizes** to a sane maximum (e.g. 1600px on the long
edge) and re-encodes to JPEG at a reasonable quality (e.g. 0.85). This is
existing-pattern territory — the `User.image` upload already does similar.
A recipe with ten 1600px JPEGs at q=0.85 is typically 2–5 MB total, which is
acceptable for SQLite and well within Postgres comfort.

**Soft limit:** 20 images per recipe (cookbook spreads are usually 1–4 pages;
20 is generous and prevents accidental dump-the-whole-album behaviour).

> **Open decision** (§5.3): client-side resize target + image cap (proposed
> 1600px / q=0.85 / 20 images). Confirm or tune.

### 2.7 URL importer (§2.7 of Cookbook)

**No change.** The importer pulls schema.org `recipeInstructions` (text) and
will never produce image mode — there's no JSON-LD field for "the user's
private photo of the page". Image mode is hand-entered only. (R-007 — don't
build importer affordances for a hand-entry-only feature.)

### 2.8 Search

Step text contributes to recipe search for the freeform/structured modes.
Image mode contributes nothing to search from its step content — that's
expected and acceptable. The recipe is still searchable by **name, tags,
cuisine, category, and linked ingredients** (the high-signal axes). This
matches the freeform mode's de-facto reality (free text rarely
keyword-searches usefully either) and aligns with the user's read of the
tradeoff in the 2026-06-25 discussion.

### 2.9 Assistant tool integration

The Dora assistant's recipe tools (search, suggestions, expiry rescue) read
ingredients and metadata, not step content. **No changes needed.** Image-mode
recipes flow through unchanged.

---

## 3. Cross-cutting (covered elsewhere)

| Concern | Home |
|---|---|
| Steps-mode tab toggle UI standard | A1/A1b theme tokens, A3 modal patterns |
| Drag-reorder pattern | Reuse `vuedraggable` (RecipeStepsEditor already does) |
| Image upload pattern | Existing `User.image` / `Recipe.image` (FU-039) flow |
| Cook mode finish flow + celebration | C-3 §2.1 (unchanged) |
| Ingredients panel rendering | C-3 §2.3 + Cookbook §2.13 (unchanged) |
| Substitute swap (B8) | Unchanged — works orthogonally to step rendering |
| Cookability / shopping list / pantry deduction | Driven by ingredients; unaffected |

---

## 4. From the original spec (historical — `docs/00_original_spec/`)

The original spec doesn't directly anticipate image-mode steps. The closest
note is the *"Store recipes as markdown files, point to file in DB / custom
location"* idea (PROPOSAL_COOKBOOK §4, marked **superseded**) — same impulse
to let the user keep recipes in whatever physical form they already have,
without forcing structured re-entry. The current design (structured DB rows
for ingredients + a flexible steps-mode for the procedural content) is the
modern reading of that impulse.

No items extracted from the original spec for this proposal.

---

## 5. Open decisions (for co-design)

**Status: closed — all five resolved with the user 2026-06-25 and built the same
day (`DORA_WORKLOG.md` 2026-06-25). All landed on the proposed default.**

1. **Mode-switch semantics** (§2.1) — ✅ **peer / non-destructive** (proposed).
   All three step payloads coexist; `steps_mode` is just the active render selector.
2. **Cook-mode rendering** (§2.4) — ✅ **vertical scroll** gallery, full-width
   images, tap-to-zoom (proposed; no carousel widget).
3. **Resize target + image cap** (§2.6) — ✅ **1600px long edge / JPEG q=0.85 /
   20-image soft cap** (proposed). Also spawned the centralised image-upload
   memory (`feedback-centralise-image-upload`, R-003).
4. **Recipe-level vs step images** — ✅ **kept distinct** (proposed). `Recipe.image`
   (dish hero) unchanged; this added only `RecipeStepImage` step photos.
5. **Manual timer in image mode** (§2.4) — ✅ **standalone timer kept available**
   (proposed).

---

## 6. Suggested sequencing

One chunk; this is small enough to land as a single C-4 add-on.

1. **`steps_mode` enum + migration.** Add the column to `Recipe`; backfill
   existing rows (`structured` if step rows exist, else `freeform`). New
   `RecipeStepImage` table. Server-side validation (steps_mode `image` ⇒
   at least one image row).
2. **Editor.** `RecipeStepImagesEditor.vue` + the mode toggle on the detail
   page; client-side resize before upload. Validation + save.
3. **Viewer.** `RecipeStepImagesViewer.vue` (read-only variant) for the
   detail page steps slot.
4. **Cook mode branch.** `RecipeCookModeImageView.vue`; wire the branch into
   `RecipeCookMode.vue` on `steps_mode === 'image'`. Confirm ingredients
   panel, finish flow, B8 swaps, and serving-adjust all still work.
5. **Polish + docs.** CHANGELOG entry; `DORA_WORKLOG.md` handoff; help-page
   blurb if the help overlay (C-help) is active.

No dependency on Cookbook structured-steps work (already landed) or on the
dish-hero image (FU-039) — image-mode steps and `Recipe.image` are separate.

---

## 7. Feedback coverage

This proposal is **not driven by a specific feedback bullet** in
`02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` — it's an additive
feature surfaced in conversation on 2026-06-25 (the user noted that the
biggest barrier to seeding the cookbook with their own recipes is retyping
steps from a physical source). The only closely-related bullet is L249
("Recipes should have an image…") which concerns the **dish hero image**
and is already covered by Cookbook §2.3 / FU-039 — a different surface.

| Bullet (line) | Summary | Relation to this proposal |
|---|---|---|
| L249 | Recipes should have an image and display it; people eat with their eyes | **Different feature.** Covered by `PROPOSAL_COOKBOOK.md` §2.3 (single dish hero image via `Recipe.image`). Image *steps* are ordered procedural photos — a separate concern. |

No `COVERAGE_GAPS.md` items move from gap → covered as a result of this
proposal (the gap file tracks feedback bullets, not user-suggested
enhancements).

---

## 8. Engineering-standards check

| Rule | Application |
|---|---|
| **R-001** (componentisation-first) | New `RecipeStepImagesEditor.vue` + `RecipeStepImagesViewer.vue` + `RecipeCookModeImageView.vue` — no inline markup in the host pages. |
| **R-002** (theme tokens only) | Editor + viewer + cook-mode-image-view use existing tokens (`--c-surface-*`, `--c-line`, `--radius-md`, `--space-*`); no hex. |
| **R-003** (single source of truth) | `steps_mode` lives on the server as the authoritative enum; no client-side mode inference. Replaces the implicit "does it have rows?" detection. |
| **R-005** (portable data access) | Bytes-in-db keeps the storage portable between SQLite and Postgres without a separate blob store, matching `Recipe.image` / `User.image`. |
| **R-006** (clean migrations) | New `RecipeStepImage` table + `Recipe.steps_mode` column added in one migration; backfill is a single deterministic UPDATE (`structured` where step rows exist, else `freeform`). Pre-release: no preserving guards needed (memory: [Pre-release: breaking changes OK]). |
| **R-007** (scope discipline) | No OCR. No captions. No per-image titles. No alt-text. No automatic step extraction. No carousel widget (pending §5.2). Image mode is deliberately the dumbest mode. |
| **R-010** (strong types over stringly-typed matching) | `steps_mode` is a closed enum validated server-side; `mime_type` is validated against an allow-list (`image/jpeg`, `image/png`, `image/webp`). |

No new ADR-worthy decisions emerge from this proposal — it composes existing
patterns. If §5.1 (peer-switch keeping multi-mode data) becomes a recurring
shape elsewhere (e.g. for shopping-list view modes), promote it then.
