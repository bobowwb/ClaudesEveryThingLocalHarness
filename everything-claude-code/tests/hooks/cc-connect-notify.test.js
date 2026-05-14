/**
 * Tests for scripts/hooks/cc-connect-notify.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOOK = require('../../scripts/hooks/cc-connect-notify');

function createTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'cc-connect-notify-'));
}

function cleanup(dirPath) {
  fs.rmSync(dirPath, { recursive: true, force: true });
}

function createCcConnectShim(binDir, logFile) {
  fs.mkdirSync(binDir, { recursive: true });
  const shimJs = path.join(binDir, 'cc-connect-shim.js');
  fs.writeFileSync(
    shimJs,
    [
      "const fs = require('fs');",
      "let input = '';",
      "process.stdin.setEncoding('utf8');",
      "process.stdin.on('data', chunk => { input += chunk; });",
      "process.stdin.on('end', () => {",
      `  fs.appendFileSync(${JSON.stringify(logFile)}, JSON.stringify({ args: process.argv.slice(2), input }) + '\\n');`,
      '});'
    ].join('\n')
  );

  if (process.platform === 'win32') {
    const shimCmd = path.join(binDir, 'cc-connect.cmd');
    fs.writeFileSync(shimCmd, `@echo off\r\nnode "${shimJs}" %*\r\n`);
    return shimCmd;
  }

  const shimPath = path.join(binDir, 'cc-connect');
  fs.writeFileSync(shimPath, `#!/usr/bin/env node\nrequire(${JSON.stringify(shimJs)});\n`);
  fs.chmodSync(shimPath, 0o755);
  return shimPath;
}

function withPath(binDir, env = {}) {
  const pathKey = Object.keys(process.env).find(key => key.toLowerCase() === 'path') || (process.platform === 'win32' ? 'Path' : 'PATH');
  const nextPath = `${binDir}${path.delimiter}${process.env[pathKey] || process.env.PATH || ''}`;
  return {
    ...process.env,
    ...env,
    [pathKey]: nextPath,
    PATH: nextPath
  };
}

function readLog(logFile) {
  if (!fs.existsSync(logFile)) return [];
  return fs
    .readFileSync(logFile, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

function test(name, fn) {
  try {
    fn();
    console.log(`  \u2713 ${name}`);
    return true;
  } catch (error) {
    console.log(`  \u2717 ${name}`);
    console.log(`    Error: ${error.message}`);
    return false;
  }
}

function runTests() {
  console.log('\n=== Testing cc-connect-notify.js ===\n');

  let passed = 0;
  let failed = 0;

  if (test('does nothing unless explicitly enabled', () => {
    const tempDir = createTempDir();
    const logFile = path.join(tempDir, 'calls.log');
    const binDir = path.join(tempDir, 'bin');
    createCcConnectShim(binDir, logFile);

    try {
      const raw = JSON.stringify({ last_assistant_message: 'Done with task' });
      const output = HOOK.run(raw, { env: withPath(binDir), isLocked: () => true });
      assert.strictEqual(output, raw);
      assert.deepStrictEqual(readLog(logFile), []);
    } finally {
      cleanup(tempDir);
    }
  })) passed++; else failed++;

  if (test('skips when enabled but workstation is not locked', () => {
    const tempDir = createTempDir();
    const logFile = path.join(tempDir, 'calls.log');
    const binDir = path.join(tempDir, 'bin');
    createCcConnectShim(binDir, logFile);

    try {
      const raw = JSON.stringify({ last_assistant_message: 'Done with task' });
      const output = HOOK.run(raw, {
        env: withPath(binDir, { ECC_CC_CONNECT_NOTIFY: '1' }),
        isLocked: () => false
      });
      assert.strictEqual(output, raw);
      assert.deepStrictEqual(readLog(logFile), []);
    } finally {
      cleanup(tempDir);
    }
  })) passed++; else failed++;

  if (test('sends summary through cc-connect stdin when forced always', () => {
    const tempDir = createTempDir();
    const logFile = path.join(tempDir, 'calls.log');
    const binDir = path.join(tempDir, 'bin');
    const shim = createCcConnectShim(binDir, logFile);

    try {
      const raw = JSON.stringify({
        cwd: 'C:/repo',
        last_assistant_message: 'Implemented the harness fix.\n\nDetails omitted.'
      });
      const output = HOOK.run(raw, {
        env: withPath(binDir, {
          ECC_CC_CONNECT_NOTIFY: '1',
          ECC_CC_CONNECT_NOTIFY_WHEN: 'always',
          ECC_CC_CONNECT_PROJECT: 'ecc',
          ECC_CC_CONNECT_SESSION: 'weixin:user',
          ECC_CC_CONNECT_BIN: shim
        }),
        isLocked: () => false
      });
      const calls = readLog(logFile);
      assert.strictEqual(output, raw);
      assert.strictEqual(calls.length, 1);
      assert.deepStrictEqual(calls[0].args, ['send', '--stdin', '-p', 'ecc', '-s', 'weixin:user']);
      assert.ok(calls[0].input.includes('Claude Code result'));
      assert.ok(calls[0].input.includes('Implemented the harness fix.'));
      assert.ok(calls[0].input.includes('C:/repo'));
    } finally {
      cleanup(tempDir);
    }
  })) passed++; else failed++;

  if (test('truncates long summaries before sending', () => {
    const tempDir = createTempDir();
    const logFile = path.join(tempDir, 'calls.log');
    const binDir = path.join(tempDir, 'bin');
    const shim = createCcConnectShim(binDir, logFile);

    try {
      const raw = JSON.stringify({ last_assistant_message: 'x'.repeat(5000) });
      HOOK.run(raw, {
        env: withPath(binDir, {
          ECC_CC_CONNECT_NOTIFY: '1',
          ECC_CC_CONNECT_NOTIFY_WHEN: 'always',
          ECC_CC_CONNECT_MAX_CHARS: '120',
          ECC_CC_CONNECT_BIN: shim
        }),
        isLocked: () => true
      });
      const [call] = readLog(logFile);
      assert.ok(call.input.length < 260, `Expected bounded message, got ${call.input.length}`);
      assert.ok(call.input.includes('...'));
    } finally {
      cleanup(tempDir);
    }
  })) passed++; else failed++;

  console.log(`\nResults: Passed: ${passed}, Failed: ${failed}`);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
