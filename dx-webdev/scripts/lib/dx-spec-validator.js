'use strict';

/*
 * Zero-dependency JSON Schema validator, scoped to the keyword subset used by
 * references/dx-page-spec-schema.json.
 *
 * Why not ajv: dx-webdev ships no package.json and its README states that
 * "Scripts use Node.js and no external npm dependencies". Adding a dependency
 * would break that contract for every consumer of the plugin. The schema is
 * authored against this validator's documented subset, so the two are kept in
 * step by the test suite rather than by a general-purpose engine.
 *
 * Supported keywords:
 *   $ref (internal JSON pointers only), $defs, type, const, enum, required,
 *   properties, patternProperties, additionalProperties, items, minItems,
 *   maxItems, uniqueItems, minLength, minimum, maximum, pattern, allOf, oneOf
 *
 * Extension keywords:
 *   errorMessage    - replaces the generated message for a failing keyword
 *   x-discriminator - { propertyName } beside oneOf; selects the single
 *                     variant to report against, the way ajv's discriminator
 *                     option does, so errors name one shape instead of "did
 *                     not match any of 8 subschemas".
 */

const TYPE_CHECKS = {
    string: (v) => typeof v === 'string',
    number: (v) => typeof v === 'number' && Number.isFinite(v),
    integer: (v) => typeof v === 'number' && Number.isInteger(v),
    boolean: (v) => typeof v === 'boolean',
    null: (v) => v === null,
    array: (v) => Array.isArray(v),
    object: (v) => v !== null && typeof v === 'object' && !Array.isArray(v),
};

function typeOf(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    if (Number.isInteger(value)) return 'integer';
    return typeof value;
}

function describe(value) {
    const kind = typeOf(value);
    if (kind === 'object') return 'an object';
    if (kind === 'array') return `an array (${value.length} items)`;
    if (kind === 'string') return JSON.stringify(value.length > 60 ? `${value.slice(0, 57)}...` : value);
    return JSON.stringify(value);
}

class Validator {
    constructor(rootSchema) {
        this.root = rootSchema;
    }

    resolveRef(ref) {
        if (typeof ref !== 'string' || !ref.startsWith('#/')) {
            throw new Error(`Unsupported $ref (internal pointers only): ${ref}`);
        }

        return ref
            .slice(2)
            .split('/')
            .map((token) => token.replace(/~1/g, '/').replace(/~0/g, '~'))
            .reduce((node, token) => {
                if (!node || !Object.prototype.hasOwnProperty.call(node, token)) {
                    throw new Error(`Unresolvable $ref: ${ref}`);
                }
                return node[token];
            }, this.root);
    }

    validate(data) {
        const errors = [];
        this.check(data, this.root, '', errors);
        return errors;
    }

    push(errors, path, message, schema) {
        errors.push({
            path: path || '/',
            message: (schema && schema.errorMessage) || message,
        });
    }

    check(data, schema, path, errors) {
        if (schema === true || schema === undefined) return;
        if (schema === false) {
            this.push(errors, path, 'is not allowed here.', null);
            return;
        }

        // $ref may carry siblings in 2020-12; apply both.
        if (schema.$ref) {
            this.check(data, this.resolveRef(schema.$ref), path, errors);
        }

        if (schema.type !== undefined) {
            const allowed = Array.isArray(schema.type) ? schema.type : [schema.type];
            if (!allowed.some((t) => TYPE_CHECKS[t] && TYPE_CHECKS[t](data))) {
                this.push(errors, path, `must be ${allowed.join(' or ')}, but got ${describe(data)}.`, schema);
                return; // further keywords would only produce noise
            }
        }

        if (Object.prototype.hasOwnProperty.call(schema, 'const') && !deepEqual(data, schema.const)) {
            this.push(errors, path, `must be ${JSON.stringify(schema.const)}.`, schema);
        }

        if (schema.enum && !schema.enum.some((candidate) => deepEqual(data, candidate))) {
            this.push(
                errors,
                path,
                `must be one of: ${schema.enum.map((v) => JSON.stringify(v)).join(', ')}. Got ${describe(data)}.`,
                schema,
            );
        }

        if (typeof data === 'string') this.checkString(data, schema, path, errors);
        if (typeof data === 'number') this.checkNumber(data, schema, path, errors);
        if (Array.isArray(data)) this.checkArray(data, schema, path, errors);
        if (TYPE_CHECKS.object(data)) this.checkObject(data, schema, path, errors);

        if (Array.isArray(schema.allOf)) {
            schema.allOf.forEach((sub) => this.check(data, sub, path, errors));
        }

        if (Array.isArray(schema.oneOf)) {
            this.checkOneOf(data, schema, path, errors);
        }
    }

