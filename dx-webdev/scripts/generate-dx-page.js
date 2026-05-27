#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const TEMPLATES = new Set(['basic-page', 'crud-grid', 'dashboard', 'form-workflow']);
const DEFAULT_DX_VERSION = '25.2.3';
const DEFAULT_JQUERY_URL = 'https://code.jquery.com/jquery-3.7.1.min.js';

function fail(message) {
    console.error(`ERROR: ${message}`);
    process.exit(1);
}

function parseArgs(argv) {
    const args = {};

    for (let i = 2; i < argv.length; i += 1) {
        const arg = argv[i];

        if (arg === '--spec' || arg === '--out') {
            const value = argv[i + 1];
            if (!value || value.startsWith('--')) {
                fail(`Missing value for ${arg}`);
            }

            args[arg.slice(2)] = value;
            i += 1;
        } else if (arg === '--help' || arg === '-h') {
            console.log('Usage: node scripts/generate-dx-page.js --spec <path> --out <directory>');
            process.exit(0);
        } else {
            fail(`Unknown argument: ${arg}`);
        }
    }

    return args;
}

function readJson(filePath) {
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (error) {
        fail(`Unable to read valid JSON from ${filePath}: ${error.message}`);
    }
}

function assertObject(value, name) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        fail(`${name} must be a JSON object`);
    }
}

function normalizeTemplate(spec) {
    if (spec.template && !TEMPLATES.has(spec.template)) {
        fail(`template must be one of: ${Array.from(TEMPLATES).join(', ')}`);
    }

    if (spec.template) {
        return spec.template;
    }

    const widgetTypes = Array.isArray(spec.widgets)
        ? spec.widgets.map((widget) => String(widget.type || '').toLowerCase())
        : [];

    if (widgetTypes.includes('dxdatagrid')) {
        return 'crud-grid';
    }

    if (widgetTypes.includes('dxform')) {
        return 'form-workflow';
    }

    return 'basic-page';
}

function sanitizeId(value, fallback) {
    const id = String(value || fallback || '').trim();

    if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(id)) {
        fail(`Invalid container id: ${id || '<empty>'}. Use letters, numbers, underscores, or dashes.`);
    }

    return id;
}

function normalizeWidgetType(value) {
    const raw = String(value || '').trim();

    if (!raw) {
        fail('Each widget must include a type');
    }

    if (raw.startsWith('dx')) {
        return raw;
    }

    return `dx${raw.charAt(0).toUpperCase()}${raw.slice(1)}`;
}

function normalizeWidgets(spec, templateName) {
    const defaults = {
        'basic-page': [
            { id: 'pageToolbar', type: 'dxToolbar' },
            { id: 'primaryAction', type: 'dxButton' },
            { id: 'activityList', type: 'dxList', dataKey: 'items' },
            { id: 'pageLoadPanel', type: 'dxLoadPanel' },
        ],
        'crud-grid': [
            { id: 'gridToolbar', type: 'dxToolbar' },
            { id: 'ordersGrid', type: 'dxDataGrid', dataKey: 'orders' },
            { id: 'gridLoadPanel', type: 'dxLoadPanel' },
        ],
        dashboard: [
            { id: 'filterToolbar', type: 'dxToolbar' },
            { id: 'metricsGrid', type: 'dxDataGrid', dataKey: 'metrics' },
            { id: 'dashboardLoadPanel', type: 'dxLoadPanel' },
        ],
        'form-workflow': [
            { id: 'requestForm', type: 'dxForm', dataKey: 'request' },
            { id: 'submitButton', type: 'dxButton' },
            { id: 'workflowLoadPanel', type: 'dxLoadPanel' },
        ],
    };

    const widgets = Array.isArray(spec.widgets) && spec.widgets.length > 0
        ? spec.widgets
        : defaults[templateName];

    return widgets.map((widget, index) => {
        assertObject(widget, `widgets[${index}]`);

        return {
            id: sanitizeId(widget.id || widget.containerId, `widget${index + 1}`),
            type: normalizeWidgetType(widget.type),
            dataKey: widget.dataKey || widget.data || defaultDataKey(widget.type),
            options: widget.options && typeof widget.options === 'object' && !Array.isArray(widget.options)
                ? widget.options
                : {},
            label: widget.label || widget.title || '',
            className: widget.className || '',
        };
    });
}

