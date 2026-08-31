'use strict';

$(function() {
    const sampleData = {
        "rows": [
            {
                "id": 1,
                "name": "Alpha"
            },
            {
                "id": 2,
                "name": "Beta"
            }
        ],
        "record": {
            "name": "Alpha"
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
        $('#w0_dxDataGrid').dxDataGrid({
            "elementAttr": {
                "class": "basic-page__w0-dx-data-grid"
            },
            "dataSource": [
                {
                    "id": 1,
                    "name": "Alpha"
                },
                {
                    "id": 2,
                    "name": "Beta"
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
            "onDataErrorOccurred": handleDataError
        });

        $('#w1_dxTreeList').dxTreeList({
            "elementAttr": {
                "class": "basic-page__w1-dx-tree-list"
            },
            "dataSource": [
                {
                    "id": 1,
                    "name": "Alpha"
                },
                {
                    "id": 2,
                    "name": "Beta"
                }
            ],
            "showBorders": true,
            "columnAutoWidth": true,
            "onDataErrorOccurred": handleDataError
        });

        $('#w2_dxForm').dxForm({
            "elementAttr": {
                "class": "basic-page__w2-dx-form"
            },
            "formData": {
                "name": "Alpha"
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
                    "editorOptions": {
                        "inputAttr": {
                            "aria-label": "Requester"
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
                    "dataField": "priority",
                    "editorType": "dxSelectBox",
                    "editorOptions": {
                        "items": [
                            "Low",
                            "Normal",
                            "High"
                        ],
                        "inputAttr": {
                            "aria-label": "Priority"
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
            "validationGroup": "workflowValidation"
        });

        $('#w3_dxList').dxList({
            "elementAttr": {
                "class": "basic-page__w3-dx-list"
            },
            "dataSource": [
                {
                    "id": 1,
                    "name": "Alpha"
                },
                {
                    "id": 2,
                    "name": "Beta"
                }
            ],
            "noDataText": "No activity yet.",
            "displayExpr": joinFields(["name"])
        });

        $('#w4_dxToolbar').dxToolbar({
            "elementAttr": {
                "class": "basic-page__w4-dx-toolbar"
            },
            "items": [
                {
                    "location": "before",
                    "text": "Gallery"
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

        $('#w5_dxButton').dxButton({
            "elementAttr": {
                "class": "basic-page__w5-dx-button"
            },
            "text": "Gallery action",
            "type": "default",
            "stylingMode": "contained",
            "onClick": notifyAction('Action completed', 'success', 1600)
        });

        $('#w6_dxLoadPanel').dxLoadPanel({
            "elementAttr": {
                "class": "basic-page__w6-dx-load-panel"
            },
            "visible": false,
            "shading": true,
            "showIndicator": true,
            "message": "Loading..."
        });

        $('#w7_dxAccordion').dxAccordion({
            "elementAttr": {
                "class": "basic-page__w7-dx-accordion"
            }
        });

        $('#w8_dxBox').dxBox({
            "elementAttr": {
                "class": "basic-page__w8-dx-box"
            }
        });

        $('#w9_dxButtonGroup').dxButtonGroup({
            "elementAttr": {
                "class": "basic-page__w9-dx-button-group"
            }
        });

        $('#w10_dxCalendar').dxCalendar({
            "elementAttr": {
                "class": "basic-page__w10-dx-calendar"
            }
        });

        $('#w11_dxCardView').dxCardView({
            "elementAttr": {
                "class": "basic-page__w11-dx-card-view"
            }
        });

        $('#w12_dxChart').dxChart({
            "elementAttr": {
                "class": "basic-page__w12-dx-chart"
            }
        });

        $('#w13_dxChat').dxChat({
            "elementAttr": {
                "class": "basic-page__w13-dx-chat"
            }
        });

        $('#w14_dxCheckBox').dxCheckBox({
            "elementAttr": {
                "class": "basic-page__w14-dx-check-box"
            }
        });

        $('#w15_dxContextMenu').dxContextMenu({
            "elementAttr": {
                "class": "basic-page__w15-dx-context-menu"
            }
        });

        $('#w16_dxDateBox').dxDateBox({
            "elementAttr": {
                "class": "basic-page__w16-dx-date-box"
            }
        });

        $('#w17_dxDrawer').dxDrawer({
            "elementAttr": {
                "class": "basic-page__w17-dx-drawer"
            }
        });

        $('#w18_dxDropDownBox').dxDropDownBox({
            "elementAttr": {
                "class": "basic-page__w18-dx-drop-down-box"
            }
        });

        $('#w19_dxDropDownButton').dxDropDownButton({
            "elementAttr": {
                "class": "basic-page__w19-dx-drop-down-button"
            }
        });

        $('#w20_dxFileManager').dxFileManager({
            "elementAttr": {
                "class": "basic-page__w20-dx-file-manager"
            }
        });

        $('#w21_dxFileUploader').dxFileUploader({
            "elementAttr": {
                "class": "basic-page__w21-dx-file-uploader"
            }
        });

        $('#w22_dxFilterBuilder').dxFilterBuilder({
            "elementAttr": {
                "class": "basic-page__w22-dx-filter-builder"
            }
        });

        $('#w23_dxFunnel').dxFunnel({
            "elementAttr": {
                "class": "basic-page__w23-dx-funnel"
            }
        });

        $('#w24_dxGallery').dxGallery({
            "elementAttr": {
                "class": "basic-page__w24-dx-gallery"
            }
        });

        $('#w25_dxGantt').dxGantt({
            "elementAttr": {
                "class": "basic-page__w25-dx-gantt"
            }
        });

        $('#w26_dxHtmlEditor').dxHtmlEditor({
            "elementAttr": {
                "class": "basic-page__w26-dx-html-editor"
            }
        });

        $('#w27_dxMenu').dxMenu({
            "elementAttr": {
                "class": "basic-page__w27-dx-menu"
            }
        });

        $('#w28_dxNumberBox').dxNumberBox({
            "elementAttr": {
                "class": "basic-page__w28-dx-number-box"
            }
        });

        $('#w29_dxPieChart').dxPieChart({
            "elementAttr": {
                "class": "basic-page__w29-dx-pie-chart"
            }
        });

        $('#w30_dxPivotGrid').dxPivotGrid({
            "elementAttr": {
                "class": "basic-page__w30-dx-pivot-grid"
            }
        });

        $('#w31_dxPivotGridFieldChooser').dxPivotGridFieldChooser({
            "elementAttr": {
                "class": "basic-page__w31-dx-pivot-grid-field-chooser"
            }
        });

        $('#w32_dxPopover').dxPopover({
            "elementAttr": {
                "class": "basic-page__w32-dx-popover"
            }
        });

        $('#w33_dxPopup').dxPopup({
            "elementAttr": {
                "class": "basic-page__w33-dx-popup"
            }
        });

        $('#w34_dxProgressBar').dxProgressBar({
            "elementAttr": {
                "class": "basic-page__w34-dx-progress-bar"
            }
        });

        $('#w35_dxRadioGroup').dxRadioGroup({
            "elementAttr": {
                "class": "basic-page__w35-dx-radio-group"
            }
        });

        $('#w36_dxResponsiveBox').dxResponsiveBox({
            "elementAttr": {
                "class": "basic-page__w36-dx-responsive-box"
            }
        });

        $('#w37_dxScheduler').dxScheduler({
            "elementAttr": {
                "class": "basic-page__w37-dx-scheduler"
            }
        });

        $('#w38_dxScrollView').dxScrollView({
            "elementAttr": {
                "class": "basic-page__w38-dx-scroll-view"
            }
        });

        $('#w39_dxSelectBox').dxSelectBox({
            "elementAttr": {
                "class": "basic-page__w39-dx-select-box"
            }
        });

        $('#w40_dxSortable').dxSortable({
            "elementAttr": {
                "class": "basic-page__w40-dx-sortable"
            }
        });

        $('#w41_dxSpeedDialAction').dxSpeedDialAction({
            "elementAttr": {
                "class": "basic-page__w41-dx-speed-dial-action"
            }
        });

        $('#w42_dxSplitter').dxSplitter({
            "elementAttr": {
                "class": "basic-page__w42-dx-splitter"
            }
        });

        $('#w43_dxStepper').dxStepper({
            "elementAttr": {
                "class": "basic-page__w43-dx-stepper"
            }
        });

        $('#w44_dxSwitch').dxSwitch({
            "elementAttr": {
                "class": "basic-page__w44-dx-switch"
            }
        });

        $('#w45_dxTabPanel').dxTabPanel({
            "elementAttr": {
                "class": "basic-page__w45-dx-tab-panel"
            }
        });

        $('#w46_dxTabs').dxTabs({
            "elementAttr": {
                "class": "basic-page__w46-dx-tabs"
            }
        });

        $('#w47_dxTagBox').dxTagBox({
            "elementAttr": {
                "class": "basic-page__w47-dx-tag-box"
            }
        });

        $('#w48_dxTextArea').dxTextArea({
            "elementAttr": {
                "class": "basic-page__w48-dx-text-area"
            }
        });

        $('#w49_dxTextBox').dxTextBox({
            "elementAttr": {
                "class": "basic-page__w49-dx-text-box"
            }
        });

        $('#w50_dxTileView').dxTileView({
            "elementAttr": {
                "class": "basic-page__w50-dx-tile-view"
            }
        });

        $('#w51_dxToast').dxToast({
            "elementAttr": {
                "class": "basic-page__w51-dx-toast"
            }
        });

        $('#w52_dxTooltip').dxTooltip({
            "elementAttr": {
                "class": "basic-page__w52-dx-tooltip"
            }
        });

        $('#w53_dxTreeView').dxTreeView({
            "elementAttr": {
                "class": "basic-page__w53-dx-tree-view"
            }
        });

        $('#w54_dxValidationGroup').dxValidationGroup({
            "elementAttr": {
                "class": "basic-page__w54-dx-validation-group"
            }
        });

        $('#w55_dxValidationSummary').dxValidationSummary({
            "elementAttr": {
                "class": "basic-page__w55-dx-validation-summary"
            }
        });

        $('#w56_dxValidator').dxValidator({
            "elementAttr": {
                "class": "basic-page__w56-dx-validator"
            }
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
