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

function hasFrameworkArtifacts(source) {
    return /\bfrom\s+['"](?:react|vue|@angular\/[^'"]+)['"]/i.test(source)
        || /\bReactDOM\b|\bcreateApp\s*\(|\bnew\s+Vue\s*\(|\bngModule\b/i.test(source)
        || /<script[^>]+(?:react|vue|angular)/i.test(source)
        || /\.(jsx|tsx)\b/i.test(source);
}

function findBroadDxOverrides(css) {
    const warnings = [];
    const ruleRegex = /(^|})\s*([^{}]+)\s*\{/g;
    let match;

    while ((match = ruleRegex.exec(css)) !== null) {
        const selector = match[2].trim();
        const selectors = selector.split(',').map((item) => item.trim());

        selectors.forEach((item) => {
            if (/^\.dx-[A-Za-z0-9_-]+(?::|\.|\s|$)/.test(item)) {
                warnings.push(`Broad global DevExtreme selector: ${item}`);
            }
        });
    }

    return warnings;
}

function countHardCodedColors(css) {
    const cssWithoutVariables = css.replace(/:root\s*\{[^}]*\}/gi, '');
    const matches = cssWithoutVariables.match(/#[0-9A-Fa-f]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)|\b(?:red|blue|green|black|white|gray|grey|orange|purple|brown)\b/g);

    return matches ? matches.length : 0;
}

function main() {
    const args = parseArgs(process.argv);

    if (args.help) {
        console.log('Usage: node scripts/audit-dx-output.js --dir <directory>');
        process.exit(0);
    }

    if (args.error || !args.dir) {
        console.error(`ERROR: ${args.error || 'Missing --dir <directory>'}`);
        process.exit(1);
    }

    const dir = path.resolve(args.dir);
    const files = {};
    const warnings = [];
    const serious = [];

    ['index.html', 'styles.css', 'app.js'].forEach((fileName) => {
        const filePath = path.join(dir, fileName);
        if (!fs.existsSync(filePath)) {
            warnings.push(`Missing expected file: ${fileName}`);
            files[fileName] = '';
            return;
        }

        files[fileName] = fs.readFileSync(filePath, 'utf8');
    });

    const source = `${files['index.html']}\n${files['styles.css']}\n${files['app.js']}`;
    const css = files['styles.css'];
    const appJs = files['app.js'];

    findBroadDxOverrides(css).forEach((warning) => warnings.push(warning));

    const hardColorCount = countHardCodedColors(css);
    if (hardColorCount > 8) {
        warnings.push(`Hard-coded color usage is high (${hardColorCount}); prefer CSS variables for design roles.`);
    }

    if (!/dxLoadPanel|loading|load-panel|showIndicator/i.test(source)) {
        warnings.push('Missing visible loading-state handling.');
    }

    if (!/noDataText|empty-state|data-empty-state/i.test(source)) {
        warnings.push('Missing empty-state handling.');
    }

    if (!/try\s*\{|catch\s*\(|onDataErrorOccurred|error-state|notify\([^)]*error/i.test(source)) {
        warnings.push('Missing error-state handling.');
    }

    if (/\.dxForm\s*\(/.test(appJs) && !/validationRules|validationGroup|showValidationSummary|isValid/i.test(appJs)) {
        warnings.push('dxForm is used without validation handling.');
    }

    if (/\.dx[A-Z][A-Za-z0-9_]*\s*\(/.test(appJs) && !/elementAttr|cssClass|inputAttr/i.test(appJs)) {
        warnings.push('Styled widgets should expose wrapper anchors with elementAttr, cssClass, or inputAttr.');
    }

    if (!/@media|grid-template|flex-wrap|minmax\(|clamp\(/i.test(css)) {
        warnings.push('Responsive CSS was not detected.');
    }

    if (hasFrameworkArtifacts(source)) {
        serious.push('Serious artifact detected: framework or JSX/TSX code/reference.');
    }

    if (/themebuilder|theme-builder|dx-themebuilder/i.test(source)) {
        serious.push('Serious artifact detected: ThemeBuilder marker.');
    }

    console.log('DevExtreme output audit');
    console.log('=======================');

    if (warnings.length === 0 && serious.length === 0) {
        console.log('PASS: No audit warnings found.');
    }

    warnings.forEach((warning) => {
        console.log(`WARN: ${warning}`);
    });

    serious.forEach((message) => {
        console.log(`FAIL: ${message}`);
    });

    if (serious.length > 0) {
        console.log('RESULT: serious artifacts found');
    } else if (warnings.length > 0) {
        console.log('RESULT: warnings only');
    } else {
        console.log('RESULT: clean');
    }
    process.exit(serious.length > 0 ? 1 : 0);
}

main();
