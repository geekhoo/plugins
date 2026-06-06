---
name: dx-options-recipes
description: Use when the user explicitly asks for DevExtreme jQuery recipes, starter configurations, or sample option sets.
---

# DevExtreme Options Recipes

Use this skill only when the user explicitly asks for recipes, starter configurations, or sample option sets. For targeted UX reconfiguration, prefer the capability-map skill so the agent selects options from intent and constraints instead of copying a canned surface.

Enterprise `dxDataGrid`:

```javascript
searchPanel: { visible: true },
filterRow: { visible: true },
headerFilter: { visible: true },
columnChooser: { enabled: true },
grouping: { autoExpandAll: false },
sorting: { mode: 'multiple' },
selection: { mode: 'multiple' },
keyboardNavigation: { enabled: true },
focusedRowEnabled: true,
paging: { pageSize: 20 },
pager: { showInfo: true, showPageSizeSelector: true },
stateStoring: { enabled: true, type: 'localStorage', storageKey: 'orders-grid' }
```

CRUD grid with popup form editing:

```javascript
editing: {
    mode: 'popup',
    allowAdding: true,
    allowUpdating: true,
    allowDeleting: true,
    popup: { title: 'Order', showTitle: true },
    form: { items: ['customer', 'status', 'dueDate'] }
}
```

Master-detail grid:

```javascript
masterDetail: {
    enabled: true,
    template(container, options) {
        $('<div>').dxDataGrid({ dataSource: options.data.lines }).appendTo(container);
    }
}
```

Filter toolbar:

```javascript
items: [
    { location: 'before', widget: 'dxSelectBox', options: { dataSource: statuses } },
    { location: 'after', widget: 'dxButton', options: { text: 'Refresh', icon: 'refresh' } }
]
```

Searchable dashboard: put filters first with `dxToolbar`, use `dxDataGrid` search and filter options, and keep summary cards as scoped HTML/CSS when no widget is needed.

Validation-heavy `dxForm`:

```javascript
items: [{
    dataField: 'email',
    editorType: 'dxTextBox',
    validationRules: [
        { type: 'required' },
        { type: 'email' }
    ],
    editorOptions: { inputAttr: { 'aria-label': 'Email' } }
}]
```

Read-only review mode: disable editing, set editor `readOnly: true`, use clear status labels, and preserve formatting.

Responsive form layout: use `colCountByScreen`, `labelLocation`, `minColWidth`, and grouped items.

Toast and load panel feedback: use `DevExpress.ui.notify(...)` for short feedback and `dxLoadPanel` for blocking or long-running work.

Always consider `elementAttr` and `inputAttr` for stable styling anchors and accessible labels.
