---
name: dx-styling-without-themebuilder
description: Use when styling DevExtreme jQuery apps with local CSS variables and scoped selectors.
---

# Styling Without ThemeBuilder

Use this skill when styling DevExtreme jQuery output.

Start with official DevExtreme theme CSS, then add app-level variables in `styles.css`. Use wrapper-scoped selectors and stable anchors from `elementAttr`, `inputAttr`, `cssClass`, and templates. Prefer widget options over CSS overrides whenever the option exists.

Good selectors:

```css
.orders-page .orders-grid {
    min-height: 420px;
}

.orders-page .priority-cell {
    font-weight: 600;
}

.orders-page .dx-state-focused {
    outline: 2px solid var(--app-focus);
}
```

Bad selectors:

```css
.dx-button {
    border-radius: 20px;
}

.dx-datagrid td {
    padding: 24px !important;
}
```

Broad global `.dx-*` overrides are allowed only for an intentional app-wide skin rule. Do not edit generated theme files. Do not emit ThemeBuilder output.

Keep styling accessible: visible focus rings, sufficient contrast, disabled states, validation states, and stable responsive constraints. Layout CSS should prevent text overflow and avoid widget resize jumps.
