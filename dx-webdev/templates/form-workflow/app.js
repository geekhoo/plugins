'use strict';

$(function() {
    const request = {
        requester: 'Case Owner',
        category: 'Access Review',
        priority: 'Normal',
        notes: '',
    };

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        DevExpress.ui.notify(message, 'error', 2400);
    }

    try {
        $('#requestForm').dxForm({
            formData: request,
            labelLocation: 'top',
            colCountByScreen: { xs: 1, sm: 1, md: 2, lg: 2 },
            showValidationSummary: true,
            validationGroup: 'workflowValidation',
            elementAttr: { class: 'form-workflow__request-form' },
            items: [
                {
                    dataField: 'requester',
                    isRequired: true,
                    editorOptions: { inputAttr: { 'aria-label': 'Requester' } },
                },
                {
                    dataField: 'category',
                    isRequired: true,
                    editorType: 'dxSelectBox',
                    editorOptions: {
                        items: ['Access Review', 'Change Request', 'Incident'],
                        inputAttr: { 'aria-label': 'Category' },
                    },
                },
                {
                    dataField: 'priority',
                    editorType: 'dxSelectBox',
                    editorOptions: {
                        items: ['Low', 'Normal', 'High'],
                        inputAttr: { 'aria-label': 'Priority' },
                    },
                },
                {
                    dataField: 'notes',
                    editorType: 'dxTextArea',
                    colSpan: 2,
                    validationRules: [{ type: 'required', message: 'Notes are required.' }],
                    editorOptions: {
                        minHeight: 96,
                        inputAttr: { 'aria-label': 'Notes' },
                    },
                },
            ],
        });

        $('#workflowLoadPanel').dxLoadPanel({
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Submitting...',
        });

        $('#submitButton').dxButton({
            text: 'Submit',
            type: 'default',
            stylingMode: 'contained',
            elementAttr: { class: 'form-workflow__submit-button' },
            onClick: function() {
                const result = DevExpress.validationEngine.validateGroup('workflowValidation');
                if (!result.isValid) {
                    DevExpress.ui.notify('Resolve validation errors before submitting.', 'warning', 1800);
                    return;
                }

                DevExpress.ui.notify('Workflow submitted', 'success', 1600);
            },
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
