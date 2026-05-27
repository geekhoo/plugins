'use strict';

$(function() {
    const sampleData = {
        "orders": [
            {
                "id": 1001,
                "customer": "Northwind Traders",
                "status": "Ready",
                "total": 1280.5
            },
            {
                "id": 1002,
                "customer": "Contoso Retail",
                "status": "Review",
                "total": 842
            }
        ]
    };

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        DevExpress.ui.notify(message, 'error', 2400);
    }

    try {
        $('#ordersToolbar').dxToolbar({
            "elementAttr": {
                "class": "orders-toolbar-widget"
            },
            "items": [
                {
                    "location": "before",
                    "text": "Orders Workbench"
                },
                {
                    "location": "after",
                    "widget": "dxButton",
                    "options": {
                        "text": "Refresh",
                        "icon": "refresh",
                        "type": "default"
                    }
                }
            ]
        });

        $('#ordersList').dxList({
            "elementAttr": {
                "class": "orders-list-widget"
            },
            "dataSource": [
                {
                    "id": 1001,
                    "customer": "Northwind Traders",
                    "status": "Ready",
                    "total": 1280.5
                },
                {
                    "id": 1002,
                    "customer": "Contoso Retail",
                    "status": "Review",
                    "total": 842
                }
            ],
            "noDataText": "No orders match the current filters.",
            "displayExpr": "customer",
            "searchEnabled": true
        });

        $('#loadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "basic-page__load-panel"
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
