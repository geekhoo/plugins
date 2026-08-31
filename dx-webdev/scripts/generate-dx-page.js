#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const {
    validateAgainstSchema,
    validateSemantics,
    formatErrors,
} = require('./lib/dx-spec-validator');

const SCHEMA_PATH = path.resolve(__dirname, '..', 'references', 'dx-page-spec-schema.json');
const DEFAULT_DX_VERSION = '25.2.3';
const DEFAULT_JQUERY_URL = 'https://code.jquery.com/jquery-3.7.1.min.js';
const DEFAULT_OUTPUT_FILES = { html: 'index.html', css: 'styles.css', js: 'app.js' };

function fail(message) {
    console.error(`ERROR: ${message}`);
    process.exit(1);
}

/* ------------------------------------------------------------------ *
 * Emitted-code representation
 *
 * RawJs is the ONLY way a value reaches the generated file as executable
 * JavaScript, and only this module constructs it. Spec-supplied strings are
 * always serialized as string literals, so no spec value can become code.
 * ------------------------------------------------------------------ */
class RawJs {
    constructor(code) {
        this.code = code;
    }
}

function raw(code) {
    return new RawJs(code);
}

function lit(value) {
    return JSON.stringify(value);
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

/* ------------------------------------------------------------------ *
 * Validation gate
 * ------------------------------------------------------------------ */
function validateSpec(spec, specPath) {
    const schema = readJson(SCHEMA_PATH);

    if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
        fail(formatErrors([{ path: '/', message: 'must be a JSON object.' }], specPath));
    }

    let errors = validateAgainstSchema(spec, schema);

    // Cross-reference checks only make sense on a structurally sound spec.
    if (errors.length === 0) {
        errors = validateSemantics(spec);
    }

    if (errors.length > 0) {
        fail(formatErrors(errors, specPath));
    }
}

/* ------------------------------------------------------------------ *
 * Handlers: typed spec values -> generator-emitted call sites
 * ------------------------------------------------------------------ */
function compileHandler(handler) {
    if (handler.kind === 'named-reference') {
        return raw(`runHandler(${lit(handler.name)})`);
    }

    if (handler.kind === 'notify') {
        const type = handler.notifyType || 'info';
        const time = handler.displayTime === undefined ? 2000 : handler.displayTime;
        return raw(`notifyAction(${lit(handler.message)}, ${lit(type)}, ${time})`);
    }

    // Unreachable: the schema constrains kind to the two variants above.
    fail(`Unsupported handler kind: ${handler.kind}`);
}

function isHandlerKey(key) {
    return /^on[A-Z]/.test(key);
}

/**
 * Walk a spec-supplied options tree and replace handler objects with RawJs
 * call sites. Everything else is copied verbatim as data.
 */
function compileOptions(value, key) {
    if (Array.isArray(value)) {
        return value.map((item) => compileOptions(item, null));
    }

    if (value && typeof value === 'object') {
        if (key !== null && isHandlerKey(key)) {
            return compileHandler(value);
        }

        const out = {};
        Object.keys(value).forEach((childKey) => {
            out[childKey] = compileOptions(value[childKey], childKey);
        });
        return out;
    }

    return value;
}

/* ------------------------------------------------------------------ *
 * Normalization
 * ------------------------------------------------------------------ */
function defaultWidgets(templateName) {
    const defaults = {
        'basic-page': [
            { id: 'pageToolbar', type: 'dxToolbar', label: 'Operations' },
            { id: 'primaryAction', type: 'dxButton', label: 'Run Review' },
            { id: 'activityList', type: 'dxList', dataKey: 'items', displayFields: ['text', 'status'] },
            { id: 'pageLoadPanel', type: 'dxLoadPanel' },
        ],
        'crud-grid': [
            { id: 'gridToolbar', type: 'dxToolbar', label: 'Orders' },
            { id: 'ordersGrid', type: 'dxDataGrid', dataKey: 'orders' },
            { id: 'gridLoadPanel', type: 'dxLoadPanel' },
        ],
        dashboard: [
            { id: 'filterToolbar', type: 'dxToolbar', label: 'Filters' },
            { id: 'metricsGrid', type: 'dxDataGrid', dataKey: 'metrics' },
            { id: 'dashboardLoadPanel', type: 'dxLoadPanel' },
        ],
        'form-workflow': [
            { id: 'requestForm', type: 'dxForm', dataKey: 'request' },
            { id: 'submitButton', type: 'dxButton', label: 'Submit', submitsValidationGroup: 'workflowValidation' },
            { id: 'workflowLoadPanel', type: 'dxLoadPanel' },
        ],
    };

    return defaults[templateName];
}

