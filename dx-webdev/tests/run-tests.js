#!/usr/bin/env node
'use strict';

/*
 * dx-webdev generator test suite. Zero dependencies.
 *
 *   node tests/run-tests.js                 run every check
 *   UPDATE_GOLDEN=1 node tests/run-tests.js refresh committed golden output
 *
 * Coverage:
 *   - one golden case per template (basic-page, crud-grid, dashboard, form-workflow)
 *   - a widget gallery derived from the schema's own type lists, so every widget
 *     type the contract admits is generated and golden-compared; adding a type
 *     to the schema without regenerating fails here rather than silently
 *   - node --check over every generated .js
 *   - HTML well-formedness plus scripts/validate-dx-html-js.js on every output
 *   - negative cases: each invalid spec must be rejected before generation,
 *     with a path-qualified message and no files written
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync, spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const GENERATOR = path.join(ROOT, 'scripts', 'generate-dx-page.js');
const HTML_VALIDATOR = path.join(ROOT, 'scripts', 'validate-dx-html-js.js');
const SCHEMA = JSON.parse(fs.readFileSync(path.join(ROOT, 'references', 'dx-page-spec-schema.json'), 'utf8'));
const GOLDEN_DIR = path.join(__dirname, 'golden');
const VALID_DIR = path.join(__dirname, 'fixtures', 'valid');
const INVALID_DIR = path.join(__dirname, 'fixtures', 'invalid');
const UPDATE = process.env.UPDATE_GOLDEN === '1';

const results = { pass: 0, fail: 0, updated: 0 };
const failures = [];

function ok(name) {
    results.pass += 1;
    console.log(`  PASS  ${name}`);
}

function bad(name, detail) {
    results.fail += 1;
    failures.push({ name, detail });
    console.log(`  FAIL  ${name}`);
    detail.split('\n').forEach((line) => console.log(`        ${line}`));
}

function tempDir(label) {
    return fs.mkdtempSync(path.join(os.tmpdir(), `dx-test-${label}-`));
}

/* ---------------------------------------------------------------- *
 * Widget gallery, derived from the schema so coverage cannot drift
 * ---------------------------------------------------------------- */
function allWidgetTypes() {
    const types = [];
    SCHEMA.$defs.widget.oneOf.forEach((variant) => {
        const tag = variant.properties.type;
        if (tag.const) types.push(tag.const);
        if (tag.enum) types.push(...tag.enum);
    });
    return types;
}

function buildGallerySpec() {
    const types = allWidgetTypes();
    const dataBound = { dxDataGrid: 'rows', dxTreeList: 'rows', dxList: 'rows', dxForm: 'record' };

    return {
        schemaVersion: '1.0.0',
        title: 'Widget Gallery',
        template: 'basic-page',
        widgets: types.map((type, i) => {
            const widget = { id: `w${i}_${type}`, type };
            if (dataBound[type]) widget.dataKey = dataBound[type];
            if (type === 'dxList') widget.displayFields = ['name'];
            if (type === 'dxButton') widget.label = 'Gallery action';
            if (type === 'dxToolbar') widget.label = 'Gallery';
            return widget;
        }),
        sampleData: {
            rows: [{ id: 1, name: 'Alpha' }, { id: 2, name: 'Beta' }],
            record: { name: 'Alpha' },
        },
    };
}

/* ---------------------------------------------------------------- *
 * Output checks
 * ---------------------------------------------------------------- */
