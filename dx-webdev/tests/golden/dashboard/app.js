'use strict';

$(function() {
    const sampleData = {
        "metrics": [
            {
                "region": "North",
                "pipeline": 42,
                "revenue": 182000,
                "risk": "Low"
            },
            {
                "region": "Central",
                "pipeline": 31,
                "revenue": 145000,
                "risk": "Medium"
            },
            {
                "region": "West",
                "pipeline": 27,
                "revenue": 121500,
                "risk": "High"
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
        $('#filterToolbar').dxToolbar({
            "elementAttr": {
                "class": "dashboard__filter-toolbar"
            },
            "items": [
                {
                    "location": "before",
                    "text": "Filters"
                },
                {
                    "location": "before",
                    "widget": "dxSelectBox",
                    "options": {
                        "width": 180,
                        "items": [
                            "All regions",
                            "North",
                            "Central",
                            "West"
                        ],
                        "value": "All regions",
                        "inputAttr": {
                            "aria-label": "Region filter"
                        },
                        "onValueChanged": runHandler("applyRegionFilter")
                    }
                },
                {
                    "location": "after",
                    "widget": "dxButton",
                    "options": {
                        "text": "Apply",
                        "type": "default",
                        "icon": "filter",
                        "onClick": notifyAction("Filters applied", "info", 1200)
                    }
                }
            ]
        });

        $('#metricsGrid').dxDataGrid({
            "elementAttr": {
                "class": "dashboard__metrics-grid"
            },
            "dataSource": [
                {
                    "region": "North",
                    "pipeline": 42,
                    "revenue": 182000,
                    "risk": "Low"
                },
                {
                    "region": "Central",
                    "pipeline": 31,
                    "revenue": 145000,
                    "risk": "Medium"
                },
                {
                    "region": "West",
                    "pipeline": 27,
                    "revenue": 121500,
                    "risk": "High"
                }
            ],
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
                "allowAdding": false,
                "allowUpdating": false,
                "allowDeleting": false,
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
                    "dataField": "region"
                },
                {
                    "dataField": "pipeline",
                    "caption": "Pipeline",
                    "dataType": "number",
                    "alignment": "right"
                },
                {
                    "dataField": "revenue",
                    "dataType": "number",
                    "format": "currency",
                    "alignment": "right"
                },
                {
                    "dataField": "risk"
                }
            ],
            "summary": {
                "totalItems": [
                    {
                        "column": "pipeline",
                        "summaryType": "sum"
                    },
                    {
                        "column": "revenue",
                        "summaryType": "sum",
                        "valueFormat": "currency"
                    }
                ]
            }
        });

        $('#dashboardLoadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "dashboard__dashboard-load-panel"
            },
            "visible": false,
            "shading": true,
            "showIndicator": true,
            "message": "Loading dashboard..."
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