function normalizeWidgets(spec, templateName) {
    const widgets = Array.isArray(spec.widgets) && spec.widgets.length > 0
        ? spec.widgets
        : defaultWidgets(templateName);

    return widgets.map((widget) => ({
        id: widget.id,
        type: widget.type,
        containerId: widget.containerId,
        dataKey: widget.dataKey || defaultDataKey(widget.type),
        options: widget.options || {},
        columns: widget.columns,
        items: widget.items,
        displayFields: widget.displayFields,
        submitsValidationGroup: widget.submitsValidationGroup,
        label: widget.label || '',
        className: widget.className || '',
    }));
}

function defaultDataKey(type) {
    if (type === 'dxDataGrid') return 'rows';
    if (type === 'dxList') return 'items';
    if (type === 'dxForm') return 'formData';
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

/* ------------------------------------------------------------------ *
 * Markup
 * ------------------------------------------------------------------ */
function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function widgetMount(widget) {
    const classes = ['widget-host'];
    if (widget.className) {
        classes.push(widget.className);
    }

    return `                <div id="${widget.id}" class="${classes.join(' ')}"></div>`;
}

function buildSections(spec, templateName, widgets) {
    // No declared containers: one section per widget (the historical layout).
    if (!Array.isArray(spec.containers)) {
        return widgets.map((widget) => [
            `            <section class="widget-panel ${templateName}-panel">`,
            widget.label ? `                <h2>${escapeHtml(widget.label)}</h2>` : '',
            widgetMount(widget),
            '            </section>',
        ].filter(Boolean).join('\n')).join('\n');
    }

    // Declared containers own the sections; widgets are grouped into them.
    return spec.containers.map((container) => {
        const classes = ['widget-panel', `${templateName}-panel`];
        if (container.className) {
            classes.push(container.className);
        }

        const members = widgets.filter((widget) => widget.containerId === container.id);

        return [
            `            <section class="${classes.join(' ')}" data-container="${escapeHtml(container.id)}">`,
            container.label ? `                <h2>${escapeHtml(container.label)}</h2>` : '',
            ...members.map(widgetMount),
            '            </section>',
        ].filter(Boolean).join('\n');
    }).join('\n');
}

function buildBody(spec, title, templateName, widgets) {
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
        buildSections(spec, templateName, widgets),
        '            <p class="state-message" data-empty-state>No records to display when the data source is empty.</p>',
        '            <p class="state-message state-message-error" data-error-state hidden>Unable to load the page data.</p>',
        '        </main>',
        '    </div>',
    ].filter(Boolean).join('\n');
}

function replaceRegion(source, startMarker, endMarker, replacement) {
    const start = source.indexOf(startMarker);
    const end = source.indexOf(endMarker);

    if (start === -1 || end === -1 || end < start) {
        return source;
    }

    return `${source.slice(0, start + startMarker.length)}\n${replacement}\n${source.slice(end)}`;
}

function buildHtml(templateHtml, spec, templateName, widgets, outputFiles) {
    const version = spec.devextremeVersion || DEFAULT_DX_VERSION;
    const themeCss = spec.themeCss || `https://cdn3.devexpress.com/jslib/${version}/css/dx.light.css`;
    const devextremeJs = spec.devextremeJs || `https://cdn3.devexpress.com/jslib/${version}/js/dx.all.js`;
    const jqueryJs = spec.jqueryJs || DEFAULT_JQUERY_URL;
    const title = spec.title;

    let html = templateHtml
        .replace(/<title>.*?<\/title>/i, `<title>${escapeHtml(title)}</title>`)
        .replace(/<link id="dx-theme"[^>]*>/i, `<link id="dx-theme" rel="stylesheet" href="${escapeHtml(themeCss)}">`)
        .replace(/<script id="jquery-script"[^>]*><\/script>/i, `<script id="jquery-script" src="${escapeHtml(jqueryJs)}"></script>`)
        .replace(/<script id="dx-script"[^>]*><\/script>/i, `<script id="dx-script" src="${escapeHtml(devextremeJs)}"></script>`)
        // Honour declared output names so a renamed stylesheet/script still loads.
        .replace(/href="\.\/styles\.css"/i, `href="./${escapeHtml(outputFiles.css)}"`)
        .replace(/src="\.\/app\.js"/i, `src="./${escapeHtml(outputFiles.js)}"`);

    return replaceRegion(
        html,
        '<!-- DX_WIDGET_REGION_START -->',
        '<!-- DX_WIDGET_REGION_END -->',
        buildBody(spec, title, templateName, widgets),
    );
}

