#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
    const args = {};

    for (let i = 2; i < argv.length; i += 1) {
        const arg = argv[i];

        if (arg === '--dir') {
            const value = argv[i + 1];
            if (!value || value.startsWith('--')) {
                return { error: 'Missing value for --dir' };
            }

            args.dir = value;
            i += 1;
        } else if (arg === '--help' || arg === '-h') {
            args.help = true;
        } else {
            return { error: `Unknown argument: ${arg}` };
        }
    }

    return args;
}

function collectScriptSources(html) {
    const scripts = [];
    const scriptRegex = /<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*><\/script>/gi;
    let match;

    while ((match = scriptRegex.exec(html)) !== null) {
        scripts.push({ src: match[1], index: match.index });
    }

    return scripts;
}

function collectIds(html) {
    const ids = new Set();
    const idRegex = /\bid=["']([^"']+)["']/gi;
    let match;

    while ((match = idRegex.exec(html)) !== null) {
        ids.add(match[1]);
    }

    return ids;
}

function collectInitializedIds(appJs) {
    const ids = [];
    const initRegex = /\$\(\s*['"]#([A-Za-z][A-Za-z0-9_-]*)['"]\s*\)\s*\.dx[A-Z][A-Za-z0-9_]*\s*\(\s*(?!['"])/g;
    let match;

    while ((match = initRegex.exec(appJs)) !== null) {
        ids.push(match[1]);
    }

    return ids;
}

function hasFrameworkArtifacts(source) {
    const patterns = [
        /\bfrom\s+['"]react['"]/i,
        /\bfrom\s+['"]vue['"]/i,
        /\bfrom\s+['"]@angular\//i,
        /\bimport\s+React\b/i,
        /\bReactDOM\b/i,
        /\bcreateApp\s*\(/i,
        /\bnew\s+Vue\s*\(/i,
        /\bngModule\b/i,
        /<script[^>]+react/i,
        /<script[^>]+vue/i,
        /<script[^>]+angular/i,
    ];

    return patterns.some((pattern) => pattern.test(source));
}

function hasJsxTsxMarkers(source) {
    return /\.(jsx|tsx)\b/i.test(source)
        || /\btsx\b/i.test(source)
        || /\bjsx\b/i.test(source)
        || /<[A-Z][A-Za-z0-9]*(\s+[A-Za-z_:][^>]*)?>/.test(source);
}

function main() {
    const args = parseArgs(process.argv);

    if (args.help) {
        console.log('Usage: node scripts/validate-dx-html-js.js --dir <directory>');
        process.exit(0);
    }

    if (args.error || !args.dir) {
        console.error(`ERROR: ${args.error || 'Missing --dir <directory>'}`);
        process.exit(1);
    }

    const dir = path.resolve(args.dir);
    const requiredFiles = ['index.html', 'styles.css', 'app.js'];
    const errors = [];
    const passes = [];

    requiredFiles.forEach((fileName) => {
        const filePath = path.join(dir, fileName);
        if (!fs.existsSync(filePath)) {
            errors.push(`Missing required file: ${fileName}`);
        } else {
            passes.push(`Found ${fileName}`);
        }
    });

    if (errors.length > 0) {
        printReport(passes, errors);
        process.exit(1);
    }

    const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
    const css = fs.readFileSync(path.join(dir, 'styles.css'), 'utf8');
    const appJs = fs.readFileSync(path.join(dir, 'app.js'), 'utf8');
    const allSource = `${html}\n${css}\n${appJs}`;
    const scripts = collectScriptSources(html);
    const jqueryScript = scripts.find((script) => /jquery/i.test(script.src));
    const dxScript = scripts.find((script) => /devextreme|dx\.all|dx\.web/i.test(script.src));

    if (!/devextreme|dx\.[A-Za-z0-9_-]+\.css/i.test(html)) {
        errors.push('DevExtreme CSS reference was not found in index.html');
    } else {
        passes.push('DevExtreme CSS reference found');
    }

    if (!dxScript) {
        errors.push('DevExtreme JavaScript reference was not found in index.html');
    } else {
        passes.push('DevExtreme JavaScript reference found');
    }

    if (!jqueryScript) {
        errors.push('jQuery script reference was not found in index.html');
    } else {
        passes.push('jQuery script reference found');
    }

    if (jqueryScript && dxScript) {
        if (jqueryScript.index < dxScript.index) {
            passes.push('jQuery is loaded before DevExtreme JavaScript');
        } else {
            errors.push('jQuery must be loaded before DevExtreme JavaScript');
        }
    }

    const initializedIds = collectInitializedIds(appJs);
    if (initializedIds.length === 0) {
        errors.push('app.js does not contain DevExtreme jQuery initialization patterns');
    } else {
        passes.push(`Found DevExtreme jQuery init patterns: ${initializedIds.join(', ')}`);
    }

    const htmlIds = collectIds(html);
    initializedIds.forEach((id) => {
        if (!htmlIds.has(id)) {
            errors.push(`Initialized container #${id} does not exist in index.html`);
        }
    });

    if (initializedIds.length > 0 && initializedIds.every((id) => htmlIds.has(id))) {
        passes.push('All initialized container IDs exist in index.html');
    }

    if (hasFrameworkArtifacts(allSource)) {
        errors.push('Framework artifact detected: React, Vue, or Angular code/reference');
    } else {
        passes.push('No React/Vue/Angular artifacts detected');
    }

    if (hasJsxTsxMarkers(allSource)) {
        errors.push('JSX/TSX marker detected');
    } else {
        passes.push('No JSX/TSX markers detected');
    }

    if (/themebuilder|theme-builder|dx-themebuilder/i.test(allSource)) {
        errors.push('ThemeBuilder marker detected');
    } else {
        passes.push('No ThemeBuilder markers detected');
    }

    printReport(passes, errors);
    process.exit(errors.length > 0 ? 1 : 0);
}

function printReport(passes, errors) {
    console.log('DevExtreme HTML/JS validation report');
    console.log('=====================================');

    passes.forEach((message) => {
        console.log(`PASS: ${message}`);
    });

    errors.forEach((message) => {
        console.log(`FAIL: ${message}`);
    });

    console.log(errors.length === 0 ? 'RESULT: valid' : 'RESULT: invalid');
}

main();
