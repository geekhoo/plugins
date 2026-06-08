#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

function parseArgs(argv) {
  const args = {
    viewports: [],
    out: "browser-probe-artifacts",
    timeoutMs: 30000,
    waitUntil: "domcontentloaded",
    settleMs: 0,
    expectText: [],
    selectorExists: [],
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--url") {
      args.url = next;
      i += 1;
    } else if (arg === "--viewport") {
      args.viewports.push(parseViewport(next));
      i += 1;
    } else if (arg === "--out") {
      args.out = next;
      i += 1;
    } else if (arg === "--timeout-ms") {
      args.timeoutMs = Number(next);
      i += 1;
    } else if (arg === "--wait-until") {
      args.waitUntil = next;
      i += 1;
    } else if (arg === "--settle-ms") {
      args.settleMs = Number(next);
      i += 1;
    } else if (arg === "--expect-text") {
      args.expectText.push(next);
      i += 1;
    } else if (arg === "--selector-exists") {
      args.selectorExists.push(next);
      i += 1;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.url) {
    throw new Error("Missing required --url");
  }
  if (args.viewports.length === 0) {
    args.viewports.push(parseViewport("1440x900"));
  }
  if (!Number.isFinite(args.timeoutMs) || args.timeoutMs <= 0) {
    throw new Error("--timeout-ms must be a positive number");
  }
  if (!["commit", "domcontentloaded", "load", "networkidle"].includes(args.waitUntil)) {
    throw new Error('--wait-until must be one of: commit, domcontentloaded, load, networkidle');
  }
  if (!Number.isFinite(args.settleMs) || args.settleMs < 0) {
    throw new Error("--settle-ms must be zero or a positive number");
  }
  return args;
}

function parseViewport(value) {
  const match = /^(\d+)x(\d+)$/.exec(value || "");
  if (!match) {
    throw new Error(`Invalid viewport "${value}". Use WIDTHxHEIGHT, for example 1440x900.`);
  }
  return {
    width: Number(match[1]),
    height: Number(match[2]),
    label: `${match[1]}x${match[2]}`,
  };
}

function printHelp() {
  console.log(`Usage:
  node scripts/browser_probe.mjs --url <url> [--viewport 1440x900] [--out artifacts/browser-probe]
    [--wait-until domcontentloaded|load|networkidle|commit] [--settle-ms 500]
    [--expect-text "Dashboard"] [--selector-exists "#app"]

Captures screenshot, console messages, page errors, failed requests, 4xx/5xx responses, and basic DOM facts.
Requires playwright-core or playwright plus Chrome. Set CHROME_PATH for nonstandard Chrome installs.`);
}

async function importPlaywright() {
  try {
    return await import("playwright-core");
  } catch (coreError) {
    try {
      return await import("playwright");
    } catch {
      throw new Error(
        `Missing Playwright package. Install playwright-core or playwright, or use the Browser plugin. First error: ${coreError.message}`,
      );
    }
  }
}

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function findChromeExecutable() {
  const candidates = [
    process.env.CHROME_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (await pathExists(candidate)) {
      return candidate;
    }
  }
  return null;
}

async function runProbe({ chromium }, args, viewport) {
  const consoleMessages = [];
  const pageErrors = [];
  const requestFailures = [];
  const failedResponses = [];
  const chromePath = await findChromeExecutable();
  if (!chromePath) {
    throw new Error("Chrome executable not found. Install Chrome or set CHROME_PATH.");
  }

  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
  });

  try {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
    });
    const page = await context.newPage();

    page.on("console", (message) => {
      consoleMessages.push({
        type: message.type(),
        text: message.text(),
      });
    });
    page.on("pageerror", (error) => {
      pageErrors.push(error.message);
    });
    page.on("requestfailed", (request) => {
      requestFailures.push({
        url: request.url(),
        method: request.method(),
        failure: request.failure()?.errorText || "unknown",
      });
    });
    page.on("response", (response) => {
      if (response.status() >= 400) {
        failedResponses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        });
      }
    });

    const response = await page.goto(args.url, {
      waitUntil: args.waitUntil,
      timeout: args.timeoutMs,
    });
    if (args.settleMs > 0) {
      await page.waitForTimeout(args.settleMs);
    }

    const safeUrl = args.url.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").slice(0, 60);
    const baseName = `${safeUrl || "page"}-${viewport.label}`;
    const screenshotPath = path.join(args.out, `${baseName}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    const domFacts = await page.evaluate(
      ({ expectText, selectorExists }) => {
        const headings = Array.from(document.querySelectorAll("h1,h2"))
          .slice(0, 10)
          .map((node) => ({
            tag: node.tagName.toLowerCase(),
            text: (node.textContent || "").trim().slice(0, 160),
          }));
        const bodyText = document.body?.innerText || "";
        return {
          title: document.title,
          url: location.href,
          bodyTextLength: bodyText.length,
          linkCount: document.links.length,
          imageCount: document.images.length,
          formCount: document.forms.length,
          headings,
          expectations: {
            expectedText: expectText.map((text) => ({
              text,
              found: bodyText.includes(text),
            })),
            selectorExists: selectorExists.map((selector) => {
              try {
                return {
                  selector,
                  found: Boolean(document.querySelector(selector)),
                };
              } catch (error) {
                return {
                  selector,
                  found: false,
                  error: error.message,
                };
              }
            }),
          },
        };
      },
      {
        expectText: args.expectText,
        selectorExists: args.selectorExists,
      },
    );

    await context.close();
    const failedExpectations = [
      ...domFacts.expectations.expectedText
        .filter((expectation) => !expectation.found)
        .map((expectation) => `Missing expected text: ${expectation.text}`),
      ...domFacts.expectations.selectorExists
        .filter((expectation) => !expectation.found)
        .map((expectation) =>
          expectation.error
            ? `Invalid or missing selector: ${expectation.selector} (${expectation.error})`
            : `Missing selector: ${expectation.selector}`,
        ),
    ];
    return {
      viewport: viewport.label,
      navigationStatus: response?.status() ?? null,
      screenshotPath,
      consoleMessages,
      pageErrors,
      requestFailures,
      failedResponses,
      domFacts,
      failedExpectations,
    };
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  await fs.mkdir(args.out, { recursive: true });
  const playwright = await importPlaywright();
  const results = [];

  for (const viewport of args.viewports) {
    results.push(await runProbe(playwright, args, viewport));
  }

  const report = {
    url: args.url,
    waitUntil: args.waitUntil,
    settleMs: args.settleMs,
    generatedAt: new Date().toISOString(),
    results,
  };
  const reportPath = path.join(args.out, "browser-probe.json");
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ reportPath, results }, null, 2));
  if (results.some((result) => result.failedExpectations.length > 0)) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ error: error.message }, null, 2));
  process.exit(1);
});
