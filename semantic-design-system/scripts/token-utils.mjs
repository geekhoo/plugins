import fs from 'node:fs';
import path from 'node:path';

export function stripJsonComments(input) {
  let output = '';
  let inString = false;
  let escape = false;
  let inLineComment = false;
  let inBlockComment = false;

  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    const next = input[i + 1];

    if (inLineComment) {
      if (ch === '\n') {
        inLineComment = false;
        output += ch;
      }
      continue;
    }

    if (inBlockComment) {
      if (ch === '*' && next === '/') {
        inBlockComment = false;
        i++;
      }
      continue;
    }

    if (!inString && ch === '/' && next === '/') {
      inLineComment = true;
      i++;
      continue;
    }

    if (!inString && ch === '/' && next === '*') {
      inBlockComment = true;
      i++;
      continue;
    }

    output += ch;

    if (inString) {
      if (escape) escape = false;
      else if (ch === '\\') escape = true;
      else if (ch === '"') inString = false;
    } else if (ch === '"') {
      inString = true;
    }
  }

  return output;
}

export function readJsonLike(file) {
  const raw = fs.readFileSync(file, 'utf8');
  return JSON.parse(stripJsonComments(raw));
}

export function walkFiles(dir, predicate = () => true) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  const stack = [dir];
  while (stack.length) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'dist' || entry.name === 'build') continue;
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (predicate(full)) out.push(full);
    }
  }
  return out.sort();
}

export function deepMerge(target, source) {
  if (!isPlainObject(source)) return source;
  const out = isPlainObject(target) ? { ...target } : {};
  for (const [key, value] of Object.entries(source)) {
    if (isPlainObject(value) && isPlainObject(out[key])) out[key] = deepMerge(out[key], value);
    else out[key] = value;
  }
  return out;
}

export function isPlainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value);
}

// Single, standardized location for design-token source files, resolved relative
// to the working/project folder (PLUGIN_PROJECT_DIR, CLAUDE_PROJECT_DIR, or cwd). There is intentionally
// no per-install override env var: scripts default here, and an explicit CLI/MCP
// argument is the only override.
export const DEFAULT_TOKEN_DIR = 'design/tokens';

// DTCG 2025.10 recommends the `.tokens` and `.tokens.json` extensions. We also
// accept `.tokens.jsonc` so authored files may carry comments. We intentionally
// do NOT match bare `.json`/`.jsonc`, so stray files such as package.json or
// tsconfig.json living under the token directory are never parsed as tokens.
export const TOKEN_FILE_RE = /\.tokens(\.jsonc?)?$/;

// Files living under a `themes/` directory are treated as theme/mode overrides
// rather than base tokens, so they are emitted into themed selectors instead of
// corrupting the base `:root`.
export function isThemeFile(file) {
  return /[\\/]themes[\\/]/.test(file);
}

export function loadTokenTree(tokenDir, predicate = f => TOKEN_FILE_RE.test(f)) {
  const files = walkFiles(tokenDir, predicate);
  let tree = {};
  for (const file of files) {
    try {
      tree = deepMerge(tree, readJsonLike(file));
    } catch (error) {
      error.message = `${file}: ${error.message}`;
      throw error;
    }
  }
  return { tree, files };
}

export function collectTokens(node, options = {}) {
  const tokens = new Map();
  const errors = [];
  const aliases = [];
  const inheritedType = options.inheritedType;
  const pathParts = options.pathParts || [];

  function visit(value, parts, typeFromParent) {
    if (!isPlainObject(value)) return;
    const currentType = typeof value.$type === 'string' ? value.$type : typeFromParent;

    if (Object.prototype.hasOwnProperty.call(value, '$value')) {
      const tokenPath = parts.join('.');
      tokens.set(tokenPath, { path: tokenPath, node: value, type: currentType });
      if (!currentType) errors.push(`${tokenPath}: missing $type directly or inherited from parent group`);
      for (const ref of findAliasRefs(value.$value)) aliases.push({ from: tokenPath, to: ref });
      return;
    }

    for (const [key, child] of Object.entries(value)) {
      if (key.startsWith('$')) continue;
      visit(child, [...parts, key], currentType);
    }
  }

  visit(node, pathParts, inheritedType);
  return { tokens, errors, aliases };
}

