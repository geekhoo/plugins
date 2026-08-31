'use strict';

$(function() {
    const sampleData = {
        "request": {
            "requester": "Case Owner",
            "email": "case.owner@contoso.example",
            "category": "Access Review",
            "notes": ""
        }
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
        $('#requestForm').dxForm({
            "elementAttr": {
                "class": "form-workflow__request-form"
            },
            "formData": {
                "requester": "Case Owner",
                "email": "case.owner@contoso.example",
                "category": "Access Review",
                "notes": ""
            },
            "labelLocation": "top",
            "colCountByScreen": {
                "xs": 1,
                "sm": 1,
                "md": 2,
                "lg": 2
            },
            "items": [
                {
                    "dataField": "requester",
                    "isRequired": true,
                    "validationRules": [
                        {
                            "type": "stringLength",
                            "min": 3,
                            "message": "Requester name is too short."
                        }
                    ],
                    "editorOptions": {
                        "inputAttr": {
                            "aria-label": "Requester"
                        }
                    }
                },
                {
                    "dataField": "email",
                    "validationRules": [
                        {
                            "type": "email",
                            "message": "Enter a valid work email."
                        }
                    ],
                    "editorOptions": {
                        "inputAttr": {
                            "aria-label": "Email"
                        }
                    }
                },
                {
                    "dataField": "category",
                    "isRequired": true,
                    "editorType": "dxSelectBox",
                    "editorOptions": {
                        "items": [
                            "Access Review",
                            "Change Request",
                            "Incident"
                        ],
                        "inputAttr": {
                            "aria-label": "Category"
                        }
                    }
                },
                {
                    "dataField": "notes",
                    "editorType": "dxTextArea",
                    "colSpan": 2,
                    "validationRules": [
                        {
                            "type": "required",
                            "message": "Notes are required."
                        }
                    ],
                    "editorOptions": {
                        "minHeight": 96,
                        "inputAttr": {
                            "aria-label": "Notes"
                        }
                    }
                }
            ],
            "showValidationSummary": true,
            "validationGroup": "workflowValidation",
            "onFieldDataChanged": runHandler("trackFieldChange")
        });

        $('#submitButton').dxButton({
            "elementAttr": {
                "class": "form-workflow__submit-button"
            },
            "text": "Submit request",
            "type": "default",
            "stylingMode": "contained",
            "onClick": submitValidationGroup("workflowValidation", runHandler("submitAccessRequest"))
        });

        $('#workflowLoadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "form-workflow__workflow-load-panel"
            },
            "visible": false,
            "shading": true,
            "showIndicator": true,
            "message": "Submitting..."
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
