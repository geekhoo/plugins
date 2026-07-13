# Worked example

**Request**: "Make the Forecast band collapsed by default and reduce the first child column to 90px."

**Correct output:**

```
## Grid Update: Collapse Forecast band by default; reduce ForecastQ1 width to 90px

### Affected Columns/Bands
- Primary: Forecast band — set expanded: false; ForecastQ1 column — width 120 → 90
- Dependencies: ForecastQ2 width may need adjustment if band has a fixed total width CSS rule

### Update Checklist (implement in this order)

**JS (programs.page.js):**
- [ ] 1. Forecast band config — set `expanded: false`
- [ ] 2. ForecastQ1 column — set `width: 90`

**CSS (programs-v2.cshtml.css):**
- [ ] 3. Check `.mf-component-programs ::deep .dx-band-row` for any fixed width on the Forecast band cell — update if present
- [ ] 4. No other CSS changes needed for this update

### CSS Scoping Check
- Uses ::deep for DevExtreme-appended elements? YES
- Scoped to .mf-component-programs? YES

### Verification Steps
- [ ] Reload page — Forecast band should render collapsed on load
- [ ] Expand the Forecast band and confirm ForecastQ1 renders at 90px
- [ ] Confirm ForecastQ2 width is visually unaffected
- [ ] Verify header styling in both expanded and collapsed state
```