const VOID_ELEMENTS = new Set([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

function checkHtmlWellFormed(html) {
    const stripped = html.replace(/<!--[\s\S]*?-->/g, '').replace(/<!doctype[^>]*>/i, '');
    const stack = [];
    const tagRegex = /<(\/?)([a-zA-Z][a-zA-Z0-9-]*)((?:"[^"]*"|'[^']*'|[^>"'])*)(\/?)>/g;
    let match;

    while ((match = tagRegex.exec(stripped)) !== null) {
        const [, closing, nameRaw, attrs, selfClose] = match;
        const name = nameRaw.toLowerCase();

        if (closing) {
            const open = stack.pop();
            if (open !== name) {
                return `</${name}> closes <${open || 'nothing'}>`;
            }
        } else if (!selfClose && !VOID_ELEMENTS.has(name)) {
            stack.push(name);
        }

        const quotes = (attrs.match(/"/g) || []).length;
        if (quotes % 2 !== 0) {
            return `unbalanced attribute quoting on <${name}>`;
        }
    }

    return stack.length ? `unclosed element(s): ${stack.join(', ')}` : null;
}

function checkGeneratedDir(caseName, dir, outputFiles) {
    // Every emitted .js must parse.
    fs.readdirSync(dir).filter((f) => f.endsWith('.js')).forEach((file) => {
        const full = path.join(dir, file);
        const check = spawnSync(process.execPath, ['--check', full], { encoding: 'utf8' });
        if (check.status === 0) {
            ok(`${caseName}: node --check ${file}`);
        } else {
            bad(`${caseName}: node --check ${file}`, check.stderr.trim());
        }
    });

    // Every emitted .html must be well formed.
    fs.readdirSync(dir).filter((f) => f.endsWith('.html')).forEach((file) => {
        const problem = checkHtmlWellFormed(fs.readFileSync(path.join(dir, file), 'utf8'));
        if (problem) {
            bad(`${caseName}: html well-formed ${file}`, problem);
        } else {
            ok(`${caseName}: html well-formed ${file}`);
        }
    });

    // Every mount element referenced by app.js must exist in the markup.
    const js = fs.readFileSync(path.join(dir, outputFiles.js), 'utf8');
    const html = fs.readFileSync(path.join(dir, outputFiles.html), 'utf8');
    const mounted = [...js.matchAll(/\$\('#([A-Za-z][\w-]*)'\)\.(dx[A-Za-z0-9]+)\(/g)];
    const missing = mounted.map((m) => m[1]).filter((id) => !html.includes(`id="${id}"`));
    if (mounted.length === 0) {
        bad(`${caseName}: widget initializers present`, 'app.js contains no $("#id").dxWidget( calls');
    } else if (missing.length) {
        bad(`${caseName}: every initialized id exists in markup`, `missing: ${missing.join(', ')}`);
    } else {
        ok(`${caseName}: ${mounted.length} initialized id(s) all present in markup`);
    }

    // No spec-authored function source may reach the output.
    const smuggled = /:\s*function\s*\(|=>\s*\{?\s*fetch|document\.cookie/.test(
        js.slice(js.indexOf('try {')),
    );
    if (smuggled) {
        bad(`${caseName}: no function bodies in widget options`, 'raw function source found in the init block');
    } else {
        ok(`${caseName}: no function bodies in widget options`);
    }

    // The standalone output validator must also accept it.
    if (outputFiles.html === 'index.html' && outputFiles.js === 'app.js' && outputFiles.css === 'styles.css') {
        const res = spawnSync(process.execPath, [HTML_VALIDATOR, '--dir', dir], { encoding: 'utf8' });
        if (res.status === 0) {
            ok(`${caseName}: validate-dx-html-js.js`);
        } else {
            bad(`${caseName}: validate-dx-html-js.js`, res.stdout.trim());
        }
    }
}

function compareGolden(caseName, dir) {
    const goldenCase = path.join(GOLDEN_DIR, caseName);

    if (UPDATE) {
        fs.rmSync(goldenCase, { recursive: true, force: true });
        fs.mkdirSync(goldenCase, { recursive: true });
        fs.readdirSync(dir).forEach((file) => {
            fs.copyFileSync(path.join(dir, file), path.join(goldenCase, file));
        });
        results.updated += 1;
        console.log(`  GOLD  ${caseName}: refreshed`);
        return;
    }

    if (!fs.existsSync(goldenCase)) {
        bad(`${caseName}: golden output exists`, `no golden directory at tests/golden/${caseName}. Run UPDATE_GOLDEN=1 node tests/run-tests.js`);
        return;
    }

    const actual = fs.readdirSync(dir).sort();
    const expected = fs.readdirSync(goldenCase).sort();

    if (actual.join(',') !== expected.join(',')) {
        bad(`${caseName}: golden file set`, `expected [${expected.join(', ')}], got [${actual.join(', ')}]`);
        return;
    }

    let clean = true;
    expected.forEach((file) => {
        const a = fs.readFileSync(path.join(dir, file), 'utf8');
        const b = fs.readFileSync(path.join(goldenCase, file), 'utf8');
        if (a !== b) {
            clean = false;
            bad(`${caseName}: golden match ${file}`, firstDiff(b, a));
        }
    });

    if (clean) ok(`${caseName}: golden match (${expected.length} files)`);
}

function firstDiff(expected, actual) {
    const e = expected.split('\n');
    const a = actual.split('\n');
    for (let i = 0; i < Math.max(e.length, a.length); i += 1) {
        if (e[i] !== a[i]) {
            return `line ${i + 1}\n  expected: ${JSON.stringify(e[i])}\n  actual:   ${JSON.stringify(a[i])}`;
        }
    }
    return 'files differ in trailing content';
}

/* ---------------------------------------------------------------- *
 * Cases
 * ---------------------------------------------------------------- */
function runValidCase(caseName, specPath) {
    const dir = tempDir(caseName);
    const res = spawnSync(process.execPath, [GENERATOR, '--spec', specPath, '--out', dir], { encoding: 'utf8' });

    if (res.status !== 0) {
        bad(`${caseName}: generator exits 0`, `${res.stdout}${res.stderr}`.trim());
        return;
    }
    ok(`${caseName}: generator exits 0`);

    const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
    const outputFiles = Object.assign(
        { html: 'index.html', css: 'styles.css', js: 'app.js' },
        spec.outputFiles || {},
    );

    checkGeneratedDir(caseName, dir, outputFiles);
    compareGolden(caseName, dir);
    fs.rmSync(dir, { recursive: true, force: true });
}

// Each invalid spec must be refused, and the refusal must name the offending path.
const NEGATIVE_EXPECTATIONS = {
    'missing-required-widgets.json': 'is missing required property "widgets"',
    'unknown-top-level-key.json': '/themCss  is not a recognized property',
    'notify-as-widget.json': '/widgets/0/type  is "DevExpress.ui.notify"',
    'function-body-in-option.json': '/widgets/0/options/displayExpr  must not contain JavaScript source',
    'arrow-body-in-option.json': '/widgets/0/options/itemTemplate  must not contain JavaScript source',
    'raw-string-handler.json': '/widgets/0/options/onClick',
    'callback-validation-rule.json': '/widgets/0/items/0/validationRules/0/type',
    'undeclared-container.json': 'references undeclared container "panelZ"',
    'datakey-not-in-sampledata.json': 'is not a key of sampleData',
    'sampledata-shape-mismatch.json': 'must be an object because widget "requestForm" (dxForm) binds it as formData',
    'bad-schema-version.json': 'schemaVersion must be "1.0.0"',
    'duplicate-widget-ids.json': 'duplicates widget id "sameId"',
    'unknown-handler-kind.json': '/widgets/0/options/onClick/kind  is "eval"',
    'legacy-outputfiles-array.json': '/outputFiles  must be object',
};

function runInvalidCase(fixture) {
    const specPath = path.join(INVALID_DIR, fixture);
    const dir = tempDir('reject');
    const res = spawnSync(process.execPath, [GENERATOR, '--spec', specPath, '--out', dir], { encoding: 'utf8' });
    const output = `${res.stdout}${res.stderr}`;

    if (res.status === 0) {
        bad(`reject ${fixture}: non-zero exit`, 'generator accepted a spec that violates the contract');
        fs.rmSync(dir, { recursive: true, force: true });
        return;
    }
    ok(`reject ${fixture}: non-zero exit`);

    const expected = NEGATIVE_EXPECTATIONS[fixture];
    if (expected && !output.includes(expected)) {
        bad(`reject ${fixture}: error names the offending path`, `expected to find: ${expected}\nactual output:\n${output.trim()}`);
    } else {
        ok(`reject ${fixture}: error names the offending path`);
    }

    // Rejection must happen before anything is written.
    const written = fs.readdirSync(dir);
    if (written.length > 0) {
        bad(`reject ${fixture}: no files written`, `generator wrote ${written.join(', ')} despite rejecting the spec`);
    } else {
        ok(`reject ${fixture}: no files written`);
    }

    fs.rmSync(dir, { recursive: true, force: true });
}

/* ---------------------------------------------------------------- *
 * Main
 * ---------------------------------------------------------------- */
console.log('dx-webdev generator test suite');
console.log('==============================');

console.log('\nScript syntax');
[GENERATOR, HTML_VALIDATOR, path.join(ROOT, 'scripts', 'lib', 'dx-spec-validator.js')].forEach((file) => {
    const res = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
    if (res.status === 0) ok(`node --check ${path.relative(ROOT, file)}`);
    else bad(`node --check ${path.relative(ROOT, file)}`, res.stderr.trim());
});

console.log('\nSchema self-checks');
try {
    const types = allWidgetTypes();
    const dupes = types.filter((t, i) => types.indexOf(t) !== i);
    if (dupes.length) bad('widget type discriminator values are unique', `duplicated: ${dupes.join(', ')}`);
    else ok(`widget type discriminator values are unique (${types.length} types)`);
} catch (error) {
    bad('schema widget variants are readable', error.message);
}

console.log('\nGolden: templates');
runValidCase('basic-page', path.join(ROOT, 'references', 'example-page-spec.json'));
['crud-grid', 'dashboard', 'form-workflow', 'defaults-no-containers'].forEach((name) => {
    runValidCase(name, path.join(VALID_DIR, `${name}.json`));
});

console.log('\nGolden: every supported widget type');
const galleryPath = path.join(os.tmpdir(), `dx-gallery-${process.pid}.json`);
fs.writeFileSync(galleryPath, `${JSON.stringify(buildGallerySpec(), null, 2)}\n`, 'utf8');
runValidCase('widget-gallery', galleryPath);
fs.rmSync(galleryPath, { force: true });

console.log('\nNegative: schema-invalid specs must be refused');
fs.readdirSync(INVALID_DIR).filter((f) => f.endsWith('.json')).sort().forEach(runInvalidCase);

console.log('\n==============================');
console.log(`pass ${results.pass}   fail ${results.fail}${UPDATE ? `   golden refreshed ${results.updated}` : ''}`);

if (failures.length) {
    console.log('\nFailures:');
    failures.forEach((f) => console.log(`  - ${f.name}`));
}

process.exit(results.fail > 0 ? 1 : 0);
