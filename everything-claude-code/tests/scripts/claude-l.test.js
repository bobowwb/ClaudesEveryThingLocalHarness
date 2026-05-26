/**
 * Static safety tests for scripts/claude-l.cmd
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'claude-l.cmd');

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
  console.log('\n=== Testing claude-l.cmd ===\n');

  let passed = 0;
  let failed = 0;
  const source = fs.readFileSync(SCRIPT, 'utf8');

  if (test('does not embed proxy secrets', () => {
    assert.ok(!/sk-[A-Za-z0-9_-]{8,}/.test(source), 'Should not contain API keys');
    assert.ok(!/Bearer\s+[A-Za-z0-9._-]{16,}/.test(source), 'Should not contain bearer tokens');
  })) passed++; else failed++;

  if (test('defaults model without prompting every launch', () => {
    assert.ok(source.includes('CLAUDE_L_PROMPT_MODEL'), 'Should expose opt-in prompt flag');
    assert.ok(source.includes('CLAUDE_L_DEFAULT_MODEL=anthropic--claude-4.7-opus'), 'Should default to Claude 4.7 Opus proxy model');
    assert.ok(source.includes('set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"'), 'Should set default model automatically');
  })) passed++; else failed++;

  if (test('uses proxy token auth without API key conflict', () => {
    assert.ok(source.includes('set "ANTHROPIC_BASE_URL=http://localhost:6655/anthropic"'), 'Should force the local proxy base URL');
    assert.ok(source.includes('set "ANTHROPIC_API_KEY="'), 'Should clear API key before launching Claude');
    assert.ok(!source.includes('set "ANTHROPIC_API_KEY=%ANTHROPIC_AUTH_TOKEN%"'), 'Should not export both token and API key');
    assert.ok(source.includes('set "ANTHROPIC_CUSTOM_HEADERS=Authorization: Bearer %ANTHROPIC_AUTH_TOKEN%"'), 'Should send bearer token to proxy');
  })) passed++; else failed++;

  if (test('checks claude command availability before launch', () => {
    assert.ok(source.includes('where claude'), 'Should check for claude on PATH');
    assert.ok(source.includes('Claude CLI not found'), 'Should print actionable missing CLI error');
  })) passed++; else failed++;

  if (test('propagates claude exit code', () => {
    assert.ok(source.includes('set "CLAUDE_L_EXIT=%ERRORLEVEL%"'), 'Should capture claude exit code');
    assert.ok(source.includes('exit /b %CLAUDE_L_EXIT%'), 'Should exit with claude status');
  })) passed++; else failed++;

  console.log(`\nResults: Passed: ${passed}, Failed: ${failed}`);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
