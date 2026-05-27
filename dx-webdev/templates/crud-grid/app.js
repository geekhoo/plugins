'use strict';

$(function() {
    const orders = [
        { id: 1001, customer: 'Acme Health', status: 'New', total: 12840, dueDate: '2026-06-02' },
        { id: 1002, customer: 'Northwind Care', status: 'Review', total: 9250, dueDate: '2026-06-05' },
        { id: 1003, customer: 'Contoso Clinics', status: 'Approved', total: 15300, dueDate: '2026-06-11' },
    ];

    function showError(message) {
        $('[data-error-state]').prop('hidden', false).text(message);
        DevExpress.ui.notify(message, 'error', 2400);
    }

    try {
        $('#gridToolbar').dxToolbar({
            elementAttr: { class: 'crud-grid__toolbar' },
            items: [
                { location: 'before', text: 'Orders' },
                {
                    location: 'after',
                    widget: 'dxButton',
                    options: {
                        text: 'Export',
                        icon: 'exportxlsx',
                        stylingMode: 'outlined',
                    },
                },
            ],
        });

        $('#ordersGrid').dxDataGrid({
            dataSource: orders,
            keyExpr: 'id',
            showBorders: true,
            columnAutoWidth: true,
            noDataText: 'No orders match the current filters.',
            elementAttr: { class: 'crud-grid__orders-grid' },
            searchPanel: { visible: true, width: 240 },
            filterRow: { visible: true },
            headerFilter: { visible: true },
            columnChooser: { enabled: true },
            grouping: { contextMenuEnabled: true },
            sorting: { mode: 'multiple' },
            selection: { mode: 'single' },
            focusedRowEnabled: true,
            keyboardNavigation: { enabled: true },
            paging: { pageSize: 10 },
            pager: {
                visible: true,
                showInfo: true,
                showPageSizeSelector: true,
                allowedPageSizes: [5, 10, 20],
            },
            editing: {
                mode: 'popup',
                allowAdding: true,
                allowUpdating: true,
                allowDeleting: true,
                popup: {
                    title: 'Edit order',
                    showTitle: true,
                    width: 720,
                    height: 'auto',
                },
                form: {
                    labelLocation: 'top',
                    colCount: 2,
                },
            },
            columns: [
                { dataField: 'id', caption: 'Order', allowEditing: false, width: 110 },
                { dataField: 'customer', validationRules: [{ type: 'required' }] },
                { dataField: 'status', validationRules: [{ type: 'required' }] },
                {
                    dataField: 'total',
                    dataType: 'number',
                    format: { type: 'currency', precision: 0 },
                    alignment: 'right',
                    validationRules: [{ type: 'required' }, { type: 'range', min: 0 }],
                },
                { dataField: 'dueDate', dataType: 'date', validationRules: [{ type: 'required' }] },
            ],
            summary: {
                totalItems: [{ column: 'total', summaryType: 'sum', valueFormat: 'currency' }],
            },
            onDataErrorOccurred: function(e) {
                showError(e.error && e.error.message ? e.error.message : 'Data error');
            },
        });

        $('#gridLoadPanel').dxLoadPanel({
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Loading orders...',
        });
    } catch (error) {
        showError(error && error.message ? error.message : 'Unexpected initialization error');
    }
});
