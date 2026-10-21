# Implementation Plan — Error-handling polish (FU-099)

**Status:** Plan for review · **Date:** 2026-06-29 · **No code yet.**
**Source FU:** `DORA_FOLLOWUPS.md` FU-099 (raised 2026-06-09; design
discussion + decisions resolved 2026-06-29).
**Phase:** App-wide polish — touches the API error contract, the client
error layer, and ~166 page-level catch blocks.

---

## 0. Verify-state-first: what already exists vs. what's missing

Re-checked 2026-06-29 against the live code (full audit by an Explore
agent, findings in [DORA_WORKLOG.md](../../DORA_WORKLOG.md) for this date).

**Already in good shape — do not rebuild:**
- **Backend wire contract is already RFC-7807-ish.** Every error
  returns a `ProblemDetails` dataclass via
  `dora_api/infrastructure/api_response.py:12-17` with
  `{ detail, status, errors, title, type }`. Status codes are
  well-differentiated (400 validation / 422 business-rule / 404
  not-found / 401 / 403 / 500).
- **Pydantic `ValidationError` is already caught at one site**
  (`dora_api/infrastructure/middleware.py:147-160`) and folded into a
  400 `bad_request(...)` with an `errors` map keyed by dotted field
  path. The error-shape contract is centralised; the gap is **what's
  inside each error entry**, not where it's caught.
- **Global 500 handler** logs the stack and returns a generic message
  (`dora_api/startup.py:169-179`). No trace leakage.
- **`X-Request-Id` correlation id** round-trips: client generates →
  server logs + echoes → both surfaces have it. The 5xx toast already
  shows it.
- **Client `NormalisedApiError`** type
  (`web_app/src/services/api/axiosHttpClient.ts:194-316`) carries
  `status / code / details / correlationId / isNetworkError`. The
  axios interceptor already fires the global 5xx toast, retries
  idempotent GETs on 502/503/504, and routes 401 to login.
- **`extractFieldErrors(err)`**
  (`web_app/src/services/errorHandling/apiErrorHandler.ts:14-55`)
  already separates field-keyed errors from general (`""` / `"_"` /
  `"noKey"` / `"general"`) errors. ~12 form dialogs already render
  inline `error-message` per field (RecipeEditDialog,
  CreateStockItemDialog, LoginPage, NewListDialog, etc.).

**Not built — this plan delivers it:**
- **Friendly-message translation on the server.** The middleware
  currently extracts `err["msg"]` from `ValidationError.errors()`
  verbatim — that's the raw Pydantic prose
  (*"Input should be a valid integer"*, *"String should have at
  least 1 character"*, *"Extra inputs not allowed"*) that ends up in
  toasts and inline slots.
- **Structured wire shape per error.** Each error entry today is a
  bare string. New shape: `{ msg, code, raw }` — friendly copy +
  Pydantic code + raw message kept for dev visibility.
- **Inline-and-toast convention.** ~12 forms use inline rendering;
  ~150+ catch blocks toast a single generic string. No standing rule
  for which surface goes where. New convention: when a request fails
  with field-keyed errors AND those fields are part of the page's
  form, render inline + a short generic confirmation toast; non-field
  errors stay toast-only.
- **4xx dev visibility.** The 5xx path already `console.warn`s with
  correlation id; the 4xx path doesn't. New convention: every 4xx
  also logs to console at warn level, with the same shape.
- **Correlation id in every negative toast.** Currently only the
  global 5xx toast surfaces it. New convention: every page-level
  negative toast caption ends with a small `· ref: <8-char id>`.

---

## 1. Resolved decisions (from the 2026-06-29 design discussion)

Captured for the next agent — these are settled, do not re-litigate.

| # | Question | Decision |
|---|---|---|
| 1 | Where does Pydantic → human translation live? | **Server-side.** Backend ships a friendly message per field; client just renders it. Reason: keeps copy in one language (Python), shared across any future client. |
| 2 | Inline vs toast? | **Inline + brief generic toast.** Field errors render next to the offending input; the toast caption is generic ("Couldn't save — check the highlighted fields") with no raw strings. Non-field errors stay toast-only. |
| 3 | Per-field copy budget? | **~15 common Pydantic codes** get crisp copy. Unknown codes fall back to a single "This value isn't valid." (R-007: don't pre-write copy for codes we don't actually hit). |
| 4 | Dev visibility? | **Always `console.warn` on 4xx** with the full normalised error + correlation id. Every negative toast caption ends with `ref: <8-char id>`. |
| 5 | Wire shape per error? | **`{ msg, code, raw }`** — friendly + Pydantic code + raw msg. Negligible payload cost; preserves the debug path. |
| 6 | Network / 5xx fallback copy? | **Keep current strings**, add the correlation id ref. |
| 7 | Rollout scope? | **Layer first, then migrate every form in one PR.** Avoids a "two patterns" drift period. |

---

## 2. The wire contract (after this change)

### 2.1 Validation error response (today vs. after)

**Today** (Pydantic `ValidationError` on a recipe save with a bad
`servings`):
```json
{
  "type": "https://httpstatuses.io/400",
  "title": "Malformed request.",
  "status": 400,
  "detail": "See errors property for more details.",
  "errors": {
    "servings": ["Input should be a valid integer, unable to parse string as an integer"]
  }
}
```

**After:**
```json
{
  "type": "https://httpstatuses.io/400",
  "title": "Malformed request.",
  "status": 400,
  "detail": "See errors property for more details.",
  "errors": {
    "servings": [
      {
        "msg": "Must be a whole number.",
        "code": "int_parsing",
        "raw": "Input should be a valid integer, unable to parse string as an integer"
      }
    ]
  }
}
```

The shape change is contained: `errors[field]` is now `list[ErrorEntry]`
instead of `list[str]`. Other ProblemDetails fields are unchanged.

### 2.2 Domain errors (`business_rule_violation`,
`entity_existence_failure`, `bad_request` with custom errors)