/* ------------------------------------------------------------------ *
 * Styles
 * ------------------------------------------------------------------ */
function buildCss(templateCss, spec) {
    const tokens = spec.tokens ? cssVariablesFromObject(spec.tokens) : '';

    if (!tokens) {
        return templateCss;
    }

    return templateCss.replace(':root {', `:root {\n${tokens}`);
}

function cssVariablesFromObject(tokens) {
    const lines = [];

    Object.keys(tokens).forEach((groupName) => {
        const group = tokens[groupName];

        Object.keys(group).forEach((tokenName) => {
            const rawValue = group[tokenName];
            const value = rawValue && typeof rawValue === 'object' ? rawValue.value : rawValue;

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

/* ------------------------------------------------------------------ *
 * Widget options
 * ------------------------------------------------------------------ */
function formNeedsValidation(items) {
    return (items || []).some((item) => item.isRequired === true || Array.isArray(item.validationRules));
}

function defaultFormItems() {
    return [
        { dataField: 'requester', isRequired: true, editorOptions: { inputAttr: { 'aria-label': 'Requester' } } },
        {
            dataField: 'category',
            isRequired: true,
            editorType: 'dxSelectBox',
            editorOptions: { items: ['Access Review', 'Change Request', 'Incident'], inputAttr: { 'aria-label': 'Category' } },
        },
        {
            dataField: 'priority',
            editorType: 'dxSelectBox',
            editorOptions: { items: ['Low', 'Normal', 'High'], inputAttr: { 'aria-label': 'Priority' } },
        },
        {
            dataField: 'notes',
            editorType: 'dxTextArea',
            colSpan: 2,
            validationRules: [{ type: 'required', message: 'Notes are required.' }],
            editorOptions: { minHeight: 96, inputAttr: { 'aria-label': 'Notes' } },
        },
    ];
}

function buildOptions(widget, sampleData, templateName) {
    const type = widget.type;
    const data = widget.dataKey ? sampleData[widget.dataKey] : undefined;
    const base = {
        elementAttr: { class: `${templateName}__${toKebab(widget.id)}` },
    };

    if (type === 'dxDataGrid') {
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
            // Generator-owned handler, emitted as a named function in app.js.
            onDataErrorOccurred: raw('handleDataError'),
        });

        if (widget.columns) {
            base.columns = compileOptions(widget.columns, null);
        }
    } else if (type === 'dxTreeList') {
        Object.assign(base, {
            dataSource: data || [],
            showBorders: true,
            columnAutoWidth: true,
            onDataErrorOccurred: raw('handleDataError'),
        });

        if (widget.columns) {
            base.columns = compileOptions(widget.columns, null);
        }
    } else if (type === 'dxForm') {
        const items = widget.items ? compileOptions(widget.items, null) : defaultFormItems();

        Object.assign(base, {
            formData: data || {},
            labelLocation: 'top',
            colCountByScreen: { xs: 1, sm: 1, md: 2, lg: 2 },
            items,
        });

        // Declarative validation rules are only meaningful if something runs
        // them, so wire the group and summary whenever any rule is present.
        if (formNeedsValidation(widget.items || defaultFormItems())) {
            base.showValidationSummary = true;
            base.validationGroup = 'workflowValidation';
        }
    } else if (type === 'dxList') {
        Object.assign(base, {
            dataSource: data || [],
            noDataText: 'No activity yet.',
        });

        if (widget.displayFields) {
            base.displayExpr = raw(`joinFields(${JSON.stringify(widget.displayFields)})`);
        }
    } else if (type === 'dxToolbar') {
        Object.assign(base, {
            items: widget.items ? compileOptions(widget.items, null) : [
                { location: 'before', text: widget.label || 'Workspace' },
                {
                    location: 'after',
                    widget: 'dxButton',
                    options: {
                        text: 'Refresh',
                        icon: 'refresh',
                        stylingMode: 'outlined',
                        elementAttr: { class: 'toolbar-refresh-button' },
                        onClick: raw("notifyAction('Refresh requested', 'info', 1400)"),
                    },
                },
            ],
        });
    } else if (type === 'dxButton') {
        Object.assign(base, {
            text: widget.label || 'Submit',
            type: 'default',
            stylingMode: 'contained',
            onClick: raw("notifyAction('Action completed', 'success', 1600)"),
        });
    } else if (type === 'dxLoadPanel') {
        Object.assign(base, {
            visible: false,
            shading: true,
            showIndicator: true,
            message: 'Loading...',
        });
    }

    const merged = mergeObjects(base, compileOptions(widget.options, null));

    // Validation-gated submit wraps whatever click handler survived the merge.
    if (widget.submitsValidationGroup) {
        const inner = merged.onClick instanceof RawJs
            ? merged.onClick.code
            : "notifyAction('Workflow submitted', 'success', 1600)";
        merged.onClick = raw(`submitValidationGroup(${lit(widget.submitsValidationGroup)}, ${inner})`);
    }

    return merged;
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
            && !(sourceValue instanceof RawJs)
            && targetValue
            && typeof targetValue === 'object'
            && !Array.isArray(targetValue)
            && !(targetValue instanceof RawJs)
        ) {
            merged[key] = mergeObjects(targetValue, sourceValue);
        } else {
            merged[key] = sourceValue;
        }
    });

    return merged;
}