function defaultDataKey(type) {
    const normalized = normalizeWidgetType(type).toLowerCase();

    if (normalized === 'dxdatagrid') {
        return 'rows';
    }

    if (normalized === 'dxlist') {
        return 'items';
    }

    if (normalized === 'dxform') {
        return 'formData';
    }

    return '';
}

function sampleDataFor(templateName) {
    const samples = {
        'basic-page': {
            items: [
                { text: 'Review queue prepared', status: 'Ready' },
                { text: 'Data refresh completed', status: 'Complete' },
                { text: 'Validation pass required', status: 'Pending' },
            ],
        },
        'crud-grid': {
            orders: [
                { id: 1001, customer: 'Acme Health', status: 'New', total: 12840, dueDate: '2026-06-02' },
                { id: 1002, customer: 'Northwind Care', status: 'Review', total: 9250, dueDate: '2026-06-05' },
                { id: 1003, customer: 'Contoso Clinics', status: 'Approved', total: 15300, dueDate: '2026-06-11' },
            ],
        },
        dashboard: {
            metrics: [
                { region: 'North', pipeline: 42, revenue: 182000, risk: 'Low' },
                { region: 'Central', pipeline: 31, revenue: 145000, risk: 'Medium' },
                { region: 'West', pipeline: 27, revenue: 121500, risk: 'High' },
            ],
        },
        'form-workflow': {
            request: {
                requester: 'Case Owner',
                category: 'Access Review',
                priority: 'Normal',
                notes: '',
            },
        },
    };

    return samples[templateName];
}

