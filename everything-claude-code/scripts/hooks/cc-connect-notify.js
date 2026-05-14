#!/usr/bin/env node
/**
 * cc-connect Notification Hook (Stop)
 *
 * Opt-in Stop hook that forwards a concise Claude Code result summary to an
 * active cc-connect session. By default it only sends while Windows is locked.
 *
 * Environment:
 *   ECC_CC_CONNECT_NOTIFY=1
 *   ECC_CC_CONNECT_NOTIFY_WHEN=locked|always   (default: locked)
 *   ECC_CC_CONNECT_PROJECT=<name>              (optional)
 *   ECC_CC_CONNECT_SESSION=<key>               (optional)
 *   ECC_CC_CONNECT_MAX_CHARS=<n>               (default: 1200)
 */

'use strict';

const { spawnSync } = require('child_process');
const { log } = require('../lib/utils');

const DEFAULT_MAX_CHARS = 1200;

function enabled(env = process.env) {
  return /^(1|true|yes|on)$/i.test(String(env.ECC_CC_CONNECT_NOTIFY || '').trim());
}

function parseMaxChars(env = process.env) {
  const parsed = Number.parseInt(env.ECC_CC_CONNECT_MAX_CHARS || '', 10);
  if (!Number.isFinite(parsed) || parsed < 80) {
    return DEFAULT_MAX_CHARS;
  }
  return Math.min(parsed, 8000);
}

function truncate(text, maxChars) {
  const value = String(text || '').trim();
  if (value.length <= maxChars) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxChars - 3)).trimEnd()}...`;
}

function extractSummary(input, maxChars) {
  const candidates = [
    input?.last_assistant_message,
    input?.result,
    input?.summary,
    input?.message
  ];
  const summary = candidates.find(value => typeof value === 'string' && value.trim());
  return truncate(summary || 'Claude Code finished responding.', maxChars);
}

function isWindowsLocked() {
  if (process.platform !== 'win32') {
    return false;
  }

  const result = spawnSync(
    'powershell.exe',
    ['-NoProfile', '-Command', "[bool](Get-Process LogonUI -ErrorAction SilentlyContinue)"],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 3000 }
  );

  if (result.error || result.status !== 0) {
    return false;
  }

  return String(result.stdout || '').trim().toLowerCase() === 'true';
}

function shouldSend(env = process.env, locked = isWindowsLocked()) {
  if (!enabled(env)) {
    return false;
  }

  const mode = String(env.ECC_CC_CONNECT_NOTIFY_WHEN || 'locked').trim().toLowerCase();
  if (mode === 'always') {
    return true;
  }
  return locked;
}

function buildMessage(input, env = process.env) {
  const maxChars = parseMaxChars(env);
  const summary = extractSummary(input, maxChars);
  const cwd = typeof input?.cwd === 'string' && input.cwd.trim() ? input.cwd.trim() : process.cwd();
  const session = typeof input?.session_id === 'string' && input.session_id.trim() ? `\nSession: ${input.session_id.trim()}` : '';
  return `Claude Code result\nProject: ${cwd}${session}\n\n${summary}`;
}

function buildArgs(env = process.env) {
  const args = ['send', '--stdin'];
  if (env.ECC_CC_CONNECT_PROJECT && env.ECC_CC_CONNECT_PROJECT.trim()) {
    args.push('-p', env.ECC_CC_CONNECT_PROJECT.trim());
  }
  if (env.ECC_CC_CONNECT_SESSION && env.ECC_CC_CONNECT_SESSION.trim()) {
    args.push('-s', env.ECC_CC_CONNECT_SESSION.trim());
  }
  return args;
}

function sendMessage(message, env = process.env) {
  const command = env.ECC_CC_CONNECT_BIN && env.ECC_CC_CONNECT_BIN.trim()
    ? env.ECC_CC_CONNECT_BIN.trim()
    : 'cc-connect';
  const result = spawnSync(command, buildArgs(env), {
    input: message,
    encoding: 'utf8',
    env,
    shell: process.platform === 'win32',
    stdio: ['pipe', 'pipe', 'pipe'],
    timeout: 10000
  });

  if (result.error || result.status !== 0) {
    const reason = result.error ? result.error.message : (result.stderr || `exit ${result.status}`);
    log(`[CcConnectNotify] cc-connect send failed: ${String(reason).trim()}`);
    return false;
  }

  return true;
}

function run(raw, options = {}) {
  const env = options.env || process.env;
  const isLocked = typeof options.isLocked === 'function' ? options.isLocked : isWindowsLocked;

  try {
    const input = raw && raw.trim() ? JSON.parse(raw) : {};
    if (enabled(env) && shouldSend(env, isLocked())) {
      sendMessage(buildMessage(input, env), env);
    }
  } catch (error) {
    log(`[CcConnectNotify] Error: ${error.message}`);
  }

  return raw;
}

module.exports = {
  buildArgs,
  buildMessage,
  enabled,
  extractSummary,
  isWindowsLocked,
  run,
  shouldSend,
  truncate
};

if (require.main === module) {
  const MAX_STDIN = 1024 * 1024;
  let data = '';

  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => {
    if (data.length < MAX_STDIN) {
      data += chunk.substring(0, MAX_STDIN - data.length);
    }
  });
  process.stdin.on('end', () => {
    const output = run(data);
    if (output) process.stdout.write(output);
  });
}
