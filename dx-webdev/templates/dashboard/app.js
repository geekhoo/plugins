'use strict';

$(function() {
    const metrics = [
        { region: 'North', pipeline: 42, revenue: 182000, risk: 'Low' },
        { region: 'Central', pipeline: 31, revenue: 145000, risk: 'Medium' },
        { region: 'West', pipeline: 27, revenue: 121500, risk: 'High' },
    ];

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        DevExpress.ui.notify(message, 'error', 2400);
    }

    try {
        $('#filterToolbar').dxToolbar({
            elementAttr: { class: 'dashboard__filter-toolbar' },
            items: [
                { location: 'before', text: 'Filters' },
                {
                    location: 'before',
                    widget: 'dxSelectBox',
                    options: {
                        width: 180,
                        items: ['All regions', 'North', 'Central', 'West'],
                        value: 'All regions',
                        inputAttr: { 'aria-label': 'Region filter' },
                    },
                },
                {
                    location: 'after',
                    widget: 'dxButton',
                    options: {
                        text: 'Apply',
                        type: 'default',
                        icon: 'filter',
                    },
                },
            ],
        });

        $('#metricsGrid').dxDataGrid({
            dataSource: metrics,
            keyExpr: 'region',
            showBorders: true,
            columnAutoWidth: true,
            noDataText: 'No metrics match the current filters.',
            elementAttr: { class: 'dashboard__metrics-grid' },
            searchPanel: { visible: true, width: 240 },
            filterRow: { visible: true },
            headerFilter: { visible: true },
            paging: { pageSize: 10 },
            columns: [
                { dataField: 'region' },
                { dataField: 'pipeline', caption: 'Pipeline', dataType: 'number', alignment: 'right' },
                { dataField: 'revenue', dataType: 'number', format: 'currency', alignment: 'right' },
                { dataField: 'risk' },
            ],
            summary: {
                totalItems: [
                    { column: 'pipeline', summaryType: 'sum' },
                    { column: 'revenue', summaryType: 'sum', valueFormat: 'currency' },
                ],
            },
            onDataErrorOccurred: function(e) {
                showError(e.error && e.error.message ? e.error.message : 'Data error');
            },
        });

        $('#dashboardLoadPanel').dxLoadPanel({
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Loading dashboard...',
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
