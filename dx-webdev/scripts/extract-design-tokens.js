#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const SUPPORTED_GROUPS = {
    color: 'color',
    colors: 'color',
    spacing: 'spacing',
    radius: 'radius',
    radii: 'radius',
    borderRadius: 'radius',
    typography: 'typography',
    type: 'typography',
    elevation: 'elevation',
    shadow: 'elevation',
    shadows: 'elevation',
};

function fail(message) {
    console.error(`ERROR: ${message}`);
    process.exit(1);
}

function parseArgs(argv) {
    const args = {};

    for (let i = 2; i < argv.length; i += 1) {
        const arg = argv[i];

        if (arg === '--tokens' || arg === '--out') {
            const value = argv[i + 1];
            if (!value || value.startsWith('--')) {
                fail(`Missing value for ${arg}`);
            }

            args[arg.slice(2)] = value;
            i += 1;
        } else if (arg === '--help' || arg === '-h') {
            console.log('Usage: node scripts/extract-design-tokens.js --tokens <path> --out <path>');
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

function toKebab(value) {
    return String(value)
        .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
        .replace(/[^A-Za-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .toLowerCase();
}

function tokenValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        if (Object.prototype.hasOwnProperty.call(value, 'value')) {
            return value.value;
        }

        if (Object.prototype.hasOwnProperty.call(value, '$value')) {
            return value.$value;
        }
    }

    return value;
}

function walkTokens(group, prefix, output) {
    Object.keys(group).forEach((key) => {
        const value = group[key];
        const resolved = tokenValue(value);

        if (typeof resolved === 'string' || typeof resolved === 'number') {
            output.push({ name: `${prefix}-${toKebab(key)}`, value: resolved });
            return;
        }

        if (resolved && typeof resolved === 'object' && !Array.isArray(resolved)) {
            walkTokens(resolved, `${prefix}-${toKebab(key)}`, output);
        }
    });
}

function extractVariables(tokens) {
    const variables = [];

    Object.keys(tokens).forEach((groupName) => {
        const cssGroup = SUPPORTED_GROUPS[groupName];
        const group = tokens[groupName];

        if (!cssGroup || !group || typeof group !== 'object' || Array.isArray(group)) {
            return;
        }

        walkTokens(group, `dx-${cssGroup}`, variables);
    });

    return variables;
}

function main() {
    const args = parseArgs(process.argv);

    if (!args.tokens || !args.out) {
        fail('Both --tokens and --out are required');
    }

    const tokenPath = path.resolve(args.tokens);
    const outPath = path.resolve(args.out);
    const tokens = readJson(tokenPath);

    if (!tokens || typeof tokens !== 'object' || Array.isArray(tokens)) {
        fail('Token input must be a JSON object');
    }

    const variables = extractVariables(tokens);

    if (variables.length === 0) {
        fail('No supported color, spacing, radius, typography, or elevation tokens found');
    }

    const css = [
        ':root {',
        ...variables.map((token) => `    --${token.name}: ${token.value};`),
        '}',
        '',
    ].join('\n');

    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, css, 'utf8');
    console.log(outPath);
}

main();
