# JS config rules (enforce these on every change)

```js
// Correct — stays inside Markefin.runWhenAvailable, no new globals
Markefin.runWhenAvailable('.programs-v2-wrapper', (root) => {
    $(root).find('.programs-grid').dxDataGrid({
        columns: [
            {
                caption: 'Band Name',
                isBand: true,
                expanded: false,       // default expand/collapse state
                columns: [
                    { dataField: 'FieldA', width: 120, cssClass: 'col-field-a' },
                    { dataField: 'FieldB', width: 80,  visible: true }
                ]
            }
        ]
    });
});
```

- `width` values in the JS config are in pixels (number, no unit suffix)
- `expanded` on a band controls the default state on page load; changing it is a user-visible behavior change — flag it in the checklist
- `allowHiding: false` prevents the column chooser from toggling the column; set it intentionally, not by default