export function findAliasRefs(value) {
  const refs = [];
  const scan = v => {
    if (typeof v === 'string') {
      const re = /\{([^}]+)\}/g;
      let match;
      while ((match = re.exec(v))) refs.push(match[1].trim());
    } else if (Array.isArray(v)) {
      for (const item of v) scan(item);
    } else if (isPlainObject(v)) {
      for (const item of Object.values(v)) scan(item);
    }
  };
  scan(value);
  return refs;
}

export function resolveAlias(value, tokens, seen = []) {
  if (typeof value === 'string') {
    const full = value.match(/^\{([^}]+)\}$/);
    if (full) {
      const ref = full[1].trim();
      if (seen.includes(ref)) throw new Error(`Circular alias: ${[...seen, ref].join(' -> ')}`);
      const target = tokens.get(ref);
      if (!target) throw new Error(`Unresolved alias: ${ref}`);
      return resolveAlias(target.node.$value, tokens, [...seen, ref]);
    }
    return value.replace(/\{([^}]+)\}/g, (_, ref) => {
      const target = tokens.get(ref.trim());
      if (!target) throw new Error(`Unresolved alias: ${ref.trim()}`);
      return tokenValueToCss(resolveAlias(target.node.$value, tokens, [...seen, ref.trim()]));
    });
  }

  if (Array.isArray(value)) return value.map(v => resolveAlias(v, tokens, seen));
  if (isPlainObject(value)) {
    const out = {};
    for (const [key, child] of Object.entries(value)) out[key] = resolveAlias(child, tokens, seen);
    return out;
  }

  return value;
}

export function tokenValueToCss(value) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (Array.isArray(value)) return value.join(', ');
  if (!isPlainObject(value)) return String(value);

  if ('hex' in value) {
    if (typeof value.alpha === 'number' && value.alpha < 1) {
      const [r, g, b] = hexToRgb(value.hex);
      return `rgba(${r}, ${g}, ${b}, ${round(value.alpha)})`;
    }
    return value.hex;
  }

  if ('value' in value && 'unit' in value) return `${round(value.value)}${value.unit}`;

  if ('duration' in value && 'timingFunction' in value) {
    const duration = tokenValueToCss(value.duration);
    const delay = value.delay ? tokenValueToCss(value.delay) : '0ms';
    const easing = tokenValueToCss(value.timingFunction);
    return `${duration} ${easing} ${delay}`;
  }

  if ('offsetX' in value && 'offsetY' in value && 'blur' in value) {
    const color = tokenValueToCss(value.color || 'rgba(0,0,0,.16)');
    const x = tokenValueToCss(value.offsetX);
    const y = tokenValueToCss(value.offsetY);
    const blur = tokenValueToCss(value.blur);
    const spread = value.spread ? tokenValueToCss(value.spread) : '0px';
    return `${x} ${y} ${blur} ${spread} ${color}`;
  }

  if ('fontFamily' in value || 'fontSize' in value || 'fontWeight' in value) return JSON.stringify(value);

  return JSON.stringify(value);
}

function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  const full = clean.length === 3 ? clean.split('').map(c => c + c).join('') : clean;
  const int = Number.parseInt(full, 16);
  return [(int >> 16) & 255, (int >> 8) & 255, int & 255];
}

function round(value) {
  if (typeof value !== 'number') return value;
  return Number.parseFloat(value.toFixed(4));
}

export function cssVarName(tokenPath, prefix = 'ds') {
  const parts = tokenPath.split('.');
  if (parts[0] === 'semantic') parts.shift();
  if (parts[0] === 'component') {
    return `--${prefix}-${parts.join('-')}`.replace(/\./g, '-');
  }
  if (parts[0] === 'primitive') parts.shift();
  return `--${prefix}-${parts.join('-')}`.replace(/\./g, '-');
}

export function projectPath(input, fallback = '.') {
  const base =
    process.env.PLUGIN_PROJECT_DIR ||
    process.env.CODEX_PROJECT_DIR ||
    process.env.CLAUDE_PROJECT_DIR ||
    process.cwd();
  const value = input || fallback;
  return path.isAbsolute(value) ? value : path.join(base, value);
}