Same structured shape. Existing helpers take a plain string today —
they wrap it as `{ msg: <string>, code: "domain", raw: null }` so the
client side speaks one shape. **No copy changes in domain errors —
those are already authored by us, already user-readable.** This is a
shape lift only.

### 2.3 5xx + network — unchanged

The global 500 handler still returns the generic `ProblemDetails`.
The client interceptor still fires the global 5xx toast. The only
copy tweak: append `ref: <id>` to the 5xx toast caption (it's already
there; verify it's prominent).

---

## 3. Server-side changes

### 3.1 New `dora_api/infrastructure/error_translation.py`

A single module owning the Pydantic-code → friendly-copy table.
Pure-Python, no Flask deps, importable from tests.

```python
PYDANTIC_FRIENDLY: dict[str, str] = {
    "missing":              "This field is required.",
    "extra_forbidden":      "This field isn't supported here.",
    "int_parsing":          "Must be a whole number.",
    "int_type":             "Must be a whole number.",
    "float_parsing":        "Must be a number.",
    "float_type":           "Must be a number.",
    "string_type":          "Must be text.",
    "string_too_short":     "Can't be empty.",
    "string_too_long":      "Too long.",
    "bool_parsing":         "Must be true or false.",
    "bool_type":            "Must be true or false.",
    "uuid_parsing":         "Not a valid id.",
    "uuid_type":            "Not a valid id.",
    "datetime_parsing":     "Not a valid date / time.",
    "value_error":          "This value isn't valid.",  # generic fallback for custom validators
}
FRIENDLY_FALLBACK = "This value isn't valid."

def translate_pydantic_error(code: str, msg: str) -> str:
    return PYDANTIC_FRIENDLY.get(code, FRIENDLY_FALLBACK)
```

Inclusion list is intentionally narrow (R-007) — these are the codes
the Pydantic 2.x schemas in this repo actually emit. **Out-of-band
codes get the fallback**, which is the same UX as
"please check this field". If a real code hits the fallback in
production, we add it to the map — that's the maintenance loop.

The constraint-aware variants (e.g. `string_too_short` carries the
min in `ctx["min_length"]`) are **deliberately not interpolated** in
the first pass. "Can't be empty." reads better than
"Must be at least 1 character." in the common case; if we hit a real
schema with `min_length=5` we can extend the translator to read
`ctx`. R-007 — don't pre-build for codes we don't use.

### 3.2 New `ErrorEntry` dataclass

In `api_response.py`, alongside `ProblemDetails`:

```python
@dataclass
class ErrorEntry:
    msg: str           # the user-friendly message
    code: str          # the Pydantic code or "domain" for our own errors
    raw: str | None    # the raw Pydantic msg, or None for domain errors
```

### 3.3 Update `bad_request` / `business_rule_violation` / friends

Each helper today takes `errors: dict[str, list[str]] | None`. Lift to
`dict[str, list[ErrorEntry]] | None` with a **convenience overload**:
if a caller passes a plain string, wrap it as
`ErrorEntry(msg=string, code="domain", raw=None)`. This keeps the 50+
existing call sites in domain code working without per-site edits —
they keep passing strings, the helper does the lift.

### 3.4 Update `middleware.py:147-160`

Instead of:
```python
_Errors = {
    ".".join(str(loc) for loc in err["loc"]): [err["msg"]]
    for err in e.errors()
}
```

Do:
```python
_Errors: dict[str, list[ErrorEntry]] = {}
for err in e.errors():
    field = ".".join(str(loc) for loc in err["loc"])
    code = err["type"]
    _Errors.setdefault(field, []).append(ErrorEntry(
        msg=translate_pydantic_error(code, err["msg"]),
        code=code,
        raw=err["msg"],
    ))
```

### 3.5 Test coverage

New `tests/e2e/dora_api/test_error_translation.py`:
- Round-trip a body with a wrong-type field → assert response shape,
  assert `msg` is the friendly version, `raw` is the Pydantic string,
  `code` is `int_parsing`.
- Round-trip a body missing a required field → assert `code` is
  `missing`, `msg` is "This field is required.".
- Round-trip a domain error (e.g. delete-not-found) → assert shape
  lifts the string into `{msg, code: "domain", raw: null}`.
- Round-trip an unknown Pydantic code (synthesise via a custom
  validator that raises a non-standard error) → assert it falls back
  to "This value isn't valid." (and `raw` preserves the real text).

---

## 4. Client-side changes

### 4.1 Update the `NormalisedApiError.details` type

Today, `details.errors` is `Record<string, string[]> | undefined`.
Lift to:
```typescript
interface ApiErrorEntry {
    msg: string;
    code: string;
    raw: string | null;
}
type ApiErrorsMap = Record<string, ApiErrorEntry[]>;
```

The handler in `axiosHttpClient.ts:211-278` already passes the
`details` blob through; only the type changes.

### 4.2 Update `apiErrorHandler.ts`

`describeApiError(err)` — for field-keyed errors, return the
**generic toast caption**, not the joined raw strings:

```typescript
// Was:
const captionParts = Object.values(err.details.errors).flat();
return captionParts.join(' ');

// Now:
if (Object.keys(err.details.errors).some(k => isFieldKey(k))) {
    return "Couldn't save — check the highlighted fields.";
}
// fall through to general-error / network / unknown branches
```

`extractFieldErrors(err)` — now returns `Record<string, string>`
keyed by field, value is the **friendly `msg`** from the new
`ApiErrorEntry`. Drops the raw Pydantic string from the UI path.

### 4.3 Correlation id in every negative toast

A new tiny helper in `apiErrorHandler.ts`:

```typescript
export function correlationSuffix(err: unknown): string {
    if (err instanceof NormalisedApiError && err.correlationId) {
        return ` · ref: ${err.correlationId.slice(0, 8)}`;
    }
    return '';
}
```

Page-level catch blocks append this to the caption. Cheap, one call
per site.

### 4.4 4xx console visibility

In `axiosHttpClient.ts:handleError`, extend the 5xx `console.warn`
block to also fire on 4xx. Same shape, same fields. Devs get full
context in DevTools for **every** API failure, not just server crashes.

### 4.5 New composable `useFormErrors()` for the inline pattern

The ~12 dialogs that already do the inline pattern (RecipeEditDialog,
CreateStockItemDialog, etc.) hand-roll the same five lines:

```typescript
const fieldErrors = ref<Record<string, string>>({});
const generalError = ref<string | null>(null);
function handleSaveError(err: unknown, fallback: string) {
    const extracted = extractFieldErrors(err);
    fieldErrors.value = extracted.fieldErrors;
    generalError.value = extracted.generalError ?? fallback;
}
```

Componentise (R-001): `useFormErrors()` returns
`{ fieldErrors, generalError, handleSaveError, reset }`. The 12
existing sites + every newly-migrated site call this — one place to
change the convention later.

---

## 5. Migration sweep (~166 catch blocks)

### 5.1 Pattern map

Each catch block today is one of three shapes:

**Shape A — toast-only, single field-typed form (~30 sites):**
```typescript
catch (err) {
    $q.notify({ ..., caption: describeApiError(err) || '' });
}
```
→ Migrate to `useFormErrors()` + inline field rendering + a generic
toast. The toast caption becomes
``Notify({ caption: `Couldn't save${correlationSuffix(err)}` })``.

**Shape B — toast-only, action that's not a form (~120 sites):**
e.g. "Apply alert", "Generate shopping list", "Mark cooked". No
fields. Just a toast.
→ Caption stays as is (`describeApiError(err)` for known network /
auth / unknown branches; the change is the generic caption for
validation), **plus `correlationSuffix(err)`** appended.

**Shape C — already inline-pattern (~12 sites):**
→ Replace the hand-rolled five lines with the `useFormErrors()` call.
Behaviour unchanged except the caption is now the friendly server
copy.

### 5.2 Sweep mechanics

Single PR. The sweep is largely mechanical — each catch block fits
one of the three shapes; `useFormErrors()` is a near drop-in for
shape C, shape A is the highest-value migration (toast → inline),
shape B is one-line.

**Order:**
1. Land the server changes (§3) + new e2e tests — green build.
2. Land the client layer changes (§4) — `vue-tsc` green on all
   existing call sites (the lift to `ApiErrorEntry` is the only
   touch).
3. Migrate the 12 shape-C sites — pure cleanup.
4. Migrate the ~30 shape-A sites (the meaningful UX wins).
5. Sweep the ~120 shape-B sites with `correlationSuffix`.

Each chunk reviewable independently if the diff gets unwieldy.

### 5.3 What does **not** get touched in this PR

- The actual ProblemDetails wire fields (`type`, `title`, `status`,
  `detail`) — already RFC-7807-shaped.
- Status-code choices per endpoint (already well-differentiated).
- The 5xx global toast or the 401 redirect (both already correct).
- The retry logic for 502/503/504 (already correct).
- Logging shape on the server (already structured + correlation-id'd).

---

## 6. Engineering-standards close-gate checklist

- **R-001 (componentisation):** `useFormErrors()` is the recurring
  pattern lifted out — 12+ near-identical hand-rolls today.
- **R-003 (single source):** `PYDANTIC_FRIENDLY` is the only place the
  code → copy map lives. `correlationSuffix` is the only place the
  ref-id format lives.
- **R-007 (scope discipline):** inclusion list is the ~15 codes our
  schemas actually emit; unknown codes hit the fallback, get added
  if real users hit them. No pre-building.
- **R-008 (code-style minimalism):** no per-field bespoke copy; one
  table, one fallback.
- **Candidate new rule (evaluate at close):** "Page-level catch
  blocks render `extractFieldErrors` inline + a generic toast — never
  raw error strings in the caption." If two more "the catch block
  leaked a raw string" follow-ups land after this PR, promote to
  `R-021`. For now, the rule is implicit in `useFormErrors()`'s
  docstring.

---

## 7. Feedback coverage table

The original FU listed six design questions (`F1..F6` for this doc).
Each maps to a section.

| # | FU question | Resolved in |
|---|---|---|
| F1 | Server vs client mapping | §1 / §3 — server-side, with code + raw preserved |
| F2 | Inline vs toast | §1 / §4.5 — inline + brief generic toast for forms, toast-only for non-form |
| F3 | Generic vs specific copy | §1 / §3.1 — ~15 codes + fallback, no per-field bespoke |
| F4 | Network / unknown failures | §2.3 — keep current strings, add ref-id |
| F5 | Dev debuggability | §4.3 / §4.4 — console.warn on all 4xx, ref in every toast |
| F6 | Scope | §1 / §5 — sweep every catch block in one PR |

---

## 8. Open questions / carry-overs

None. All seven design questions resolved 2026-06-29. The plan is
ready to execute.
