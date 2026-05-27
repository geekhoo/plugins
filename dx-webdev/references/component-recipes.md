# Component Recipes

## Grid

Use `dxDataGrid` for data-heavy tables. Typical options:

```javascript
searchPanel: { visible: true },
filterRow: { visible: true },
headerFilter: { visible: true },
columnChooser: { enabled: true },
sorting: { mode: 'multiple' },
paging: { pageSize: 20 },
pager: { showInfo: true, showPageSizeSelector: true },
focusedRowEnabled: true,
keyboardNavigation: { enabled: true }
```

For financial or operational grids, align numeric columns right, add `format`, and use `summary.totalItems`.

## CRUD Grid

Use popup editing when row editing would feel cramped:

```javascript
editing: {
    mode: 'popup',
    allowAdding: true,
    allowUpdating: true,
    allowDeleting: true,
    form: { colCount: 2 }
}
```

Add `validationRules` on required columns and form editors.

## Form

Use `dxForm` for labeled inputs, validation, and adaptive layout:

```javascript
colCountByScreen: { xs: 1, sm: 1, md: 2, lg: 3 },
items: [{
    dataField: 'email',
    editorType: 'dxTextBox',
    validationRules: [{ type: 'required' }, { type: 'email' }],
    editorOptions: { inputAttr: { 'aria-label': 'Email' } }
}]
```

## Toolbar

Use `dxToolbar` for page commands and filters:

```javascript
items: [
    { location: 'before', text: 'Orders' },
    { location: 'after', widget: 'dxButton', options: { text: 'Refresh', icon: 'refresh' } }
]
```

## Popup

Use `dxPopup` for modal workflows:

```javascript
showTitle: true,
title: 'Edit order',
width: 640,
height: 'auto',
dragEnabled: false,
hideOnOutsideClick: true
```

## Dashboard

Put filters first, keep summary cards as scoped HTML/CSS, and use DevExtreme widgets for interactive data regions. `dxToolbar`, `dxSelectBox`, `dxDateRangeBox`, `dxDataGrid`, and `dxLoadPanel` are common.

## Validation And Feedback

Use `validationRules`, validation groups, disabled submit states, `DevExpress.ui.notify(...)`, and `dxLoadPanel`. Include empty and error states for remote or filtered data.
