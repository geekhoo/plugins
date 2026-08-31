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
                        "type": "default",
                        "onClick": runHandler("refreshOrders")
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
            "displayExpr": joinFields(["customer","status"]),
            "searchEnabled": true,
            "onItemClick": notifyAction("Order opened", "info", 1400)
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
