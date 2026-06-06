---
name: dx-component-selection
description: Use when choosing DevExtreme jQuery widgets from UX intent and data shape.
---

# DevExtreme Component Selection

Use this skill when deciding which DevExtreme jQuery widgets belong in a page.

Choose widgets based on workflow, data shape, editing model, density, accessibility, keyboard behavior, and responsive needs. For complex data-heavy pages, plan the widget composition before writing code.

Common mappings:

- Editable table: `dxDataGrid`
- Hierarchical table: `dxTreeList`
- Form: `dxForm`
- Command bar: `dxToolbar`
- Modal workflow: `dxPopup`
- Drawer or detail panel: `dxDrawer` or `dxPopup`
- Tabbed content: `dxTabPanel` or `dxTabs`
- Step workflow: `dxStepper` plus `dxForm`
- Select input: `dxSelectBox`
- Tag input: `dxTagBox`
- Date input: `dxDateBox` or `dxDateRangeBox`
- Notifications: `dxToast` or `DevExpress.ui.notify`
- Load state: `dxLoadPanel`
- Menus: `dxMenu` or `dxContextMenu`
- Navigation: `dxTreeView`, `dxList`, `dxTabs`, or `dxDrawer`

Do not invent custom controls where DevExtreme provides an appropriate widget. Use custom HTML only for layout, summary cards, static content, or templates where a widget option does not cover the need.
