/**
 * E2E: Hello World button test
 *
 * TDD spec — written before the implementation exists.
 * Run with: node tests/e2e/hello-world.test.js
 *
 * Browser steps (executed via Playwright MCP):
 *   1. Open hello-world.html
 *   2. Click the "Hello World" button
 *   3. Assert the text "Hello World" appears in #output
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const HTML_FILE = path.resolve(__dirname, 'hello-world.html');
const FILE_URL = 'file:///' + HTML_FILE.replace(/\\/g, '/');

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    return true;
  } catch (err) {
    console.log(`  ✗ ${name}: ${err.message}`);
    return false;
  }
}

let passed = 0;
let failed = 0;

console.log('\n=== E2E: Hello World button ===\n');
console.log('Static checks (pre-browser):');

// ── RED: these all fail before hello-world.html exists ─────────────────────

if (test('hello-world.html exists', () => {
  assert.ok(fs.existsSync(HTML_FILE), `missing: ${HTML_FILE}`);
})) passed++; else failed++;

if (test('page contains a button with id="btn"', () => {
  assert.ok(fs.existsSync(HTML_FILE), 'file missing');
  const html = fs.readFileSync(HTML_FILE, 'utf8');
  assert.ok(/<button[^>]+id=["']btn["']/.test(html), 'no <button id="btn"> found');
})) passed++; else failed++;

if (test('page contains an output element with id="output"', () => {
  assert.ok(fs.existsSync(HTML_FILE), 'file missing');
  const html = fs.readFileSync(HTML_FILE, 'utf8');
  assert.ok(/id=["']output["']/.test(html), 'no element with id="output" found');
})) passed++; else failed++;

if (test('button click handler sets output text to "Hello World"', () => {
  assert.ok(fs.existsSync(HTML_FILE), 'file missing');
  const html = fs.readFileSync(HTML_FILE, 'utf8');
  assert.ok(
    /textContent\s*=\s*['"]Hello World['"]/.test(html),
    'handler does not assign textContent = "Hello World"'
  );
})) passed++; else failed++;

console.log('\nBrowser interaction (run Playwright MCP steps manually):');
console.log(`  URL: ${FILE_URL}`);
console.log('  Step 1: navigate to hello-world.html');
console.log('  Step 2: click button#btn');
console.log('  Step 3: assert #output text === "Hello World"');

console.log(`\nPassed: ${passed}`);
console.log(`Failed: ${failed}`);

process.exit(failed > 0 ? 1 : 0);
