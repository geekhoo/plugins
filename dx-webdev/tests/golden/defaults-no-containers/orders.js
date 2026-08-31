'use strict';

$(function() {
    const sampleData = {
        "items": [
            {
                "text": "Review queue prepared",
                "status": "Ready"
            },
            {
                "text": "Data refresh completed",
                "status": "Complete"
            },
            {
                "text": "Validation pass required",
                "status": "Pending"
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
        $('#pageToolbar').dxToolbar({
            "elementAttr": {
                "class": "basic-page__page-toolbar"
            },
            "items": [
                {
                    "location": "before",
                    "text": "Operations"
                },
                {
                    "location": "after",
                    "widget": "dxButton",
                    "options": {
                        "text": "Refresh",
                        "icon": "refresh",
                        "stylingMode": "outlined",
                        "elementAttr": {
                            "class": "toolbar-refresh-button"
                        },
                        "onClick": notifyAction('Refresh requested', 'info', 1400)
                    }
                }
            ]
        });

        $('#primaryAction').dxButton({
            "elementAttr": {
                "class": "basic-page__primary-action"
            },
            "text": "Run Review",
            "type": "default",
            "stylingMode": "contained",
            "onClick": notifyAction('Action completed', 'success', 1600)
        });

        $('#activityList').dxList({
            "elementAttr": {
                "class": "basic-page__activity-list"
            },
            "dataSource": [
                {
                    "text": "Review queue prepared",
                    "status": "Ready"
                },
                {
                    "text": "Data refresh completed",
                    "status": "Complete"
                },
                {
                    "text": "Validation pass required",
                    "status": "Pending"
                }
            ],
            "noDataText": "No activity yet.",
            "displayExpr": joinFields(["text","status"])
        });

        $('#pageLoadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "basic-page__page-load-panel"
            },
            "visible": false,
            "shading": true,
            "showIndicator": true,
            "message": "Loading..."
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