    checkString(data, schema, path, errors) {
        if (schema.minLength !== undefined && data.length < schema.minLength) {
            this.push(errors, path, `must be at least ${schema.minLength} character(s) long.`, schema);
        }
        if (schema.pattern !== undefined && !new RegExp(schema.pattern).test(data)) {
            this.push(errors, path, `does not match the required pattern ${schema.pattern}.`, schema);
        }
    }

    checkNumber(data, schema, path, errors) {
        if (schema.minimum !== undefined && data < schema.minimum) {
            this.push(errors, path, `must be >= ${schema.minimum}.`, schema);
        }
        if (schema.maximum !== undefined && data > schema.maximum) {
            this.push(errors, path, `must be <= ${schema.maximum}.`, schema);
        }
    }

    checkArray(data, schema, path, errors) {
        if (schema.minItems !== undefined && data.length < schema.minItems) {
            this.push(errors, path, `must contain at least ${schema.minItems} item(s), got ${data.length}.`, schema);
        }
        if (schema.maxItems !== undefined && data.length > schema.maxItems) {
            this.push(errors, path, `must contain at most ${schema.maxItems} item(s), got ${data.length}.`, schema);
        }
        if (schema.uniqueItems) {
            const seen = new Set();
            data.forEach((item, i) => {
                const key = JSON.stringify(item);
                if (seen.has(key)) {
                    this.push(errors, `${path}/${i}`, 'is a duplicate; items must be unique.', schema);
                }
                seen.add(key);
            });
        }
        if (schema.items !== undefined) {
            data.forEach((item, i) => this.check(item, schema.items, `${path}/${i}`, errors));
        }
    }

    checkObject(data, schema, path, errors) {
        const keys = Object.keys(data);

        (schema.required || []).forEach((key) => {
            if (!Object.prototype.hasOwnProperty.call(data, key)) {
                this.push(errors, path, `is missing required property "${key}".`, null);
            }
        });

        keys.forEach((key) => {
            const childPath = `${path}/${key.replace(/~/g, '~0').replace(/\//g, '~1')}`;
            let matched = false;

            if (schema.properties && Object.prototype.hasOwnProperty.call(schema.properties, key)) {
                matched = true;
                this.check(data[key], schema.properties[key], childPath, errors);
            }

            if (schema.patternProperties) {
                Object.keys(schema.patternProperties).forEach((pattern) => {
                    if (new RegExp(pattern).test(key)) {
                        matched = true;
                        this.check(data[key], schema.patternProperties[pattern], childPath, errors);
                    }
                });
            }

            if (!matched && schema.additionalProperties !== undefined) {
                if (schema.additionalProperties === false) {
                    const known = Object.keys(schema.properties || {});
                    const hint = known.length ? ` Known properties: ${known.join(', ')}.` : '';
                    this.push(errors, childPath, `is not a recognized property.${hint}`, null);
                } else {
                    this.check(data[key], schema.additionalProperties, childPath, errors);
                }
            }
        });
    }

    checkOneOf(data, schema, path, errors) {
        const variants = schema.oneOf;
        const discriminator = schema['x-discriminator'];

        if (discriminator && TYPE_CHECKS.object(data)) {
            const key = discriminator.propertyName;
            const tag = data[key];
            const permitted = [];

            const selected = variants.find((variant) => {
                const resolved = variant.$ref ? this.resolveRef(variant.$ref) : variant;
                const tagSchema = (resolved.properties || {})[key];
                if (!tagSchema) return false;
                if (Object.prototype.hasOwnProperty.call(tagSchema, 'const')) {
                    permitted.push(tagSchema.const);
                    return tagSchema.const === tag;
                }
                if (Array.isArray(tagSchema.enum)) {
                    permitted.push(...tagSchema.enum);
                    return tagSchema.enum.includes(tag);
                }
                return false;
            });

            if (!selected) {
                this.push(
                    errors,
                    `${path}/${key}`,
                    `${tag === undefined ? 'is required and ' : `is ${describe(tag)}, which `}`
                    + `must be one of: ${permitted.map((v) => JSON.stringify(v)).join(', ')}.`,
                    null,
                );
                return;
            }

            this.check(data, selected, path, errors);
            return;
        }

        // Undiscriminated union: report against the closest-fitting variant so
        // the caller sees a real message instead of a pile of dead branches.
        const attempts = variants.map((variant) => {
            const collected = [];
            this.check(data, variant, path, collected);
            const resolved = variant.$ref ? this.resolveRef(variant.$ref) : variant;
            return { errors: collected, typeMatches: variantAcceptsType(resolved, data) };
        });

        if (attempts.some((a) => a.errors.length === 0)) return;

        const preferred = attempts.filter((a) => a.typeMatches);
        const pool = preferred.length ? preferred : attempts;
        const best = pool.reduce((a, b) => (a.errors.length <= b.errors.length ? a : b));
        best.errors.forEach((e) => errors.push(e));
    }
}

function variantAcceptsType(schema, data) {
    if (!schema || schema.type === undefined) return true;
    const allowed = Array.isArray(schema.type) ? schema.type : [schema.type];
    return allowed.some((t) => TYPE_CHECKS[t] && TYPE_CHECKS[t](data));
}