/* ------------------------------------------------------------------ *
 * JavaScript emission
 * ------------------------------------------------------------------ */
function jsValue(value, indent) {
    if (value instanceof RawJs) {
        return value.code;
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

const RUNTIME_HELPERS = [
    '    function notify(message, notifyType, displayTime) {',
    "        DevExpress.ui.notify(message, notifyType || 'info', displayTime || 2000);",
    '    }',
    '',
    '    function notifyAction(message, notifyType, displayTime) {',
    '        return function() {',
    '            notify(message, notifyType, displayTime);',
    '        };',
    '    }',
    '',
    '    function showError(message) {',
    "        $('[data-error-state]').prop('hidden', false).text(message);",
    "        notify(message, 'error', 2400);",
    '    }',
    '',
    '    function handleDataError(e) {',
    "        showError(e && e.error && e.error.message ? e.error.message : 'Data error');",
    '    }',
    '',
    '    function runHandler(name) {',
    '        return function(e) {',
    '            var registry = window.dxPageHandlers || {};',
    "            if (typeof registry[name] !== 'function') {",
    '                notify(\'Handler "\' + name + \'" is not registered on window.dxPageHandlers.\', \'warning\', 2400);',
    '                return undefined;',
    '            }',
    '            return registry[name](e);',
    '        };',
    '    }',
    '',
    '    function joinFields(fields) {',
    '        return function(item) {',
    "            if (!item) { return ''; }",
    '            return fields',
    '                .map(function(field) { return item[field]; })',
    "                .filter(function(part) { return part !== undefined && part !== null && part !== ''; })",
    "                .join(' - ');",
    '        };',
    '    }',
    '',
    '    function submitValidationGroup(group, next) {',
    '        return function(e) {',
    '            var result = DevExpress.validationEngine.validateGroup(group);',
    '            if (!result.isValid) {',
    "                notify('Resolve validation errors before submitting.', 'warning', 1800);",
    '                return undefined;',
    '            }',
    '            return next(e);',
    '        };',
    '    }',
].join('\n');

function buildAppJs(spec, templateName, widgets) {
    const sampleData = spec.sampleData || sampleDataFor(templateName);

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
        RUNTIME_HELPERS,
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

/* ------------------------------------------------------------------ *
 * Entry point
 * ------------------------------------------------------------------ */
function main() {
    const args = parseArgs(process.argv);

    if (!args.spec || !args.out) {
        fail('Both --spec and --out are required');
    }

    const specPath = path.resolve(args.spec);
    const outDir = path.resolve(args.out);
    const spec = readJson(specPath);

    validateSpec(spec, specPath);

    const templateName = spec.template;
    const widgets = normalizeWidgets(spec, templateName);
    const outputFiles = Object.assign({}, DEFAULT_OUTPUT_FILES, spec.outputFiles || {});

    const templateDir = path.resolve(__dirname, '..', 'templates', templateName);
    const indexTemplatePath = path.join(templateDir, 'index.html');
    const stylesTemplatePath = path.join(templateDir, 'styles.css');

    if (!fs.existsSync(indexTemplatePath) || !fs.existsSync(stylesTemplatePath)) {
        fail(`Template ${templateName} is incomplete`);
    }

    fs.mkdirSync(outDir, { recursive: true });

    const files = [
        [outputFiles.html, buildHtml(fs.readFileSync(indexTemplatePath, 'utf8'), spec, templateName, widgets, outputFiles)],
        [outputFiles.css, buildCss(fs.readFileSync(stylesTemplatePath, 'utf8'), spec)],
        [outputFiles.js, buildAppJs(spec, templateName, widgets)],
    ];

    files.forEach(([fileName, contents]) => {
        const outputPath = path.join(outDir, fileName);
        fs.writeFileSync(outputPath, contents, 'utf8');
        console.log(outputPath);
    });
}

main();
