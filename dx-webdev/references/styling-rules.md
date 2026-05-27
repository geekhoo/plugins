# Styling Rules

Use this order for DevExtreme jQuery pages:

1. Load an official DevExtreme base theme CSS first.
2. Define app CSS variables in `styles.css`.
3. Apply wrapper-scoped overrides for page-specific layout and appearance.
4. Use templates only when widget options are not enough.

Prefer widget options for density, icons, text, validation, disabled state, editor behavior, paging, filtering, and layout before adding CSS overrides.

Good scoped selectors:

```css
.orders-page .orders-grid {
    min-height: 420px;
}

.orders-page .status-ready {
    color: var(--app-success);
}
```

Avoid broad global selectors unless an app-wide skin rule is intentional:

```css
.dx-button {
    border-radius: 16px;
}

.dx-datagrid .dx-row > td {
    padding: 20px !important;
}
```

Do not edit generated theme files. Do not use ThemeBuilder output. Keep focus rings visible, contrast sufficient, disabled states clear, validation messages legible, and responsive layouts stable.
