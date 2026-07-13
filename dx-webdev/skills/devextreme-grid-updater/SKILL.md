---
name: devextreme-grid-updater
description: >
  Use whenever the user mentions updating the grid, changing column width, updating a
  band, fixing grid styling, programs grid, ProgramsV2 grid, or any DevExtreme DataGrid
  column or band change in the v2 project — even implicit asks like "make the column
  wider" or "hide that band". Enforces a dependency scan and an ordered, atomic checklist.
---

# DevExtreme Grid Updater

## Why this skill exists

The ProgramsV2 DataGrid has tightly coupled column/band configuration split across two files:

- **JS config**: `<v2-repo>\wwwroot\js\pages\programs.page.js`
- **CSS**: `<v2-repo>\wwwroot\css\pages\programs-v2.cshtml.css`

(`<v2-repo>` = the v2 project root on this machine — locate it first; do not assume a
hardcoded user-profile path.)

Changing one column's width, visibility, or header style without checking its siblings and parent band almost always breaks something else — adjacent column widths shift, band headers misalign, or expand/collapse state becomes inconsistent. This skill enforces a read-first, validate-dependencies, then write approach so every change is atomic and complete.

> **Do not make structural changes to the grid without explicit instruction.** This skill is for the changes the user asks for — scoped to column/band config, widths, visibility, header styling, and expand/collapse defaults. Adding new columns, removing bands, or changing the grid's data source are out of scope unless explicitly requested.

---

## Step 1 — Read current state before touching anything

Before proposing any change, read both source files to understand what is actually there:

```
Read: <v2-repo>\wwwroot\js\pages\programs.page.js
Read: <v2-repo>\wwwroot\css\pages\programs-v2.cshtml.css
```

Look for:
- All column definitions inside the `Markefin.runWhenAvailable` init block — note `dataField`, `width`, `visible`, `allowHiding`, `cssClass`, and band membership
- Band definitions — `isBand: true`, `expanded` default, child columns
- CSS rules scoped under `.mf-component-programs ::deep` that target `dx-header-row`, `dx-band-row`, `dx-datagrid-headers`, or column-specific classes

The `Markefin.runWhenAvailable` pattern looks like:

```js
Markefin.runWhenAvailable('.programs-v2-wrapper', (root) => {
    $(root).find('.programs-grid').dxDataGrid({
        columns: [ ... ]
    });
});
```

Note: the wrapper selector (`.programs-v2-wrapper`), the grid selector (`.programs-grid`), and the CSS scoping class (`.mf-component-programs`) used throughout this skill are illustrative — confirm the actual selectors by reading the real files in Step 1 before using them in any change.

Never create new globals on `window.Markefin`. All grid init must stay inside this pattern.

---

## Step 2 — Validate interdependencies

For the column or band the user wants to change, answer these before writing anything:

1. **Siblings in the same band**: If you change this column's width, do sibling column widths need to be recalculated so the band total stays consistent?
2. **Band expand/collapse**: Does the change affect what is visible in the collapsed state? If so, does `expanded: false/true` on the band need to change?
3. **CSS double-coverage**: Is there a CSS rule that hardcodes a width or visibility that conflicts with the JS config? (DevExtreme-appended classes like `dx-col-{n}` can do this.)
4. **Header class coupling**: Does the column have a custom `cssClass` that CSS rules depend on? Renaming or removing it will silently break styling.
5. **`allowHiding` implications**: If `visible` is being changed, is `allowHiding` set in a way that would prevent the user from restoring it via the column chooser?

If any of these are "yes", add the dependent change to the checklist.

---

## Step 3 — Produce the update checklist

Output the following structure. Fill every section — do not omit sections even if they are "no changes needed" (write that explicitly so it is clear it was checked).

```
## Grid Update: {description of change}

### Affected Columns/Bands
- Primary: {column name or dataField} — {what is changing}
- Dependencies: {other columns/bands affected, or "none identified"}

### Update Checklist (implement in this order)

**JS (programs.page.js):**
- [ ] 1. {specific property path}.{property} = {new value}
- [ ] 2. {next JS change, if any}

**CSS (programs-v2.cshtml.css):**
- [ ] 3. {selector rule to add/update, with full ::deep path}
- [ ] 4. {next CSS change, if any}

### CSS Scoping Check
- Uses ::deep for DevExtreme-appended elements? [YES / NO — list any violations]
- Scoped to .mf-component-programs? [YES / NO]

### Verification Steps
- [ ] Reload page and confirm column widths render as expected
- [ ] Check band expand/collapse behavior in both states
- [ ] Verify header styling in both expanded and collapsed state
- [ ] Confirm no sibling column has visually shifted
```

---

## CSS and JS rules (enforce on every change)

Before writing any CSS, load `references/css-scoping.md` (`.mf-component-programs ::deep`
prefix required for DevExtreme-appended elements; never style via `dx-col-{n}` index
classes; CSS width overrides beat JS config — flag conflicts). Before writing any JS,
load `references/js-config-rules.md` (stay inside `Markefin.runWhenAvailable`, no new
globals; pixel-number widths; `expanded` and `allowHiding` semantics).

---

## Implementation order rationale

Always apply JS changes before CSS changes. DevExtreme renders column structure from the JS config; CSS rules that target generated classes will silently do nothing if the JS config produces different markup than expected. Getting the structure right first makes CSS debugging deterministic.

---

## Example

A full worked request→checklist example is in `references/example-update.md`.
