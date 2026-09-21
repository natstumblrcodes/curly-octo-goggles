# Alchemical Visions Bubble-Effect Forensic Diagnostic

## Scope and evidence standard

This diagnostic does **not** change either theme source.  The repository contains two
non-identical theme deliverables, `TheFinalCode.html` (183,210 bytes) and
`THEFINALCODE.txt` (185,445 bytes), so every mechanical test is run against both
rather than assuming one is the code pasted into Tumblr.  The reproducible generator
is [`tools/diagnose_bubbles.py`](../tools/diagnose_bubbles.py).

A result is called **established** below only when it can be verified locally from
those inputs.  Tumblr save acceptance cannot be truthfully inferred from an HTML
parser or a local file: it requires uploading the generated fixture to the account.
The generator produces those byte-controlled fixtures and a JSON manifest, so that
last comparison can be performed without manually editing a test file.

## Test 1 — baseline and restoration control

Before generating a test fixture, the command copies each source into
`diagnostics/baseline/` and writes SHA-256 checksums.  Those baseline files and all
fixtures are intentionally ignored by Git: they are exact local forensic copies, not
a second maintained theme.

For each source, the generator also copies the original fixture to a `restored`
fixture.  The recorded SHA-256 values match and `cmp` returns success.  Therefore the
restoration control is byte-for-byte equal to its original; it does not merely render
the same.

## Tests 2–5 — controlled bubble removals and count ladder

There are exactly 16 bubble elements in each source: eight in the desktop region and
eight in the mobile region.  `bubbles-removed` removes **only** those 16 complete
`<img class="effect bubble" …>` start tags.  It leaves the `.effects` and
`.effect-region` containers, CSS, all non-bubble effects, assets, scripts, and the
remaining document bytes untouched.  The manifest records the kept and removed
document-order indices for every fixture.

Logical subgroup fixtures are:

| Fixture | Kept document-order bubbles | Purpose |
|---|---:|---|
| `group-a` | 1–4 | first desktop subgroup |
| `group-b` | 5–8 | second desktop subgroup |
| `groups-a-b` | 1–8 | both desktop subgroups |
| `one`, `two`, `three`, `four`, `eight`, `twelve` | prefix of the stated size | exact threshold search |
| `25-percent`, `50-percent`, `75-percent`, `100%` original | 4, 8, 12, 16 | requested count checkpoints |

The 25/50/75 fixtures deliberately retain a document-order prefix (four/eight/twelve)
rather than random elements.  This makes a first failing count reproducible.  If a
checkpoint fails in Tumblr, upload the next lower count and then the one-by-one ladder
between them; the smallest failing count is then established by adjacent controlled
comparisons.  No result from Tumblr was available in this environment, so neither a
smallest failing count nor bubble involvement has yet been established.

## Test 6 — identical asset test

All 16 bubble elements in **each** source use the same exact URL:

```text
https://res.cloudinary.com/dgpfj9fox/image/upload/v1789052152/3A6035E1-3030-4B8A-907B-33747ECA5B74_fphjhy.png
```

Thus no comparison in the current theme can distinguish one bubble *asset* from
another—the image asset is identical in every bubble.  The subgroup/count fixtures
can distinguish repeated-reference quantity from element position only after their
Tumblr save outcomes are recorded.

## Tests 7–9 — URL, markup, and CSS relationship

Static URL parsing establishes HTTPS, the `res.cloudinary.com` host, a normal
Cloudinary `/image/upload/...png` path, and no whitespace/unusual characters in the
bubble URL.  Every bubble `src` and `style` attribute is quoted; the source contains
no control characters, no duplicate IDs, and Python's HTML parser reports no parsing
errors.  The 16 inline styles each contain only well-formed `property:value`
declarations, including a valid custom property such as `--drift:-14px`.

Independent network accessibility could **not** be established here: direct HTTPS
requests to Cloudinary were blocked by the execution environment's proxy with HTTP
403/CONNECT 403 before Cloudinary could respond.  That is an environment limitation,
not evidence that the Cloudinary URL is invalid.

The relevant dependency chain is static and complete: `.effect-region` supplies the
positioned/overflow-clipped region; `.effect` supplies positioned visible image
behavior; `.bubble` supplies bottom position, opacity, filter, and `rise` animation;
`rise` reads `--drift`; and the desktop/mobile region classes position the two
containers.  The bubble markup has no IDs, scripts, pseudo-elements, or nesting that
is unique to a particular bubble.  Consequently no local evidence supports a
bubble-specific HTML parser or CSS failure.

## Tests 10–11 — aggregate complexity and whitespace minification

The complete bubble markup is already a single line in both sources.  Whitespace-only
minification of the affected `.effects` blocks changes **0 bytes** in both files, so
fixture A (original) and fixture B (whitespace-minified) are byte-identical.  This
rules out removable whitespace/newlines in the present effects block as an explanation
for a different Tumblr result; it does not establish or rule out a Tumblr aggregate
limit for total elements, repeated attributes, or external references.

Because each reported Tumblr result must be supplied by an actual save attempt, the
following are currently **not established**: the original failure condition, the
smallest accepting change, whether bubbles contribute, a quantity threshold, or an
aggregate-complexity rejection.  Treating any of them as a cause would violate the
controlled-comparison requirement.

## Required Tumblr upload matrix

Run this once from the repository root:

```bash
./tools/diagnose_bubbles.py
```

Then upload the indicated generated file unchanged and record Save accepted/rejected:

1. `*.original` and `*.bubbles-removed` (bubble involvement).
2. `*.restored` (restoration control).
3. `*.group-a`, `*.group-b`, and `*.groups-a-b` (subgroup interaction).
4. `*.25-percent`, `*.50-percent`, `*.75-percent`, and original (count checkpoints),
   then the exact `one`/`two`/`three`/`four`/`eight`/`twelve` ladder around any boundary.
5. `*.effects-whitespace-minified` (only if it differs; it currently does not).

Use one of the two source families consistently for the upload matrix—the files are
not byte-identical outside the effects block.  Save the result beside the corresponding
manifest entry.  The smallest permanent fix is **no theme-source change** until that
matrix demonstrates a boundary.  Once a boundary is proven, optimize only the proven
redundancy while retaining the exact element count/appearance required by the evidence.
