---
name: dx-ux-review
description: Use when reviewing DevExtreme jQuery pages for fit, correctness, scope, states, and validation.
---

# DevExtreme UX Review

Use this checklist when reviewing generated or modified DevExtreme jQuery pages:

- Correct widget selected for each UX need.
- No framework code, JSX, TSX, or wrapper package usage.
- No ThemeBuilder output.
- Correct script and CSS load order.
- Widget containers exist in `index.html`.
- Widget options are used instead of unnecessary CSS overrides.
- Styling is wrapper-scoped.
- Loading, empty, error, disabled, and validation states exist where relevant.
- Keyboard navigation and focus behavior are considered.
- Labels and input attributes are present.
- Responsive layout is stable.
- Text does not overflow its container.
- Data formatting is appropriate for dates, numbers, currency, status, and summaries.
- Static validation scripts pass.
- Browser smoke test is recommended for generated UI.

Report concrete file and line findings first when reviewing code. Do not claim browser validation unless it was actually run.
