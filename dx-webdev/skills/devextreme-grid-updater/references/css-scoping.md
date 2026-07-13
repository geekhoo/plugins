# CSS scoping rules (enforce these on every change)

DevExtreme generates DOM elements dynamically at runtime — those elements are outside the Blazor component's static HTML, so they are not subject to normal scoped CSS. The `::deep` combinator is required for any rule that targets a DevExtreme-appended class.

Pattern the user's project uses:

```css
/* Correct — ::deep targets runtime-appended DevExtreme elements */
.mf-component-programs ::deep .dx-header-row .dx-datagrid-text-content {
    font-weight: 600;
}

.mf-component-programs ::deep .dx-band-row td:nth-child(2) {
    background-color: var(--mf-band-color);
}

/* Wrong — DevExtreme elements won't match without ::deep */
.mf-component-programs .dx-header-row .dx-datagrid-text-content {
    font-weight: 600;
}
```

When adding or editing CSS rules:
- Always start with `.mf-component-programs ::deep`
- Never target `dx-col-{n}` index-based classes for styling that must survive column reordering — prefer `cssClass` defined in the JS column config
- Width overrides in CSS take precedence over JS config; flag any conflict explicitly in the checklist