function buildBody(title, templateName, widgets) {
    const widgetMarkup = widgets.map((widget) => {
        const classes = ['widget-host'];
        if (widget.className) {
            classes.push(widget.className);
        }

        return [
            `            <section class="widget-panel ${templateName}-panel">`,
            widget.label ? `                <h2>${escapeHtml(widget.label)}</h2>` : '',
            `                <div id="${widget.id}" class="${classes.join(' ')}"></div>`,
            '            </section>',
        ].filter(Boolean).join('\n');
    }).join('\n');

    const dashboardSummary = templateName === 'dashboard'
        ? [
            '            <section class="summary-grid" aria-label="Dashboard summary">',
            '                <article><span>Open Pipeline</span><strong>$448K</strong></article>',
            '                <article><span>At Risk</span><strong>7</strong></article>',
            '                <article><span>Cycle Time</span><strong>4.2d</strong></article>',
            '            </section>',
        ].join('\n')
        : '';

    return [
        '    <div class="app-shell">',
        '        <header class="app-header">',
        `            <h1 data-page-title>${escapeHtml(title)}</h1>`,
        '            <p class="app-subtitle">Generated DevExtreme jQuery interface</p>',
        '        </header>',
        '        <main class="app-content">',
        dashboardSummary,
        widgetMarkup,
        '            <p class="state-message" data-empty-state>No records to display when the data source is empty.</p>',
        '            <p class="state-message state-message-error" data-error-state hidden>Unable to load the page data.</p>',
        '        </main>',
        '    </div>',
    ].filter(Boolean).join('\n');
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function replaceRegion(source, startMarker, endMarker, replacement) {
    const start = source.indexOf(startMarker);
    const end = source.indexOf(endMarker);

    if (start === -1 || end === -1 || end < start) {
        return source;
    }

    return `${source.slice(0, start + startMarker.length)}\n${replacement}\n${source.slice(end)}`;
}

function buildHtml(templateHtml, spec, templateName, widgets) {
    const version = spec.devextremeVersion || DEFAULT_DX_VERSION;
    const themeCss = spec.themeCss || `https://cdn3.devexpress.com/jslib/${version}/css/dx.light.css`;
    const devextremeJs = spec.devextremeJs || `https://cdn3.devexpress.com/jslib/${version}/js/dx.all.js`;
    const jqueryJs = spec.jqueryJs || DEFAULT_JQUERY_URL;
    const title = spec.title || 'DevExtreme jQuery App';

    let html = templateHtml
        .replace(/<title>.*?<\/title>/i, `<title>${escapeHtml(title)}</title>`)
        .replace(/<link id="dx-theme"[^>]*>/i, `<link id="dx-theme" rel="stylesheet" href="${escapeHtml(themeCss)}">`)
        .replace(/<script id="jquery-script"[^>]*><\/script>/i, `<script id="jquery-script" src="${escapeHtml(jqueryJs)}"></script>`)
        .replace(/<script id="dx-script"[^>]*><\/script>/i, `<script id="dx-script" src="${escapeHtml(devextremeJs)}"></script>`);

    html = replaceRegion(
        html,
        '<!-- DX_WIDGET_REGION_START -->',
        '<!-- DX_WIDGET_REGION_END -->',
        buildBody(title, templateName, widgets),
    );

    return html;
}

function buildCss(templateCss, spec) {
    const tokens = spec.tokens && typeof spec.tokens === 'object' && !Array.isArray(spec.tokens)
        ? cssVariablesFromObject(spec.tokens)
        : '';

    if (!tokens) {
        return templateCss;
    }

    return templateCss.replace(':root {', `:root {\n${tokens}`);
}

function cssVariablesFromObject(tokens) {
    const lines = [];

    Object.keys(tokens).forEach((groupName) => {
        const group = tokens[groupName];

        if (!group || typeof group !== 'object' || Array.isArray(group)) {
            return;
        }

        Object.keys(group).forEach((tokenName) => {
            const raw = group[tokenName];
            const value = raw && typeof raw === 'object' && Object.prototype.hasOwnProperty.call(raw, 'value')
                ? raw.value
                : raw;

            if (typeof value === 'string' || typeof value === 'number') {
                lines.push(`    --${toKebab(groupName)}-${toKebab(tokenName)}: ${value};`);
            }
        });
    });

    return lines.join('\n');
}

function toKebab(value) {
    return String(value)
        .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
        .replace(/[^A-Za-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .toLowerCase();
}

function buildOptions(widget, sampleData, templateName) {
    const type = widget.type.toLowerCase();
    const data = widget.dataKey ? sampleData[widget.dataKey] : undefined;
    const base = {
        elementAttr: { class: `${templateName}__${toKebab(widget.id)}` },
    };

    if (type === 'dxdatagrid') {
        Object.assign(base, {
            dataSource: data || [],
            keyExpr: inferKeyExpr(data),
            showBorders: true,
            columnAutoWidth: true,
            noDataText: 'No records match the current filters.',
            searchPanel: { visible: true, width: 240 },
            filterRow: { visible: true },
            headerFilter: { visible: true },
            paging: { pageSize: 10 },
            pager: { visible: true, showPageSizeSelector: true, allowedPageSizes: [5, 10, 20] },
            editing: {
                mode: 'popup',
                allowAdding: true,
                allowUpdating: true,
                allowDeleting: true,
                popup: { title: 'Edit record', showTitle: true, width: 720 },
                form: { labelLocation: 'top' },
            },
            onDataErrorOccurred: "function(e) { showError(e.error && e.error.message ? e.error.message : 'Data error'); }",
        });
    } else if (type === 'dxform') {
        Object.assign(base, {
            formData: data || {},
            labelLocation: 'top',
            colCountByScreen: { xs: 1, sm: 1, md: 2, lg: 2 },
            showValidationSummary: true,
            validationGroup: 'workflowValidation',
            items: [
                { dataField: 'requester', isRequired: true, editorOptions: { inputAttr: { 'aria-label': 'Requester' } } },
                { dataField: 'category', isRequired: true, editorType: 'dxSelectBox', editorOptions: { items: ['Access Review', 'Change Request', 'Incident'], inputAttr: { 'aria-label': 'Category' } } },
                { dataField: 'priority', editorType: 'dxSelectBox', editorOptions: { items: ['Low', 'Normal', 'High'], inputAttr: { 'aria-label': 'Priority' } } },
                { dataField: 'notes', editorType: 'dxTextArea', colSpan: 2, validationRules: [{ type: 'required', message: 'Notes are required.' }], editorOptions: { minHeight: 96, inputAttr: { 'aria-label': 'Notes' } } },
            ],
        });
    } else if (type === 'dxlist') {
        Object.assign(base, {
            dataSource: data || [],
            noDataText: 'No activity yet.',
            displayExpr: functionDisplayExpr(),
        });
    } else if (type === 'dxtoolbar') {
        Object.assign(base, {
            items: [
                { location: 'before', text: widget.label || 'Workspace' },
                { location: 'after', widget: 'dxButton', options: { text: 'Refresh', icon: 'refresh', stylingMode: 'outlined', elementAttr: { class: 'toolbar-refresh-button' }, onClick: "function() { DevExpress.ui.notify('Refresh requested', 'info', 1400); }" } },
            ],
        });
    } else if (type === 'dxbutton') {
        Object.assign(base, {
            text: widget.label || 'Submit',
            type: 'default',
            stylingMode: 'contained',
            onClick: "function() { DevExpress.ui.notify('Action completed', 'success', 1600); }",
        });
    } else if (type === 'dxloadpanel') {
        Object.assign(base, {
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Loading...',
        });
    }

    return mergeObjects(base, widget.options);
}

function functionDisplayExpr() {
    return "function(item) { return item && item.text ? item.text + ' - ' + item.status : String(item || ''); }";
}

function inferKeyExpr(data) {
    if (Array.isArray(data) && data.length > 0 && data[0] && Object.prototype.hasOwnProperty.call(data[0], 'id')) {
        return 'id';
    }

    return undefined;
}

function mergeObjects(target, source) {
    const merged = Object.assign({}, target);

    Object.keys(source || {}).forEach((key) => {
        const sourceValue = source[key];
        const targetValue = merged[key];

        if (
            sourceValue
            && typeof sourceValue === 'object'
            && !Array.isArray(sourceValue)
            && targetValue
            && typeof targetValue === 'object'
            && !Array.isArray(targetValue)
        ) {
            merged[key] = mergeObjects(targetValue, sourceValue);
        } else {
            merged[key] = sourceValue;
        }
    });

    return merged;
}

function jsValue(value, indent) {
    if (typeof value === 'string' && value.startsWith('function(')) {
        return value;
    }

    if (Array.isArray(value)) {
        if (value.length === 0) {
            return '[]';
        }

        return `[\n${value.map((item) => `${' '.repeat(indent + 4)}${jsValue(item, indent + 4)}`).join(',\n')}\n${' '.repeat(indent)}]`;
    }

    if (value && typeof value === 'object') {
        const entries = Object.keys(value)
            .filter((key) => value[key] !== undefined)
            .map((key) => `${' '.repeat(indent + 4)}${JSON.stringify(key)}: ${jsValue(value[key], indent + 4)}`);

        if (entries.length === 0) {
            return '{}';
        }

        return `{\n${entries.join(',\n')}\n${' '.repeat(indent)}}`;
    }

    return JSON.stringify(value);
}

function buildAppJs(spec, templateName, widgets) {
    const sampleData = spec.sampleData && typeof spec.sampleData === 'object' && !Array.isArray(spec.sampleData)
        ? spec.sampleData
        : sampleDataFor(templateName);

    const initBlocks = widgets.map((widget) => {
        const options = buildOptions(widget, sampleData, templateName);

        return `        $('#${widget.id}').${widget.type}(${jsValue(options, 8)});`;
    }).join('\n\n');

    return [
        "'use strict';",
        '',
        '$(function() {',
        `    const sampleData = ${JSON.stringify(sampleData, null, 4).replace(/\n/g, '\n    ')};`,
        '',
        '    function showError(message) {',
        "        $('[data-error-state]').prop('hidden', false).text(message);",
        "        DevExpress.ui.notify(message, 'error', 2400);",
        '    }',
        '',
        '    try {',
        initBlocks,
        '    } catch (error) {',
        "        showError(error && error.message ? error.message : 'Unexpected initialization error');",
        '    }',
        '});',
        '',
    ].join('\n');
}

function main() {
    const args = parseArgs(process.argv);

    if (!args.spec || !args.out) {
        fail('Both --spec and --out are required');
    }

    const specPath = path.resolve(args.spec);
    const outDir = path.resolve(args.out);
    const spec = readJson(specPath);
    assertObject(spec, 'spec');

    const templateName = normalizeTemplate(spec);
    const widgets = normalizeWidgets(spec, templateName);
    const templateDir = path.resolve(__dirname, '..', 'templates', templateName);
    const indexTemplatePath = path.join(templateDir, 'index.html');
    const stylesTemplatePath = path.join(templateDir, 'styles.css');

    if (!fs.existsSync(indexTemplatePath) || !fs.existsSync(stylesTemplatePath)) {
        fail(`Template ${templateName} is incomplete`);
    }

    fs.mkdirSync(outDir, { recursive: true });

    const files = {
        'index.html': buildHtml(fs.readFileSync(indexTemplatePath, 'utf8'), spec, templateName, widgets),
        'styles.css': buildCss(fs.readFileSync(stylesTemplatePath, 'utf8'), spec),
        'app.js': buildAppJs(spec, templateName, widgets),
    };

    Object.keys(files).forEach((fileName) => {
        const outputPath = path.join(outDir, fileName);
        fs.writeFileSync(outputPath, files[fileName], 'utf8');
        console.log(outputPath);
    });
}

main();
