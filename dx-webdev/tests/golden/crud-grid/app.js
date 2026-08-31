'use strict';

$(function() {
    const sampleData = {
        "orders": [
            {
                "id": 1001,
                "customer": "Acme Health",
                "status": "New",
                "total": 12840,
                "dueDate": "2026-06-02",
                "contactEmail": "ops@acme.example"
            },
            {
                "id": 1002,
                "customer": "Northwind Care",
                "status": "Review",
                "total": 9250,
                "dueDate": "2026-06-05",
                "contactEmail": "ops@northwind.example"
            },
            {
                "id": 1003,
                "customer": "Contoso Clinics",
                "status": "Approved",
                "total": 15300,
                "dueDate": "2026-06-11",
                "contactEmail": "ops@contoso.example"
            }
        ]
    };

    function notify(message, notifyType, displayTime) {
        DevExpress.ui.notify(message, notifyType || 'info', displayTime || 2000);
    }

    function notifyAction(message, notifyType, displayTime) {
        return function() {
            notify(message, notifyType, displayTime);
        };
    }

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        notify(message, 'error', 2400);
    }

    function handleDataError(e) {
        showError(e && e.error && e.error.message ? e.error.message : 'Data error');
    }

    function runHandler(name) {
        return function(e) {
            var registry = window.dxPageHandlers || {};
            if (typeof registry[name] !== 'function') {
                notify('Handler "' + name + '" is not registered on window.dxPageHandlers.', 'warning', 2400);
                return undefined;
            }
            return registry[name](e);
        };
    }

    function joinFields(fields) {
        return function(item) {
            if (!item) { return ''; }
            return fields
                .map(function(field) { return item[field]; })
                .filter(function(part) { return part !== undefined && part !== null && part !== ''; })
                .join(' - ');
        };
    }

    function submitValidationGroup(group, next) {
        return function(e) {
            var result = DevExpress.validationEngine.validateGroup(group);
            if (!result.isValid) {
                notify('Resolve validation errors before submitting.', 'warning', 1800);
                return undefined;
            }
            return next(e);
        };
    }

    try {
        $('#gridToolbar').dxToolbar({
            "elementAttr": {
                "class": "crud-grid__grid-toolbar"
            },
            "items": [
                {
                    "location": "before",
                    "text": "Orders"
                },
                {
                    "location": "after",
                    "widget": "dxButton",
                    "options": {
                        "text": "Export",
                        "icon": "exportxlsx",
                        "stylingMode": "outlined",
                        "onClick": runHandler("exportOrders")
                    }
                }
            ]
        });

        $('#ordersGrid').dxDataGrid({
            "elementAttr": {
                "class": "crud-grid__orders-grid"
            },
            "dataSource": [
                {
                    "id": 1001,
                    "customer": "Acme Health",
                    "status": "New",
                    "total": 12840,
                    "dueDate": "2026-06-02",
                    "contactEmail": "ops@acme.example"
                },
                {
                    "id": 1002,
                    "customer": "Northwind Care",
                    "status": "Review",
                    "total": 9250,
                    "dueDate": "2026-06-05",
                    "contactEmail": "ops@northwind.example"
                },
                {
                    "id": 1003,
                    "customer": "Contoso Clinics",
                    "status": "Approved",
                    "total": 15300,
                    "dueDate": "2026-06-11",
                    "contactEmail": "ops@contoso.example"
                }
            ],
            "keyExpr": "id",
            "showBorders": true,
            "columnAutoWidth": true,
            "noDataText": "No records match the current filters.",
            "searchPanel": {
                "visible": true,
                "width": 240
            },
            "filterRow": {
                "visible": true
            },
            "headerFilter": {
                "visible": true
            },
            "paging": {
                "pageSize": 10
            },
            "pager": {
                "visible": true,
                "showPageSizeSelector": true,
                "allowedPageSizes": [
                    5,
                    10,
                    20
                ]
            },
            "editing": {
                "mode": "popup",
                "allowAdding": true,
                "allowUpdating": true,
                "allowDeleting": true,
                "popup": {
                    "title": "Edit record",
                    "showTitle": true,
                    "width": 720
                },
                "form": {
                    "labelLocation": "top"
                }
            },
            "onDataErrorOccurred": handleDataError,
            "columns": [
                {
                    "dataField": "id",
                    "caption": "Order",
                    "allowEditing": false,
                    "width": 110
                },
                {
                    "dataField": "customer",
                    "validationRules": [
                        {
                            "type": "required"
                        },
                        {
                            "type": "stringLength",
                            "min": 2,
                            "max": 80,
                            "message": "Customer name is 2-80 characters."
                        }
                    ]
                },
                {
                    "dataField": "status",
                    "validationRules": [
                        {
                            "type": "required"
                        }
                    ]
                },
                {
                    "dataField": "total",
                    "dataType": "number",
                    "format": {
                        "type": "currency",
                        "precision": 0
                    },
                    "alignment": "right",
                    "validationRules": [
                        {
                            "type": "required"
                        },
                        {
                            "type": "numeric"
                        },
                        {
                            "type": "range",
                            "min": 0,
                            "message": "Total cannot be negative."
                        }
                    ]
                },
                {
                    "dataField": "dueDate",
                    "dataType": "date",
                    "validationRules": [
                        {
                            "type": "required"
                        }
                    ]
                },
                {
                    "dataField": "contactEmail",
                    "validationRules": [
                        {
                            "type": "email",
                            "message": "Enter a valid contact email."
                        },
                        {
                            "type": "pattern",
                            "pattern": "@(acme|northwind|contoso)\\.example$",
                            "message": "Use an approved domain."
                        }
                    ]
                }
            ],
            "summary": {
                "totalItems": [
                    {
                        "column": "total",
                        "summaryType": "sum",
                        "valueFormat": "currency"
                    }
                ]
            },
            "onRowUpdated": notifyAction("Order saved", "success", 1600)
        });

        $('#gridLoadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "crud-grid__grid-load-panel"
            },
            "visible": false,
            "shading": true,
            "showIndicator": true,
            "message": "Loading orders..."
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