function deepEqual(a, b) {
    if (a === b) return true;
    if (typeOf(a) !== typeOf(b)) return false;
    if (Array.isArray(a)) {
        return a.length === b.length && a.every((item, i) => deepEqual(item, b[i]));
    }
    if (a !== null && typeof a === 'object') {
        const ka = Object.keys(a);
        const kb = Object.keys(b);
        return ka.length === kb.length && ka.every((k) => deepEqual(a[k], b[k]));
    }
    return false;
}

/**
 * Validate `spec` against `schema`.
 * Returns an array of { path, message }; empty means valid.
 */
function validateAgainstSchema(spec, schema) {
    return new Validator(schema).validate(spec);
}

/**
 * Cross-reference checks that JSON Schema cannot express.
 * Runs after schema validation and uses the same error shape.
 */
function validateSemantics(spec) {
    const errors = [];
    const widgets = Array.isArray(spec.widgets) ? spec.widgets : [];
    const containers = Array.isArray(spec.containers) ? spec.containers : null;
    const sampleKeys = new Set(Object.keys(spec.sampleData || {}));

    const containerIds = new Set();
    (containers || []).forEach((container, i) => {
        if (containerIds.has(container.id)) {
            errors.push({
                path: `/containers/${i}/id`,
                message: `duplicates container id "${container.id}"; container ids must be unique.`,
            });
        }
        containerIds.add(container.id);
    });

    const widgetIds = new Set();
    const usedContainers = new Set();

    widgets.forEach((widget, i) => {
        if (widgetIds.has(widget.id)) {
            errors.push({
                path: `/widgets/${i}/id`,
                message: `duplicates widget id "${widget.id}"; each widget needs its own mount element.`,
            });
        }
        widgetIds.add(widget.id);

        if (containers) {
            if (widget.containerId === undefined) {
                errors.push({
                    path: `/widgets/${i}/containerId`,
                    message: 'is required because the spec declares containers. '
                        + `Use one of: ${Array.from(containerIds).join(', ')}.`,
                });
            } else if (!containerIds.has(widget.containerId)) {
                errors.push({
                    path: `/widgets/${i}/containerId`,
                    message: `references undeclared container "${widget.containerId}". `
                        + `Declared containers: ${Array.from(containerIds).join(', ') || '(none)'}.`,
                });
            } else {
                usedContainers.add(widget.containerId);
            }
        } else if (widget.containerId !== undefined) {
            errors.push({
                path: `/widgets/${i}/containerId`,
                message: `references container "${widget.containerId}", but the spec declares no containers. `
                    + 'Add a "containers" array or drop containerId.',
            });
        }

        if (widget.dataKey !== undefined && !sampleKeys.has(widget.dataKey)) {
            errors.push({
                path: `/widgets/${i}/dataKey`,
                message: `references "${widget.dataKey}", which is not a key of sampleData. `
                    + `Available keys: ${Array.from(sampleKeys).join(', ') || '(sampleData is empty)'}.`,
            });
        }

        if (widget.dataKey !== undefined && sampleKeys.has(widget.dataKey)) {
            const value = spec.sampleData[widget.dataKey];
            const wantsArray = widget.type !== 'dxForm';
            if (wantsArray && !Array.isArray(value)) {
                errors.push({
                    path: `/sampleData/${widget.dataKey}`,
                    message: `must be an array because widget "${widget.id}" (${widget.type}) binds it as a dataSource.`,
                });
            }
            if (!wantsArray && Array.isArray(value)) {
                errors.push({
                    path: `/sampleData/${widget.dataKey}`,
                    message: `must be an object because widget "${widget.id}" (dxForm) binds it as formData.`,
                });
            }
        }
    });

    (containers || []).forEach((container, i) => {
        if (!usedContainers.has(container.id)) {
            errors.push({
                path: `/containers/${i}/id`,
                message: `container "${container.id}" holds no widgets; every declared container must be used.`,
            });
        }
    });

    const outputs = spec.outputFiles || {};
    const byName = {};
    Object.keys(outputs).forEach((slot) => {
        const name = outputs[slot];
        if (byName[name]) {
            errors.push({
                path: `/outputFiles/${slot}`,
                message: `"${name}" is already used by outputFiles.${byName[name]}; output names must be distinct.`,
            });
        }
        byName[name] = slot;
    });

    return errors;
}

function formatErrors(errors, specPath) {
    const lines = [`Spec validation failed for ${specPath} (${errors.length} error${errors.length === 1 ? '' : 's'}):`];
    errors.forEach((error) => lines.push(`  ${error.path}  ${error.message}`));
    lines.push('Contract: references/dx-page-spec-schema.json');
    return lines.join('\n');
}

module.exports = { validateAgainstSchema, validateSemantics, formatErrors };
