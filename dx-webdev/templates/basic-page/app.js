'use strict';

$(function() {
    const activity = [
        { text: 'Review queue prepared', status: 'Ready' },
        { text: 'Data refresh completed', status: 'Complete' },
        { text: 'Validation pass required', status: 'Pending' },
    ];

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        DevExpress.ui.notify(message, 'error', 2400);
    }

    try {
        $('#pageToolbar').dxToolbar({
            elementAttr: { class: 'basic-page__toolbar' },
            items: [
                { location: 'before', text: 'Operations' },
                {
                    location: 'after',
                    widget: 'dxButton',
                    options: {
                        text: 'Refresh',
                        icon: 'refresh',
                        stylingMode: 'outlined',
                        onClick: function() {
                            DevExpress.ui.notify('Refresh requested', 'info', 1400);
                        },
                    },
                },
            ],
        });

        $('#primaryAction').dxButton({
            text: 'Run Review',
            type: 'default',
            stylingMode: 'contained',
            elementAttr: { class: 'basic-page__primary-action' },
            onClick: function() {
                DevExpress.ui.notify('Review started', 'success', 1600);
            },
        });

        $('#activityList').dxList({
            dataSource: activity,
            noDataText: 'No activity yet.',
            elementAttr: { class: 'basic-page__activity-list' },
            itemTemplate: function(item) {
                return $('<div>')
                    .addClass('activity-item')
                    .text(`${item.text} - ${item.status}`);
            },
        });

        $('#pageLoadPanel').dxLoadPanel({
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Loading...',
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
